"""Shared lab files are copied into the security ZIP, not downloaded at runtime."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'docs/public/access-log-monitoring/lab'
SECURITY = ROOT / 'docs/public/security-log-monitoring/lab'


def security_assets():
    shared = ['loki.yaml', 'demo.py', 'grafana/provisioning/datasources/loki.yaml',
              'grafana/provisioning/dashboards/local.yaml']
    own = ['README.md', 'security_demo.py', 'grafana/provisioning/alerting/local.json',
           'grafana/dashboards/access-log.json']
    files = {name: (BASE / name).read_bytes() for name in shared}
    files.update({name: (SECURITY / name).read_bytes() for name in own})
    compose = (BASE / 'compose.yaml').read_text(encoding='utf-8')
    compose = compose.replace('name: access-log-lab', 'name: security-log-lab')
    compose = compose.replace('127.0.0.1:18780:8080', '127.0.0.1:18790:8080')
    compose = compose.replace('127.0.0.1:13000:3000', '127.0.0.1:13010:3000')
    compose = compose.replace('/lab/demo.py, server', '/lab/security_demo.py, server')
    compose = compose.replace('/lab/demo.py, traffic', '/lab/security_demo.py, traffic')
    compose = compose.replace('- ./demo.py:/lab/demo.py:ro',
                              '- ./demo.py:/lab/demo.py:ro\n      - ./security_demo.py:/lab/security_demo.py:ro')
    # Traffic and demo read the same scenario file; no public control endpoint.
    compose = compose.replace('    depends_on: [demo]', '      - demo-state:/state\n    depends_on: [demo]')
    files['compose.yaml'] = compose.encode()
    files['config.alloy'] = (BASE / 'config.alloy').read_text(encoding='utf-8').replace(
        'access-log-lab', 'security-log-lab').encode()
    return files
