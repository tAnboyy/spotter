"""Real PostgreSQL checks. Only an explicitly supplied local test database is erased."""
import os
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from backend.app import CATALOG, create_app
from backend.spotter.database import Database
from backend.spotter.migrate_sqlite import TABLES, migrate
from backend.spotter.models import CreateSession, ProfileUpdate, ScheduleUpdate
from backend.spotter.store import Store, StoreError
from backend.tests import test_session as sessions
from backend.tests import test_set_tracking as tracking


@pytest.fixture
def pg_url():
    url = os.environ.get('SPOTTER_TEST_DATABASE_URL')
    if not url:
        pytest.skip('Set SPOTTER_TEST_DATABASE_URL to a disposable local PostgreSQL database')
    parsed = urlsplit(url)
    if parsed.hostname not in {'localhost', '127.0.0.1'} or not parsed.path.startswith('/spotter_test'):
        pytest.fail('PostgreSQL tests require a localhost database named spotter_test*')
    Store(url, CATALOG)
    with Database(url).connect() as db:
        for table in TABLES:
            db.execute(f'DELETE FROM {table}')
    yield url
    with Database(url).connect() as db:
        for table in TABLES:
            db.execute(f'DELETE FROM {table}')


@pytest.mark.parametrize('scenario', [
    sessions.test_full_workout_with_deferred_exercise,
    sessions.test_duplicate_and_conflicting_reuse,
    sessions.test_concurrent_set_completions_count_once,
    sessions.test_wrong_target_and_phase,
    sessions.test_strict_never_substitutes,
    sessions.test_alternative_requires_confirmation,
    sessions.test_excluded_alternative_is_not_offered,
    sessions.test_all_taken_blocks_without_loop,
    sessions.test_rest_survives_restart,
    sessions.test_end_prevents_rest_and_keeps_partial_sets,
    sessions.test_reject_empty_plan,
], ids=lambda scenario: scenario.__name__)
def test_postgres_session_rules(pg_url, scenario):
    scenario(Store(pg_url, CATALOG))


@pytest.mark.parametrize('scenario', [
    tracking.test_timer_history_weight_and_restart,
    tracking.test_concurrent_completion_and_weight_do_not_rewrite_history,
    tracking.test_ending_stops_timer_without_fabricating_completed_set,
    tracking.test_legacy_active_set_does_not_invent_timing,
], ids=lambda scenario: scenario.__name__)
def test_postgres_tracking(pg_url, scenario):
    store = Store(pg_url, CATALOG)
    created = store.create(CreateSession(selected_muscle_group_ids=['chest'], plan=[{
        'exercise_id': 'chest-press', 'sets': 2, 'reps': 10, 'weight_lb': 50,
    }]))
    scenario((store, created['snapshot'], created['access_token']))


def test_postgres_profile_schedule_and_login_race(pg_url):
    identity = {'google_sub': str(uuid4()), 'email': 'test@example.com', 'name': 'Test'}
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: Store(pg_url, CATALOG).sign_in_google(identity), range(2)))
    assert results[0]['profile']['user_id'] == results[1]['profile']['user_id']
    store = Store(pg_url, CATALOG)
    auth = store.sign_in_google(identity)
    for result in results:
        with pytest.raises(StoreError):
            store.get_profile(result['access_token'])
    profile = auth['profile']
    store.save_profile(auth['access_token'], ProfileUpdate(
        name='Updated', preferences=profile['preferences'], muscle_group_ids=['chest'], plan=None))
    schedule = ScheduleUpdate(schedule=[{'weekday': 0, 'time': '18:00', 'muscle_group_ids': ['chest'],
        'plan': [{'exercise_id': 'chest-press', 'sets': 2, 'reps': 10, 'weight_lb': 50}]}])
    store.save_schedule(auth['access_token'], schedule)
    restored = Store(pg_url, CATALOG).get_profile(auth['access_token'])
    assert restored['name'] == 'Updated'
    assert restored['schedule'][0]['time'] == '18:00'


def test_postgres_http_stream_and_no_idle_worker(pg_url, monkeypatch):
    app = create_app(pg_url)
    def unexpected_poll():
        pytest.fail('PostgreSQL must not run idle expiry scans')
    monkeypatch.setattr(app.state.store, 'expire_due', unexpected_poll)
    with TestClient(app) as client:
        created = client.post('/sessions', json={}).json()
        state, token = created['snapshot'], created['access_token']
        sid = state['session_id']
        assert client.get(f'/sessions/{sid}', headers={'Authorization': 'Bearer bad'}).status_code == 401
        with client.websocket_connect(f'/sessions/{sid}/stream') as ws:
            ws.send_json({'access_token': token})
            assert ws.receive_json()['snapshot']['version'] == 1
            response = client.post(f'/sessions/{sid}/events',
                headers={'Authorization': f'Bearer {token}'},
                json=sessions.action(state, 'equipment_taken').model_dump(mode='json'))
            assert response.status_code == 200
            assert ws.receive_json()['snapshot']['version'] == 2


def test_sqlite_migration_preserves_all_records_and_refuses_merge(pg_url, tmp_path):
    source = str(tmp_path / 'source.sqlite3')
    store = Store(source, CATALOG)
    state, token = sessions.session(store)
    state = sessions.apply(store, state, token, 'equipment_claimed')
    auth = store.sign_in_google({'google_sub': 'migrate', 'email': 'test@example.com', 'name': 'Migration'})
    store.save_schedule(auth['access_token'], ScheduleUpdate(schedule=[{
        'weekday': 0, 'time': '18:00', 'muscle_group_ids': ['chest'],
        'plan': [{'exercise_id': 'chest-press', 'sets': 2, 'reps': 10, 'weight_lb': 50}],
    }]))
    counts = migrate(source, pg_url)
    assert counts == {'sessions': 1, 'events': 1, 'users': 1, 'user_schedules': 1}
    with Database(pg_url).connect() as db:
        assert db.execute('SELECT COUNT(*) FROM sessions').fetchone()[0] == 0
    assert migrate(source, pg_url, apply=True) == counts
    restored = Store(pg_url, CATALOG)
    assert restored.get(state['session_id'], token)['phase'] == 'exercising'
    assert restored.get_profile(auth['access_token'])['schedule'][0]['time'] == '18:00'
    with store.connect() as src, restored.connect() as dst:
        for table, columns in TABLES.items():
            sql = f"SELECT {','.join(columns)} FROM {table}"
            assert src.execute(sql).fetchall() == dst.execute(sql).fetchall()
    with pytest.raises(ValueError, match='refusing'):
        migrate(source, pg_url, apply=True)


def test_postgres_rolls_back_state_when_event_insert_fails(pg_url):
    store = Store(pg_url, CATALOG)
    state, token = sessions.session(store)
    with pytest.raises(RuntimeError):
        with store.connect() as db:
            changed = dict(state, version=999)
            store.save(db, changed)
            raise RuntimeError('injected failure before event persistence')
    assert store.get(state['session_id'], token)['version'] == 1


def test_migration_failure_rolls_back_all_copied_tables(pg_url, tmp_path):
    import psycopg
    source = str(tmp_path / 'bad-source.sqlite3')
    store = Store(source, CATALOG)
    sessions.session(store)
    store.sign_in_google({'google_sub': 'bad-migrate', 'email': 'test@example.com', 'name': 'Bad'})
    with store.connect() as db:
        # SQLite permits NUL in text; PostgreSQL rejects it after the session
        # insert, exercising an actual mid-transfer failure and full rollback.
        db.execute('UPDATE users SET name=?', ('bad\x00name',))
    with pytest.raises(psycopg.DataError):
        migrate(source, pg_url, apply=True)
    with Database(pg_url).connect() as db:
        assert all(db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0] == 0 for table in TABLES)
