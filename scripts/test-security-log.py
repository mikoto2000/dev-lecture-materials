"""Check actual authentication events, privacy and observed peer addresses."""
import http.client
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'docs/public/security-log-monitoring/lab/security_demo.py'
spec = importlib.util.spec_from_file_location('security_demo', SOURCE)
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)


class SecurityTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        demo.STATE = Path(self.directory.name) / 'mode'
        demo.LOG = Path(self.directory.name) / 'access.jsonl'
        self.server = demo.ThreadingHTTPServer(('127.0.0.1', 0), demo.App)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.directory.cleanup()

    def request(self, method, path, payload=None, headers=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=3)
        try:
            connection.request(method, path, json.dumps(payload) if payload is not None else None,
                               headers=headers or {})
            response = connection.getresponse()
            status = response.status
            response.read()
            return status
        finally:
            connection.close()

    def rows(self):
        self.server.shutdown()
        self.server.server_close()
        return [json.loads(line) for line in demo.LOG.read_text().splitlines()]

    def test_auth_failure_and_success(self):
        self.assertEqual(self.request('POST', '/login', {'username': 'demo-user', 'password': 'wrong'}), 401)
        self.assertEqual(self.request('POST', '/login', {'username': 'demo-user', 'password': 'local-demo-only'}), 200)
        rows = self.rows()
        self.assertEqual([row['outcome'] for row in rows], ['failure', 'success'])
        self.assertTrue(all(row['event'] == 'auth' for row in rows))
        self.assertNotIn('password', json.dumps(rows))
        self.assertNotIn('local-demo-only', json.dumps(rows))

    def test_untrusted_header_and_private_input(self):
        self.request('GET', '/items?token=private-input', headers={'X-Forwarded-For': '203.0.113.10'})
        row = self.rows()[0]
        self.assertEqual(row['client_ip'], '127.0.0.1')
        self.assertEqual(row['path'], '/items')
        self.assertNotIn('private-input', json.dumps(row))

    def test_unknown_account_is_not_stored(self):
        self.assertEqual(self.request('POST', '/login', {'username': 'private-person', 'password': 'private-password'}), 401)
        row = self.rows()[0]
        self.assertEqual(row['account'], 'other')
        self.assertNotIn('private-person', json.dumps(row))
        self.assertNotIn('private-password', json.dumps(row))

    def test_missing_paths(self):
        for path in ('/unknown-a', '/unknown-b', '/unknown-c', '/old-help'):
            self.assertEqual(self.request('GET', path), 404)
        self.assertEqual(len(self.rows()), 4)


if __name__ == '__main__':
    unittest.main()
