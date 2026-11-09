from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from scripts.backup_database import backup_database
from scripts.restore_database import restore_database


def make_db(path: Path, value: str) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS sample (value TEXT NOT NULL)")
        conn.execute("DELETE FROM sample")
        conn.execute("INSERT INTO sample(value) VALUES (?)", (value,))


def read_value(path: Path) -> str:
    with sqlite3.connect(path) as conn:
        return conn.execute("SELECT value FROM sample").fetchone()[0]


def test_sqlite_backup_and_restore_round_trip(tmp_path):
    live = tmp_path / "live.sqlite3"
    backup = tmp_path / "backup.sqlite3"
    restored = tmp_path / "restored.sqlite3"
    make_db(live, "before deploy")

    result = backup_database(live, backup)
    assert result == backup.resolve()
    assert read_value(backup) == "before deploy"
    assert backup.stat().st_mode & 0o777 == 0o600

    make_db(live, "after deploy")
    restore_database(backup, restored)
    assert read_value(restored) == "before deploy"


def test_backup_refuses_overwrite_without_force(tmp_path):
    live = tmp_path / "live.sqlite3"
    backup = tmp_path / "backup.sqlite3"
    make_db(live, "one")
    backup_database(live, backup)
    with pytest.raises(FileExistsError):
        backup_database(live, backup)
    backup_database(live, backup, overwrite=True)


def test_restore_requires_explicit_replace_confirmation(tmp_path):
    backup = tmp_path / "backup.sqlite3"
    live = tmp_path / "live.sqlite3"
    make_db(backup, "backup")
    make_db(live, "live")
    with pytest.raises(FileExistsError):
        restore_database(backup, live)
    restore_database(backup, live, confirm_replace=True)
    assert read_value(live) == "backup"
