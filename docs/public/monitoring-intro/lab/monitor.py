#!/usr/bin/env python3
"""Finite fixed-localhost probes, semantic/latency checks, and alert transitions."""
from __future__ import annotations

import argparse
import http.client
import json
from pathlib import Path
import subprocess
import sys
import time

from common import (DEFAULT_STATE, HOST, PATHS, PORT, LabError, atomic_json,
                    bounded_float, bounded_int, observation_path, utc_now)

MAX_BODY_BYTES = 4096


def request_once(path: str, timeout: float) -> dict:
    """Worker: one GET, no redirects, proxies, DNS, retries, or external targets."""
    connection = http.client.HTTPConnection(HOST, PORT, timeout=timeout)
    try:
        connection.request("GET", path, headers={"Connection": "close"})
        response = connection.getresponse()
        body = response.read(MAX_BODY_BYTES + 1)
        if len(body) > MAX_BODY_BYTES:
            return {"status": response.status, "error": "response body too large"}
        return {"status": response.status, "body": body.decode("utf-8", errors="replace")}
    except (OSError, http.client.HTTPException) as exc:
        return {"status": None, "error": "request failed: " + type(exc).__name__}
    finally:
        connection.close()


def check(path: str, expect_name: str | None, max_ms: float | None, timeout: float) -> dict:
    started = time.monotonic()
    # A socket timeout alone is not a total deadline (a slow stream can reset it).
    # Bound the entire child instead. subprocess.run kills and reaps timed-out
    # children. OS process creation/termination scheduling can add slight overhead.
    try:
        result = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--_probe", "--path", path,
             "--timeout", str(timeout)], capture_output=True, text=True,
            timeout=timeout, check=False,
        )
        data = json.loads(result.stdout) if result.returncode == 0 else {
            "status": None, "error": "probe worker failed"}
    except subprocess.TimeoutExpired:
        data = {"status": None, "error": f"timeout after {timeout:g}s"}
    except (ValueError, OSError):
        data = {"status": None, "error": "probe worker unavailable"}
    elapsed = round((time.monotonic() - started) * 1000, 2)
    status = data.get("status")
    reason = data.get("error")
    if reason is None and status != 200:
        reason = f"HTTP {status}; expected 200"
    if reason is None and expect_name is not None:
        try:
            payload = json.loads(data.get("body", ""))
            if not isinstance(payload, dict):
                reason = "expected JSON object"
            elif type(payload.get("id")) is not int or payload["id"] != 1:
                reason = "id mismatch; expected integer 1"
            elif payload.get("name") != expect_name:
                reason = "name mismatch"
        except (ValueError, TypeError):
            reason = "invalid JSON body"
    if reason is None and max_ms is not None and elapsed > max_ms:
        reason = f"latency exceeds {max_ms:g}ms"
    return {"schema": 1, "checked_at": utc_now(), "path": path, "ok": reason is None,
            "status": status, "elapsed_ms": elapsed, "reason": reason or "ok"}


class AlertState:
    """Consecutive confirmation, deduplication, and recovery after a real alert."""
    def __init__(self, failures: int, recoveries: int):
        self.failures, self.recoveries = failures, recoveries
        self.bad, self.good, self.alerting = 0, 0, False

    def observe(self, ok: bool) -> str | None:
        if not ok:
            self.good = 0
            self.bad += 1
            if not self.alerting and self.bad >= self.failures:
                self.alerting = True
                return "ALERT"
        else:
            self.bad = 0
            self.good += 1
            if self.alerting and self.good >= self.recoveries:
                self.alerting = False
                return "RECOVERY"
        return None


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--path", choices=PATHS, default="/health")
    result.add_argument("--expect-name", help="require integer id=1 and this JSON name, e.g. monitoring-demo")
    result.add_argument("--max-ms", type=bounded_float(1, 10000), help="latency-quality limit in ms")
    result.add_argument("--timeout", type=bounded_float(0.1, 5), default=1.0,
                        help="total probe deadline in seconds (default: 1)")
    result.add_argument("--count", type=bounded_int(1, 120), default=1)
    result.add_argument("--interval", type=bounded_float(0.1, 60), default=2.0,
                        help="seconds to wait AFTER each completed check (default: 2)")
    result.add_argument("--failures", type=bounded_int(1, 120), default=1)
    result.add_argument("--recoveries", type=bounded_int(1, 120), default=1)
    result.add_argument("--state-file", default=DEFAULT_STATE)
    result.add_argument("--_probe", action="store_true", help=argparse.SUPPRESS)
    return result


def main() -> int:
    args = parser().parse_args()
    if args._probe:
        print(json.dumps(request_once(args.path, args.timeout)))
        return 0
    try:
        state_file = observation_path(args.state_file)
        transitions = AlertState(args.failures, args.recoveries)
        any_failure = False
        for index in range(args.count):
            result = check(args.path, args.expect_name, args.max_ms, args.timeout)
            # Every completed observation is a heartbeat, even a failing one.
            atomic_json(state_file, result)
            print("CHECK " + json.dumps(result, sort_keys=True), flush=True)
            transition = transitions.observe(result["ok"])
            if transition:
                print(transition + " " + json.dumps({"timestamp": result["checked_at"],
                      "path": args.path, "reason": result["reason"]}), flush=True)
            any_failure |= not result["ok"]
            if index + 1 < args.count:
                time.sleep(args.interval)
        return 1 if any_failure else 0
    except KeyboardInterrupt:
        print("Monitor stopped.", file=sys.stderr)
        return 130
    except (OSError, LabError) as exc:
        print(f"Monitor state error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
