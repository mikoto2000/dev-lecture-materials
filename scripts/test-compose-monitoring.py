#!/usr/bin/env python3
"""Bounded Docker integration test; removes only its unique CI project/volumes.

Run on a disposable Docker host. Python is a CI dependency, not a learner setup
requirement. No published application account is created by this infrastructure
smoke test; the course's Kuma UI/monitor behavior has a separate runtime review.
"""
from __future__ import annotations

import http.client
import json
from pathlib import Path
import socket
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "docs/public/monitoring-intro/lab"
PROJECT = "monitoring-ci-" + uuid.uuid4().hex[:12]
BASE = ["docker", "compose", "--project-directory", str(LAB), "--project-name", PROJECT,
        "--profile", "notifications"]


def compose(*args, timeout=45):
    result = subprocess.run([*BASE, *args], capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise AssertionError(f"compose {' '.join(args)} failed ({result.returncode}):\n"
                             f"{result.stdout[-4000:]}\n{result.stderr[-4000:]}")
    return result.stdout


def request(path, port=18080, timeout=4):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
    try:
        connection.request("GET", path)
        response = connection.getresponse()
        return response.status, response.read(32768)
    finally:
        connection.close()


def wait_http(port, path, seconds=90):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            status, body = request(path, port, timeout=2)
            if status == 200:
                return body
        except (OSError, http.client.HTTPException):
            pass
        time.sleep(1)
    raise AssertionError(f"Port {port}{path} did not become ready within {seconds}s")


def control(*args):
    return compose("exec", "-T", "demo", "python", "labctl.py", *args)


def expect_row(name):
    status, body = request("/items/1")
    assert status == 200, (status, body)
    assert json.loads(body) == {"id": 1, "name": name}, body


def kuma_request(url, payload=None):
    # Kuma's Node runtime checks real service DNS/networking, including while
    # demo is stopped. No client package installation or outgoing URL is needed.
    script = r"""
const http = require('node:http');
const url = process.argv[1];
const payload = process.argv[2];
const req = http.request(url, {method: payload ? 'POST' : 'GET',
  headers: payload ? {'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(payload)} : {}}, res => {
  let size = 0;
  res.on('data', chunk => {size += chunk.length; if (size > 8192) req.destroy(new Error('body too large'));});
  res.on('end', () => {console.log(res.statusCode); process.exit(res.statusCode === 200 ? 0 : 1);});
});
const timer = setTimeout(() => {req.destroy(new Error('deadline'));}, 5000);
req.on('error', error => {clearTimeout(timer); console.error(error.message); process.exit(1);});
if (payload) req.write(payload);
req.end();
"""
    return compose("exec", "-T", "kuma", "node", "-e", script, url, payload or "")


def main():
    # Do not stop another lab, overwrite its ports, or touch its data.
    for port in (13001, 18080):
        with socket.socket() as probe:
            try:
                probe.bind(("127.0.0.1", port))
            except OSError as exc:
                raise SystemExit(f"Port {port} is busy; leave the existing app untouched") from exc
    subprocess.run(["docker", "info"], check=True, capture_output=True, timeout=30)
    try:
        compose("up", "-d", "--build", timeout=600)
        wait_http(18080, "/health")
        # A new Kuma v2 volume redirects / to the database-selection screen.
        # Do not treat that expected redirect as a failed startup.
        wait_http(13001, "/setup-database")
        assert request("/", 13001)[0] == 302
        expect_row("monitoring-demo")
        assert "200" in kuma_request("http://demo:18080/items/1")
        print("PASS: images start; Kuma UI and service-name networking respond", flush=True)

        control("wrong-data", "on")
        expect_row("wrong-demo")
        control("delay", "0.8")
        started = time.monotonic()
        expect_row("wrong-demo")
        assert time.monotonic() - started >= 0.7
        control("db-unavailable", "on")
        assert request("/health")[0] == 200
        assert request("/items/1")[0] == 503
        compose("stop", "demo")
        compose("start", "demo")
        wait_http(18080, "/health")
        evidence = control("inspect")
        assert '"database_present": false' in evidence and '"database_parked": true' in evidence
        assert '"delay_seconds": 0.8' in evidence
        assert request("/items/1")[0] == 503
        control("db-unavailable", "off")
        expect_row("wrong-demo")
        print("PASS: real SQLite fault, wrong data, delay, and restart preservation", flush=True)

        compose("stop", "demo")
        payload = json.dumps({"msg": "compose CI synthetic DOWN receipt", "heartbeat": {"status": 0},
                              "monitor": {"name": "compose-ci"}})
        assert "200" in kuma_request("http://notification-sink:18081/", payload)
        logs = compose("logs", "--no-color", "--tail", "20", "notification-sink")
        assert "notification_received" in logs and "compose CI synthetic DOWN receipt" in logs
        print("PASS: independent bounded webhook receives while demo is stopped", flush=True)

        # Named volumes survive removal/recreation. Include a scoped Kuma data
        # marker to verify that /app/data survives without relying on private APIs.
        compose("exec", "-T", "kuma", "node", "-e",
                "require('node:fs').writeFileSync('/app/data/compose-ci-marker.txt','preserved')")
        compose("down", timeout=90)
        compose("up", "-d", timeout=120)
        wait_http(18080, "/health")
        wait_http(13001, "/setup-database")
        expect_row("wrong-demo")
        assert '"delay_seconds": 0.8' in control("inspect")
        compose("exec", "-T", "kuma", "node", "-e",
                "if(require('node:fs').readFileSync('/app/data/compose-ci-marker.txt','utf8')!=='preserved')process.exit(1)")
        compose("stop", "demo")
        compose("run", "--rm", "demo", "python", "labctl.py", "reset", timeout=60)
        compose("up", "-d", "demo")
        wait_http(18080, "/health")
        expect_row("monitoring-demo")
        assert '"delay_seconds": 0' in control("inspect")
        print("PASS: down preserves both volumes; stopped-app one-off reset restores demo", flush=True)
    except BaseException:
        try:
            print(compose("logs", "--no-color", "--tail", "40"))
        except Exception as exc:
            print(f"Could not collect test logs: {exc}")
        raise
    finally:
        # PROJECT is generated above and never comes from user input. This test
        # owns these containers and volumes; it never invokes global cleanup.
        compose("down", "--volumes", timeout=90)
    print(f"PASS: removed test-owned project {PROJECT}")


if __name__ == "__main__":
    main()
