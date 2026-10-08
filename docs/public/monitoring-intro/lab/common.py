"""Small shared utilities. All writable paths belong to this disposable lab."""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import re
import stat
import tempfile
from datetime import datetime, timezone

LAB_DIR = Path(__file__).resolve().parent
STATE_DIR = LAB_DIR / ".state"
DB_NAME = "lab.sqlite3"
PARKED_NAME = "lab.sqlite3.unavailable"
LOG_NAME = "requests.jsonl"
DELAY_NAME = "delay.json"
DEFAULT_STATE = ".state/last-check.json"
HOST, PORT = "127.0.0.1", 18080
PATHS = ("/health", "/items/1")


class LabError(Exception):
    """A safe, actionable error that may be shown to the learner."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def state_dir() -> Path:
    if STATE_DIR.is_symlink():
        raise LabError("Refusing symlink: lab/.state")
    STATE_DIR.mkdir(mode=0o700, exist_ok=True)
    if not STATE_DIR.is_dir():
        raise LabError("lab/.state must be a directory")
    return STATE_DIR


def state_path(name: str) -> Path:
    """Only direct children, regular files, and no links (including hard links)."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name):
        raise LabError("State filename must be a simple name inside lab/.state")
    path = state_dir() / name
    if path.is_symlink():
        raise LabError(f"Refusing symlink: .state/{name}")
    if path.exists():
        info = path.stat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise LabError(f"Refusing non-regular or hard-linked state file: {name}")
    return path


def observation_path(value: str = DEFAULT_STATE) -> Path:
    # Interpret CLI paths relative to the lab, never the invoking shell's cwd.
    path = Path(value)
    if path.is_absolute() or path.parent != Path(".state") or path.suffix != ".json":
        raise LabError("--state-file must be .state/<simple-name>.json inside this lab")
    # Reserve application files so monitoring cannot overwrite fault settings.
    if path.name == DELAY_NAME:
        raise LabError("--state-file cannot use the reserved delay.json filename")
    return state_path(path.name)


def read_json(path: Path, limit: int = 16384):
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise LabError("State JSON exceeds the lab size limit")
    return json.loads(data)


def atomic_json(path: Path, value) -> None:
    """Flush then atomically replace; readers never see a half-written JSON file."""
    state_path(path.name)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=state_dir(),
                                         prefix=".write-", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(value, stream, ensure_ascii=True, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        state_path(path.name)
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def database_path() -> Path:
    path = state_path(DB_NAME)
    # SQLite may use these adjacent files; do not let it follow planted links.
    for suffix in ("-journal", "-wal", "-shm"):
        state_path(DB_NAME + suffix)
    return path


def bounded_float(low: float, high: float):
    def parse(value: str) -> float:
        import argparse
        try:
            number = float(value)
        except ValueError:
            raise argparse.ArgumentTypeError("must be a number") from None
        if not math.isfinite(number) or not low <= number <= high:
            raise argparse.ArgumentTypeError(f"must be between {low} and {high}")
        return number
    return parse


def bounded_int(low: int, high: int):
    def parse(value: str) -> int:
        import argparse
        try:
            number = int(value)
        except ValueError:
            raise argparse.ArgumentTypeError("must be an integer") from None
        if not low <= number <= high:
            raise argparse.ArgumentTypeError(f"must be between {low} and {high}")
        return number
    return parse
