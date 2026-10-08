#!/usr/bin/env python3
"""Local-only teaching webhook receiver; no monitoring or outgoing requests."""
from __future__ import annotations

import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

from common import utc_now

MAX_BODY = 8192


def receipt(payload: dict, size: int) -> dict:
    record = {"event": "notification_received", "received_at": utc_now(),
              "body_bytes": size}
    # Never log all of the payload, headers, URLs, credentials, or request paths.
    # This local exercise uses only synthetic monitor names and messages.
    if isinstance(payload.get("msg"), str):
        record["message"] = payload["msg"][:200]
    monitor = payload.get("monitor")
    if isinstance(monitor, dict) and isinstance(monitor.get("name"), str):
        record["monitor_name"] = monitor["name"][:80]
    heartbeat = payload.get("heartbeat")
    if isinstance(heartbeat, dict) and type(heartbeat.get("status")) is int:
        if heartbeat["status"] in (0, 1, 2, 3):
            record["heartbeat_status"] = heartbeat["status"]
    return record


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def log_message(self, *_args):
        pass

    def respond(self, status: int) -> None:
        self.send_response(status)
        self.send_header("Content-Length", "0")
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True

    def do_POST(self):
        if self.path != "/":
            self.respond(404)
            return
        if self.headers.get("Transfer-Encoding"):
            self.respond(400)
            return
        lengths = self.headers.get_all("Content-Length", [])
        if len(lengths) != 1 or not lengths[0].isascii() or not lengths[0].isdigit():
            self.respond(411)
            return
        length = int(lengths[0]) if len(lengths[0]) < 10 else MAX_BODY + 1
        if not 0 < length <= MAX_BODY:
            self.respond(413)
            return
        try:
            body = bytearray()
            deadline = time.monotonic() + 3
            while len(body) < length:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("Body deadline exceeded")
                self.connection.settimeout(remaining)
                chunk = self.rfile.read1(length - len(body))
                if not chunk:
                    break
                body.extend(chunk)
            if len(body) != length:
                self.respond(400)
                return
            payload = json.loads(body)
            if not isinstance(payload, dict):
                self.respond(400)
                return
        except (OSError, ValueError, RecursionError):
            self.respond(400)
            return
        print(json.dumps(receipt(payload, length), ensure_ascii=True), flush=True)
        self.respond(200)


class Server(HTTPServer):
    # Sequential handling bounds concurrency; an incomplete request has 3 s.
    allow_reuse_address = True

    def get_request(self):
        sock, address = super().get_request()
        sock.settimeout(3)
        return sock, address


if __name__ == "__main__":
    with Server(("0.0.0.0", 18081), Handler) as server:
        print("Local notification sink listening on container port 18081", flush=True)
        try:
            server.serve_forever(poll_interval=0.1)
        except KeyboardInterrupt:
            pass
