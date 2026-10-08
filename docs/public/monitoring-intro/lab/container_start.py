#!/usr/bin/env python3
"""Seed only a brand-new empty lab volume, then run the container's demo app."""
from __future__ import annotations

import os
import sqlite3
import sys

from common import (DELAY_NAME, LAB_DIR, LOG_NAME, PARKED_NAME, LabError,
                    database_path, state_dir, state_path)
from labctl import reset


def initialize_if_empty() -> bool:
    directory = state_dir()
    database_path()
    for name in (PARKED_NAME, DELAY_NAME, LOG_NAME):
        state_path(name)
    # A parked DB, delay setting, log, or unknown file means existing state.
    # Never silently turn a fault into recovery or overwrite a learner's files.
    if next(directory.iterdir(), None) is not None:
        print("Existing lab state preserved; no initialization.", flush=True)
        return False
    reset()
    return True


def main() -> int:
    try:
        initialize_if_empty()
        # Explicit container-only bind; app.py still defaults to 127.0.0.1.
        os.execv(sys.executable, [sys.executable, "-u", str(LAB_DIR / "app.py"),
                                  "--host", "0.0.0.0"])
    except (OSError, sqlite3.Error, LabError) as exc:
        print(f"Container startup failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
