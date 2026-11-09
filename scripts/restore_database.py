#!/usr/bin/env python3
"""Restore a validated SQLite backup. Stop TRAVESÍA before restoring."""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def restore_database(source: str | Path, destination: str | Path, *, confirm_replace: bool = False) -> Path:
    source_path = Path(source).expanduser().resolve()
    destination_path = Path(destination).expanduser().resolve()
    if source_path == destination_path:
        raise ValueError("Restore source and destination must be different files.")
    if not source_path.is_file():
        raise FileNotFoundError(f"Backup file not found: {source_path}")
    if destination_path.exists() and not confirm_replace:
        raise FileExistsError("Destination exists; pass --confirm-replace only after taking a separate backup.")
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{destination_path.name}.", suffix=".restore", dir=destination_path.parent)
    os.close(fd)
    temporary_path = Path(temporary_name)
    try:
        source_uri = source_path.as_uri() + "?mode=ro"
        with sqlite3.connect(source_uri, uri=True, timeout=30) as backup_db:
            check = backup_db.execute("PRAGMA quick_check").fetchone()
            if not check or check[0] != "ok":
                raise sqlite3.DatabaseError("Backup failed PRAGMA quick_check.")
            with sqlite3.connect(temporary_path, timeout=30) as target_db:
                backup_db.backup(target_db, pages=256, sleep=0.05)
                restored_check = target_db.execute("PRAGMA quick_check").fetchone()
                if not restored_check or restored_check[0] != "ok":
                    raise sqlite3.DatabaseError("Restored copy failed PRAGMA quick_check.")
        os.chmod(temporary_path, 0o600)
        os.replace(temporary_path, destination_path)
        return destination_path
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("backup", help="Verified backup SQLite file")
    parser.add_argument("--destination", default=os.environ.get("CITYPULSEX_DB", str(ROOT / "instance" / "citypulsex.sqlite3")))
    parser.add_argument("--confirm-replace", action="store_true", help="Confirm that the existing destination may be replaced")
    args = parser.parse_args()
    try:
        restored = restore_database(args.backup, args.destination, confirm_replace=args.confirm_replace)
    except (OSError, sqlite3.Error, ValueError) as exc:
        print(f"Restore failed: {exc}", file=sys.stderr)
        return 1
    print(f"Verified database restored to: {restored}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
