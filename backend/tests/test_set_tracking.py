import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from backend.app import CATALOG, create_app
from backend.spotter.models import CreateSession, Event, Snapshot, WeightChange
from backend.spotter.store import Store, StoreError
from backend.spotter.tool_contract import SubmitWorkoutAction
from fastapi.testclient import TestClient


@pytest.fixture
def workout(tmp_path):
    store = Store(str(tmp_path / 'tracking.sqlite3'), CATALOG)
    created = store.create(CreateSession(selected_muscle_group_ids=['chest'], plan=[{
        'exercise_id': 'chest-press', 'sets': 2, 'reps': 10, 'weight_lb': 50,
    }]))
    return store, created['snapshot'], created['access_token']


def event(state, kind, payload=None):
    return Event(event_id=uuid4(), expected_version=state['version'], source='voice', type=kind,
                 exercise_instance_id=state['current']['instance_id'], set_index=state['set_index'], payload=payload or {})


def apply(store, state, token, kind, now, payload=None):
    return store.event(state['session_id'], token, event(state, kind, payload), now=now)['snapshot']


def test_timer_history_weight_and_restart(workout):
    store, state, token = workout
    start = datetime(2026, 10, 11, 12, tzinfo=timezone.utc)
    assert state['set_started_at'] is None
    claim = event(state, 'equipment_claimed')
    state = store.event(state['session_id'], token, claim, now=start)['snapshot']
    assert datetime.fromisoformat(state['set_started_at']) == start
    assert store.event(state['session_id'], token, claim, now=start + timedelta(seconds=5))['snapshot'] == state
    store = Store(store.path, CATALOG)
    assert store.get(state['session_id'], token, start + timedelta(seconds=10))['set_started_at'] == state['set_started_at']
    completion = event(state, 'set_completed')
    state = store.event(state['session_id'], token, completion, now=start + timedelta(seconds=32.5))['snapshot']
    record = state['current']['set_records'][0]
    assert record['duration_seconds'] == 32.5 and record['weight_lb'] == 50 and record['planned_reps'] == 10
    assert state['set_started_at'] is None and state['phase'] == 'resting'
    assert 'increasing by 5 lb to 55 lb' in state['last_decision']
    state = apply(store, state, token, 'weight_updated', start + timedelta(seconds=35), {'weight_increase_lb': 5})
    assert state['current']['weight_lb'] == 55 and state['current']['set_records'][0]['weight_lb'] == 50
    deadline = datetime.fromisoformat(state['rest_deadline'])
    replay = store.event(state['session_id'], token, completion, now=deadline + timedelta(seconds=2))
    assert replay['replayed'] and len(replay['snapshot']['current']['set_records']) == 1
    store = Store(store.path, CATALOG)
    state = store.get(state['session_id'], token, deadline + timedelta(seconds=7))
    assert datetime.fromisoformat(state['set_started_at']) == deadline
    state = apply(store, state, token, 'set_completed', deadline + timedelta(seconds=21))
    assert state['phase'] == 'completed' and state['set_started_at'] is None
    records = store.summary(state['session_id'], token)['completed'][0]['set_records']
    assert [r['duration_seconds'] for r in records] == [32.5, 21.0]
    assert [r['weight_lb'] for r in records] == [50, 55]
    assert 'increasing' not in state['last_decision']
    Snapshot.model_validate(state)


@pytest.mark.parametrize('payload', [{}, {'weight_lb': 55, 'weight_increase_lb': 5}, {'weight_increase_lb': -5}, {'weight_lb': '55'}, {'weight_lb': True}, {'weight_lb': 52}, {'unknown': 5}])
def test_bad_weight_payloads_rejected(workout, payload):
    _, state, _ = workout
    with pytest.raises(ValidationError):
        event(state, 'weight_updated', payload)


def test_weight_phase_target_bounds_and_unknown(workout):
    store, state, token = workout
    now = datetime.now(timezone.utc)
    with pytest.raises(StoreError):
        apply(store, state, token, 'weight_updated', now, {'weight_lb': 55})
    state = apply(store, state, token, 'equipment_claimed', now)
    bad = event(state, 'weight_updated', {'weight_lb': 55})
    bad.set_index = 2
    with pytest.raises(StoreError):
        store.event(state['session_id'], token, bad, now=now)
    with pytest.raises(StoreError):
        apply(store, state, token, 'weight_updated', now, {'weight_lb': 500})
    state = apply(store, state, token, 'weight_updated', now, {'weight_lb': 45})
    assert state['current']['weight_lb'] == 45 and state['set_started_at'] == now.isoformat()
    unknown = store.create(CreateSession())
    other = apply(store, unknown['snapshot'], unknown['access_token'], 'equipment_claimed', now)
    with pytest.raises(StoreError, match='Current weight is unknown'):
        apply(store, other, unknown['access_token'], 'weight_updated', now, {'weight_increase_lb': 5})


def test_concurrent_completion_and_weight_do_not_rewrite_history(workout):
    store, state, token = workout
    now = datetime.now(timezone.utc)
    state = apply(store, state, token, 'equipment_claimed', now)
    requests = [event(state, 'set_completed'), event(state, 'weight_updated', {'weight_increase_lb': 5})]
    def send(request):
        try:
            return store.event(state['session_id'], token, request, now=now + timedelta(seconds=12))
        except StoreError as error:
            return error.status
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(send, requests))
    assert sum(isinstance(r, dict) for r in results) == 1 and 409 in results
    fresh = store.get(state['session_id'], token, now + timedelta(seconds=13))
    if fresh['phase'] == 'exercising':
        fresh = apply(store, fresh, token, 'set_completed', now + timedelta(seconds=14))
        assert fresh['current']['set_records'][0]['weight_lb'] == 55
    else:
        assert fresh['current']['set_records'][0]['weight_lb'] == 50
    assert len(fresh['current']['set_records']) == 1


def test_ending_stops_timer_without_fabricating_completed_set(workout):
    store, state, token = workout
    now = datetime.now(timezone.utc)
    state = apply(store, state, token, 'equipment_claimed', now)
    state = apply(store, state, token, 'end_session', now + timedelta(seconds=10))
    assert state['set_started_at'] is None and state['current']['set_records'] == []
    assert store.summary(state['session_id'], token)['completed_sets'] == 0


def test_legacy_active_set_does_not_invent_timing(workout):
    store, state, token = workout
    state['phase'] = 'exercising'
    del state['set_started_at']
    del state['current']['set_records']
    with store.connect() as db:
        store.save(db, state)
    state = store.get(state['session_id'], token)
    state = apply(store, state, token, 'set_completed', datetime.now(timezone.utc))
    record = state['current']['set_records'][0]
    assert record['started_at'] is None and record['duration_seconds'] is None


def test_http_and_tool_weight_contract(workout, tmp_path):
    store, state, token = workout
    now = datetime.now(timezone.utc)
    state = apply(store, state, token, 'equipment_claimed', now)
    with TestClient(create_app(store.path)) as client:
        headers = {'Authorization': f'Bearer {token}'}
        request = event(state, 'weight_updated', {'weight_increase_lb': 5}).model_dump(mode='json')
        result = client.post(f"/sessions/{state['session_id']}/events", json=request, headers=headers)
        assert result.status_code == 200 and result.json()['snapshot']['current']['weight_lb'] == 55
        request['event_id'] = str(uuid4())
        request['payload'] = {'weight_lb': 55, 'weight_increase_lb': 5}
        assert client.post(f"/sessions/{state['session_id']}/events", json=request, headers=headers).status_code == 422
    args = SubmitWorkoutAction(action='weight_updated', exercise_instance_id=state['current']['instance_id'], set_index=1, weight_increase_lb=5)
    assert args.weight_increase_lb == 5
    with pytest.raises(ValidationError):
        SubmitWorkoutAction(action='set_completed', exercise_instance_id='test', set_index=1, weight_lb=55)
    with pytest.raises(ValidationError):
        WeightChange(weight_lb=55, weight_increase_lb=5)
