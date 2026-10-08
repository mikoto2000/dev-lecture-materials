#!/usr/bin/env python3
"""Isolated startup/receiver tests; use ephemeral ports and owned temporary state."""
from __future__ import annotations

import contextlib
import http.client
import io
import json
from pathlib import Path
import socket
import sqlite3
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

sys.dont_write_bytecode = True

import common
import app
from container_start import initialize_if_empty
import labctl
from notification_sink import Handler, MAX_BODY, Server, receipt


class StartupTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="monitoring-startup-test-")
        self.state = Path(self.temporary.name) / ".state"
        self.patch = mock.patch.object(common, "STATE_DIR", self.state)
        self.patch.start()
        self.output = io.StringIO()
        self.capture = contextlib.redirect_stdout(self.output)
        self.capture.__enter__()

    def tearDown(self):
        self.capture.__exit__(None, None, None)
        self.patch.stop()
        self.temporary.cleanup()

    def row(self, name=common.DB_NAME):
        with sqlite3.connect(self.state / name) as db:
            return db.execute("SELECT id, name FROM items").fetchall()

    def test_first_start_seeds_only_once(self):
        self.assertTrue(initialize_if_empty())
        self.assertEqual(self.row(), [(1, "monitoring-demo")])
        before = (self.state / common.DB_NAME).read_bytes()
        self.assertFalse(initialize_if_empty())
        self.assertEqual((self.state / common.DB_NAME).read_bytes(), before)

    def test_start_preserves_all_faults_and_logs(self):
        initialize_if_empty()
        labctl.wrong_data(True)
        labctl.toggle_database(True)
        common.atomic_json(common.state_path(common.DELAY_NAME), {"delay_seconds": 2})
        common.state_path(common.LOG_NAME).write_text("preserve evidence\n")
        before = {p.name: p.read_bytes() for p in self.state.iterdir()}
        self.assertFalse(initialize_if_empty())
        self.assertEqual({p.name: p.read_bytes() for p in self.state.iterdir()}, before)
        self.assertFalse((self.state / common.DB_NAME).exists())
        self.assertEqual(self.row(common.PARKED_NAME), [(1, "wrong-demo")])
        labctl.toggle_database(False)
        self.assertFalse(initialize_if_empty())
        self.assertEqual(self.row(), [(1, "wrong-demo")])

    def test_unknown_state_is_never_overwritten(self):
        self.state.mkdir()
        keep = self.state / "keep.txt"
        keep.write_text("owned learner state")
        self.assertFalse(initialize_if_empty())
        self.assertEqual(keep.read_text(), "owned learner state")
        self.assertFalse((self.state / common.DB_NAME).exists())

    def test_known_symlink_is_rejected(self):
        self.state.mkdir()
        outside = Path(self.temporary.name) / "outside.txt"
        outside.write_text("untouched")
        (self.state / common.DB_NAME).symlink_to(outside)
        with self.assertRaises(common.LabError):
            initialize_if_empty()
        self.assertEqual(outside.read_text(), "untouched")

    def test_explicit_reset_then_start_is_healthy(self):
        initialize_if_empty()
        labctl.wrong_data(True)
        labctl.toggle_database(True)
        common.atomic_json(common.state_path(common.DELAY_NAME), {"delay_seconds": 1})
        labctl.reset()
        self.assertFalse(initialize_if_empty())
        self.assertEqual(self.row(), [(1, "monitoring-demo")])
        self.assertFalse((self.state / common.DELAY_NAME).exists())

    def test_app_default_stays_loopback_and_container_bind_is_explicit(self):
        for args, host in (([], "127.0.0.1"), (["--host", "0.0.0.0"], "0.0.0.0")):
            with mock.patch("sys.argv", ["app.py", *args]), mock.patch.object(app, "Server") as server:
                self.assertEqual(app.main(), 0)
                server.assert_called_once_with((host, 18080), app.Handler)


class NotificationTests(unittest.TestCase):
    def setUp(self):
        self.output = io.StringIO()
        self.capture = contextlib.redirect_stdout(self.output)
        self.capture.__enter__()
        self.server = Server(("127.0.0.1", 0), Handler)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True,
                                       kwargs={"poll_interval": 0.01})
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.thread.join(timeout=4)
        self.server.server_close()
        self.capture.__exit__(None, None, None)
        self.assertFalse(self.thread.is_alive())

    def post(self, body, path="/", headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=4)
        try:
            connection.request("POST", path, body, headers or {"Content-Type": "application/json"})
            response = connection.getresponse()
            response.read()
            return response.status
        finally:
            connection.close()

    def test_kuma_payload_receipt_and_safe_fields(self):
        body = json.dumps({"msg": "test DOWN\nnew line", "heartbeat": {"status": 0, "secret": "hidden"},
                           "monitor": {"name": "lab-item", "url": "hidden"}, "token": "hidden"})
        self.assertEqual(self.post(body), 200)
        line = self.output.getvalue().strip()
        self.assertNotIn("hidden", line)
        self.assertEqual(len(line.splitlines()), 1)
        value = json.loads(line)
        self.assertEqual(value["event"], "notification_received")
        self.assertEqual(value["heartbeat_status"], 0)
        self.assertEqual(value["monitor_name"], "lab-item")
        self.assertIn("received_at", value)

    def test_reject_oversized_invalid_or_wrong_path(self):
        for body, expected in (("x" * (MAX_BODY + 1), 413), ("not JSON", 400), ("[]", 400), ("", 413)):
            self.assertEqual(self.post(body), expected)
        self.assertEqual(self.post("{}", "/unexpected?secret=value"), 404)
        self.assertEqual(self.output.getvalue(), "")
        self.assertEqual(self.post("{}"), 200)

    def test_lengths_and_transfer_encoding_are_bounded(self):
        for headers, expected in (({"Content-Length": "9" * 100}, 413),
                                  ({"Content-Length": "no"}, 411),
                                  ({"Transfer-Encoding": "chunked"}, 400)):
            self.assertEqual(self.post("{}", headers=headers), expected)
        self.assertEqual(self.output.getvalue(), "")

    def test_receipt_truncates_and_ignores_other_payload(self):
        value = receipt({"msg": "x" * 2000, "monitor": {"name": "y" * 500},
                         "heartbeat": {"status": True}, "extra": "never log"}, 3000)
        self.assertEqual(len(value["message"]), 200)
        self.assertEqual(len(value["monitor_name"]), 80)
        self.assertNotIn("heartbeat_status", value)
        self.assertNotIn("extra", value)

    def test_slow_body_has_total_deadline_and_server_recovers(self):
        with socket.create_connection(("127.0.0.1", self.port), timeout=4) as sock:
            sock.sendall(b"POST / HTTP/1.0\r\nContent-Length: 10\r\n\r\n{")
            started = time.monotonic()
            response = sock.recv(1024)
            self.assertIn(b"400", response)
            self.assertLess(time.monotonic() - started, 4)
        self.assertEqual(self.post("{}"), 200)


if __name__ == "__main__":
    unittest.main(verbosity=2)
