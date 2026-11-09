#!/usr/bin/env python3
"""Create a consistent SQLite backup, including committed WAL contents."""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def database_source() -> Path:
    return Path(os.environ.get("CITYPULSEX_DB", ROOT / "instance" / "citypulsex.sqlite3")).expanduser().resolve()


def backup_database(source: str | Path, destination: str | Path, *, overwrite: bool = False) -> Path:
    source_path = Path(source).expanduser().resolve()
    destination_path = Path(destination).expanduser().resolve()
    if source_path == destination_path:
        raise ValueError("Backup destination must be different from the live database.")
    if not source_path.is_file():
        raise FileNotFoundError(f"SQLite database not found: {source_path}")
    if destination_path.exists() and not overwrite:
        raise FileExistsError(f"Backup already exists: {destination_path} (use --force to replace it)")

    destination_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{destination_path.name}.", suffix=".tmp", dir=destination_path.parent)
    os.close(fd)
    temporary_path = Path(temporary_name)
    try:
        source_uri = source_path.as_uri() + "?mode=ro"
        with sqlite3.connect(source_uri, uri=True, timeout=30) as source_db:
            source_check = source_db.execute("PRAGMA quick_check").fetchone()
            if not source_check or source_check[0] != "ok":
                raise sqlite3.DatabaseError("Source database failed PRAGMA quick_check.")
            with sqlite3.connect(temporary_path, timeout=30) as backup_db:
                source_db.backup(backup_db, pages=256, sleep=0.05)
                backup_check = backup_db.execute("PRAGMA quick_check").fetchone()
                if not backup_check or backup_check[0] != "ok":
                    raise sqlite3.DatabaseError("Backup failed PRAGMA quick_check.")
        os.chmod(temporary_path, 0o600)
        os.replace(temporary_path, destination_path)
        return destination_path
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=str(database_source()), help="SQLite database path (defaults to CITYPULSEX_DB or instance/citypulsex.sqlite3)")
    parser.add_argument("--output", help="Backup file path (defaults to backups/citypulsex_UTC_TIMESTAMP.sqlite3)")
    parser.add_argument("--force", action="store_true", help="Replace an existing backup at --output")
    args = parser.parse_args()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = Path(args.output) if args.output else ROOT / "backups" / f"citypulsex_{stamp}.sqlite3"
    try:
        saved = backup_database(args.source, output, overwrite=args.force)
    except (OSError, sqlite3.Error, ValueError) as exc:
        print(f"Backup failed: {exc}", file=sys.stderr)
        return 1
    print(f"Backup created and verified: {saved}")
    print(f"Bytes: {saved.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
