"""Small DB-API adapter for the store's fixed, parameterized SQL statements."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Protocol

import psycopg


class Cursor(Protocol):
    def fetchone(self) -> tuple | None: ...
    def fetchall(self) -> list[tuple]: ...


class Connection:
    def __init__(self, raw: sqlite3.Connection | psycopg.Connection, postgres: bool):
        self.raw = raw
        self.postgres = postgres

    def execute(self, statement: str, parameters: tuple = ()) -> Cursor:
        # Only internal SQL uses this adapter: no quoted '?' literals or dynamic SQL.
        sql = statement.replace('?', '%s') if self.postgres else statement
        return self.raw.execute(sql, parameters)

    def executescript(self, script: str) -> None:
        # Unlike sqlite3.executescript, keep schema creation in our transaction.
        for statement in script.split(';'):
            if statement.strip():
                self.execute(statement)

    def commit(self) -> None:
        self.raw.commit()


class Database:
    def __init__(self, location: str):
        self.location = location
        self.postgres = location.startswith(('postgresql://', 'postgres://'))
        if not self.postgres:
            if '://' in location:
                raise ValueError('Database must be a SQLite file path or PostgreSQL URL')
            Path(location).parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connect(self) -> Iterator[Connection]:
        if self.postgres:
            with psycopg.connect(self.location, connect_timeout=15) as raw:
                raw.execute("SET LOCAL lock_timeout = '10s'")
                raw.execute("SET LOCAL statement_timeout = '15s'")
                # Preserve SQLite's serialized store transactions across connections
                # and processes, including deduplication, timers and profile creation.
                # Transaction-scoped locks work with Neon's transaction pooler.
                raw.execute('SELECT pg_advisory_xact_lock(1936748404)')
                yield Connection(raw, True)
        else:
            raw = sqlite3.connect(self.location, timeout=10)
            try:
                raw.execute('PRAGMA busy_timeout=10000')
                with raw:
                    raw.execute('BEGIN IMMEDIATE')
                    yield Connection(raw, False)
            finally:
                raw.close()
