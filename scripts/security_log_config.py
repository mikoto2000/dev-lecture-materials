"""Security lab resources reuse the verified access lab images and collector."""
import json
from pathlib import Path
import sys

from access_log_config import configs as access_configs, rule

LAB = Path(__file__).resolve().parents[1] / 'docs/public/security-log-monitoring/lab'
STREAM = '{job="security-log-lab"}'
VALID = STREAM + ' | json | __error__=""'
TOTAL = f'sum(count_over_time({VALID} [1m])) or vector(0)'
AUTH_ALL = f'sum by (client_ip, account) (count_over_time({VALID} | event="auth" [1m]))'
AUTH_FAIL = f'sum by (client_ip, account) (count_over_time({VALID} | event="auth" | outcome="failure" [1m]))'
FAILURES = f'({AUTH_FAIL}) or (0 * {AUTH_ALL})'
CLIENT_ALL = f'sum by (client_ip) (count_over_time({VALID} [1m]))'
CLIENT_404 = f'sum by (client_ip) (count_over_time({VALID} | status = 404 [1m]))'
NOT_FOUND = f'({CLIENT_404}) or (0 * {CLIENT_ALL})'


def configs():
    rules = [rule('security-login', 'Repeated login failures', FAILURES, 'gt', 9,
                  '>=10 failed demo logins per client_ip and account in 1m; investigate before blocking.'),
             rule('security-paths', 'Repeated missing paths', NOT_FOUND, 'gt', 19,
                  '>=20 HTTP 404 per client_ip in 1m; inspect path diversity and releases.'),
             rule('security-missing', 'Security logs missing', TOTAL, 'lt', 1,
                  'No valid security lab logs in 1m; check collector and traffic.')]
    for item in rules:
        model = item['data'][1]['model']
        model['type'] = 'threshold'
        model['expression'] = 'A'
        item['labels'] = {'lab': 'security-log'}
    base = access_configs()
    alerting = base['grafana/provisioning/alerting/local.json']
    alerting['groups'][0].update({'name': 'security-log', 'folder': 'Security Log Lab', 'rules': rules})
    dashboard = base['grafana/dashboards/access-log.json']
    dashboard.update({'uid': 'security-log-lab', 'title': 'Security Log Lab'})
    panels = dashboard['panels']
    for panel, title, expr in zip(panels[:4],
                                  ['Requests / 1m', 'Failed logins / 1m', 'HTTP 404 / 1m', 'Successful logins / 1m'],
                                  [TOTAL, FAILURES, NOT_FOUND,
                                   f'sum(count_over_time({VALID} | event="auth" | outcome="success" [1m])) or vector(0)']):
        panel['title'] = title
        panel['targets'][0]['expr'] = expr
        panel['fieldConfig']['defaults']['unit'] = 'short'
        panel['targets'][0]['legendFormat'] = '{{client_ip}} {{account}}'
    panels[4]['targets'][0]['expr'] = STREAM
    return {'grafana/provisioning/alerting/local.json': alerting,
            'grafana/dashboards/access-log.json': dashboard}


if __name__ == '__main__':
    for name, value in configs().items():
        path = LAB / name
        text = json.dumps(value, indent=2) + '\n'
        if '--check' in sys.argv:
            if not path.exists() or path.read_text(encoding='utf-8') != text:
                raise SystemExit('Security Grafana config differs: run npm run package:security-log')
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding='utf-8', newline='\n')
    print('PASS: security Grafana configurations')
