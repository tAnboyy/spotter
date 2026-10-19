from types import SimpleNamespace

import pytest

import backend.spotter.app as app_module
from backend.spotter.database import Database


def test_database_selection_priority(monkeypatch):
    selected = []
    def capture(location, catalog):
        selected.append(location)
        return SimpleNamespace(database=SimpleNamespace(postgres=True))
    monkeypatch.setattr(app_module, 'Store', capture)
    monkeypatch.setenv('DATABASE_URL', 'postgresql://configured')
    monkeypatch.setenv('SPOTTER_DATABASE', 'fallback.sqlite3')
    app_module.create_app()
    app_module.create_app('explicit.sqlite3')
    monkeypatch.setenv('DATABASE_URL', '')
    app_module.create_app()
    assert selected == ['postgresql://configured', 'explicit.sqlite3', 'fallback.sqlite3']


def test_database_rejects_unsupported_url():
    with pytest.raises(ValueError, match='PostgreSQL'):
        Database('libsql://unsupported')
