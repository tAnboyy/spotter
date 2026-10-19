from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from backend.app import CATALOG, create_app
from backend.spotter.models import CreateSession, Event, Preferences, SnapshotFrame
from backend.spotter.store import Store, StoreError


@pytest.fixture
def store(tmp_path):
    return Store(str(tmp_path / "test.sqlite3"), CATALOG)


def action(state, kind, event_id=None):
    return Event(event_id=event_id or uuid4(), expected_version=state["version"], source="web", type=kind,
                 exercise_instance_id=state["current"]["instance_id"] if state["current"] else None,
                 set_index=state["set_index"])


def session(store, **kwargs):
    created = store.create(CreateSession(**kwargs))
    return created["snapshot"], created["access_token"]


def apply(store, state, token, kind, now=None):
    return store.event(state["session_id"], token, action(state, kind), now=now)["snapshot"]


def test_full_workout_with_deferred_exercise(store):
    state, token = session(store, demo_mode=True)
    state = apply(store, state, token, "equipment_taken")
    assert state["current"]["id"] == "seated-row"
    for _ in range(2):
        state = apply(store, state, token, "equipment_claimed")
        state = apply(store, state, token, "set_completed")
        state = store.get(state["session_id"], token, datetime.fromisoformat(state["rest_deadline"]) + timedelta(seconds=1))
        state = apply(store, state, token, "set_completed")
    assert state["phase"] == "blocked"
    state = apply(store, state, token, "retry_deferred")
    assert state["current"]["id"] == "chest-press"
    state = apply(store, state, token, "equipment_claimed")
    state = apply(store, state, token, "set_completed")
    state = store.get(state["session_id"], token, datetime.fromisoformat(state["rest_deadline"]) + timedelta(seconds=1))
    state = apply(store, state, token, "set_completed")
    assert state["phase"] == "completed"
    assert store.summary(state["session_id"], token)["completed_sets"] == 6


def test_duplicate_and_conflicting_reuse(store):
    state, token = session(store)
    event = action(state, "equipment_claimed")
    first = store.event(state["session_id"], token, event)
    replay = store.event(state["session_id"], token, event)
    assert replay["replayed"] and replay["snapshot"] == first["snapshot"]
    event.source = "watch"
    with pytest.raises(StoreError) as exc:
        store.event(state["session_id"], token, event)
    assert exc.value.status == 409


def test_concurrent_set_completions_count_once(store):
    state, token = session(store)
    state = apply(store, state, token, "equipment_claimed")
    def submit(_):
        try:
            store.event(state["session_id"], token, action(state, "set_completed"))
            return "accepted"
        except StoreError as exc:
            return exc.status
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(submit, range(2)))
    assert sorted(map(str, results)) == ["409", "accepted"]
    assert store.get(state["session_id"], token)["current"]["completed_sets"] == 1


def test_wrong_target_and_phase(store):
    state, token = session(store)
    with pytest.raises(StoreError):
        apply(store, state, token, "set_completed")
    event = action(state, "equipment_claimed")
    event.exercise_instance_id = "old-exercise"
    with pytest.raises(StoreError):
        store.event(state["session_id"], token, event)


def test_strict_never_substitutes(store):
    state, token = session(store)
    state = apply(store, state, token, "equipment_taken")
    assert state["pending_alternative"] is None
    assert state["deferred"][0]["id"] == "chest-press"


def test_alternative_requires_confirmation(store):
    state, token = session(store, preferences=Preferences(mode="alternatives"))
    state = apply(store, state, token, "equipment_taken")
    assert state["phase"] == "awaiting_alternative_confirmation"
    state = apply(store, state, token, "alternative_accepted")
    assert state["current"]["id"] == "pec-deck"
    assert state["phase"] == "awaiting_equipment"


def test_excluded_alternative_is_not_offered(store):
    state, token = session(store, preferences=Preferences(mode="alternatives", excluded_exercise_ids=["pec-deck"]))
    state = apply(store, state, token, "equipment_taken")
    assert state["pending_alternative"] is None
    assert state["current"]["id"] == "seated-row"


def test_all_taken_blocks_without_loop(store):
    state, token = session(store)
    for _ in range(3):
        state = apply(store, state, token, "equipment_taken")
    assert state["phase"] == "blocked" and len(state["deferred"]) == 3


def test_rest_survives_restart(store):
    state, token = session(store)
    state = apply(store, state, token, "equipment_claimed")
    state = apply(store, state, token, "set_completed")
    restarted = Store(store.path, CATALOG)
    assert restarted.get(state["session_id"], token)["rest_deadline"] == state["rest_deadline"]
    future = datetime.fromisoformat(state["rest_deadline"]) + timedelta(seconds=1)
    expired = restarted.get(state["session_id"], token, future)
    assert expired["phase"] == "exercising"
    assert restarted.get(state["session_id"], token, future)["version"] == expired["version"]


def test_end_prevents_rest_and_keeps_partial_sets(store):
    state, token = session(store)
    state = apply(store, state, token, "equipment_claimed")
    state = apply(store, state, token, "set_completed")
    state = apply(store, state, token, "end_session")
    future = datetime.now(timezone.utc) + timedelta(days=1)
    assert store.get(state["session_id"], token, future)["phase"] == "ended"
    assert store.summary(state["session_id"], token)["completed_sets"] == 1


def test_bad_tokens_and_server_only_rest(tmp_path):
    with TestClient(create_app(str(tmp_path / "api.sqlite3"))) as client:
        created = client.post("/sessions", json={}).json()
        sid, token = created["snapshot"]["session_id"], created["access_token"]
        assert client.get(f"/sessions/{sid}", headers={"Authorization": "Bearer bad"}).status_code == 401
        event = action(created["snapshot"], "equipment_claimed").model_dump(mode="json")
        event["type"] = "rest_elapsed"
        assert client.post(f"/sessions/{sid}/events", json=event, headers={"Authorization": f"Bearer {token}"}).status_code == 422
        with client.websocket_connect(f"/sessions/{sid}/stream") as ws:
            ws.send_json({"access_token": token})
            assert ws.receive_json()["snapshot"]["version"] == 1


def test_reject_empty_plan(store):
    with pytest.raises(StoreError):
        session(store, preferences=Preferences(excluded_exercise_ids=["chest-press", "seated-row", "leg-extension"]))


def test_http_snapshot_contract_and_voice_not_configured(tmp_path, monkeypatch):
    from backend.spotter.models import Snapshot
    monkeypatch.delenv('ELEVENLABS_API_KEY', raising=False)
    monkeypatch.delenv('ELEVENLABS_AGENT_ID', raising=False)
    with TestClient(create_app(str(tmp_path / 'contract.sqlite3'))) as client:
        response = client.post('/sessions', json={'demo_mode': True})
        assert response.status_code == 201
        created = response.json()
        Snapshot.model_validate(created['snapshot'])
        token = created['access_token']
        sid = created['snapshot']['session_id']
        headers = {'Authorization': f'Bearer {token}'}
        assert client.post('/voice/token', json={'session_id': sid}, headers=headers).status_code == 503
        assert client.get('/health').json()['voice_configured'] is False
        preflight = client.options('/sessions', headers={'Origin': 'http://localhost:8081', 'Access-Control-Request-Method': 'POST'})
        assert preflight.headers['access-control-allow-origin'] == 'http://localhost:8081'
        event = action(created['snapshot'], 'equipment_claimed').model_dump(mode='json')
        accepted = client.post(f'/sessions/{sid}/events', headers=headers, json=event)
        assert accepted.status_code == 200
        Snapshot.model_validate(accepted.json()['snapshot'])
        assert accepted.json()['snapshot']['phase'] == 'exercising'


def test_snapshot_broadcast_after_another_client_action(tmp_path):
    with TestClient(create_app(str(tmp_path / 'stream.sqlite3'))) as client:
        created = client.post('/sessions', json={}).json()
        state = created['snapshot']
        sid, token = state['session_id'], created['access_token']
        with client.websocket_connect(f'/sessions/{sid}/stream') as ws:
            ws.send_json({'access_token': token})
            assert ws.receive_json()['snapshot']['version'] == 1
            result = client.post(f'/sessions/{sid}/events', headers={'Authorization': f'Bearer {token}'}, json=action(state, 'equipment_taken').model_dump(mode='json'))
            assert result.status_code == 200
            assert ws.receive_json()['snapshot']['current']['id'] == 'seated-row'


def test_stream_reconnect_returns_authoritative_snapshot_and_pong(tmp_path):
    with TestClient(create_app(str(tmp_path / 'reconnect.sqlite3'))) as client:
        created = client.post('/sessions', json={}).json()
        state = created['snapshot']
        sid, token = state['session_id'], created['access_token']
        with client.websocket_connect(f'/sessions/{sid}/stream') as ws:
            ws.send_json({'access_token': token})
            first = SnapshotFrame.model_validate(ws.receive_json())
            assert first.snapshot.version == 1

        event = action(state, 'equipment_taken').model_dump(mode='json')
        event['source'] = 'watch'
        accepted = client.post(
            f'/sessions/{sid}/events',
            headers={'Authorization': f'Bearer {token}'},
            json=event,
        )
        assert accepted.status_code == 200
        assert accepted.json()['replayed'] is False

        with client.websocket_connect(f'/sessions/{sid}/stream') as ws:
            ws.send_json({'access_token': token})
            reconnected = SnapshotFrame.model_validate(ws.receive_json())
            assert reconnected.snapshot.version == accepted.json()['snapshot']['version']
            assert reconnected.snapshot.current.id == 'seated-row'
            ws.send_text('ping')
            assert ws.receive_json() == {'type': 'pong'}

        replay = client.post(
            f'/sessions/{sid}/events',
            headers={'Authorization': f'Bearer {token}'},
            json=event,
        )
        assert replay.status_code == 200
        assert replay.json()['replayed'] is True
        assert replay.json()['snapshot'] == accepted.json()['snapshot']


@pytest.mark.parametrize('authorization', [{}, {'access_token': ''}, {'access_token': 'bad'}])
def test_stream_rejects_invalid_authorization(tmp_path, authorization):
    with TestClient(create_app(str(tmp_path / 'stream-auth.sqlite3'))) as client:
        created = client.post('/sessions', json={}).json()
        sid = created['snapshot']['session_id']
        with client.websocket_connect(f'/sessions/{sid}/stream') as ws:
            ws.send_json(authorization)
            with pytest.raises(WebSocketDisconnect) as exc:
                ws.receive_json()
            assert exc.value.code == 1008


def test_catalog_machine_knowledge_integrity():
    assert len(CATALOG['exercises']) == 18
    assert len(CATALOG['muscle_groups']) == 10
    exercise_ids = {exercise['id'] for exercise in CATALOG['exercises']}
    group_ids = {group['id'] for group in CATALOG['muscle_groups']}
    assert len(exercise_ids) == 18
    for exercise in CATALOG['exercises']:
        assert exercise['primary_muscle_group'] in group_ids
        assert set(exercise['secondary_muscle_groups']) <= group_ids
        assert set(exercise['alternatives']) <= exercise_ids
        assert exercise['review_status'] == 'professional_review_pending'
        assert exercise['sources'] and all(source['url'].startswith('https://') for source in exercise['sources'])
        assert exercise['weight_min_lb'] < exercise['weight_max_lb']
        assert exercise['weight_min_lb'] % exercise['weight_step_lb'] == 0
        assert exercise['weight_max_lb'] % exercise['weight_step_lb'] == 0
        for alternative_id in exercise['alternatives']:
            alternative = next(item for item in CATALOG['exercises'] if item['id'] == alternative_id)
            assert alternative['primary_muscle_group'] == exercise['primary_muscle_group']


def test_plan_preview_is_balanced_deduplicated_and_capped(tmp_path):
    with TestClient(create_app(str(tmp_path / 'plan-preview.sqlite3'))) as client:
        preview = client.post('/plans/preview', json={'muscle_group_ids': ['chest', 'back', 'quadriceps']})
        assert preview.status_code == 200
        assert [item['exercise_id'] for item in preview.json()['plan']] == [
            'chest-press', 'lat-pulldown', 'leg-press',
            'pec-deck', 'seated-row', 'leg-extension',
        ]
        capped = client.post('/plans/preview', json={'muscle_group_ids': [
            'chest', 'back', 'shoulders', 'biceps', 'triceps',
            'quadriceps', 'hamstrings', 'glutes', 'calves', 'core',
        ]})
        ids = [item['exercise_id'] for item in capped.json()['plan']]
        assert len(ids) == 8
        assert len(ids) == len(set(ids))
        assert client.post('/plans/preview', json={'muscle_group_ids': ['unknown']}).status_code == 422


def test_custom_plan_settings_and_validation(tmp_path):
    with TestClient(create_app(str(tmp_path / 'custom-plan.sqlite3'))) as client:
        body = {
            'selected_muscle_group_ids': ['chest'],
            'plan': [{'exercise_id': 'chest-press', 'sets': 3, 'reps': 12, 'weight_lb': 25}],
            'demo_mode': True,
        }
        created = client.post('/sessions', json=body)
        assert created.status_code == 201
        current = created.json()['snapshot']['current']
        assert (current['id'], current['sets'], current['reps'], current['weight_lb']) == ('chest-press', 3, 12, 25)

        duplicate = {**body, 'plan': body['plan'] * 2}
        assert client.post('/sessions', json=duplicate).status_code == 422
        wrong_group = {**body, 'selected_muscle_group_ids': ['calves']}
        assert client.post('/sessions', json=wrong_group).status_code == 422
        out_of_range = {**body, 'plan': [{**body['plan'][0], 'weight_lb': 500}]}
        assert client.post('/sessions', json=out_of_range).status_code == 422
        invalid_increment = {**body, 'plan': [{**body['plan'][0], 'weight_lb': 7}]}
        assert client.post('/sessions', json=invalid_increment).status_code == 422


def test_custom_alternative_resets_weight(store):
    request = CreateSession(
        preferences=Preferences(mode='alternatives'),
        selected_muscle_group_ids=['chest'],
        plan=[{'exercise_id': 'chest-press', 'sets': 3, 'reps': 12, 'weight_lb': 25}],
    )
    created = store.create(request)
    state, token = created['snapshot'], created['access_token']
    state = apply(store, state, token, 'equipment_taken')
    state = apply(store, state, token, 'alternative_accepted')
    assert state['current']['id'] == 'pec-deck'
    assert state['current']['weight_lb'] is None
    assert state['current']['sets'] == 2
    assert state['current']['reps'] == 10
