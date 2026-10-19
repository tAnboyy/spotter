# Snowflake workout analytics

SQLite remains authoritative for live workouts. The operator command exports accepted events to Snowflake and queries equipment insights. Snowflake outages do not affect sets/rest/voice. This is an explicit batch sync, not automatic streaming or a replacement database.

## Setup

Install the optional connector from the repository root:

```sh
python -m pip install -r backend/requirements-snowflake.txt
```

Use your virtual environment's Python (`.venv/bin/python` on macOS, `.venv\Scripts\python.exe` on Windows). Configure a named `spotter` connection in the Python connector's local `connections.toml`, outside the repository. See the [official connection guide](https://docs.snowflake.com/en/developer-guide/python-connector/python-connector-connect#connecting-using-the-connections-toml-file) for OS-specific locations and authentication choices.

```toml
[spotter]
account = "YOUR_ORG-YOUR_ACCOUNT"
user = "YOUR_USER"
authenticator = "externalbrowser"
warehouse = "YOUR_WAREHOUSE"
database = "YOUR_DATABASE"
schema = "YOUR_DEDICATED_SPOTTER_SCHEMA"
role = "YOUR_ROLE"
```

The database/schema/warehouse must already exist. The role needs USAGE on those resources, CREATE TABLE/VIEW in the dedicated schema, and access to the objects it creates. Browser authentication requires account support; otherwise use an account-approved connector authentication method. Keep passwords/keys out of chat and Git.

Set the connection name in the terminal (the command does not automatically load backend/.env):

macOS:
```sh
export SNOWFLAKE_CONNECTION_NAME=spotter
```
Windows PowerShell:
```powershell
$env:SNOWFLAKE_CONNECTION_NAME = 'spotter'
```

Inspect counts locally, then sync:

```sh
python -m backend.spotter.snowflake_sync --dry-run
python -m backend.spotter.snowflake_sync
```

Use `--database path/to/spotter.sqlite3` when needed. The source opens read-only and a missing path fails without creating a database. The sync creates `SPOTTER_WORKOUT_EVENTS` and replaces the dedicated `SPOTTER_EQUIPMENT_INSIGHTS` view; it prints queried Snowflake results only after sync succeeds. Connection/authentication/SQL failures exit unsuccessfully. Run only one sync operator at a time: standard Snowflake tables do not enforce unique keys. Sequential retries use MERGE on session/event IDs and do not append duplicate events. Every run scans all accepted events; appropriate for the hackathon, not a large production dataset. Local deletion does not delete already exported cloud rows.

## Demo

1. Run a workout, report Taken, claim another machine, complete a set.
2. Run the sync command.
3. Open a Snowflake worksheet in the configured schema and run:

```sql
SELECT * FROM SPOTTER_EQUIPMENT_INSIGHTS
ORDER BY TAKEN_REPORTS DESC, COMPLETED_SETS DESC;

SELECT DATA:action::VARCHAR AS ACTION, COUNT(*) AS ACCEPTED_EVENTS
FROM SPOTTER_WORKOUT_EVENTS GROUP BY 1 ORDER BY 2 DESC;
```

Taken counts are user reports, not measured occupancy. Reps are planned, not sensor-counted. Set duration is elapsed backend time. Demo-mode rows are grouped separately, but non-demo mode does not prove a real gym visit. The allowlist exports pseudonymous session/event IDs, exercise identifiers/names, action/source, timestamps/version/phase, demo mode and recorded set metrics. It excludes account/profile data, tokens/hashes, trainer preferences, free-form motivation and transcripts. Sessions with no accepted actions are absent; counts are not a total of all created sessions.

Local tests validate extraction and replay behavior. Live account authentication, SQL execution, repeated-sync row counts and judge-visible results require a configured account; do not claim these passed until verified.
