"""Build/check the provisioned dashboard and rules from shared LogQL expressions."""
import json
from pathlib import Path
import sys

LAB = Path(__file__).resolve().parents[1] / 'docs/public/access-log-monitoring/lab'
STREAM = '{job="access-log-lab"}'
VALID = STREAM + ' | json | __error__=""'
TOTAL = f'sum(count_over_time({VALID} [1m]))'
ERRORS = f'(sum(count_over_time({VALID} | status >= 500 [1m])) or vector(0))'
SLOW = f'(sum(count_over_time({VALID} | request_time_ms >= 1000 [1m])) or vector(0))'
RATE = f'100 * {ERRORS} / {TOTAL}'
ERROR_ALERT = f'(({RATE}) >= bool 20) and ({TOTAL} >= 10)'
SLOW_ALERT = f'({SLOW} >= bool 3) and ({TOTAL} >= 10)'
MISSING = f'{TOTAL} or vector(0)'
P95 = f'quantile_over_time(0.95, {STREAM} | json | unwrap request_time_ms | __error__="" [1m]) by ()'


def rule(uid, title, expression, comparator, threshold, summary):
    return {
        'uid': uid, 'title': title, 'condition': 'B', 'for': '20s',
        'noDataState': 'KeepLast', 'execErrState': 'Error',
        'labels': {'lab': 'access-log'}, 'annotations': {'summary': summary},
        'data': [
            {'refId': 'A', 'datasourceUid': 'loki',
             'relativeTimeRange': {'from': 60, 'to': 0},
             'model': {'refId': 'A', 'expr': expression, 'queryType': 'instant',
                       'instant': True, 'intervalMs': 1000, 'maxDataPoints': 43200,
                       'datasource': {'type': 'loki', 'uid': 'loki'}}},
            {'refId': 'B', 'datasourceUid': '__expr__',
             'relativeTimeRange': {'from': 0, 'to': 0},
             'model': {'refId': 'B', 'type': 'classic_conditions',
                       'datasource': {'type': '__expr__', 'uid': '__expr__'},
                       'conditions': [{'type': 'query', 'query': {'params': ['A']},
                                       'reducer': {'type': 'last', 'params': []},
                                       'evaluator': {'type': comparator, 'params': [threshold]},
                                       'operator': {'type': 'and'}}]}},
        ],
    }


def configs():
    rules = [
        rule('access-errors', 'Access errors', ERROR_ALERT, 'gt', 0,
             '5xx >= 20% with >= 10 completed requests in 1m. Check Explore and request_id.'),
        rule('access-slow', 'Access slow', SLOW_ALERT, 'gt', 0,
             'At least 3 requests >= 1000ms with >= 10 completed requests in 1m.'),
        rule('access-missing', 'Access logs missing', MISSING, 'lt', 1,
             'No valid access logs in 1m. Check traffic, demo, Alloy, Loki and clock.'),
    ]
    alerting = {
        'apiVersion': 1,
        'groups': [{'orgId': 1, 'name': 'access-log', 'folder': 'Access Log Lab',
                    'interval': '10s', 'rules': rules}],
        'contactPoints': [{'orgId': 1, 'name': 'local-webhook', 'receivers': [
            {'uid': 'local-webhook', 'type': 'webhook', 'disableResolveMessage': False,
             'settings': {'url': 'http://notification-sink:8081', 'httpMethod': 'POST'}}]}],
        'policies': [{'orgId': 1, 'receiver': 'local-webhook',
                      'group_by': ['alertname'], 'group_wait': '5s',
                      'group_interval': '10s', 'repeat_interval': '1h'}],
    }
    panels = []
    for index, (title, expression, unit) in enumerate([
        ('Requests / 1m', MISSING, 'short'), ('5xx / 1m (%)', RATE, 'percent'),
        ('Slow requests / 1m (>= 1000 ms)', SLOW, 'short'), ('p95 / 1m (ms)', P95, 'ms'),
    ]):
        panels.append({'id': index + 1, 'title': title, 'type': 'timeseries',
                       'gridPos': {'x': (index % 2) * 12, 'y': (index // 2) * 8, 'w': 12, 'h': 8},
                       'datasource': {'type': 'loki', 'uid': 'loki'},
                       'targets': [{'refId': 'A', 'expr': expression, 'queryType': 'range'}],
                       'fieldConfig': {'defaults': {'unit': unit}, 'overrides': []}})
    panels.append({'id': 5, 'title': 'Access logs', 'type': 'logs',
                   'gridPos': {'x': 0, 'y': 16, 'w': 24, 'h': 10},
                   'datasource': {'type': 'loki', 'uid': 'loki'},
                   'targets': [{'refId': 'A', 'expr': STREAM, 'queryType': 'range'}]})
    dashboard = {'uid': 'access-log-lab', 'title': 'Access Log Lab', 'schemaVersion': 39,
                 'version': 1, 'editable': False, 'timezone': 'browser',
                 'time': {'from': 'now-15m', 'to': 'now'}, 'refresh': '5s', 'panels': panels}
    return {'grafana/provisioning/alerting/local.json': alerting,
            'grafana/dashboards/access-log.json': dashboard}


if __name__ == '__main__':
    for name, value in configs().items():
        path = LAB / name
        text = json.dumps(value, indent=2, ensure_ascii=False) + '\n'
        if '--check' in sys.argv:
            if not path.exists() or path.read_text(encoding='utf-8') != text:
                raise SystemExit(f'{name} differs: run npm run package:access-log')
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding='utf-8', newline='\n')
    print('PASS: Grafana configurations match LogQL sources')
