"""Real-stack integration test using an isolated project and random loopback ports."""
from __future__ import annotations

import base64
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

from access_log_config import ERROR_ALERT, MISSING, P95, RATE, SLOW, SLOW_ALERT, STREAM, TOTAL

LAB = Path(__file__).resolve().parents[1] / 'docs/public/access-log-monitoring/lab'
PROJECT = 'access-log-ci-' + uuid.uuid4().hex[:10]
AUTH = base64.b64encode(b'learner:access-log-local-only').decode()


def run_test():
    with tempfile.TemporaryDirectory(prefix='access-log-ci-') as directory:
        target = Path(directory)
        shutil.copytree(LAB, target, dirs_exist_ok=True)
        compose_file = target / 'compose.yaml'
        compose_file.write_text(compose_file.read_text().replace('127.0.0.1:13000:3000', '127.0.0.1:0:3000')
                                .replace('127.0.0.1:18780:8080', '127.0.0.1:0:8080'))
        base = ['docker', 'compose', '--project-directory', str(target), '-p', PROJECT]

        def compose(*args, timeout=60):
            result = subprocess.run([*base, *args], capture_output=True, text=True, timeout=timeout)
            if result.returncode:
                raise AssertionError(f'{args}: {result.stdout[-2000:]} {result.stderr[-4000:]}')
            return result.stdout

        def wait(label, operation, seconds=150):
            deadline = time.monotonic() + seconds
            last = None
            while time.monotonic() < deadline:
                try:
                    last = operation()
                    if last:
                        print('PASS:', label, flush=True)
                        return last
                except (OSError, ValueError, KeyError, AssertionError) as error:
                    last = str(error)
                time.sleep(3)
            raise AssertionError(f'Timeout: {label}: {last}')

        def api(path):
            request = urllib.request.Request(url + path, headers={'Authorization': 'Basic ' + AUTH})
            with urllib.request.urlopen(request, timeout=8) as response:
                return json.load(response)

        def query(expression):
            endpoint = 'query_range' if expression == STREAM else 'query'
            payload = api('/api/datasources/proxy/uid/loki/loki/api/v1/' + endpoint + '?' +
                          urllib.parse.urlencode({'query': expression}))
            assert payload['status'] == 'success', payload
            return payload['data']['result']

        def scalar(expression):
            result = query(expression)
            return float(result[0]['value'][1]) if result else None

        def state(title):
            groups = api('/api/prometheus/grafana/api/v1/rules')['data']['groups']
            rules = [rule for group in groups for rule in group['rules'] if rule['name'] == title]
            assert len(rules) == 1, groups
            assert rules[0]['health'] == 'ok', rules[0]
            return rules[0]['state']

        def notification(title, status):
            lines = compose('logs', '--no-log-prefix', 'notification-sink').splitlines()
            payloads = [json.loads(line) for line in lines if line.startswith('{')]
            return any(alert['labels'].get('alertname') == title and alert['status'] == status
                       for payload in payloads for alert in payload['alerts'])

        def mode(value):
            compose('exec', '-T', 'demo', 'python', '/lab/demo.py', 'mode', value)

        try:
            compose('config', '--quiet')
            compose('up', '-d', timeout=300)
            address = compose('port', 'grafana', '3000').strip()
            assert address.startswith('127.0.0.1:'), address
            url = 'http://' + address
            wait('Grafana initialized', lambda: api('/api/health').get('database') == 'ok')
            wait('Alloy file collection -> Loki -> Grafana query', lambda: (scalar(TOTAL) or 0) >= 10)
            assert scalar(RATE) == 0
            assert scalar(SLOW) == 0
            assert scalar(P95) is not None
            assert query(STREAM)[0]['values']
            dashboard = api('/api/dashboards/uid/access-log-lab')['dashboard']
            assert len(dashboard['panels']) == 5
            wait('normal error rule', lambda: state('Access errors') == 'inactive')
            mode('error')
            wait('5xx alert query crosses threshold', lambda: scalar(ERROR_ALERT) == 1)
            wait('5xx Firing', lambda: state('Access errors') == 'firing')
            wait('5xx webhook firing', lambda: notification('Access errors', 'firing'))
            mode('normal')
            wait('5xx recovery', lambda: state('Access errors') == 'inactive')
            wait('5xx webhook resolved', lambda: notification('Access errors', 'resolved'))
            mode('slow')
            wait('slow alert query crosses threshold', lambda: scalar(SLOW_ALERT) == 1)
            wait('slow Firing', lambda: state('Access slow') == 'firing')
            wait('slow webhook firing', lambda: notification('Access slow', 'firing'))
            assert scalar(RATE) == 0, 'Slow HTTP 200 must not be counted as 5xx'
            mode('normal')
            wait('slow recovery', lambda: state('Access slow') == 'inactive')
            wait('slow webhook resolved', lambda: notification('Access slow', 'resolved'))
            compose('stop', 'traffic')
            wait('no valid logs', lambda: scalar(MISSING) == 0)
            wait('missing logs Firing', lambda: state('Access logs missing') == 'firing')
            wait('missing logs webhook firing', lambda: notification('Access logs missing', 'firing'))
            compose('start', 'traffic')
            wait('missing logs recovery', lambda: state('Access logs missing') == 'inactive')
            wait('missing logs webhook resolved', lambda: notification('Access logs missing', 'resolved'))
            ids = compose('ps', '-aq').split()
            inspected = json.loads(subprocess.check_output(['docker', 'inspect', *ids], text=True))
            volumes = {mount['Name'] for item in inspected for mount in item['Mounts'] if mount['Type'] == 'volume'}
            compose('down')
            existing = subprocess.check_output(['docker', 'volume', 'ls', '-q'], text=True).split()
            assert volumes <= set(existing), 'down must retain lab data'
            compose('up', '-d')
            url = 'http://' + compose('port', 'grafana', '3000').strip()
            wait('restart retains dashboard', lambda: api('/api/dashboards/uid/access-log-lab')['dashboard']['uid'] == 'access-log-lab')
            print('PASS: isolated persistence and real-stack alert lifecycle', flush=True)
        except BaseException:
            print(compose('logs', '--tail', '10'), flush=True)
            raise
        finally:
            compose('down', '--volumes', '--remove-orphans', timeout=90)


if __name__ == '__main__':
    run_test()
