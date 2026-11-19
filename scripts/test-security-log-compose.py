"""Test the standalone learner ZIP, per-dimension alert labels, and false positives."""
import base64
import json
from pathlib import Path
import subprocess
import tempfile
import time
import urllib.parse
import urllib.request
import uuid
import zipfile

from security_log_config import FAILURES, NOT_FOUND, STREAM, TOTAL
from security_log_compose import check

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / 'docs/public/security-log-monitoring/security-log-lab.zip'


def main():
    with tempfile.TemporaryDirectory(prefix='security-log-ci-') as directory:
        with zipfile.ZipFile(ARCHIVE) as archive:
            archive.extractall(directory)
        lab = Path(directory) / 'security-log-lab'
        check(lab)
        file = lab / 'compose.yaml'
        file.write_text(file.read_text().replace('127.0.0.1:13010:3000', '127.0.0.1:0:3000')
                        .replace('127.0.0.1:18790:8080', '127.0.0.1:0:8080'))
        project = 'security-log-ci-' + uuid.uuid4().hex[:10]
        base = ['docker', 'compose', '--project-directory', str(lab), '-p', project]

        def compose(*args, timeout=60):
            result = subprocess.run([*base, *args], capture_output=True, text=True, timeout=timeout)
            if result.returncode:
                raise AssertionError(f'{args}: {result.stdout[-1000:]} {result.stderr[-2000:]}')
            return result.stdout

        def api(path):
            token = base64.b64encode(b'learner:access-log-local-only').decode()
            req = urllib.request.Request(url + path, headers={'Authorization': 'Basic ' + token})
            with urllib.request.urlopen(req, timeout=8) as response:
                return json.load(response)

        def query(expr):
            result = api('/api/datasources/proxy/uid/loki/loki/api/v1/query?' +
                         urllib.parse.urlencode({'query': expr}))
            assert result['status'] == 'success'
            return result['data']['result']

        def state(title):
            groups = api('/api/prometheus/grafana/api/v1/rules')['data']['groups']
            rows = [rule for group in groups for rule in group['rules'] if rule['name'] == title]
            assert len(rows) == 1, groups
            assert rows[0]['health'] == 'ok', rows[0]
            return rows[0]

        def received(title, status):
            payloads = [json.loads(line) for line in compose('logs', '--no-log-prefix', 'notification-sink').splitlines()
                        if line.startswith('{')]
            return [a for row in payloads for a in row['alerts']
                    if a['labels'].get('alertname') == title and a['status'] == status]

        def wait(label, action, seconds=150):
            deadline = time.monotonic() + seconds
            last = None
            while time.monotonic() < deadline:
                try:
                    last = action()
                    if last:
                        print('PASS:', label, flush=True)
                        return last
                except (OSError, ValueError, KeyError, AssertionError) as error:
                    last = str(error)
                time.sleep(3)
            raise AssertionError(f'Timeout {label}: {last}')

        def mode(value):
            compose('exec', '-T', 'demo', 'python', '/lab/security_demo.py', 'mode', value)

        try:
            compose('config', '--quiet')
            compose('up', '-d', timeout=300)
            url = 'http://' + compose('port', 'grafana', '3000').strip()
            wait('security Grafana ready', lambda: api('/api/health')['database'] == 'ok')
            wait('security logs collected', lambda: float(query(TOTAL)[0]['value'][1]) >= 10)
            assert api('/api/dashboards/uid/security-log-lab')['dashboard']['title'] == 'Security Log Lab'
            for scenario, title in [('login', 'Repeated login failures'), ('scan', 'Repeated missing paths'),
                                    ('typo', 'Repeated missing paths')]:
                wait('clean rolling window before ' + scenario,
                     lambda: all(float(row['value'][1]) == 0 for expr in (FAILURES, NOT_FOUND) for row in query(expr)))
                firing_before = len(received(title, 'firing'))
                mode(scenario)
                wait(scenario + ' Firing', lambda: state(title)['state'] == 'firing')
                alerts = wait(scenario + ' firing webhook',
                              lambda: received(title, 'firing') if len(received(title, 'firing')) > firing_before else None)
                assert alerts[-1]['labels'].get('client_ip'), alerts
                if scenario == 'login':
                    assert alerts[-1]['labels'].get('account') == 'demo-user', alerts
                    assert float(query(FAILURES)[0]['value'][1]) >= 10
                else:
                    assert float(query(NOT_FOUND)[0]['value'][1]) >= 20
                    distribution = query('sum by (path) (count_over_time(' + STREAM +
                                         ' | json | status = 404 | __error__="" [1m]))')
                    paths = {item['metric']['path'] for item in distribution}
                    if scenario == 'scan':
                        assert paths == {'/unknown-a', '/unknown-b', '/unknown-c'}, paths
                    else:
                        assert paths == {'/old-help'}, paths
                before = len(received(title, 'resolved'))
                mode('normal')
                wait(scenario + ' recovery', lambda: state(title)['state'] == 'inactive')
                wait(scenario + ' resolved webhook', lambda: len(received(title, 'resolved')) > before)
            print('PASS: standalone ZIP, authentication and path investigation, false positive, notifications', flush=True)
        except BaseException:
            print(compose('logs', '--tail', '10'), flush=True)
            raise
        finally:
            compose('down', '--volumes', '--remove-orphans', timeout=90)


if __name__ == '__main__':
    main()
