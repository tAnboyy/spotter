# Initial implementation handoff

## Create-a-plan flow — October 11

Signed-in setup now opens on today’s muscle map and Build my workout. Create a plan sits at the top and opens a left-hand vertical list of Monday–Sunday. Choosing a day shows its time, then that day’s muscle map underneath, then build and Save. The same panel is used for every day, including Tuesday. Each save writes the whole week through the existing PUT /profile/schedule. Today’s workout remains a separate one-off plan. No contract change.

Changed: `mobile/src/screens/trainer-screen.tsx`, `mobile/src/components/weekly-schedule.tsx`, README, MASTER_PLAN, API notes. Welcome/continue/rest-day entry is no longer the default route.

## Weekly setup and returning-user flow — October 11

First-time signed-in profiles now configure a recurring week using the existing muscle map and plan editor for each day/time. Save days, then Finish weekly setup. Returning profiles select today from the device-local date and show Welcome back plus today's focus; Continue opens the saved equipment plan for daily edits. Rest days show the closest next workout and Train today. Choose different muscles makes a one-off plan; Edit weekly schedule changes the recurring templates. Drafts survive day switches; unsaved days block Finish. No reminders or automatic workout start.

Changed: backend WeeklyWorkout/ScheduleUpdate/UserProfile models, schedule store/table and PUT /profile/schedule; generated schemas/OpenAPI/examples; shared API/schema, trainer flow, weekly-schedule.tsx and workout-schedule.ts; stable session reset for finished-session restoration; backend schedule tests and scripts/check_schedule.cjs; runbooks. Existing profiles migrate to schedule:[] without losing last plan/session data. Schedule writes validate every machine with the existing engine; ordinary profile saves and daily edits preserve the weekly template. Watch/voice action contracts unchanged.

Checks: **65 backend tests pass** (one upstream warning); schedule date/week-wrap helper PASS; mobile typecheck/lint/export PASS. Browser synthetic-profile walkthrough passes two-day setup, return/today greeting, saved equipment continuation, daily editing, template preservation, unsaved day recovery, rest-day next workout and custom muscles. The production root route also passed profile restoration, finished-session cleanup and narrow-screen layout. OAuth was not verified by the fixture. Temporary test route removed and production build has four routes. Mac next: pull after human-authorized publication, configure Google locally, test genuine first/return login and native rendering. No publish/commit/push for this task. Exact commands/evidence: docs/VALIDATION.md.

## Set timer and confirmed weights — October 11

Explicit scope assignment implemented persisted set_started_at and per-exercise set_records (timestamps, duration, planned reps, weight). Equipment confirmation starts set 1; the rest deadline starts subsequent sets. Completion stops/saves; skip/end does not fabricate a completed record. Added weight_updated with exactly one weight_lb/weight_increase_lb payload and current instance/set validation. Completed histories retain their original weights; unknown-baseline increases are rejected. Legacy records/timing are not reconstructed.

Changed: backend engine/models/store/tool contract and new test_set_tracking.py; generated contracts/tools and contracts/examples/set-tracking.json; shared client schema/API/session clock, trainer, new set-tracking.tsx, voice types/handler; watch Codable fields/timer/history; prompt/runbooks. Schema version 1 remains additive for output. Apply the new optional weight arguments and enum to the published Mat client tool and paste the updated prompt before voice testing. No provider mutation performed.

Checks: contract export PASS, backend **51 passed** (one upstream warning), mobile typecheck/lint/web export PASS. Windows button walkthrough passes timer, saved 5.6s at 50 lb, suggestion, explicit increase to 55 lb, immutable prior record and refresh. Next Mac action: native compile/timer checks and spoken found-machine → set-done → increase-by-5lb scenario after provider configuration. No microphone/native acceptance or publication claim. Production preview uses an ignored test HTTP helper for exported routes; the known local Expo development install issue remains separate. Exact checks are in docs/VALIDATION.md.

## Google-first landing page — October 11

Web now opens a themed landing page with the official Google popup sign-in button. After backend verification, the trainer displays a first-name welcome and opens saved setup/plan or an existing session. Sign-out clears setup drafts and returns to the landing page. Changed client files: `mobile/src/screens/landing-screen.tsx`, `mobile/src/screens/trainer-screen.tsx`, `mobile/src/auth/google-sign-in.web.tsx`; existing profile/backend work preserved and no contract change. Native Google auth remains pending; native development setup and browser watch session pairing are retained.

Windows `npm run typecheck`, `npm run lint -- --no-cache`, and production web export PASS. Desktop and 390px browser layout/button rendering PASS with screenshots in `docs/evidence/google-landing-*.png`. Actual Google account sign-in/welcome transition NOT RUN. Preview currently serves `mobile/dist` on port 8081 with Python's local HTTP server because Expo dev mode hits the installed `expo-modules-core/src/ts-declarations/global` resolution error; see the validation entry for exact commands. Next: test Google sign-in live, then repair the local development install. No publication performed.

## Interactive 3D muscle model

The web muscle selector now loads the pinned `mobile/public/models/muscular.glb` anatomy asset through React Three Fiber and a locally bundled Draco decoder. The source annotation mesh is removed before body-only bounds are calculated, so the vertical rotation axis passes through the body. It rotates continuously on a fixed horizontal orbit around the chest, supports left/right drag, resolves clicks through unmapped superficial geometry to the first mapped workout muscle, and renders selected groups bright red against dimmed cool-gray anatomy. Pitch, pan, and zoom are disabled. The ten labeled buttons remain the accessible input path. Native resolution still uses the existing front/back SVG schematic; a web load/WebGL failure also falls back to that schematic.

The GLB is unchanged at 8,819,872 bytes with SHA-256 `5234472152a791baf002bed614707c33ba3ab2b278e41f41899a79a453d40785`. `mobile/public/models/ATTRIBUTION.md` and `UPSTREAM-LICENSE.txt` preserve BodyParts3D/Z-Anatomy attribution and share-alike terms. The pinned Three.js Draco files have their own notice under `mobile/public/draco/`.

Plan editing now totals sets against each exercise's primary and secondary muscle groups. Above six sets for a group, approval is disabled until the user acknowledges the non-diagnostic fatigue caution; every draft edit resets acknowledgment. Windows verification passed typecheck, lint, production export, all 35 backend tests, checksum validation, model load/continuous rotation, direct mesh selection, accessible-button selection, manual orbit with resumed rotation, the no-warning-at-six boundary, warning-at-seven behavior, secondary-group counting, and acknowledgment reset. Evidence: `docs/evidence/interactive-3d-centered-contrast.png`, `interactive-3d-highlight-fixed-orbit.png`, and `interactive-3d-volume-caution.png`. Native rendering was not run on Windows.

## Muscle-first builder scope change

The fixed three-machine setup has been expanded locally to a source-backed fictional catalog of 18 machines and ten muscle groups. The backend exposes deterministic plan previews and validates approved custom plans with sets, reps and optional pounds. The shared setup includes a front/back muscle map, editable plan and weight sliders. Existing fixed `full-body` requests remain compatible. Guidance is developer-paraphrased and explicitly pending professional review; there is no vector database. Contract schemas and browser evidence must accompany this change before handoff.

## Windows backend — Stage 3 transport complete

The backend-owned Stage 3 transport work is complete locally. WebSocket authorization, snapshot and pong frames now use exported Pydantic contracts. Tests cover initial state, watch-sourced acknowledgments, duplicate replay, external broadcasts, authoritative reconnects, ping/pong and rejected authorization. Contract export and the backend suite pass with 31 tests. A Windows two-tab live-agent walkthrough now passes state synchronization, external explanations, reconnect, duplicate-control protection, voice reconnect and one full six-set routine. Stage 3 remains partial pending audible-output confirmation, a spoken question, voice-vs-control concurrency and a second full spoken run; see `docs/VALIDATION.md`.

## Current handoff to Thanmay — Stage 2 testing

Google sign-in is now the web entry gate and uses the existing SQLite file. A themed landing page precedes setup; successful sign-in shows a first-name welcome and restores saved preferences/plan. Native Google sign-in is still pending and the watch route retains session-token pairing. Configure the same web client ID as `GOOGLE_CLIENT_ID` and `EXPO_PUBLIC_GOOGLE_CLIENT_ID`, then restart backend and Expo. Approving a plan while signed in saves name, muscle groups and plan for the next visit. Web setup requires sign-in; native development setup is retained.

Latest status supersedes the historical notes below: user published Mat with the project prompt, correct target-omission instruction, three attached client tools and authentication. Real API authorization passes with ElevenAgents Write. Credentials remain in ignored backend/.env and must be configured locally on Mac; they are not part of this commit.

Pull main while preserving local changes. Install the repaired lock with npm ci in mobile/, then run npm run typecheck and npm run lint. From repository root start backend with .venv/bin/python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --env-file backend/.env; run npm run web in mobile/. Test all seven Stage 2 web checks and the native audio spike, recording evidence in docs/VALIDATION.md. Pay particular attention to optional End/Retry targets and rejected missing/stale exercise targets.

Windows backend suite: 27 passed; backend health and published-agent checks PASS. Windows frontend install did not complete: first attempt had network resets; retry downloaded most remaining packages but was stopped at the user's request to hand off to Mac. Typecheck, lint, browser launch and live audio remain NOT RUN on Windows. No dependency manifest or Expo/React Native version was changed by the lock repair. The stash was not applied.

## Windows launch repair

User assigned local app launch/install repair. mobile/package-lock.json repaired with npm install --package-lock-only --ignore-scripts --no-audit --no-fund; no package.json or Expo/React Native dependency version changes. Fix supplies missing nested @emnapi core/runtime/wasi-threads entries and satisfies the top-level wasi-threads dependency. Initial npm ci accepted the repaired lock but downloads ended in ECONNRESET; cached retry was stopped for the Mac handoff before completion. Update validation with final install/typecheck/lint results before claiming readiness.

Backend was started by the user after two automatic approval-review timeouts and a stalled sandbox attempt. Read-only health check outside sandbox: HTTP 200, voice_configured true. Published ElevenLabs agent check: HTTP 200, Mat prompt and target-omission instruction active, three tool IDs attached, authentication true. No secret or conversation token logged; no conversation started. Browser automation opening localhost also hit an automatic review timeout, not a finding that the service was unsafe. Live browser/audio verification remains pending.

## ElevenLabs dashboard configuration follow-up

User authorized browser configuration. Three existing client tools were attached to My Agent's draft; all Wait for response settings verified enabled, guidance exercise_id required and LLM-supplied, state tool has no arguments. Action tool saved with eight enum values and optional exercise_instance_id/set_index; both remain LLM-supplied. Agent project prompt/greeting and three preview variables configured; authentication enabled in draft. Publishing and actual audio were not performed. Browser access ended during final return-to-tools check; the saved tool form and draft attachment list were verified earlier, but publication remains a user action.

Minimal coordinated client fix in mobile/src/voice/voice-panel.web.tsx normalizes omitted session-action arguments to null; every exercise action must match both current instance and set. Backend tool contract, agent prompt/specification and generated tool JSON updated together. This one client edit is necessary for the user's dashboard configuration request; no mobile manifests/lockfile or native modules changed. Local backend suite: 27 passed, one upstream deprecation warning. Frontend typecheck/lint could not run: npm ci rejects checked-in lockfile @emnapi/core/runtime/wasi-threads entries; no-lock fallback install stalled and was stopped. Thanmay should repair/regenerate the lockfile in his area, run typecheck/lint, and verify live End/Retry and rejected incomplete exercise tool calls. No commit/push of this follow-up.

## Stage 2 Windows-owner update — October 10, 2026

Local, uncommitted update: backend/voice.py isolates typed private-agent authorization; backend/app.py uses it without changing conversation_token response shape. Invalid/cross-session access is checked before provider contact; finished sessions cannot request new tokens. Provider errors/malformed responses are sanitized; token responses are not cached. Ten-second provider timeout fits the client's twelve-second deadline. backend/tests/test_voice.py covers these behaviors and generated tool parity.

backend/tool_contract.py is now canonical for three tool argument schemas. scripts/export_contracts.py exports agent/tools.json and contracts/client-tools.json plus VoiceRequest/VoiceAuthorization HTTP schemas. Action names, argument names, session schema and frontend interface are preserved. Generated tool JSON is a dashboard specification, not an API provisioning payload. No mobile/watch files or dependency manifests were edited.

agent/prompt.md clarifies current.instance_id mapping, phase-aware introductions, read-only Repeat/questions, action acknowledgments, uncertain intent, data boundaries and curated-content limits. agent/README.md contains private-agent dashboard setup and Mac/Windows launch steps; agent/GUIDANCE.md defines the catalog review boundary. Professional content review is still pending.

User confirmed no agent exists yet and requested setup instructions. Next user action: create/configure Mat using agent/README.md and put credentials in ignored backend/.env locally. Next Thanmay action: verify the same client tools in the browser, record all seven live web checks, and perform the iPhone simulator native spike. In particular, test an initial introduction after the state tool returns, Repeat/no mutations, successful/rejected Set done, mic denial/disconnect, end cleanup and idle/noise. Phase-specific prompt rules do not replace UI/action validation. Existing native adapter and voice lifecycle gaps remain Thanmay's work.

Stage 2 remains open until live web evidence and a native PASS/concrete blocker are recorded. Automated provider responses are simulated and do not establish a real conversation, prompt performance or audio routing. No provider agent, public deployment, commit or push was created by this work.

Local changes are not pushed. Both developers should inspect git status and existing edits before starting.

## Backend/agent owner

The initial backend is implemented in `backend/` with SQLite persistence, serialized event transitions and schema export. Main files: models.py, engine.py, store.py, app.py. Tests cover strict reorder, approved alternatives, exclusions, blocked flow, duplicate/stale/concurrent commands, rest restart and ended sessions.

Take ownership of backend/catalog/contracts/agent. Coordinate any event or response shape changes with the frontend owner. `scripts/export_contracts.py` exports Pydantic models and OpenAPI. Web schemas in mobile/src/api/schema.ts are manually aligned for the initial version; automation should verify parity before future changes.

Configure the external ElevenLabs agent using agent/prompt.md and agent/tools.json. Tool file is a human setup specification, not a blindly importable provider request body. Required tools block on response. Agent must support app-provided dynamic variables.

Catalog is developer-authored, professional review pending. Refine with verified guidance before real use.

## Frontend owner

Shared app lives under mobile/src. Web and native ElevenLabs provider adapters use the shared workout voice panel and client-tool handlers. The native adapter and LiveKit development-build configuration are implemented; the first iOS build attempt failed before launch (missing WebRTC header/ExpoModulesJSI failure with Xcode 26.1.1). See docs/DEVICE_CHECKS.md and docs/VALIDATION.md. `api/session-storage.web.ts` keeps local session access per tab; native storage is memory-only until a later stage adds SecureStore. Windows/native verification remains separate.

## Coordination

Browser watch uses direct session ID/token entry as a local development pairing method. Short-lived pairing code, native WatchConnectivity, SwiftUI app, physical mic routing and Photon are not implemented. Finish live web checks before moving the full flow to native.

Never mark a stage passed based solely on tests or exported bundle. Record browser interaction and audio evidence in docs/VALIDATION.md.

## Verified on October 10

Backend: 14 pytest checks pass. Frontend: typecheck, lint and static web export pass. Browser: full strict routine completes six sets; separate watch tab synchronizes Taken and summary; refresh retains a running rest; alternatives require acceptance; early end retains a partial substituted set. See docs/VALIDATION.md for exact limits. npm dependency audit remains open.

Next backend-owner action: configure the ElevenLabs agent/client tools, then put credentials in ignored backend/.env and launch using README's --env-file command. Next frontend-owner action: validate live web audio/tools after the team creates and configures the ElevenLabs agent, then retry the native voice spike after resolving the Xcode and LiveKit build blockers. Current local services are available at localhost:8000 and localhost:8081; restart them through README commands if unavailable.


## October 19 — independent frontend/backend Vercel roots

Current layout supersedes earlier deployment instructions: frontend Root Directory
mobile; backend Root Directory backend. Each has vercel.json and upload ignores.
Root vercel.json/pyproject.toml/requirements.txt are removed. Backend pyproject
selects app:app. Both projects can use ordinary Git integration to the same branch.

Backend runtime modules moved into backend/spotter; backend/app.py is the entrypoint
facade. Relative imports let the package run within either root. Root run helper
and backend.app imports remain usable; direct internal imports now use
backend.spotter.*. Catalog moved to backend/catalog/demo.json and remains the sole
source; SQL migrations moved to backend/spotter/migrations. Update teammate work
against these paths instead of recreating root catalog or old implementation files.
Operator module commands are python -m backend.spotter.migrate_sqlite and
python -m backend.spotter.snowflake_sync from repository root. Local env/data were
not moved or uploaded; explicitly configured relative SQLite paths still depend
on process cwd. Neon remains selected through DATABASE_URL.

Validation: 98 tests passed with disposable local PostgreSQL URL; frontend
typecheck/lint/export pass; isolated backend copy passes API/session/stream/rest
checks; contract export has no changes; catalog/SQL bytes preserved. Exact commands
and limits are in docs/VALIDATION.md. Hosted Vercel transport/Neon/voice/native
acceptance remains pending. No real-data migration, commit, push or deploy.
Next owner action: commit all file moves atomically, change the two Vercel project
roots, clear old overrides, set per-project envs and deploy the new Git commit.
Full setup: docs/DEPLOYMENT.md.
