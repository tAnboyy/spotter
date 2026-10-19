"""Explicit, retryable workout analytics export; never runs in the request path."""
import argparse
import json
import os
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def extract(database: str) -> list[dict]:
    """Read a consistent snapshot and export an allowlist, excluding profiles/secrets."""
    rows = []
    with sqlite3.connect(Path(database).resolve().as_uri() + '?mode=ro', uri=True) as db:
        for session_id, event_id, request_json, result_json in db.execute(
            'SELECT session_id,event_id,request,result FROM events ORDER BY session_id,event_id'
        ):
            request, state = json.loads(request_json), json.loads(result_json)
            entries = [e for key in ('queue', 'deferred', 'completed', 'skipped') for e in state.get(key, [])]
            if state.get('current'):
                entries.append(state['current'])
            exercise = next((e for e in entries if e['instance_id'] == request.get('exercise_instance_id')), {})
            record = next((r for r in exercise.get('set_records', []) if r['set_index'] == request.get('set_index')), {}) if request['type'] == 'set_completed' else {}
            rows.append({
                'session_id': session_id, 'event_id': event_id,
                'action': request['type'], 'source': request['source'],
                'occurred_at': state['server_time'], 'session_created_at': state['created_at'],
                'session_version': state['version'], 'phase': state['phase'],
                'demo_mode': state.get('demo_mode', False),
                'exercise_id': exercise.get('id'), 'exercise_name': exercise.get('name'),
                'exercise_instance_id': request.get('exercise_instance_id'),
                'set_index': request.get('set_index'),
                'duration_seconds': record.get('duration_seconds'),
                'planned_reps': record.get('planned_reps'), 'weight_lb': record.get('weight_lb'),
            })
    return rows


def sync(connection, rows: list[dict]) -> int:
    """One operator at a time; staging is connection-local and retries merge by event ID."""
    with connection.cursor() as cursor:
        cursor.execute('CREATE TABLE IF NOT EXISTS SPOTTER_WORKOUT_EVENTS (SESSION_ID VARCHAR, EVENT_ID VARCHAR, DATA VARIANT)')
        cursor.execute('CREATE OR REPLACE TEMPORARY TABLE SPOTTER_EVENT_STAGE (SESSION_ID VARCHAR, EVENT_ID VARCHAR, PAYLOAD VARCHAR)')
        for offset in range(0, len(rows), 500):
            cursor.executemany('INSERT INTO SPOTTER_EVENT_STAGE VALUES (%s,%s,%s)', [
                (r['session_id'], r['event_id'], json.dumps(r)) for r in rows[offset:offset + 500]
            ])
        cursor.execute('''MERGE INTO SPOTTER_WORKOUT_EVENTS t USING
            (SELECT SESSION_ID, EVENT_ID, PARSE_JSON(PAYLOAD) AS DATA FROM SPOTTER_EVENT_STAGE) s
            ON t.SESSION_ID=s.SESSION_ID AND t.EVENT_ID=s.EVENT_ID
            WHEN NOT MATCHED THEN INSERT (SESSION_ID,EVENT_ID,DATA) VALUES (s.SESSION_ID,s.EVENT_ID,s.DATA)''')
        cursor.execute('''CREATE OR REPLACE VIEW SPOTTER_EQUIPMENT_INSIGHTS AS
            SELECT DATA:demo_mode::BOOLEAN AS DEMO_MODE,
                DATA:exercise_id::VARCHAR AS EXERCISE_ID,
                DATA:exercise_name::VARCHAR AS EXERCISE_NAME,
                COUNT_IF(DATA:action::VARCHAR='equipment_taken') AS TAKEN_REPORTS,
                COUNT_IF(DATA:action::VARCHAR='equipment_claimed') AS EQUIPMENT_CLAIMS,
                COUNT_IF(DATA:action::VARCHAR='set_completed') AS COMPLETED_SETS,
                AVG(IFF(DATA:action::VARCHAR='set_completed', DATA:duration_seconds::FLOAT, NULL)) AS AVG_SET_SECONDS
            FROM SPOTTER_WORKOUT_EVENTS WHERE DATA:exercise_id::VARCHAR IS NOT NULL
            GROUP BY 1,2,3''')
    return len(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', default=os.environ.get('SPOTTER_DATABASE', str(ROOT / 'data/spotter.sqlite3')))
    parser.add_argument('--dry-run', action='store_true', help='Validate local extraction; print only counts, without connecting')
    args = parser.parse_args()
    rows = extract(args.database)
    if args.dry_run:
        print(json.dumps({'mode': 'dry_run', 'accepted_events': len(rows), 'sessions': len({r['session_id'] for r in rows})}))
        return
    name = os.environ.get('SNOWFLAKE_CONNECTION_NAME')
    if not name:
        parser.error('Set SNOWFLAKE_CONNECTION_NAME to a configured Python connector connection; see docs/SNOWFLAKE.md')
    try:
        import snowflake.connector
    except ImportError:
        parser.error('Install backend/requirements-snowflake.txt first')
    with snowflake.connector.connect(connection_name=name, autocommit=True) as connection:
        count = sync(connection, rows)
        print(json.dumps({'status': 'synced', 'source_events': count}))
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM SPOTTER_EQUIPMENT_INSIGHTS ORDER BY TAKEN_REPORTS DESC')
            print(json.dumps({'equipment_insights': [dict(zip([c[0] for c in cursor.description], row)) for row in cursor.fetchall()]}, default=str))


if __name__ == '__main__':
    main()
