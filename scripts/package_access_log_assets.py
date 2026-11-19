"""Shared lab files are copied into the security ZIP, not downloaded at runtime."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'docs/public/access-log-monitoring/lab'
SECURITY = ROOT / 'docs/public/security-log-monitoring/lab'


def replace_required(text, old, new, count=1):
    actual = text.count(old)
    if actual != count:
        raise ValueError(f'Security lab template changed: expected {count} occurrences of {old!r}, found {actual}')
    return text.replace(old, new)


def security_assets():
    shared = ['loki.yaml', 'demo.py', 'grafana/provisioning/datasources/loki.yaml',
              'grafana/provisioning/dashboards/local.yaml']
    own = ['README.md', 'security_demo.py', 'grafana/provisioning/alerting/local.json',
           'grafana/dashboards/access-log.json']
    files = {name: (BASE / name).read_bytes() for name in shared}
    files.update({name: (SECURITY / name).read_bytes() for name in own})
    compose = (BASE / 'compose.yaml').read_text(encoding='utf-8')
    compose = replace_required(compose, 'name: access-log-lab', 'name: security-log-lab')
    compose = replace_required(compose, '127.0.0.1:18780:8080', '127.0.0.1:18790:8080')
    compose = replace_required(compose, '127.0.0.1:13000:3000', '127.0.0.1:13010:3000')
    compose = replace_required(compose, '/lab/demo.py, server', '/lab/security_demo.py, server')
    compose = replace_required(compose, '/lab/demo.py, traffic', '/lab/security_demo.py, traffic')
    compose = replace_required(compose, '- ./demo.py:/lab/demo.py:ro\n',
                               '- ./demo.py:/lab/demo.py:ro\n      - ./security_demo.py:/lab/security_demo.py:ro\n', count=3)
    # Traffic and demo read the same scenario file; no public control endpoint.
    compose = replace_required(compose, '    depends_on: [demo]', '      - demo-state:/state\n    depends_on: [demo]')
    files['compose.yaml'] = compose.encode()
    files['config.alloy'] = replace_required((BASE / 'config.alloy').read_text(encoding='utf-8'),
                                             'access-log-lab', 'security-log-lab').encode()
    return files
