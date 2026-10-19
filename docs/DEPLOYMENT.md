# Separate Vercel frontend and backend projects

Root `vercel.json` is the frontend configuration. Keep the frontend Vercel
project's Root Directory at repository root, Framework Other, Node 24.x.
It installs in mobile/, exports the website and serves mobile/dist.
Set EXPO_PUBLIC_API_URL to the backend HTTPS domain and
EXPO_PUBLIC_GOOGLE_CLIENT_ID to the Google web client ID. Public values are
baked into each export; rebuild after changes.

## Backend configuration

`backend/vercel.json` is an alternate configuration, used **from repository root**.
Root `pyproject.toml` selects backend.app:app and root requirements.txt forwards
to backend/requirements.txt. Keeping the repository as build root preserves
backend package imports, catalog/demo.json and migration assets.

Deploy to your separate backend project explicitly with Vercel CLI:

```sh
npx vercel --project YOUR_BACKEND_PROJECT --local-config backend/vercel.json --prod
```

Replace YOUR_BACKEND_PROJECT with the backend project name or ID. Keep that
project's Root Directory at repository root too. Do not run this command from
backend/, and do not point the frontend project at this alternate configuration.
No deployment is performed by adding the file.

Important: a nested vercel.json does not automatically select itself for a Git
push when the project root is the repository. A normal Git deployment still
reads root vercel.json (the frontend). Use the explicit CLI command for backend
releases, and disable automatic Git deployments on the backend project if linked
so it does not accidentally build the frontend. A Git-based backend release would
need CI that explicitly selects the alternate configuration.

Remove saved npm/Expo install/build/output overrides from the backend project;
its alternate configuration installs Python requirements and selects FastAPI.
Frontend settings remain unchanged.

Reference: [Vercel CLI --local-config](https://vercel.com/docs/cli/global-options#local-config).

## Backend environment variables

Set these in Vercel for the deployment environment:

| Variable | Value |
| --- | --- |
| DATABASE_URL | Neon PostgreSQL URL with generated SSL parameters |
| GOOGLE_CLIENT_ID | Google OAuth web client ID |
| ELEVENLABS_API_KEY | Private provider key |
| ELEVENLABS_AGENT_ID | Published agent ID |
| SPOTTER_CORS_ORIGINS | Exact frontend origin(s), comma-separated |

Use Neon for this deployment; SQLite requires a persistent filesystem. Do not
configure a local SQLite path as the deployed storage. No EXPO_PUBLIC variables
are required to deploy the backend. On the separately hosted frontend, point
EXPO_PUBLIC_API_URL to the backend's HTTPS domain.

Deploy the frontend through Git and the backend with the explicit CLI command above. Verify `/health`,
`/catalog` and `/docs`, then authenticated session/profile requests and Neon
persistence. WebSocket transport, full workout and live voice require hosted
validation; a successful build does not prove them.

Reference: [Vercel FastAPI guide](https://vercel.com/docs/frameworks/backend/fastapi).

### Neon and existing records

The backend loads ignored `backend/.env`, preserving hosting environment values.
Selection priority is an explicit `create_app(database=...)` argument, nonempty
`DATABASE_URL`, `SPOTTER_DATABASE`, then the default SQLite file. A bad PostgreSQL
connection fails startup instead of silently falling back. Install the pinned
backend requirements first. Store initialization applies versioned SQL from
`backend/migrations/` and records it in `schema_migrations`.

To transfer existing records, stop Spotter processes writing to SQLite and back up
the file. From repository root:

```sh
.venv/bin/python -m backend.migrate_sqlite
.venv/bin/python -m backend.migrate_sqlite --apply
```

On Windows replace `.venv/bin/python` with `.\.venv\Scripts\python.exe`.
The default command reports only source counts. `--apply` creates the schema and
copies all four tables in one transaction, retaining IDs, token hashes, saved
state, event deduplication records and schedules. It refuses a nonempty target;
it never merges, overwrites or deletes source data. Transfer existing personal
records only with the owner's approval. To start fresh, launch against Neon
without importing; local records stay in SQLite. To return to SQLite, clear
`DATABASE_URL` and restart. Later Neon changes do not sync back automatically.

PostgreSQL transactions use one transaction-scoped advisory lock, preserving
SQLite's serialized store behavior across connections and working with Neon's
transaction pooler. This intentionally targets the current small app rather than
high-throughput scaling. Connections close after each transaction with bounded
connection, lock and statement waits.

There is no background PostgreSQL rest scan: server snapshot/action requests
reconcile persisted deadlines, including the snapshots fetched by active streams.
When everyone disconnects, reconciliation waits for the next request. Active
streams still query about twice per second; close workout tabs to allow Neon to
become idle. SQLite retains its local worker. No client can skip a deadline.

The optional Snowflake exporter still reads SQLite only. It will not export new
PostgreSQL events after switching to Neon; a PostgreSQL analytics adapter remains
a separate handoff.

Routine tests ignore developer database credentials:

```sh
.venv/bin/python -m pytest backend/tests -q
```

For PostgreSQL checks, set `SPOTTER_TEST_DATABASE_URL` to a disposable localhost
database named `spotter_test*`; these tests erase its application tables between
cases and reject cloud URLs. macOS example:

```sh
SPOTTER_TEST_DATABASE_URL=postgresql://USER@localhost:5432/spotter_test .venv/bin/python -m pytest backend/tests -q
```

PowerShell:

```powershell
$env:SPOTTER_TEST_DATABASE_URL='postgresql://USER@localhost:5432/spotter_test'
.\.venv\Scripts\python.exe -m pytest backend/tests -q
```
