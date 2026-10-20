# Two Vercel projects from one repository

Each application is now a self-contained Vercel root. Both projects connect to
this same Git repository and production branch. No alternate config flag, staging
copy or repository-root deployment is needed.

## Project settings

In Vercel, import this repository twice (or update the two existing projects).
Under Settings → Build and Deployment, use:

| Setting | Frontend project | Backend project |
| --- | --- | --- |
| Root Directory | `mobile` | `backend` |
| Framework Preset | Other | FastAPI |
| Install | `npm ci` | `python -m pip install -r requirements.txt` |
| Build | `node scripts/check_web_deploy.mjs && npm run export:web` | No custom build |
| Output | `dist` | Default |
| Config | `mobile/vercel.json` | `backend/vercel.json` |

Clear old project-level install/build/output overrides; the configs provide these
settings. Frontend Node version is 24.x. Root-level vercel.json, pyproject.toml and
requirements.txt have been removed to prevent selecting the wrong app. Backend
pyproject.toml selects `spotter.app:app` directly, where the FastAPI instance is created. Backend imports, catalog and SQL migrations all
live within its root. Including source files outside either root is unnecessary.

Reconnect the backend project's Git integration if you disconnected it for the
previous CLI workflow. Connect both projects to the same production branch.
After committing and pushing this migration, verify the new commit is selected
for each deployment; redeploying an older commit does not include the new layout.
Git-triggered deployments do not upload local Pods or virtual environments.
Per-app .vercelignore files also exclude generated native projects, environments,
local database files and caches from CLI uploads.

Reference: [Vercel monorepos](https://vercel.com/docs/monorepos).

## Environment variables

Set these in the frontend project for Production (and Preview if used):

| Variable | Value |
| --- | --- |
| EXPO_PUBLIC_API_URL | Backend HTTPS origin, without /docs or /health |
| EXPO_PUBLIC_GOOGLE_CLIENT_ID | Google OAuth web client ID |

The export validates these variables and bakes them into its JavaScript. Rebuild
after changes. Never put database URLs or provider secrets in public variables.

Set these in the backend project:

| Variable | Value |
| --- | --- |
| DATABASE_URL | Neon PostgreSQL connection string with generated SSL parameters |
| GOOGLE_CLIENT_ID | Same Google web client ID |
| ELEVENLABS_API_KEY | Private provider key |
| ELEVENLABS_AGENT_ID | Published agent ID |
| SPOTTER_CORS_ORIGINS | Exact frontend HTTPS origins, comma-separated, no trailing slash |

Production must use Neon, not SQLite on an ephemeral filesystem. Backend loads
its local .env only for development, without overriding hosting environment values.
Local .env files and SQLite backups were not moved, uploaded or imported.

Add the frontend production origin to the Google OAuth client's authorized
JavaScript origins. Preview origins need explicit Google and CORS setup too.
After changing backend environment settings, create a new backend deployment.

## Validation after deployment

1. Deploy backend; verify /health returns JSON, /catalog returns 18 exercises and
   /docs loads FastAPI's API UI. Check Vercel runtime logs for startup errors.
2. Deploy frontend; verify / and a direct /watch reload work.
3. Confirm catalog preflight succeeds from the actual frontend origin. A Vercel
   NOT_FOUND response means routing/deployment must be fixed before CORS.
4. Sign in with Google, save a profile, start a workout, complete a set, and wait
   for rest expiry. Reload and confirm saved state remains in Neon.
5. Verify live synchronization between workout and watch tabs, reconnects, actual
   voice input/output and cleanup. These hosted checks remain separate from tests.

A successful static export or local WebSocket test does not prove Vercel runtime
WebSocket support or live voice acceptance.

## Local commands and compatibility

From repository root, existing `python scripts/run_backend.py` and imports from
`backend.app` remain available through a thin entrypoint. Runtime implementation
modules now live in backend/spotter, with relative package imports. Update direct
internal imports to backend.spotter.*. From backend/, the independent entrypoint
is `python -m uvicorn app:app --host 127.0.0.1 --port 8000`.

Default SQLite location is backend/data/spotter.sqlite3, resolved from the service
files. If you explicitly set SPOTTER_DATABASE to a relative path, it remains
relative to the process working directory; use a suitable path for that command.
DATABASE_URL takes precedence. Existing local databases and ignored environment
files remain intact. Backend catalog's sole runtime source is now
backend/catalog/demo.json; edit that file rather than maintaining a duplicate.

Install from repo root with `python -m pip install -r backend/requirements.txt`.
Run regression tests with `python -m pytest backend/tests -q`. Routine tests
isolate themselves from developer/cloud DB credentials. Actual PostgreSQL cases
run only when SPOTTER_TEST_DATABASE_URL points to a disposable localhost database
named spotter_test*. Those tests erase its application tables between cases.

## Existing SQLite records and Neon

No personal records are transferred by this layout change. To migrate records,
stop SQLite writers and preserve a backup first. From repository root:

```sh
python -m backend.spotter.migrate_sqlite
python -m backend.spotter.migrate_sqlite --apply
```

The first command reports source counts. Apply copies all four application tables
in one transaction, retaining IDs, state, event deduplication records and token
hashes. It refuses a nonempty target; the source is read-only and is not deleted.
The pending real-data transfer still requires the owner's explicit approval.
Returning to SQLite requires clearing DATABASE_URL and restarting; cloud changes
do not synchronize back to the old file.

PostgreSQL transactions retain the serialized store model via a transaction-scoped
advisory lock. This targets the current small app, not high-throughput scaling.
Connections close after each transaction with bounded waits. Schema changes are
tracked in backend/spotter/migrations and schema_migrations.

PostgreSQL has no idle rest scan: server reads/actions and active streams reconcile
persisted deadlines. When disconnected, reconciliation waits for the next request.
Active streams still poll; close workout tabs to allow Neon to become idle.
SQLite retains its local worker. Client requests cannot skip rest deadlines.

Snowflake export remains SQLite-only; its updated command is
`python -m backend.spotter.snowflake_sync --dry-run`. It does not export new Neon
events. See docs/SNOWFLAKE.md for provider setup and validation boundaries.


Backend empty-output troubleshooting: the backend config intentionally omits
buildCommand and outputDirectory. Do not set Build Command to an enabled empty
override or set a static output directory. Clear dashboard overrides, deploy a
new commit without cache, and confirm deployment outputs include a Python
function. A Ready deployment containing only a zero-millisecond '.' build does
not establish API readiness. The frontend configuration is unrelated to this fix.


## Public privacy policy

Published separately with Sites on October 20, 2026:
https://spotter-privacy.mellowcabin4.chatgpt.site

Source: sites/spotter-privacy/dist/index.html; hosting identity:
sites/spotter-privacy/.openai/hosting.json. The page is public without sign-in.
Privacy/deletion contact: mdasthanmay@gmail.com. The sign-in screen links to this
URL in local source; publish the frontend to make that link visible in production.
Google brand verification remains separate: verify homepage linkage and any
required domain ownership; a working policy URL alone does not establish approval.

Terms of Service (published October 20, 2026):
https://spotter-privacy.mellowcabin4.chatgpt.site/terms/

Source: sites/spotter-privacy/dist/terms/index.html. Both legal pages link to one
another. Paste this URL into Application terms of service link. The app sign-in
terms link is in local source and awaits the next frontend deployment.
