"""Exercise actual local HTTP requests and log output without Docker."""
from contextlib import redirect_stdout
import http.client
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import threading
import unittest

LAB = Path(__file__).resolve().parents[1] / 'docs/public/access-log-monitoring/lab'
spec = importlib.util.spec_from_file_location('demo', LAB / 'demo.py')
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)


class AppTest(unittest.TestCase):
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

    def get(self, path):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        try:
            connection.request('GET', path)
            response = connection.getresponse()
            result = response.status, json.loads(response.read())
        finally:
            connection.close()
        # The handler appends immediately after writing the HTTP response.
        with demo.LOCK:
            pass
        return result

    def records(self):
        # Shutdown waits for active request threads to finish writing.
        self.server.shutdown()
        self.server.server_close()
        return [json.loads(line) for line in demo.LOG.read_text().splitlines()]

    def test_normal_and_missing(self):
        self.assertEqual(self.get('/items')[0], 200)
        self.assertEqual(self.get('/missing')[0], 404)
        rows = self.records()
        self.assertEqual([row['status'] for row in rows], [200, 404])
        self.assertEqual(len({row['request_id'] for row in rows}), 2)
        self.assertTrue(all(row['time'].endswith('Z') for row in rows))

    def test_query_is_not_recorded(self):
        status, body = self.get('/items?token=do-not-log')
        row = self.records()[0]
        self.assertEqual(status, 200)
        self.assertEqual(row['path'], '/items')
        self.assertEqual(row['request_id'], body['request_id'])
        self.assertNotIn('do-not-log', json.dumps(row))

    def test_error_and_recovery(self):
        demo.STATE.write_text('error')
        self.assertEqual(self.get('/items')[0], 503)
        demo.STATE.write_text('normal')
        self.assertEqual(self.get('/items')[0], 200)
        self.assertEqual([row['status'] for row in self.records()], [503, 200])

    def test_slow_is_http_200(self):
        demo.STATE.write_text('slow')
        self.assertEqual(self.get('/items')[0], 200)
        row = self.records()[0]
        self.assertGreaterEqual(row['request_time_ms'], 1000)


class SinkTest(unittest.TestCase):
    def test_webhook_states_and_labels(self):
        output = io.StringIO()
        server = demo.ThreadingHTTPServer(('127.0.0.1', 0), demo.Sink)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with redirect_stdout(output):
                for status in ('firing', 'resolved'):
                    connection = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=3)
                    payload = {'status': status, 'alerts': [
                        {'status': status, 'labels': {'alertname': 'Access errors'}}]}
                    connection.request('POST', '/', json.dumps(payload))
                    response = connection.getresponse()
                    self.assertEqual(response.status, 200)
                    response.read()
                    connection.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
        records = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual([row['status'] for row in records], ['firing', 'resolved'])
        self.assertEqual(records[0]['alerts'][0]['labels']['alertname'], 'Access errors')


if __name__ == '__main__':
    unittest.main()
