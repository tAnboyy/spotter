# Shared development instructions — Spotter / Mat

Applies to both developers and every coding assistant working in this repository. Read `MASTER_PLAN.md` and `docs/VALIDATION.md` before starting. Follow the current human request when it changes the plan; update affected documentation to keep it consistent.

## Product boundaries

- Build web first: shared React Native Web/iOS app, live ElevenLabs voice, deterministic workout backend, muscle-first editable setup, web watch-control panel.
- Do the early native voice spike in Stage 2; move the full experience to iPhone simulator in Stage 4 and SwiftUI watch simulator in Stage 5.
- Equipment availability is user-reported; gym inventory and guidance are developer-configured. Do not add occupancy sensors, music, dashboards or automatic form detection without a scope change.
- Keep strict exercise reordering as the core adaptation. Pre-session recommendations come only from the configured catalog; approved alternatives require user acceptance.
- Plan is intent, not completion evidence. Do not mark stages passed based on scaffolds or mocked responses.

## Two-developer ownership

| Owner | Primary files and responsibility |
|---|---|
| Thanmay — macOS | `mobile/`, `watch/`, `docs/DEMO.md`, `docs/DEVICE_CHECKS.md`: UI, platform voice adapters, client-tool handlers, native builds, simulator checks |
| Teammate — Windows | `backend/`, `backend/catalog/`, `agent/`, `contracts/`, `docs/API.md`: state engine, persistence, catalog, agent configuration, schemas, backend tests |
| Shared | `AGENTS.md`, `MASTER_PLAN.md`, `README.md`, `docs/VALIDATION.md`, root configuration: coordination and runbooks |

- Both people may contribute across areas when coordinated. Ownership prevents conflicting edits; it is not an automatic approval gate for every fix. Explicit human assignments override defaults.
- Inspect current files and `git status` before editing. Never reset, overwrite or revert another person's uncommitted work to make your task easier.
- Avoid unrelated edits outside the assigned area. When a dependency requires another owner's change, describe the exact file, change and reason in a repo-tracked handoff.
- No proactive subagents unless the human explicitly requests delegation. These instructions coordinate the two human developers and do not authorize spawning agents.
- Do not commit, push, deploy, publish or change external shared data unless the human authorizes it. Local implementation and verification can proceed within the requested scope.
- On a conflict, preserve both developers' intended behavior; inspect and resolve the overlapping logic, never blindly choose one side.

## Stack and code organization

- `mobile/`: Expo + React Native + TypeScript, web and iOS from one app. Keep routes under `src/app/`, reusable UI under `src/components/`, screens under `src/screens/`, shared API/contract adapters outside route files.
- Platform voice files resolve as `.web.ts[x]` and `.native.ts[x]`; provide the appropriate default export path if tooling requires it. Never import native-only WebRTC packages into web bundles or browser globals into shared/native modules.
- `watch/`: separate SwiftUI project with a small API client and minimal state. No watch audio streaming in the initial scope.
- `backend/`: FastAPI + Pydantic, SQLite, one process. Keep HTTP handlers thin; domain transitions belong in the session engine, storage in the persistence layer.
- `backend/catalog/`: versioned JSON fixtures with stable IDs. `agent/`: prompt, tool schemas and setup instructions. `contracts/`: canonical schemas and examples.
- Use existing code patterns once implementation exists. Avoid duplicate web/native business logic, premature abstraction and unrelated refactors.

## Coding conventions

- TypeScript: strict typing; explicit event/snapshot types and discriminated action unions. Avoid `any`; validate external data rather than trusting type assertions. Hooks clean up subscriptions, timers and audio resources.
- Python: snake_case functions/modules, PascalCase models, type hints for domain/public functions. Validate input with Pydantic and use parameterized database queries. Keep transitions testable without network/provider calls.
- Swift: PascalCase types, camelCase members, typed Codable payloads. Update observable UI state on the main actor; keep networking outside view bodies. Handle errors rather than force-unwrapping external values.
- No silent `catch` blocks or blanket success responses. Errors must be actionable and preserve session state.
- No machine-specific absolute paths, personal session IDs or hardcoded LAN addresses in code. Configuration supplies endpoints and local paths.
- Comments explain decisions or non-obvious constraints. Public behavior and setup instructions belong in the runbook.
- Formatting, type-checking and linting use the selected toolchain's checked-in configuration. Once scripts exist, document exact commands; do not invent passing results or nonexistent commands.

## Contracts: source of truth and change procedure

The plan's names are initial targets. Before client implementation, the backend owner creates versioned canonical JSON schemas/examples in `contracts/` and HTTP documentation in `docs/API.md`. FastAPI's generated OpenAPI must match those schemas. Derive client types from the canonical contract where practical; do not maintain unexplained incompatible copies.

- Agree and document `schema_version: 1`, exact endpoint paths, enum values, field nullability, tool arguments and acknowledgment/error shape in Stage 0.
- Teammate owns canonical definitions; Thanmay owns consuming handlers. A breaking change requires both developers to coordinate before merging. Assistants can draft the producer and consumer updates locally without stopping routine work for permission.
- For a contract change: update schema/examples, producer, web/native consumers, watch consumer if present, agent tools, tests and API docs together. Note compatibility or migration requirements.
- After Stage 3, prefer additive changes. Never silently rename a field or tool to fix one client.
- Treat HTTP/tool input as untrusted. Reject unknown action types and invalid IDs; runtime validation is required even when callers are typed.

### Event and snapshot requirements

Event: `event_id` (UUID), `expected_version`, `source`, `type`, `exercise_instance_id`, `set_index`, `payload`. Define which fields are nullable for each event in the schema. Clients generate one event ID per intentional action; network retries retain it.

Snapshot: session ID, schema version, monotonic session version, server time, phase, preferences, current exercise/equipment/location/set, rest deadline, remaining/deferred/completed entries, pending alternative and last decision. Distinguish exercise catalog IDs from planned exercise-instance IDs.

- Keep snake_case JSON fields across languages; map to idiomatic local names explicitly.
- Store timestamps as timezone-aware UTC and serialize ISO 8601 with an explicit timezone. Clients estimate server offset for timers. Define set indexing once in the contract (recommended 1-based).
- Session phases: `awaiting_equipment`, `awaiting_alternative_confirmation`, `exercising`, `resting`, `blocked`, `completed`, `ended`.
- Actions: `equipment_claimed`, `equipment_taken`, `alternative_accepted`, `alternative_declined`, `set_completed`, `rest_elapsed`, `skip_exercise`, `retry_deferred`, `end_session`.
- `rest_elapsed` is server-driven; an untrusted client cannot skip a deadline by sending it. Define any explicit skip-rest action separately if later authorized.
- Talk/listening controls are transient and acknowledged separately; they never complete sets.

### State integrity and synchronization

- Backend is authoritative. No client or LLM directly writes workout state.
- Validate and mutate in one transaction/serialized operation. Persist event deduplication and session updates atomically.
- Deduplicate before version checks. Retrying a processed event returns its original action result; clients must not regress to an older snapshot from a replay. Fetch current state when necessary.
- Reject stale new events with HTTP 409 plus current snapshot. Validate phase, exercise-instance ID and set index as well as version: two distinct completion requests for the same set must count once.
- Reject reusing an event ID with a different payload; it is not a valid retry.
- Publish updates only after transaction commit. REST acknowledgments remain authoritative if a WebSocket broadcast is lost.
- Apply only newer snapshot versions; after reconnect, fetch authoritative state. Never automatically retry a rejected stale action against a different exercise/version.
- Persist rest deadlines. Expire rests once, recover on restart, and ignore timer triggers after ending. A UI countdown is not the session engine.
- Taken affects this user's session, not facility-wide inventory. Strict mode defers planned exercises; when all eligible work is blocked, offer retry/skip/end rather than cycling indefinitely.
- Alternatives come from approved catalog records, respect preferences/exclusions and require acceptance. Do not transfer weights between different exercises automatically.
- Summary reflects accepted events and actual completed work, not the original plan as if finished.

## Voice and agent boundary

- ElevenLabs is the conversation provider; do not add a second independent chat loop. Provider keys stay on the backend; clients obtain short-lived authorization.
- Initial tools: `get_session_state()`, `get_exercise_guidance(exercise_id)`, `submit_workout_action(action, exercise_instance_id, set_index)`. Exact schemas in `agent/` and `contracts/` must match app handlers.
- Repeat/guidance questions do not mutate progress. Ask for clarification when completion intent is ambiguous.
- Acknowledge completion only after backend success. On failure, explain the problem and retain current state.
- Watch actions refresh agent context. A context update is not assumed to trigger speech; validate provider behavior and use a supported explicit cue path when needed.
- Use one speech queue, cancel stale exercise cues and clean up all timers/subscriptions/conversations on end.
- SDK mute is not automatically hardware-mic-off. Show Listening only after the actual client acknowledges readiness.
- Use curated setup/cues and target-muscle education. No fabricated equipment, observed-form claims or inferred completion from breathing. Reports of sharp pain stop further technique experimentation.
- Do not log raw audio, credentials or full transcripts by default. For debugging, record minimal event/tool/status information with sensitive fields redacted.

## macOS / Windows reproducibility

- Pin dependency versions through lockfiles/requirements and document supported Node/Python versions. Install Expo packages with SDK-compatible tooling; no uncoordinated dependency upgrades.
- Native ElevenLabs requires a development build, not Expo Go. Local iOS/watchOS builds and simulator validation are Thanmay's responsibility on Mac.
- Supply macOS shell and Windows PowerShell commands where syntax differs. Prefer Python/Node scripts over Unix-only task scripts; support paths with spaces and configurable data directories.
- Configure HTTP and WebSocket URLs consistently. `localhost` means the machine running that client; a Windows-hosted backend uses its LAN address from the Mac if network permits.
- Final demo can run backend locally on Mac. Maintain a no-Docker fallback and test venue network reachability early.
- Web mic requires a permitted browser context such as localhost/HTTPS. Use explicit dev CORS origins and scoped local transport settings.
- Document `.env.example` for each component; public frontend config contains only non-secret values. Ignore real `.env`, SQLite session data, `.DS_Store` and generated build outputs when adding `.gitignore`.

## Validation and handoffs

- Follow each numbered stage check in `MASTER_PLAN.md`. Record expected/actual result, owner, OS/browser/Xcode/runtime, command, PASS/FAIL/NOT RUN/CUT and evidence in `docs/VALIDATION.md`.
- Automate meaningful backend checks: transitions, duplicate/stale/concurrent actions, strict mode, exclusions, blocked search, restart-safe rests, ended-session behavior and token rejection.
- Use manual browser/simulator checks for voice input/output, permissions, external-action speech, reconnection and full session walkthroughs. Fixtures support development but do not satisfy live integration gates.
- Windows web/backend success does not prove iOS correctness. Web voice success does not prove native voice. Simulator success does not prove physical Bluetooth, locked-phone behavior, haptics or real WatchConnectivity.
- Run appropriate checks after changes; broaden them only for changed scope or unresolved failures. Report unavailable checks explicitly.
- Before switching owners or ending work, leave a repo-tracked handoff: changed files, contract impacts, exact tested commands/results, open blockers and next action. Keep secrets out. Use the task's final response for routine handoffs; add `docs/HANDOFF.md` when context must survive machines/sessions.
- Freeze feature work before the submission buffer. Preserve a complete web demo if native stages remain unfinished. Sponsor integrations stay conditional until actually working; consult the plan for rules/deadline rather than copying stale facts here.
