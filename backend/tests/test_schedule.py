from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from backend.app import CATALOG, create_app
from backend.spotter.models import ProfileUpdate, ScheduleUpdate
from backend.spotter.store import Store


def workout(weekday=0, time='18:00'):
    return {'weekday': weekday, 'time': time, 'muscle_group_ids': ['quadriceps', 'hamstrings'],
            'plan': [{'exercise_id': 'leg-press', 'sets': 3, 'reps': 10, 'weight_lb': 50}]}


@pytest.fixture
def account(tmp_path):
    path = str(tmp_path / 'schedule.sqlite3')
    app = create_app(path)
    auth = app.state.store.sign_in_google({'google_sub': 'schedule-test-user', 'email': 'test@example.com', 'name': 'Test Person'})
    with TestClient(app) as client:
        yield client, app.state.store, auth, path


def test_week_saved_restored_on_new_login_and_restart(account):
    client, store, auth, path = account
    headers = {'Authorization': f"Bearer {auth['access_token']}"}
    assert auth['profile']['schedule'] == []
    response = client.put('/profile/schedule', headers=headers, json={'schedule': [workout(4, '07:30'), workout(0)]})
    assert response.status_code == 200
    assert [day['weekday'] for day in response.json()['schedule']] == [0, 4]
    store = Store(path, CATALOG)
    again = store.sign_in_google({'google_sub': 'schedule-test-user', 'email': 'test@example.com', 'name': 'Test Person'})
    assert again['profile']['schedule'][1]['time'] == '07:30'
    assert again['profile']['schedule'][0]['plan'][0]['sets'] == 3
    assert client.get('/profile', headers=headers).status_code == 401
    assert client.get('/profile', headers={'Authorization': f"Bearer {again['access_token']}"}).json()['schedule'] == response.json()['schedule']


@pytest.mark.parametrize('days', [[], [workout(), workout()], [workout(7)], [workout(True)], [workout(time='25:00')], [workout(time='8:30')]])
def test_invalid_schedule_shape_is_rejected(account, days):
    client, _, auth, _ = account
    assert client.put('/profile/schedule', headers={'Authorization': f"Bearer {auth['access_token']}"}, json={'schedule': days}).status_code == 422


@pytest.mark.parametrize('patch', [{'muscle_group_ids': ['unknown']}, {'plan': [{'exercise_id':'leg-press','sets':3,'reps':10,'weight_lb':500}]}, {'plan':[{'exercise_id':'chest-press','sets':3,'reps':10,'weight_lb':50}]}, {'plan': []}, {'muscle_group_ids':['quadriceps','quadriceps']}])
def test_bad_day_does_not_partially_replace_saved_week(account, patch):
    client, _, auth, _ = account
    headers = {'Authorization': f"Bearer {auth['access_token']}"}
    assert client.put('/profile/schedule', headers=headers, json={'schedule':[workout()]}).status_code == 200
    bad = workout(2)
    bad.update(patch)
    assert client.put('/profile/schedule', headers=headers, json={'schedule':[workout(1), bad]}).status_code == 422
    assert client.get('/profile', headers=headers).json()['schedule'] == [workout()]


def test_daily_edits_do_not_change_weekly_template_or_other_user(account):
    client, store, auth, _ = account
    token = auth['access_token']
    store.save_schedule(token, ScheduleUpdate(schedule=[workout()]))
    daily_plan = deepcopy(workout()['plan'])
    daily_plan[0]['sets'] = 2
    profile = store.save_profile(token, ProfileUpdate(name='Test', preferences={}, muscle_group_ids=['quadriceps'], plan=daily_plan))
    assert profile['schedule'][0]['plan'][0]['sets'] == 3
    other = store.sign_in_google({'google_sub':'other-user', 'email':'other@example.com', 'name':'Other'})
    assert other['profile']['schedule'] == []
    assert client.put('/profile/schedule', json={'schedule':[workout()]}).status_code == 401


def test_schedule_catalog_exclusions_and_duplicate_equipment(account):
    client, store, auth, _ = account
    token = auth['access_token']
    store.save_profile(token, ProfileUpdate(name='Test', preferences={'excluded_exercise_ids':['leg-press']}, muscle_group_ids=[], plan=None))
    headers = {'Authorization':f'Bearer {token}'}
    assert client.put('/profile/schedule', headers=headers, json={'schedule':[workout()]}).status_code == 422
    store.save_profile(token, ProfileUpdate(name='Test', preferences={}, muscle_group_ids=[], plan=None))
    duplicate = workout()
    duplicate['plan'] *= 2
    assert client.put('/profile/schedule', headers=headers, json={'schedule':[duplicate]}).status_code == 422
