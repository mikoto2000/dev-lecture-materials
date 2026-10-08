#!/usr/bin/env python3
"""Set or undo only named faults in this lab's dedicated .state directory."""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys

from common import (DB_NAME, DEFAULT_STATE, DELAY_NAME, LOG_NAME, PARKED_NAME,
                    LabError, atomic_json, bounded_float, database_path,
                    observation_path, read_json, state_path)


# No directory removal or wildcard deletion; unknown files are left untouched.
RESET_FILES = (DB_NAME, PARKED_NAME, DB_NAME + "-journal", DB_NAME + "-wal",
               DB_NAME + "-shm", DELAY_NAME, LOG_NAME, "last-check.json")


def reset() -> None:
    paths = [state_path(name) for name in RESET_FILES]  # Validate all before deleting.
    for path in paths:
        if path.exists():
            path.unlink()
    connection = sqlite3.connect(database_path())
    try:
        connection.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
        connection.execute("INSERT INTO items VALUES (?, ?)", (1, "monitoring-demo"))
        connection.commit()
    finally:
        connection.close()
    print("Lab reset: row 1 = monitoring-demo; delay off; default observation/log cleared.")
    print("Reset/init only with the app and monitors stopped. No process was stopped.")


def toggle_database(enabled: bool) -> None:
    database, parked = database_path(), state_path(PARKED_NAME)
    source, destination = (database, parked) if enabled else (parked, database)
    if source.exists() and destination.exists():
        raise LabError("Both lab database files exist; stop the app and run reset")
    if source.exists():
        source.rename(destination)
    elif not destination.exists():
        raise LabError("No lab database found; stop the app and run init")
    print(f"db-unavailable {'on' if enabled else 'off'}")


def wrong_data(enabled: bool) -> None:
    connection = sqlite3.connect(database_path().as_uri() + "?mode=rw", uri=True, timeout=0.5)
    try:
        value = "wrong-demo" if enabled else "monitoring-demo"
        cursor = connection.execute("UPDATE items SET name = ? WHERE id = ?", (value, 1))
        if cursor.rowcount != 1:
            raise LabError("Expected seeded row 1; stop the app and run reset")
        connection.commit()
    finally:
        connection.close()
    print(f"wrong-data {'on' if enabled else 'off'}")


def inspect() -> None:
    database, parked = database_path(), state_path(PARKED_NAME)
    print(json.dumps({"database_present": database.exists(), "database_parked": parked.exists()}))
    if database.exists():
        connection = sqlite3.connect(database.as_uri() + "?mode=ro", uri=True, timeout=0.2)
        try:
            row = connection.execute("SELECT id, name FROM items WHERE id = ?", (1,)).fetchone()
            print(json.dumps({"known_row": row}))
        finally:
            connection.close()
    delay = state_path(DELAY_NAME)
    print(json.dumps({"delay": read_json(delay) if delay.exists() else {"delay_seconds": 0}}))
    observation = observation_path(DEFAULT_STATE)
    print(json.dumps({"last_check": read_json(observation) if observation.exists() else None}))
    log = state_path(LOG_NAME)
    print("Recent request log (up to 5 complete records):")
    if log.exists():
        # Read a bounded tail, not the whole log as the lab grows.
        with log.open("rb") as stream:
            size = stream.seek(0, 2)
            offset = max(0, size - 8192)
            stream.seek(offset)
            lines = stream.read(8192).decode("utf-8", errors="replace").splitlines()
        if offset:
            lines = lines[1:]
        for line in lines[-5:]:
            print(line)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init", help="seed a clean lab; stop the app and monitors first")
    commands.add_parser("reset", help="clear named lab faults; stop the app and monitors first")
    for name in ("db-unavailable", "wrong-data"):
        commands.add_parser(name).add_argument("value", choices=("on", "off"))
    commands.add_parser("delay").add_argument("seconds", type=bounded_float(0, 2))
    commands.add_parser("inspect")
    args = parser.parse_args()
    try:
        if args.command in ("init", "reset"):
            reset()
        elif args.command == "db-unavailable":
            toggle_database(args.value == "on")
        elif args.command == "wrong-data":
            wrong_data(args.value == "on")
        elif args.command == "delay":
            atomic_json(state_path(DELAY_NAME), {"delay_seconds": args.seconds})
            print(f"delay {args.seconds:g} seconds on /items/1")
        else:
            inspect()
        return 0
    except (OSError, sqlite3.Error, ValueError, LabError) as exc:
        print(f"Lab command failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
