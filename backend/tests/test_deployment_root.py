"""Exercise the backend with no files or import paths from its parent repo."""
import os
from pathlib import Path
import shutil
import subprocess
import sys


def test_backend_runs_as_an_isolated_deployment_root(tmp_path):
    source = Path(__file__).resolve().parents[1]
    deployment = tmp_path / 'deployment'
    deployment.mkdir()
    for name in ('app.py', 'requirements.txt', 'pyproject.toml', 'vercel.json'):
        shutil.copy2(source / name, deployment / name)
    for name in ('spotter', 'catalog'):
        shutil.copytree(source / name, deployment / name, ignore=shutil.ignore_patterns('__pycache__'))
    script = '''
import os, sys
sys.path.insert(0, os.getcwd())
from datetime import datetime, timedelta
from uuid import uuid4
from fastapi.testclient import TestClient
from app import app, create_app

with TestClient(app) as client:
    assert client.get('/health').status_code == 200
    assert len(client.get('/catalog').json()['exercises']) == 18
    assert client.get('/openapi.json').status_code == 200
    created = client.post('/sessions', json={}).json()
    state, token = created['snapshot'], created['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    sid = state['session_id']
    with client.websocket_connect(f'/sessions/{sid}/stream') as ws:
        ws.send_json({'access_token': token})
        assert ws.receive_json()['snapshot']['version'] == state['version']
        for kind in ('equipment_claimed', 'set_completed'):
            event = {'event_id': str(uuid4()), 'expected_version': state['version'],
                     'source': 'web', 'type': kind, 'exercise_instance_id': state['current']['instance_id'],
                     'set_index': state['set_index'], 'payload': {}}
            response = client.post(f'/sessions/{sid}/events', headers=headers, json=event)
            assert response.status_code == 200
            state = response.json()['snapshot']
            assert ws.receive_json()['snapshot']['version'] == state['version']
    assert state['phase'] == 'resting'
restored = create_app().state.store
assert datetime.fromisoformat(restored.get(sid, token)['rest_deadline']) == datetime.fromisoformat(state['rest_deadline'])
future = datetime.fromisoformat(state['rest_deadline']) + timedelta(seconds=1)
assert restored.get(sid, token, future)['phase'] == 'exercising'
print('Isolated backend root: health/catalog/OpenAPI/session/WebSocket/rest persistence PASS')
'''
    env = dict(os.environ, DATABASE_URL='', SPOTTER_DATABASE=str(tmp_path / 'isolated.sqlite3'))
    result = subprocess.run([sys.executable, '-I', '-c', script], cwd=deployment,
                            env=env, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
