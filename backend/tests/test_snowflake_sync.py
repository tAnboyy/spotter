from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from backend.app import CATALOG
from backend.spotter.models import CreateSession, Event
from backend.spotter.snowflake_sync import extract
from backend.spotter.store import Store, StoreError


def action(state, kind):
    return Event(event_id=uuid4(), expected_version=state['version'], source='phone', type=kind,
                 exercise_instance_id=state['current']['instance_id'], set_index=state['set_index'], payload={})


def test_export_accepted_events_only_and_preserves_completed_set(tmp_path):
    store = Store(str(tmp_path / 'workout.sqlite3'), CATALOG)
    created = store.create(CreateSession(selected_muscle_group_ids=['chest'], plan=[{'exercise_id': 'chest-press', 'sets': 1, 'reps': 10, 'weight_lb': 50}]))
    state, token = created['snapshot'], created['access_token']
    now = datetime.now(timezone.utc)
    with pytest.raises(StoreError):
        store.event(state['session_id'], token, action(state, 'set_completed'), now)
    claim = action(state, 'equipment_claimed')
    state = store.event(state['session_id'], token, claim, now)['snapshot']
    done = action(state, 'set_completed')
    state = store.event(state['session_id'], token, done, now + timedelta(seconds=30))['snapshot']
    store.event(state['session_id'], token, done, now + timedelta(seconds=31))
    rows = extract(store.path)
    assert len(rows) == 2
    completed = next(r for r in rows if r['action'] == 'set_completed')
    assert completed['exercise_id'] == 'chest-press'
    assert completed['duration_seconds'] == 30
    assert completed['planned_reps'] == 10
    assert completed['weight_lb'] == 50
    assert completed['phase'] == 'completed'
    assert token not in str(rows)
    assert not {'preferences', 'token_hash', 'email', 'name', 'payload', 'request', 'result'} & completed.keys()
    assert extract(store.path) == rows


def test_taken_retains_deferred_equipment(tmp_path):
    store = Store(str(tmp_path / 'workout.sqlite3'), CATALOG)
    created = store.create(CreateSession(selected_muscle_group_ids=['chest'], plan=[{'exercise_id': 'chest-press', 'sets': 1, 'reps': 10}]))
    state = created['snapshot']
    store.event(state['session_id'], created['access_token'], action(state, 'equipment_taken'))
    assert extract(store.path)[0]['exercise_id'] == 'chest-press'


def test_missing_source_does_not_create_database(tmp_path):
    path = tmp_path / 'missing.sqlite3'
    with pytest.raises(Exception, match='unable to open database'):
        extract(str(path))
    assert not path.exists()
