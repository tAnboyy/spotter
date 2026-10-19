# Spotter / Mat — staged web-first master plan

Updated October 11, 2026. This replaces the simulator-first plan. Implementation is underway. See docs/VALIDATION.md for check-by-check evidence; native and live voice gates remain open.

## Outcome and scope

Persistence update (October 19): Neon PostgreSQL is the selected hosted database.
DATABASE_URL selects PostgreSQL; SQLite remains a local fallback. Preserve the
existing serialized event semantics and versioned contracts. PostgreSQL reconciles
persisted rests on server reads/actions rather than idle polling. Importing existing
personal records is a distinct transfer; local backup remains intact. Cloud
acceptance requires evidence beyond local PostgreSQL tests.

Hosting update (October 19): export the web app to Vercel using root deployment
configuration. Keep the authoritative FastAPI backend on a single-process host with Neon
PostgreSQL, or persistent local SQLite; see `docs/DEPLOYMENT.md`. Hosted acceptance remains pending
until the public API, Google sign-in, synchronization and live voice are checked.

Web muscle visualization update (October 11): start the existing 3D anatomy automatically. Remove the web 2D view and mode switch. On failure, show an error and Retry with muscle buttons still usable; preserve selection across retries. Native rendering is unchanged.

Spotter is the product; Mat is the default, user-renamable voice coach. The user sets preferences and a routine, then follows spoken guidance through exercises, sets and rests. User-reported equipment availability triggers preference-aware reordering or an approved substitution.

Weekly setup scope update (October 11): signed-in setup opens on today’s muscle map and workout builder. Create a plan, at the top of that screen, lists Monday–Sunday vertically on the left. Each chosen day asks for a local time, then muscle selection and a saved equipment plan underneath. The same steps apply to every day. Today’s one-off workout does not rewrite the week. Schedule only; no reminders.

Workout tracking scope update (October 11): equipment confirmation starts a persisted set timer; completing a set saves duration, planned reps and weight per exercise. Rest expiry starts the next timer. Mat offers conditional next-set weight changes and only explicit user confirmation updates pounds through a validated action. Saved set history never changes retroactively. Live provider tools/prompt and native acceptance require separate verification.

Web entry scope update (October 11): show a themed landing page with Google sign-in first. After backend verification, greet the user by first name and open muscle-first setup (or restore their saved plan/session). The developer watch route continues to use session-token pairing. Native Google sign-in remains separate unfinished work.

Trainer persona scope update (October 11): users can name their trainer, customize a creature avatar (color, expression, accessory), and save a personal motivation with an opening-reminder toggle. Signed-in preferences persist in the existing profile; new sessions capture that persona. A skippable reminder appears at workout start and is requested once when voice connects. Edits during a workout apply to the next session.

First deliverable: a working React Native Web experience on Mac and Windows, with live ElevenLabs voice and a simulated watch-control panel. Next deliverables: the same workout on an iPhone simulator and a small SwiftUI Apple Watch simulator app. Physical iPhone/headphone testing is optional after those pass.

Use a fictional, developer-configured gym with 18 source-backed machines. During setup, the user selects muscle groups on a body map, reviews a deterministic recommendation of up to eight machines, and may edit sets, reps and an optional self-selected weight before approval. Guidance remains developer-paraphrased with professional review pending. Default availability is available until the user reports Taken. No automatic occupancy detection. Phone screen interaction is mainly setup; session status and fallback controls remain visible for development/recovery.

Exclude Spotify, admin dashboard, sensors, computer vision, automatic reps, indoor positioning, screenshot/PDF import and true local wake-word detection. Brief exercise questions are grounded in curated guidance; there is no claim to observe actual form.

## Architecture and ownership

One Expo/React Native TypeScript app under `mobile/` serves web and iOS. Shared screens/API code use platform-specific voice adapters. The watch is a separate SwiftUI project. Both simulators and the browser use the same backend transport initially; native WatchConnectivity is deferred.

| Component | Decision | Owner |
|---|---|---|
| Shared web/iOS screens | React Native Web + Expo; source under `mobile/src/` | Thanmay — Mac |
| Web voice | ElevenLabs React SDK adapter | Thanmay |
| Native voice | ElevenLabs React Native SDK adapter, development build | Thanmay |
| Watch simulator | SwiftUI, HTTP actions + WebSocket snapshots | Thanmay |
| State/API | FastAPI + Pydantic, SQLite, one process | Teammate — Windows |
| Catalog | Reviewed JSON gym/exercise/routine records | Teammate |
| Agent | Prompt, matching tools, setup instructions | Teammate |
| Contract | Versioned events, snapshots, tool names/examples | Teammate; both approve changes |

Repository ownership:

- Thanmay: `mobile/`, `watch/`, `docs/DEMO.md`, `docs/DEVICE_CHECKS.md`.
- Teammate: `backend/`, `catalog/`, `agent/`, `contracts/`, `docs/API.md`.
- Shared: this plan, README, validation record, submission checklist.

Thanmay owns app-level agent tool handlers; teammate owns matching agent definitions. Agree on names/arguments together. Each owner edits dependency manifests/lockfiles only in their area. Teammate can run web on Windows using the shared code; Thanmay validates native builds on Mac. No separate web product or duplicate workout engine.

```text
Shared web/iOS screens + API client
          |                   |
     Web voice           Native voice
 ElevenLabs React     ElevenLabs React Native
          |                   |
          +------ FastAPI ----+
                     |
            Authoritative session + SQLite
                     |
       Web watch panel / SwiftUI watch simulator
```

Stages advance when their exit checks pass. Independent work can overlap; no mock or browser check counts as native acceptance. Record PASS/FAIL, steps, expected/actual result, OS, dependency versions and evidence in `docs/VALIDATION.md`.

## Stage 0 — freeze the contract and run both environments

Target: 30–45 minutes. No voice or watch integration yet.

Thanmay: create the shared app, web setup/session/summary skeleton, configurable API URL and development watch panel. Verify Xcode and iOS/watchOS simulator runtimes are installed.

Teammate: create backend with health/catalog endpoints, seeded routine and event/snapshot schemas. Supply Mac and Windows run commands, environment templates and pinned dependencies. Use Python scripts without a Docker prerequisite.

Both: select the demo routine, voice tool names, strict/substitution preferences and event shapes. Commit the tested JS lockfile when publishing code; use SDK-compatible package versions rather than guessed versions.

Validation at end:

1. Each person follows the runbook from a fresh terminal; browser app and backend start.
2. Browser fetches health/catalog and displays the same configured machine and muscle-group catalog on Mac and Windows.
3. Confirm CORS allows intended local browser origins and WebSocket URL configuration is explicit.
4. Confirm no provider API key is in frontend bundles/config; `.env.example` contains placeholders only.
5. Both review one create-session, action and snapshot JSON example. Record schema version 1.

Exit: reproducible environments and one agreed contract. If venue networking blocks cross-laptop traffic, run backend locally on both laptops; final demo backend runs on Mac.

## Stage 1 — complete the workout on web using buttons

Target: 90–120 minutes. Prove session rules before introducing speech.

Thanmay: setup preferences, routine confirmation, session view, set/rest display, summary. Add a clearly labeled developer watch panel with Got it, Taken, Set done, Skip and End. Build against fixtures only until live API is ready; exit uses the real backend.

Teammate: persist sessions/events, validate actions, implement sets/rest, strict reordering, blocked state and summary. Add approved-alternative proposals/acceptance after strict mode works.

Validation at end:

1. Start a session with strict mode; current exercise waits for equipment confirmation.
2. Select Taken: defer first exercise and select next eligible planned exercise, without substitution.
3. Select Got it: transition to exercising; Set done advances exactly one set and starts rest.
4. Finish remaining sets/exercises; deferred exercise is reoffered and can be completed.
5. Refresh during rest and restart backend: same deadline/state remain; timer does not restart.
6. Double-submit the same event and submit simultaneous completions for the same set: completed count increases once.
7. Submit an old exercise/version action: reject it, return fresh state, do not advance a different exercise.
8. Mark every eligible exercise Taken: show retry/skip/end, without endless reordering.
9. In alternative mode, require acceptance of an approved substitute and respect recorded exclusions. If this feature is cut, hide its preference.
10. End early and finish normally in separate runs; summaries match recorded events. Ended sessions do not advance when an old rest timer expires.

Exit: full live backend workout passes on web. Teammate automates transition, duplicate/stale/concurrent event and timer checks; Thanmay records browser walkthroughs.

## Stage 2 — integrate web voice and run an early native audio check

Target: 90–120 minutes. Native check runs during this stage, not after all web polish.

Thanmay: implement voice adapter contract, web conversation and client tool handlers. Create a minimal iPhone simulator development build that starts/ends a live ElevenLabs conversation. Timebox native setup initially to 45–60 minutes; record a blocker and return to web if unresolved.

Teammate: configure ElevenLabs agent, curated guidance, tool schemas, private-agent authorization endpoint and prompt. Keep one conversational system rather than a parallel LLM loop.

Validation at end — web:

1. Grant mic permission, start a session, hear a live exercise introduction and receive a reply to a spoken question.
2. Say Repeat; guidance repeats without mutating workout state.
3. Say Set done: one validated tool action occurs, correct count appears and Mat acknowledges only after success.
4. Ask How should this feel: answer uses catalog guidance without claiming to see form.
5. Deny microphone permission and disconnect voice: show actionable errors, preserve session state and allow button fallback.
6. End workout: stop conversation and release audio resources; verify stream cleanup where observable.
7. Two-minute idle/noise sample with no intentional command: zero workout transitions. This is a small demo check, not proof of robust speaker identification.

Validation at end — native spike:

1. iPhone simulator development build installs and launches.
2. Permission granted; speak through Mac microphone and hear a live ElevenLabs reply.
3. End and restart conversation; no leaked/stuck audio session or app crash.
4. Record any native failure separately from web success. This spike need not integrate workouts yet.

Exit: working web conversation plus a recorded native PASS or concrete blocker. Web product work may continue on native failure; do not claim readiness to port until Stage 4 passes. Expo Go is not the native voice test target.

## Stage 3 — validate the complete adaptive web experience

Target: 60–90 minutes. This is the first demo-ready milestone.

Thanmay: connect the web watch panel to the actual event transport; handle snapshot versions, reconnection and spoken explanations for external actions. Add optional Talk control for an already-connected conversation after open-session voice works.

Teammate: complete WebSocket broadcasts, acknowledgments, reconnect snapshots and cue/decision data. Stabilize prompt and content. Freeze contract changes after this stage.

Validation at end:

1. Browser tab A runs workout/voice; tab B opens only the watch panel and joins the same session.
2. Tap Taken in B: A receives fresh state, displays next eligible exercise and Mat speaks the correct explanation once.
3. Tap Got it in B: Mat introduces confirmed exercise; both tabs display the same version.
4. Complete a set by voice while another control targets the same set: no double advancement.
5. Reconnect B: fetch authoritative state; do not replay stale commands or cues.
6. Stop backend or voice connection: controls never report false success; recover without losing completed sets.
7. If Talk is included, it acknowledges phone/web listening state, captures a question, returns a reply and closes the listening window. Do not label SDK mute as physical mic-off without verification.
8. Run full routine twice with one Taken report, a question, rest and ending. Both runs produce correct summaries.

Exit: repeatable end-to-end web demo with live voice, adaptation and synchronization. It is a valid fallback submission if native stages remain unfinished.

## Stage 4 — move the proven flow to iPhone simulator

Target: 60–120 minutes if Stage 2 native check passed; otherwise resolve the native blocker first.

Thanmay: preserve shared screens/API code, implement native adapter and integrate client tools, snapshots and error recovery. Use native build/permission configuration. Native dependencies and backend credentials are configured independently of browser setup.

Teammate: keep the backend contract stable, support integration failures and rerun regression tests. Prepare README and sponsor descriptions while Thanmay handles native builds.

Validation at end:

1. Run setup, equipment confirmation, sets/rest and summary on iPhone simulator against real backend.
2. Use voice to repeat, ask an unscripted exercise question and complete a set correctly.
3. Web watch panel sends Taken; native app receives state and speaks the change.
4. Restart phone app during rest: resume authoritative state/deadline, not a new session.
5. Disconnect/reconnect voice and backend; no duplicate completions or false connected indicators.
6. End session: native voice/audio resources stop; no later rest cue fires.
7. Run complete scenario twice. Record simulator/runtime versions and actual audio input/output route.

Exit: native simulator workflow passes. Browser microphone tests do not substitute for these checks. Locked-phone and physical Bluetooth operation remain unvalidated.

## Stage 5 — add the actual SwiftUI watch simulator interface

Target: 60–90 minutes. Start after backend contract is frozen; a static shell may be built earlier.

Thanmay: implement join session, current exercise/set display, Got it, Taken, Set done and confirmed End. Connect to backend directly using same contract as the web panel. Add Talk only if previous stages remain stable.

Teammate: support session pairing/token exchange and event acknowledgments; run stale/duplicate tests against watch-shaped payloads. Keep watch data minimal.

Validation at end:

1. Launch iPhone and watch simulators; join the same session using the development pairing flow.
2. Tap Taken: iPhone updates and Mat explains; watch reflects acknowledged current exercise.
3. Tap Got it and Set done: each action transitions once and both simulators agree.
4. Repeated taps and stale actions never advance an unintended set; pending UI resolves to success/error.
5. Reopen watch or reconnect its transport; fetch current state.
6. If Talk is implemented, trigger an existing native voice session and receive Listening acknowledgment; reply works through Mac audio. Watch mic recording is excluded.
7. End from watch; phone ends conversation and both show ended summary.
8. Rehearse two-minute scenario twice using real SwiftUI controls.

Exit: actual watch simulator app controls native phone simulator through the backend. This validates neither physical watch pairing nor native WatchConnectivity.

## Stage 6 — freeze, record and submit

Reserve final two hours; this stage takes priority over unfinished native/stretched features.

Thanmay: record at-most-two-minute video showing strongest validated platform; simulator or web labels remain visible. Capture live spoken interaction and actual state transitions. Rehearse judge questions and save fallback recording.

Teammate: finish runbook, architecture, tested-platform limitations, sponsor integration details and Devpost draft. Both verify submission and team membership.

Validation at end:

1. Follow README on a clean local setup or fresh terminal with documented dependencies; app/backend run.
2. Demo video is at most 120 seconds, audible and accessible to judges. Label accelerated demo rests and staged summaries honestly.
3. GitHub link resolves and contains required code; do not rely on unpublished local files.
4. Devpost contains one project, all teammates, selected main track and only supported sponsor claims.
5. Check submission confirmation, video access and correct project links before deadline.
6. Prepare table setup/run commands and ensure representative presence during judging.

Exit: verified submission, not merely a drafted page or locally recorded video.

## Shared contract details

Backend endpoints: health/catalog; preview a muscle-group plan; create/get session; post events; get summary; authorized voice token; WebSocket stream; exchange pairing code for session token.

Event fields: UUID event_id, expected_version, source, type, exercise_instance_id, set_index, payload. Snapshot fields: monotonic version, server time, phase, preferences, current exercise/equipment/location/set, rest deadline, queue/deferred/completed entries, pending alternative, last decision.

Events: equipment_claimed, equipment_taken, alternative_accepted/declined, set_completed, rest_elapsed, skip_exercise, retry_deferred, end_session, weight_updated. Talk is a transient client control with separate acknowledgment, not a workout completion event.

Backend must atomically deduplicate/validate/mutate and serialize concurrent events. Deduplicate retries before stale-version checks; replay original result. Full snapshots allow reconnect. Timer expiration survives restart and occurs once. Strict mode reorders only; substitute mode uses approved records and explicit acceptance. No weight transfer between different exercises.

Tools: get_session_state(), get_exercise_guidance(exercise_id), submit_workout_action(action, exercise_instance_id, set_index, weight_lb?, weight_increase_lb?). Phone/web handlers submit validated backend events. Expose only allowlisted actions. Do not let agent write arbitrary DB state.

Voice adapter interface: connect/disconnect, set listening state, get connection/listening state, supply updated workout context, request spoken cue, register tool handlers. Put implementations in platform-resolved web/native files; share API and schemas. A context update may not trigger speech: verify SDK behavior and use a supported response trigger or serialized TTS cue. Avoid overlapping speech and stale cues.

Keep provider secrets server-side; use session-scoped tokens and short-lived agent authorization. Local web mic uses localhost or HTTPS. For final demo backend runs on Mac; configurable base URL supports LAN collaboration if allowed. Configure explicit dev CORS/local transport settings. No automatic public deployment, commit or push is authorized by this plan.

## Time and fallback policy

Estimates are goals, not promises. Web functional path is priority; native stages are gated upgrades. Do not delay a complete web demo to perfect a watch enhancement.

Drop order: Photon, remembered coaching feedback, watch Talk, alternative mode, extra polish, unfinished native stages. Keep live voice, strict adaptation, deterministic sets/rest and correct summary. Hide unavailable choices. Submit strongest validated implementation and describe incomplete work as future work.

Target October 11 Charlotte time: freeze 7:30 AM, video/draft ready 8:30 AM, submission verified by 9 AM, before local 10 AM deadline. Organizer source says EST despite EDT; use local 10 AM as conservative cutoff. If stages threaten this buffer, cut scope immediately.

## Prizes, rules and evidence

Primary: General or Beginner plus ElevenLabs. Beginner requires more than half first-time hackathon participants: both for this two-person team. Photon is a stretch after Stage 3 and requires Spectrum plus a real iMessage agent number. Gemini is conditional on a qualifying verifiable API integration, not an assumed provider model choice.

One project, mandatory GitHub code link and max-two-minute video. No pre-event developed/cross-posted project submission under supplied organizer rules. Table assignment by 11 AM, judging noon–1:30 PM, two-minute demo/two-minute questions, representative present. Closing 3 PM.

Rules/prizes reference: user-designated `/Users/das/.codex/memories/extensions/ad_hoc/notes/2026-10-10-hacknc-tracks-submission.md`, source-provided and not independently verified. Devpost: https://hacknc-2026.devpost.com/ . Source has stray 2025 wording; use 2026 URL.

Technical references:

- https://elevenlabs.io/docs/eleven-agents/libraries/react
- https://elevenlabs.io/docs/eleven-agents/libraries/react-native (native dependencies; Expo Go unsupported)
- https://elevenlabs.io/docs/eleven-agents/customization/tools/client-tools

Acceptance tracker to create in `docs/VALIDATION.md`: Stage | Owner | Environment | Check | Expected | Actual | PASS/FAIL | Evidence | Open blocker. All checks initially NOT RUN. Record web, native simulator and physical-device evidence separately.

## Scope addition — Spanish trainer, October 11, 2026

User requested English/Spanish spoken coaching selection in trainer customization. Persist the selection in trainer preferences, default legacy data to English, and use the session preference for greetings/reconnections. Menus remain English. Live provider activation and bilingual voice acceptance are separate from local implementation checks; see agent/README.md and docs/VALIDATION.md.

## Scope addition — Snowflake analytics, October 11, 2026

User selected Snowflake workout analytics. Keep SQLite as the transactional workout store; add an explicit operator batch export of allowlisted accepted workout events to Snowflake with equipment-report/completed-set insights. No workout API contract or client changes. Setup and demonstration: docs/SNOWFLAKE.md. Live Snowflake validation is a separate acceptance gate.


Hosting correction (October 19): the human clarified that this Vercel project is backend-only. Root configuration now selects FastAPI/backend.app:app and Python requirements. Expo hosting is separate. Vercel Root Directory must be repository root; hosted transport and full-workout acceptance remain pending. This supersedes earlier frontend-only Vercel instructions.


Final hosting clarification (October 19): both frontend and backend target separate Vercel projects. Root vercel.json remains frontend; backend/vercel.json is selected explicitly with CLI --local-config from repository root. This supersedes the backend-only correction. Git backend auto-deployment is not automatically configured by a nested file. See docs/DEPLOYMENT.md. Hosted acceptance remains pending.
