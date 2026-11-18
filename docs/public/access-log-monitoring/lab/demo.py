"""Local-only HTTP exercise: real completed requests, controlled faults, webhook sink."""
from __future__ import annotations

from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid

STATE = Path('/state/mode')
LOG = Path('/logs/access.jsonl')
LOCK = threading.Lock()


def mode():
    return STATE.read_text().strip() if STATE.exists() else 'normal'


class App(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_GET(self):
        started = time.monotonic()
        path = self.path.split('?', 1)[0]
        current = mode()
        status = 200 if path in ('/', '/items') else 404
        if current == 'error' and path == '/items':
            status = 503
        if current == 'slow' and path == '/items':
            time.sleep(1.2)
        request_id = uuid.uuid4().hex
        body = json.dumps({'status': status, 'request_id': request_id}).encode()
        try:
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            return
        record = {
            'time': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            'method': 'GET', 'path': path, 'status': status,
            'request_time_ms': round((time.monotonic() - started) * 1000, 2),
            'request_id': request_id,
        }
        with LOCK, LOG.open('a', encoding='utf-8') as output:
            output.write(json.dumps(record) + '\n')


class Sink(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_POST(self):
        payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        print(json.dumps({'received_at': datetime.now(timezone.utc).isoformat(),
                          'status': payload.get('status'),
                          'alerts': [{'status': a.get('status'), 'labels': a.get('labels')}
                                     for a in payload.get('alerts', [])]}), flush=True)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'ok')


def traffic():
    index = 0
    while True:
        path = '/missing' if index % 10 == 9 else '/items'
        try:
            with urllib.request.urlopen('http://demo:8080' + path, timeout=4) as response:
                response.read()
        except urllib.error.HTTPError as error:
            error.read()
        except OSError as error:
            print(str(error), flush=True)
        index += 1
        time.sleep(1)


def main():
    action = sys.argv[1]
    if action == 'mode':
        value = sys.argv[2]
        if value not in ('normal', 'error', 'slow'):
            raise SystemExit('Mode must be normal, error, or slow')
        temporary = STATE.with_suffix('.tmp')
        temporary.write_text(value)
        temporary.replace(STATE)
        print(value)
    elif action == 'server':
        LOG.parent.mkdir(parents=True, exist_ok=True)
        LOG.touch(exist_ok=True)
        ThreadingHTTPServer(('0.0.0.0', 8080), App).serve_forever()
    elif action == 'sink':
        ThreadingHTTPServer(('0.0.0.0', 8081), Sink).serve_forever()
    elif action == 'traffic':
        traffic()
    else:
        raise SystemExit('Unknown action')


if __name__ == '__main__':
    main()
