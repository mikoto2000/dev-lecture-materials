"""Bounded local training traffic and synthetic authentication; no real accounts."""
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

STATE = Path('/state/security-mode')
LOG = Path('/logs/access.jsonl')
LOCK = threading.Lock()
MODES = ('normal', 'login', 'scan', 'typo')


def mode():
    return STATE.read_text().strip() if STATE.exists() else 'normal'


class App(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def handle_request(self, login=False):
        started = time.monotonic()
        path = self.path.split('?', 1)[0]
        event, account, outcome = 'access', '', ''
        status = 200 if path == '/items' else 404
        if login and path == '/login':
            length = int(self.headers.get('Content-Length', '0'))
            if length > 4096:
                self.send_error(413)
                return
            try:
                payload = json.loads(self.rfile.read(length))
                if not isinstance(payload, dict):
                    raise ValueError('Expected object')
            except (ValueError, UnicodeDecodeError):
                self.send_error(400)
                return
            # Record only the fixed training account, never supplied credentials.
            account = 'demo-user' if payload.get('username') == 'demo-user' else 'other'
            success = account == 'demo-user' and payload.get('password') == 'local-demo-only'
            event, outcome = 'auth', 'success' if success else 'failure'
            status = 200 if success else 401
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
        row = {'time': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
               'method': self.command, 'path': path, 'status': status,
               'request_time_ms': round((time.monotonic() - started) * 1000, 2),
               'request_id': request_id, 'event': event, 'account': account,
               'outcome': outcome, 'client_ip': self.client_address[0]}
        with LOCK, LOG.open('a', encoding='utf-8') as output:
            output.write(json.dumps(row) + '\n')

    def do_GET(self):
        self.handle_request()

    def do_POST(self):
        self.handle_request(login=True)


def request(path, failed=False):
    # The destination is fixed. There is no target URL or password list argument.
    data = None
    if path == '/login':
        data = json.dumps({'username': 'demo-user',
                           'password': 'wrong-demo-value' if failed else 'local-demo-only'}).encode()
    req = urllib.request.Request('http://demo:8080' + path, data=data,
                                 headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=4) as response:
            response.read()
    except urllib.error.HTTPError as error:
        error.read()
    except OSError as error:
        print(str(error), flush=True)


def traffic():
    index = 0
    while True:
        current = mode()
        if current == 'login':
            request('/login', failed=True)
        else:
            path = '/items'
            if current == 'scan':
                path = ('/unknown-a', '/unknown-b', '/unknown-c')[index % 3]
            elif current == 'typo':
                path = '/old-help'
            request(path)
            if index % 5 == 0:
                request('/login')
        index += 1
        time.sleep(1)


def main():
    action = sys.argv[1]
    if action == 'server':
        LOG.parent.mkdir(parents=True, exist_ok=True)
        LOG.touch(exist_ok=True)
        ThreadingHTTPServer(('0.0.0.0', 8080), App).serve_forever()
    elif action == 'traffic':
        traffic()
    elif action == 'mode':
        value = sys.argv[2]
        if value not in MODES:
            raise SystemExit('Mode must be normal, login, scan, or typo')
        temporary = STATE.with_suffix('.tmp')
        temporary.write_text(value)
        temporary.replace(STATE)
        print(value)
    else:
        raise SystemExit('Unknown action')


if __name__ == '__main__':
    main()
