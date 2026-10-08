#!/usr/bin/env python3
"""Disposable local HTTP service: static health versus a real SQLite read."""
from __future__ import annotations

import argparse
import json
import math
import sqlite3
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from common import (DELAY_NAME, HOST, LOG_NAME, PORT, LabError, database_path,
                    read_json, state_path, utc_now)

LOG_LOCK = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    # A request always gets a small complete response, then its connection closes.
    protocol_version = "HTTP/1.0"

    def log_message(self, *_args):
        pass  # The structured request record below replaces the default log.

    def do_GET(self):
        started = time.monotonic()
        status, body, error = 200, {"ok": True}, None
        # Never log query strings or arbitrary client-supplied paths/headers.
        logged_path = self.path if self.path in ("/health", "/items/1") else "other"
        if self.path == "/health":
            pass  # Deliberately no database check here.
        elif self.path == "/items/1":
            connection = None
            try:
                config = state_path(DELAY_NAME)
                delay = read_json(config).get("delay_seconds", 0) if config.exists() else 0
                if (type(delay) not in (float, int) or not math.isfinite(delay)
                        or not 0 <= delay <= 2):
                    raise LabError("Invalid local delay setting")
                time.sleep(delay)
                # mode=ro is important: a missing DB must NOT become an empty DB.
                connection = sqlite3.connect(database_path().as_uri() + "?mode=ro",
                                             uri=True, timeout=0.2)
                row = connection.execute("SELECT id, name FROM items WHERE id = ?", (1,)).fetchone()
                if row is None:
                    status, body, error = 503, {"error": "item unavailable"}, "known row missing"
                else:
                    body = {"id": row[0], "name": row[1]}
            except sqlite3.Error as exc:
                status, body = 503, {"error": "database unavailable"}
                # SQLite's error name conveys evidence without SQL, values, or paths.
                error = getattr(exc, "sqlite_errorname", type(exc).__name__)
            except (OSError, ValueError, TypeError, AttributeError, LabError) as exc:
                status, body, error = 503, {"error": "local lab state unavailable"}, type(exc).__name__
            finally:
                if connection is not None:
                    connection.close()
        else:
            status, body = 404, {"error": "not found"}
        disconnected = False
        try:
            payload = json.dumps(body).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(payload)
        except (BrokenPipeError, ConnectionResetError, TimeoutError):
            disconnected = True  # A timed-out probe is an expected lab event.
        record = {"timestamp": utc_now(), "path": logged_path, "status": status,
                  "duration_ms": round((time.monotonic() - started) * 1000, 2)}
        if error:
            record["db_error"] = error
        if disconnected:
            record["client_disconnected"] = True
        line = json.dumps(record, sort_keys=True)
        with LOG_LOCK:
            try:
                with state_path(LOG_NAME).open("a", encoding="utf-8") as stream:
                    stream.write(line + "\n")
            except (OSError, LabError) as exc:
                print(f"LOG ERROR: {type(exc).__name__}", file=sys.stderr, flush=True)
            print(line, flush=True)


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def get_request(self):
        sock, address = super().get_request()
        sock.settimeout(3)  # Incomplete local client requests cannot wait forever.
        return sock, address


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=(HOST, "0.0.0.0"), default=HOST,
                        help="keep loopback by default; 0.0.0.0 is for the lab container")
    args = parser.parse_args()
    try:
        database_path()
        state_path(LOG_NAME)
        state_path(DELAY_NAME)
        with Server((args.host, PORT), Handler) as server:
            print(f"Lab app: http://{args.host}:{PORT} (Ctrl+C to stop)", flush=True)
            try:
                server.serve_forever(poll_interval=0.1)
            except KeyboardInterrupt:
                print("\nLab app stopped.", flush=True)
        return 0
    except (OSError, LabError) as exc:
        print(f"Cannot start lab app: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
