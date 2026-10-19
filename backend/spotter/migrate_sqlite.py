"""Copy a consistent SQLite snapshot into an empty PostgreSQL store."""
import argparse
import json
import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

from .database import Database
from .store import Store

ROOT = Path(__file__).resolve().parents[1]
TABLES = {
    'sessions': ('id', 'token_hash', 'state'),
    'events': ('session_id', 'event_id', 'request', 'result'),
    'users': ('id', 'google_sub', 'email', 'name', 'token_hash', 'preferences', 'muscle_group_ids', 'plan'),
    'user_schedules': ('user_id', 'schedule'),
}


def migrate(source: str, destination: str, *, apply: bool = False) -> dict[str, int]:
    if not destination.startswith(('postgresql://', 'postgres://')):
        raise ValueError('Destination must be a PostgreSQL URL')
    path = Path(source).resolve()
    with sqlite3.connect(path.as_uri() + '?mode=ro', uri=True) as src:
        src.execute('BEGIN')
        # One read transaction freezes a consistent source snapshot. Identifiers
        # below come only from the fixed allowlist, never command-line input.
        rows = {
            table: src.execute(f"SELECT {','.join(columns)} FROM {table}").fetchall()
            for table, columns in TABLES.items()
        }
    counts = {table: len(values) for table, values in rows.items()}
    if not apply:
        return counts
    Store(destination, {})  # Apply versioned schema; no catalog-dependent operations.
    with Database(destination).connect() as dst:
        if any(dst.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0] for table in TABLES):
            raise ValueError('Destination contains data; refusing to merge or overwrite it')
        for table, columns in TABLES.items():
            placeholders = ','.join('?' for _ in columns)
            for row in rows[table]:
                dst.execute(f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})", row)
            actual = dst.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
            if actual != counts[table]:
                raise ValueError('Migration row count mismatch; transaction rolled back')
    return counts


def main() -> None:
    load_dotenv(ROOT / '.env', override=False)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', default=os.environ.get('SPOTTER_DATABASE', str(ROOT / 'data/spotter.sqlite3')))
    parser.add_argument('--apply', action='store_true', help='Copy records; default only reports source counts')
    args = parser.parse_args()
    destination = os.environ.get('DATABASE_URL', '')
    try:
        counts = migrate(args.source, destination, apply=args.apply)
    except ValueError as exc:
        parser.exit(1, f'{exc}\n')
    except Exception as exc:
        # Database/network errors can contain connection details. Never print DSNs.
        parser.exit(1, f'Migration failed ({type(exc).__name__}); connection details withheld.\n')
    print(json.dumps({'mode': 'applied' if args.apply else 'dry_run', 'rows': counts}))


if __name__ == '__main__':
    main()
