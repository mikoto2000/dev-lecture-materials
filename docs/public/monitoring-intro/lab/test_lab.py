#!/usr/bin/env python3
"""Run isolated stdlib-only integration tests: python3 path/to/lab/test_lab.py.

Uses a fresh owned temporary lab and fixed loopback port 18080. Stops only the
processes this suite starts. An existing app on that port is an error, not killed.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import http.client
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest

sys.dont_write_bytecode = True

from monitor import AlertState
from watchdog import assess

SCRIPTS = ("common.py", "app.py", "labctl.py", "monitor.py", "watchdog.py")
SOURCE = Path(__file__).resolve().parent


class LabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            with socket.socket() as sock:
                sock.bind(("127.0.0.1", 18080))
        except OSError as exc:
            raise RuntimeError("Port 18080 is busy. Stop your lab app before running tests.") from exc
        cls.root = Path(tempfile.mkdtemp(prefix="monitoring-course-test-"))
        for script in SCRIPTS:
            shutil.copyfile(SOURCE / script, cls.root / script)
        cls.app = None
        cls.output = None

    @classmethod
    def tearDownClass(cls):
        # Remove ONLY the exact test-owned files, then empty directories. Never
        # delete a tree, enumerate arbitrary files for deletion, or touch user state.
        if cls.app is not None:
            cls.stop_app()
        names = ("lab.sqlite3", "lab.sqlite3.unavailable", "lab.sqlite3-journal",
                 "lab.sqlite3-wal", "lab.sqlite3-shm", "delay.json", "requests.jsonl",
                 "last-check.json", "other.json", "keep.txt")
        for name in names:
            (cls.root / ".state" / name).unlink(missing_ok=True)
        if (cls.root / ".state").exists():
            (cls.root / ".state").rmdir()
        for script in SCRIPTS:
            (cls.root / script).unlink()
        for name in ("app-output.txt", "outside.txt"):
            (cls.root / name).unlink(missing_ok=True)
        cls.root.rmdir()

    def setUp(self):
        self.cli("labctl.py", "reset", expected=0)

    def tearDown(self):
        self.stop_app()

    @classmethod
    def cli(cls, script, *args, expected=None):
        # -B prevents unrelated bytecode files in the disposable directory.
        result = subprocess.run([sys.executable, "-B", str(cls.root / script), *args],
                                capture_output=True, text=True, timeout=15)
        if expected is not None and result.returncode != expected:
            raise AssertionError(f"{script} {args}: exit={result.returncode}\n{result.stdout}\n{result.stderr}")
        return result

    @classmethod
    def start_app(cls):
        cls.output = (cls.root / "app-output.txt").open("a", encoding="utf-8")
        # Child probe inherits -B via PYTHONDONTWRITEBYTECODE below in test main.
        cls.app = subprocess.Popen([sys.executable, "-B", str(cls.root / "app.py")],
                                   stdout=cls.output, stderr=cls.output)
        for _ in range(50):
            if cls.app.poll() is not None:
                raise AssertionError("Test app failed to start; check fixed port 18080")
            try:
                if cls.get("/health")[0] == 200:
                    return
            except OSError:
                pass
            time.sleep(0.04)
        raise AssertionError("Test app did not become ready")

    @classmethod
    def stop_app(cls):
        if cls.app is not None:
            if cls.app.poll() is None:
                cls.app.send_signal(signal.SIGINT)
                try:
                    cls.app.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    cls.app.kill()  # Only this exact Popen child, never a process search.
                    cls.app.wait(timeout=3)
            cls.app = None
        if cls.output is not None:
            cls.output.close()
            cls.output = None

    @staticmethod
    def get(path):
        conn = http.client.HTTPConnection("127.0.0.1", 18080, timeout=3)
        try:
            conn.request("GET", path)
            response = conn.getresponse()
            return response.status, json.loads(response.read())
        finally:
            conn.close()

    def observation(self):
        return json.loads((self.root / ".state" / "last-check.json").read_text())

    def write_observation(self, **changes):
        value = {"schema": 1, "checked_at": datetime.now(timezone.utc).isoformat(),
                 "path": "/health", "ok": True, "status": 200, "elapsed_ms": 4,
                 "reason": "ok"}
        value.update(changes)
        (self.root / ".state" / "last-check.json").write_text(json.dumps(value))
        return value

    def test_stop_restart_and_live_alert_recovery(self):
        self.start_app()
        self.cli("monitor.py", "--path", "/items/1", "--expect-name", "monitoring-demo", expected=0)
        self.stop_app()
        self.cli("monitor.py", expected=1)
        self.assertIsNone(self.observation()["status"])
        self.start_app()
        self.cli("monitor.py", expected=0)
        self.assertTrue(self.observation()["ok"])

        self.cli("labctl.py", "db-unavailable", "on", expected=0)
        process = subprocess.Popen([sys.executable, "-B", str(self.root / "monitor.py"),
                                    "--path", "/items/1", "--count", "6", "--interval", "0.2",
                                    "--failures", "2", "--recoveries", "2"],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        prefix = []
        try:
            # Read the two confirmed failures before restoring the database.
            for _ in range(3):
                prefix.append(process.stdout.readline())
            self.assertTrue(prefix[-1].startswith("ALERT "), prefix)
            self.cli("labctl.py", "db-unavailable", "off", expected=0)
            rest, errors = process.communicate(timeout=8)
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate(timeout=3)
        records = ("".join(prefix) + rest).splitlines()
        self.assertEqual(sum(line.startswith("CHECK ") for line in records), 6)
        self.assertEqual(sum(line.startswith("ALERT ") for line in records), 1)
        self.assertEqual(sum(line.startswith("RECOVERY ") for line in records), 1)
        self.assertEqual(process.returncode, 1, errors)

    def test_database_fault_static_false_confidence_and_evidence(self):
        self.start_app()
        self.cli("labctl.py", "db-unavailable", "on", expected=0)
        self.assertEqual(self.get("/health")[0], 200)
        self.assertEqual(self.get("/items/1")[0], 503)
        self.assertFalse((self.root / ".state" / "lab.sqlite3").exists())
        self.cli("monitor.py", "--path", "/health", expected=0)
        result = self.cli("monitor.py", "--path", "/items/1", "--count", "3", "--interval", "0.1", expected=1)
        self.assertEqual(result.stdout.count("ALERT "), 1)
        self.assertNotIn("RECOVERY ", result.stdout)
        evidence = self.cli("labctl.py", "inspect", expected=0)
        self.assertIn("SQLITE_CANTOPEN", evidence.stdout)
        self.cli("labctl.py", "db-unavailable", "off", expected=0)
        self.assertEqual(self.get("/items/1"), (200, {"id": 1, "name": "monitoring-demo"}))

    def test_wrong_data_requires_semantic_check(self):
        self.start_app()
        self.cli("labctl.py", "wrong-data", "on", expected=0)
        self.assertEqual(self.get("/items/1"), (200, {"id": 1, "name": "wrong-demo"}))
        self.cli("monitor.py", "--path", "/items/1", expected=0)
        self.cli("monitor.py", "--path", "/items/1", "--expect-name", "monitoring-demo", expected=1)
        self.assertEqual(self.observation()["reason"], "name mismatch")
        self.cli("labctl.py", "wrong-data", "off", expected=0)
        self.cli("monitor.py", "--path", "/items/1", "--expect-name", "monitoring-demo", expected=0)

    def test_delay_latency_and_total_timeout(self):
        self.start_app()
        self.cli("labctl.py", "delay", "0.8", expected=0)
        self.cli("monitor.py", "--path", "/items/1", "--max-ms", "500", "--timeout", "2", expected=1)
        self.assertGreaterEqual(self.observation()["elapsed_ms"], 800)
        self.assertEqual(self.observation()["reason"], "latency exceeds 500ms")
        self.cli("labctl.py", "delay", "2", expected=0)
        started = time.monotonic()
        self.cli("monitor.py", "--path", "/items/1", "--timeout", "0.2", expected=1)
        self.assertLess(time.monotonic() - started, 1.5)
        self.assertIn("timeout", self.observation()["reason"])
        self.cli("monitor.py", "--path", "/health", "--timeout", "1", expected=0)
        # Let the timed-out worker's server response finish and test graceful handling.
        time.sleep(2.1)
        self.assertIsNone(self.app.poll())
        output = (self.root / "app-output.txt").read_text()
        self.assertNotIn("Traceback", output)
        self.cli("labctl.py", "delay", "0", expected=0)
        self.cli("monitor.py", "--path", "/items/1", expected=0)

    def test_bounded_body_invalid_json_and_slow_stream(self):
        class FakeServer(HTTPServer):
            allow_reuse_address = True

        class Response(BaseHTTPRequestHandler):
            mode = "large"

            def log_message(self, *_args):
                pass

            def do_GET(self):
                payload = b"x" * 5000 if self.mode == "large" else b"not JSON"
                if self.mode in ("wrong-id", "boolean-id"):
                    payload = json.dumps({"id": 2 if self.mode == "wrong-id" else True,
                                          "name": "monitoring-demo"}).encode()
                try:
                    self.send_response(200)
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    if self.mode == "slow":
                        for byte in payload:
                            self.wfile.write(bytes([byte]))
                            self.wfile.flush()
                            time.sleep(0.15)
                    else:
                        self.wfile.write(payload)
                except (BrokenPipeError, ConnectionResetError):
                    pass

        for mode, reason in (("large", "response body too large"),
                             ("invalid", "invalid JSON body"),
                             ("wrong-id", "id mismatch; expected integer 1"),
                             ("boolean-id", "id mismatch; expected integer 1"),
                             ("slow", "timeout after 0.2s")):
            Response.mode = mode
            with FakeServer(("127.0.0.1", 18080), Response) as server:
                thread = threading.Thread(target=server.handle_request, daemon=True)
                thread.start()
                args = ["--path", "/items/1", "--expect-name", "monitoring-demo"]
                if mode == "slow":
                    args.extend(["--timeout", "0.2"])
                self.cli("monitor.py", *args, expected=1)
                self.assertEqual(self.observation()["reason"], reason)
                thread.join(timeout=3)
                self.assertFalse(thread.is_alive())

    def test_alert_thresholds_and_no_false_recovery(self):
        state = AlertState(2, 2)
        self.assertEqual([state.observe(ok) for ok in (False, True, True)], [None, None, None])
        state = AlertState(2, 2)
        sequence = (False, False, False, True, False, True, True, True, False, False)
        self.assertEqual([state.observe(ok) for ok in sequence],
                         [None, "ALERT", None, None, None, None, "RECOVERY", None, None, "ALERT"])

    def test_watchdog_missing_fresh_failure_stale_future_and_corrupt(self):
        self.assertIn("missing", self.cli("watchdog.py", expected=1).stdout)
        self.write_observation(ok=False, status=503, reason="HTTP 503; expected 200")
        self.assertIn("last_check_ok=false", self.cli("watchdog.py", expected=0).stdout)
        self.write_observation(checked_at=(datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat())
        self.assertIn("stale", self.cli("watchdog.py", "--max-age", "5", expected=1).stdout)
        self.write_observation(checked_at=(datetime.now(timezone.utc) + timedelta(seconds=60)).isoformat())
        self.assertIn("future", self.cli("watchdog.py", expected=1).stdout)
        path = self.root / ".state" / "last-check.json"
        for content in ("{", "{}", "[]", '{"schema": 1}'):
            path.write_text(content)
            self.assertIn("malformed", self.cli("watchdog.py", expected=1).stdout)
        value = self.write_observation()
        for change in ({"ok": "yes"}, {"elapsed_ms": float("nan")}, {"status": True},
                       {"checked_at": "2026-01-01T00:00:00"}):
            self.assertFalse(assess(value | change, 5)[0])
        path.unlink()
        self.cli("monitor.py", expected=1)  # App is off; completed failure is still a heartbeat.
        self.cli("watchdog.py", expected=0)

    def test_safe_paths_bounds_and_target(self):
        for args in (("--count", "0"), ("--count", "121"), ("--interval", "0"),
                     ("--failures", "0"), ("--recoveries", "0"), ("--timeout", "nan"),
                     ("--path", "http://example.com"), ("--state-file", "/tmp/elsewhere.json"),
                     ("--state-file", ".state/../elsewhere.json"), ("--state-file", ".state/delay.json")):
            self.cli("monitor.py", *args, expected=2)
        for delay in ("-1", "2.1", "nan", "inf"):
            self.cli("labctl.py", "delay", delay, expected=2)
        self.cli("monitor.py", "--state-file", ".state/other.json", expected=1)
        self.cli("watchdog.py", "--state-file", ".state/other.json", expected=0)
        outside = self.root / "outside.txt"
        outside.write_text("do not change")
        observation = self.root / ".state" / "last-check.json"
        observation.unlink(missing_ok=True)
        try:
            observation.symlink_to(outside)
            self.cli("monitor.py", expected=2)
            self.cli("labctl.py", "reset", expected=2)
            self.assertEqual(outside.read_text(), "do not change")
        finally:
            observation.unlink(missing_ok=True)
        database = self.root / ".state" / "lab.sqlite3"
        database.unlink()
        try:
            database.symlink_to(outside)
            self.cli("labctl.py", "wrong-data", "on", expected=2)
            self.cli("labctl.py", "reset", expected=2)
            self.assertEqual(outside.read_text(), "do not change")
        finally:
            database.unlink(missing_ok=True)

    def test_reset_preserves_unrelated_files_and_clears_faults(self):
        keep = self.root / ".state" / "keep.txt"
        keep.write_text("preserve")
        self.cli("labctl.py", "wrong-data", "on", expected=0)
        self.cli("labctl.py", "db-unavailable", "on", expected=0)
        self.cli("labctl.py", "delay", "2", expected=0)
        self.write_observation(ok=False)
        self.cli("labctl.py", "reset", expected=0)
        self.assertEqual(keep.read_text(), "preserve")
        for name in ("lab.sqlite3.unavailable", "delay.json", "last-check.json"):
            self.assertFalse((self.root / ".state" / name).exists())
        self.start_app()
        self.assertEqual(self.get("/items/1"), (200, {"id": 1, "name": "monitoring-demo"}))


if __name__ == "__main__":
    import os
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    unittest.main(verbosity=2)
