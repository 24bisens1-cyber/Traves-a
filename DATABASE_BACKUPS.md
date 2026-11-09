# TRAVESÍA SQLite backup and restore

TRAVESÍA stores accounts, sessions and shared-trip records in SQLite. On a production host, set `CITYPULSEX_DB` to a durable path (the Render Blueprint mounts `/app/instance`). Never commit the database, its WAL files or backups to Git.

## Create a verified backup

Stop is not required for the backup command: it uses SQLite's online backup API so committed WAL contents are included consistently.

```bash
python scripts/backup_database.py
python scripts/backup_database.py --output backups/before-release.sqlite3
```

The script checks the source and completed backup with `PRAGMA quick_check`, writes a temporary file, uses an atomic replace and sets owner-only permissions where supported.

## Restore a backup

1. Stop the TRAVESÍA web service so no writes occur during restore.
2. Take and retain a separate backup of the current database.
3. Restore the selected verified backup:

```bash
python scripts/restore_database.py backups/before-release.sqlite3 --confirm-replace
```

4. Start the service and verify `/api/health`, then sign in and check shared trips.

For Render, keep backups outside the ephemeral container filesystem or copy them to an approved encrypted object-storage location. A persistent disk is not itself a backup. Test restore procedures periodically.
