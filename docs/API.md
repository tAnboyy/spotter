# API contract, schema version 1

Pydantic models in `backend/spotter/models.py` define input/response shapes. Regenerate `contracts/*.schema.json` and `contracts/openapi.json` with `python scripts/export_contracts.py`. The web runtime schemas in `mobile/src/api/schema.ts` validate every consumed snapshot; update them when the producer changes. Set indexes start at 1; times are UTC ISO 8601.

## Routes

| Route | Authorization | Result |
|---|---|---|
| GET /health | None | API status, voice configuration, and Google sign-in configuration |
| GET /catalog | None | Fictional gym, 18 source-backed machines, muscle groups and review status |
| POST /auth/google | None | Verify a Google ID token and return a user profile plus profile access token |
| GET /profile | Bearer profile token | Saved name, preferences, last muscle groups and plan |
| PUT /profile/schedule | Bearer profile token | Replace the recurring weekly workout templates |
| PUT /profile | Bearer profile token | Replace saved name, preferences, last muscle groups and plan |
| POST /plans/preview | None, local prototype | Deterministic PlanPreview for selected muscle groups |
| POST /sessions | None, local prototype | CreateResult: snapshot + session access token |
| GET /sessions/{id} | Bearer session token | Snapshot |
| POST /sessions/{id}/events | Bearer session token | EventResult: snapshot + replayed flag |
| GET /sessions/{id}/summary | Bearer session token | Actual completed/partial/skipped/substituted work |
| POST /voice/token | Bearer session token | Short-lived ElevenLabs WebRTC token; session_id in body |
| WS /sessions/{id}/stream | First JSON frame carries access_token | Versioned snapshot frames, optional ping/pong |

Google sign-in body: `{"id_token":"..."}`. The backend verifies the token against `GOOGLE_CLIENT_ID` with Google tokeninfo, upserts a persisted user keyed by Google `sub`, and returns `{profile, access_token}`. The profile token is separate from the workout session token. `PUT /profile` stores the approved name, preferences, selected muscle groups and plan for the next visit. The web landing gates setup on Google sign-in; backend session endpoints retain their local prototype authorization policy and native development setup remains available. `/health.google_auth_configured` reports a nonblank `GOOGLE_CLIENT_ID` only.

Plan preview body: `{"muscle_group_ids":["chest","back"]}`. The backend selects up to two configured machines per group in round-robin order, removes duplicates and caps the result at eight.

Customized create body: `{"routine_id":"full-body","selected_muscle_group_ids":["chest"],"plan":[{"exercise_id":"chest-press","sets":3,"reps":12,"weight_lb":25}],"preferences":{"name":"Rahul","mode":"strict","coaching":"standard","excluded_exercise_ids":[]},"demo_mode":true}`. Plans contain 1–8 unique machines. Sets are 1–5, reps 1–30 and optional pound values must match that machine's configured range and increment. A plan exercise must train at least one selected group. Omitting both selected groups and plan retains the original `full-body` compatibility routine. Demo rests are 5 seconds; normal rests are 60.

WebSocket clients first send `StreamAuthorization` and receive a current `SnapshotFrame` after authorization. Each later committed version is sent once per connection. Reconnecting starts with the authoritative current snapshot; the server does not replay command frames. A text `ping` receives `PongFrame`. Invalid, missing or empty authorization closes with code 1008. These frame schemas are exported in `contracts/`.

Session state is persisted in SQLite. Rest expiry is backend-owned, checked periodically and on read/action. Events serialize inside BEGIN IMMEDIATE transactions; deduplication precedes version validation. Reused IDs with different content are rejected. Separate stale actions return 409 with fresh snapshot. Do not auto-retarget stale commands to a new set. Replayed old snapshots must not regress a newer client state.

Errors: 401 invalid/missing session access; 409 stale/version conflict; 422 invalid target/phase/schema/preferences; 503 voice not configured; 502 voice provider authorization failed. Domain errors return message and optional snapshot; FastAPI schema validation errors use detail. Clients handle both.

### Stage 2 voice authorization and tools

Dashboard compatibility update: submit_workout_action requires action; exercise_instance_id and set_index may be omitted for end_session/retry_deferred. Frontend normalizes omitted fields to null and rejects missing/stale instance or set for every exercise action. Event HTTP contract is unchanged. Dashboard parameter JSON uses an array of form descriptors, unlike the JSON Schema object in canonical specifications; do not paste those schemas directly into its form-JSON editor.

`POST /voice/token` accepts only `{"session_id":"..."}` and a Bearer token for that session. Invalid/cross-session tokens are rejected before provider contact. Completed/ended sessions return 409. Response remains `{"conversation_token":"..."}` for existing client compatibility, typed in VoiceAuthorization.schema.json. Successful responses use Cache-Control: no-store. Backend key and agent ID never enter this response. Provider auth has a 10-second timeout, does not follow redirects or cache tokens, and suppresses upstream bodies/errors. `/health.voice_configured` reports nonblank environment presence only.

The provider token authorizes the configured agent, not arbitrary workout actions; the separate session token still protects events. An already-connected conversation must be stopped by the frontend when the workout ends. Tokens are provider-issued short-lived credentials; this backend does not invent an expiry or claim provider-side revocation.

`backend/tool_contract.py` produces `contracts/client-tools.json` and `agent/tools.json`. The three names remain get_session_state, get_exercise_guidance(exercise_id), submit_workout_action(action, exercise_instance_id, set_index). All await responses. Guidance and state are read-only; action enum matches backend Event types and excludes rest_elapsed. Target `current.instance_id`, not `current.id`; current 1-based set_index is used for exercise actions, null targets for retry/end. Models define tool argument shapes; app handlers remain responsible for runtime validation and event submission. Agent setup: agent/README.md. No second conversation engine or backend tool executor is introduced.

Unavailable equipment is session-local. Strict mode defers it. When remaining work is deferred, enter blocked and explicitly retry it. There is no global occupancy feed. Alternative acceptance creates a new exercise instance with its own catalog defaults, resets weight to null and still requires equipment confirmation.

### Machine guidance

Each catalog machine has an exact ID, fictional location, primary/secondary muscle groups, setup, cue, common mistake, troubleshooting, stop conditions, weight-slider bounds, approved alternatives, public source URLs and `professional_review_pending` status. Guidance is developer-paraphrased and source-backed, not professionally certified. Clients and Mat retrieve exact records; there is no vector search or approximate machine matching.

## Joining browser watch controls

Stage 1 uses a development-only manual exchange of session ID/token from the trainer to `/watch`. They never appear in URLs. Each tab stores its own credential in sessionStorage so refresh works. Production login/short-lived pairing code is not implemented; do not expose this local prototype publicly.

## Known stage boundaries

SQLite backend uses one uvicorn process. WebSocket transport publishes committed snapshots by reading authoritative state, every 0.5 seconds. No native WatchConnectivity or watch mic streaming. Catalog text is developer-authored, professional review pending. Agent provisioning and live voice testing require provider configuration.


## Trainer persona (October 11, additive schema version 1)

`preferences.trainer` is accepted by profile updates and session creation and returned in profiles/snapshots. Omitted values default to `{ "name": "Mat", "color": "blue", "expression": "happy", "accessory": "headband", "motivation": "", "remind": true }`. Name is 1–30 characters; motivation is 0–240. Color: blue/mint/peach; expression: happy/calm/bold; accessory: headband/headphones/none. Existing JSON profile/session storage needs no SQL migration. The client trims name/motivation; blank names cannot be saved in the editor. Older clients may omit the field. Swift watch does not decode preferences and tolerates the additive field.

The profile stores preferences for future workouts. A running session retains its creation-time persona. Reminders are presentation/voice cues, never workout events. Web stores up to 50 handled session IDs locally (no motivation text); native uses process memory consistent with its current session restoration. Cross-device exactly-once delivery is not promised.

## Set timers and confirmed weight changes — October 11

Additive schema-version-1 extension: `Snapshot.set_started_at` is a nullable UTC timestamp; each ExerciseInstance has `set_records`, containing `set_index`, nullable `started_at`, `completed_at`, nullable `duration_seconds`, `planned_reps`, and nullable `weight_lb`. The history is stored atomically inside the session SQLite JSON and returned in snapshots and summaries. Reps remain planning values; neither timing nor reps are measured by sensors.

Equipment confirmation starts the first timer at backend acceptance. Set completion stops it and records elapsed wall-clock seconds, including pauses until the user completes the set. Between sets it is stopped during rest, then starts at the saved rest deadline (not a delayed scheduler/restart tick). Reading or reconnecting never resets a start. Skip/end clears the active timer without fabricating a completed set. Legacy sessions receive empty history and a null timer; a previously active set records unknown timing rather than inventing it. Previous completed sets are not backfilled. Old clients may ignore these additive output fields; update all clients/tools before using the new action.

`weight_updated` requires the current `exercise_instance_id` and 1-based `set_index` in exercising/resting. Payload contains exactly one positive integer: `{"weight_increase_lb":5}` or `{"weight_lb":55}`. Values use pounds, respect the catalog bounds/increment, and cannot be strings, booleans, zero or negative. An increase requires a known current weight. No other action accepts payload fields. It updates current/upcoming set weight, preserves saved set records, and does not alter rest or timer. Deduplication/stale/concurrent rules apply identically; rejected stale changes must not be retargeted automatically.

The existing `submit_workout_action` tool adds optional numeric `weight_lb` and `weight_increase_lb` arguments (exactly one only for `weight_updated`), plus the new action enum. Example: “increase by 5 lb” maps to `weight_increase_lb: 5`; “make it 55 lb” maps to `weight_lb: 55`. `agent/tools.json` and `contracts/client-tools.json` match the shared web/native handler. Synthetic examples: `contracts/examples/set-tracking.json`.

After completion with another set remaining, the decision offers a conditional catalog-step increase only when weight is known, within range, and at most 10% of the current load. It does not infer comfort or change weight automatically. Otherwise keep weight or ask for a total. The live agent must suppress progression suggestions after pain/difficulty reports and acknowledge mutations only after success. This is pending professional content review, not a certified prescription. Review background: https://pubmed.ncbi.nlm.nih.gov/19204579/ and https://acsm.org/resistance-training-guidelines-update-2026/ .

Provider configuration requirement: update the published Mat system prompt from `agent/prompt.md` and the existing client action tool from `agent/tools.json` before voice acceptance testing. Keep all three tools waiting for responses. These repo edits do not automatically publish the dashboard agent.

### Trainer language

`preferences.trainer.language` accepts `en` (English) and `es` (Spanish), defaulting to `en` when absent in old profiles, requests or persisted sessions. Profile updates and new workouts preserve the selection; unsupported codes return HTTP 422. This additive schema-version-1 field does not change workout events or units. The watch decoder ignores unused trainer preferences; no watch speech or menu translation is introduced. Voice startup uses the saved workout selection. See `agent/README.md` for required provider settings.

## Weekly workout templates — October 11

UserProfile adds `schedule` (defaults to an empty array for legacy profiles). `PUT /profile/schedule` accepts `{"schedule":[{"weekday":0,"time":"18:30","muscle_group_ids":["chest"],"plan":[{"exercise_id":"chest-press","sets":2,"reps":10,"weight_lb":50}]}]}`. Weekdays are 0 Monday through 6 Sunday. HH:MM is the user's local wall time; it is informational and sends no reminder. A week contains 1–7 distinct training days, each with 1–10 unique muscles and 1–8 valid catalog exercises. Plans receive the same catalog, muscle-match, excluded-exercise, settings and weight validation as session creation. An invalid day rejects the entire schedule write. Profile tokens remain separate from session tokens.

The new SQLite user_schedules table is keyed by user_id and created automatically without altering existing users/session data. Schedule is preserved when Google sign-in rotates a token, across backend restart, and through ordinary PUT /profile saves. Saving today's edited plan does not rewrite the weekly template. Create a plan is the explicit recurring-plan path: each saved day is written with PUT /profile/schedule. Canonical schemas: WeeklyWorkout, ScheduleUpdate, UserProfile and AuthResult. Session/watch/voice contracts are unchanged by weekly setup.

The shared app opens muscle selection after sign-in. Create a plan lists weekdays vertically; a selected day shows its HH:MM time and then that day’s muscle map and save action. Switching days keeps an unsaved draft for the day you left. Times do not gate workouts or send reminders. Previously completed/ended sessions are cleared when restored-profile setup is not the active workout screen, and an active workout is retained. Google authentication is still verified by the existing backend boundary.


## PostgreSQL persistence — October 19

No HTTP, tool, snapshot or schema-version changes. DATABASE_URL selects Neon
PostgreSQL, with SQLite retained when unset. Store transactions remain serialized
using a transaction-scoped advisory lock on PostgreSQL; deduplication and updates
commit atomically. Migration SQL is tracked in backend/spotter/migrations/.

PostgreSQL rest deadlines reconcile on server snapshot/event access (including
active streams), without an idle background database scan. With no clients, the
next request reconciles the deadline. Timer transitions remain server-authoritative
and idempotent; ended sessions do not advance. See docs/DEPLOYMENT.md for setup,
SQLite import and the current SQLite-only Snowflake exporter limitation.
