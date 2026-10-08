#!/usr/bin/env python3
"""Check observer freshness, separately from application health (same-host demo)."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
import sys

from common import (DEFAULT_STATE, PATHS, LabError, bounded_float, observation_path,
                    read_json, utc_now)


def assess(value, max_age: float, now: datetime | None = None) -> tuple[bool, str]:
    try:
        if not isinstance(value, dict) or type(value.get("schema")) is not int or value["schema"] != 1:
            raise ValueError
        if type(value.get("ok")) is not bool or value.get("path") not in PATHS:
            raise ValueError
        elapsed, status = value.get("elapsed_ms"), value.get("status")
        if type(elapsed) not in (int, float) or not math.isfinite(elapsed) or elapsed < 0:
            raise ValueError
        if status is not None and (type(status) is not int or not 100 <= status <= 599):
            raise ValueError
        if "status" not in value or not isinstance(value.get("reason"), str):
            raise ValueError
        checked = datetime.fromisoformat(value["checked_at"].replace("Z", "+00:00"))
        if checked.tzinfo is None or checked.utcoffset().total_seconds() != 0:
            raise ValueError
        age = ((now or datetime.now(timezone.utc)) - checked).total_seconds()
    except (KeyError, ValueError, TypeError, AttributeError, OverflowError):
        return False, "malformed observation"
    if age < 0:
        return False, "future observation (check clocks)"
    if age > max_age:
        return False, f"stale observation: age={age:.3f}s max={max_age:g}s"
    return True, (f"fresh observation: age={age:.3f}s last_check_ok={str(value['ok']).lower()}; "
                  "watcher alive, application health is separate")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-age", type=bounded_float(0.1, 3600), default=5.0)
    parser.add_argument("--state-file", default=DEFAULT_STATE)
    args = parser.parse_args()
    try:
        result = read_json(observation_path(args.state_file))
        ok, reason = assess(result, args.max_age)
    except FileNotFoundError:
        ok, reason = False, "missing observation"
    except (OSError, ValueError, LabError):
        ok, reason = False, "malformed or unsafe observation file"
    print("WATCHDOG " + json.dumps({"timestamp": utc_now(), "ok": ok, "reason": reason}))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
