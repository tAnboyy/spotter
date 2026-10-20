# Validation record

## English / Spanish trainer — October 11, 2026

User-authorized local implementation across mobile, backend and agent contract: trainer customization offers English/Español; `preferences.trainer.language` persists to profile and workout, defaults to English for legacy data, and rejects unsupported codes. Shared web/native voice startup sends language and localized first-message overrides on each connection; prompt/context preserve language for guidance, reminders and external-event announcements. Existing session preferences stay fixed; edits apply to the next workout. Menus remain English. Existing choice-button design is reused.

Mac validation: `npm run typecheck` PASS; `npm run lint` PASS; `npm run export:web` PASS (four routes; upstream Three.js and color-environment warnings). `.venv/bin/python -m pytest backend/tests -q`: 57 passed before the additional legacy-language test; targeted final `.venv/bin/python -m pytest backend/tests/test_auth.py -q`: 10 passed, including that new test. One upstream AnyIO deprecation warning. `scripts/export_contracts.py` and `git diff --check` PASS. Coverage checks Spanish across save/login/session readback, English defaulting and rejection of unsupported languages. Watch ignores these unused preferences; no watch schema change required.

NOT RUN: visual browser/native walkthrough and live English/Spanish microphone, speech, command mapping, reconnection and event announcements. Provider configuration was not changed or published. Agent owner must enable Spanish with a compatible voice/model, enable Language and First message overrides, and apply the updated prompt as documented in agent/README.md before live testing. No commits, pushes or deployments.

## Create-a-plan entry — October 11, 2026

Signed-in setup now starts on today’s muscle map. Create a plan opens a left-hand vertical week; each day has its own time, muscle selection, and save. `npm run typecheck` and `npm run lint -- --no-cache` PASS. `npm run export:web` PASS; the preview bundle contains Create a plan, YOUR WEEK, and Pick a training day. Browser on http://localhost:8081 shows the Google landing page. The signed-in muscle and day-by-day path was NOT RUN in this browser because it has no Google session. No commit or deploy.

## Weekly workout setup and returning welcome — October 11, 2026

Explicit human scope: recurring week, per-day local time/muscles/saved machines, device-local today selection, direct continuation into the usual editable plan, different-muscle escape, and next workout + Train today on rest days. Schedule only, no reminders. Windows owner implemented profile persistence/contracts and shared setup/welcome UI; session and voice action semantics unchanged.

Backend `.venv/Scripts/python.exe scripts/export_contracts.py` PASS. `.venv/Scripts/python.exe -m pytest backend/tests -q --basetemp .test-runs/weekly-schedule --tb=short`: **65 passed**, one upstream AnyIO warning in 5.90s. Coverage: day/time/unique-week validation, catalog/bounds/exclusions, all-or-nothing schedule write, token rotation/restart persistence, profile saves preserving weekly templates, cross-user isolation and unauthorized rejection. Existing workout/timer/voice tests still pass. `node scripts/check_schedule.cjs` PASS: local date, today selection, rest days, week wrap, focus names and 12-hour labels. `npm run typecheck`, `npm run lint -- --no-cache`, and production `npm run export:web` PASS; final build retains only the four production routes and existing upstream Three.js warning.

Browser: isolated synthetic local profile with real backend profile/schedule/session routes (Google OAuth itself bypassed by fixture, explicitly NOT a Google authentication gate). PASS: first-time Sunday setup at 09:30 with Quadriceps → two leg machines; Monday Chest at 18:30 → save a two-day week; restored profile displays Welcome back, Taylor and today's leg day; Continue opens saved leg machines directly; daily edits start a live backend plan at 3 sets × 11 reps while the weekly template remains 2 × 10; unsaved day draft survives switching days and blocks Finish; removing Sunday produces next Monday + Train today; Train today opens that saved chest plan; Choose different muscles opens the normal map. Production root-route checks also PASS for restored weekly profile, finished-session cleanup back to the welcome, and a 390px layout without clipped controls (weekly-welcome-mobile.png). Browser uses Windows system-local Sunday October 11; helper checks week wrap independently. Evidence: docs/evidence/weekly-setup.png, weekly-welcome-today.png, weekly-rest-day.png.

Temporary test route/fixture was kept out of the production source/build; profile/session access was not printed or placed in screenshots. Actual Google login remains NOT RUN for this change. Shared native screen code is type-checked, but iPhone/watch runtime NOT RUN on Windows. Profile-only schedule fields do not change watch/voice contracts. No commit/push/deployment performed.

## Persisted set timing and confirmed weight changes — October 11, 2026

Owner: Windows assistant, explicit human assignment across backend/shared UI/agent/watch consumers. Equipment confirmation starts the authoritative UTC set timer; set completion stops it and stores index, start/end, elapsed seconds, planned reps and that set's weight atomically in SQLite history. Rest expiry starts the next timer at its persisted deadline. Skip/end does not invent completed work. Legacy timing remains unavailable. New weight_updated action takes exactly one absolute/increase pound value with the current target; range/increment/phase/version validation and event deduplication apply. Previous records retain their original weights.

Commands on Windows, Python 3.13.3: `.venv/Scripts/python.exe scripts/export_contracts.py` PASS; `.venv/Scripts/python.exe -m pytest backend/tests -q --basetemp .test-runs/set-tracking-final --tb=short`: **51 passed**, one upstream AnyIO deprecation warning in 4.54s. New coverage: starts/stops, restart/late rest tick, recorded weights before/after increase, replay/no duplicate histories, concurrent completion/weight conflicts, phase/target/bounds/unknown weight rejection, invalid payloads, HTTP/tool parity, legacy timing and ending without completion. Approved execution outside sandbox was used for known Windows process/socket limitations.

Frontend: `npm run typecheck` PASS; `npm run lint -- --no-cache` PASS; `$env:NODE_OPTIONS='--max-old-space-size=4096 --max-semi-space-size=64'; npm run export:web` PASS (existing Three.js CommonJS deprecation warning). React review checks timer cleanup, server clock offset, keyed weight drafts, runtime tool validation, accessible controls and failures. Producer, generated schemas/examples, shared web/native handler and SwiftUI projection were updated together. Schema version remains 1 with additive output fields and a new opt-in action.

Browser using production export localhost:8081 and real backend localhost:8000, developer /watch route: **PASS** for equipment claim → live timer, completion → stopped timer/history (5.6s at 50 lb, 10 planned reps), conditional 5 lb suggestion, explicit button increase → 55 lb for set 2 with set 1 unchanged, reload persistence, rest expiry starting set 2, and final completion summary containing set 1 (5.6s at 50 lb) plus set 2 (44.2s at 55 lb). Evidence: `docs/evidence/set-timer-running.png`, `docs/evidence/set-history-weight-updated.png`, `docs/evidence/set-timing-summary.png`. Contract examples validate against the canonical models. This is a real button/state walkthrough, not a microphone conversation.

Live ElevenLabs speech/tool actions: **NOT RUN**. Updated prompt and optional weight arguments/action enum must be applied to the published agent; local files do not publish it. Native iPhone/watch build/runtime: **NOT RUN** on Windows; Mac owner must compile/test. Conditional progression text remains pending professional review. No commit/push/provider publication performed for this change.

## Stage 5 native watch implementation — October 10, 2026

Owner: Thanmay/macOS. Standalone SwiftUI source and shared Xcode scheme in `watch/`. Backend, agent and canonical contracts unchanged. See `watch/README.md` for reproducible build and manual pairing instructions.

| Check | Actual | Status |
|---|---|---|
| Watch compilation | Xcode 27.0 Debug build for watchOS simulator succeeds; no Swift compiler errors | PASS |
| Watch install/launch | Apple Watch Series 11 (46mm), watchOS 26.1; native “Join your workout” screen visible in Device Hub | PASS |
| Phone pairing label | Updated to cover native and browser watch; lint/typecheck pass | PASS |
| 5.1 same-session pairing | Join UI and Keychain persistence implemented; actual join not exercised | NOT RUN |
| 5.2 Taken + phone speech | Native event path implemented; shared-phone/voice walkthrough pending | NOT RUN |
| 5.3 Got it / Set done | Versioned events and acknowledged UI implemented; real control walkthrough pending | NOT RUN |
| 5.4 repeated/stale requests | Pending guard, observed-version check and exact-event retry implemented; live concurrency check pending | NOT RUN |
| 5.5 reopen/reconnect | Keychain restore and foreground refresh/backoff implemented; runtime recovery walkthrough pending | NOT RUN |
| 5.6 optional Talk | No watch microphone or Talk control added; use phone voice controls | DEFERRED |
| 5.7 confirmed End | Confirmation and backend summary implemented; cross-device audio cleanup pending | NOT RUN |
| 5.8 two rehearsals | No rehearsal run | NOT RUN |

**Stage 5 implementation is ready for pairing and manual acceptance; Stage 5 acceptance remains open.** The watch uses direct backend HTTP, not native WatchConnectivity. Physical pairing, Bluetooth, watch microphone and haptics are not validated. Existing Stage 4 live-workflow checks remain open independently.

## Latest native build result — October 10, 2026

This supersedes the earlier Xcode 26.1.1/native-build blocker entries below. Xcode 27.0 first-launch setup completed. Pinning `@livekit/react-native-webrtc` to 144.1.2 restores the WebRTC framework expected by LiveKit React Native 2.12.0 and ElevenLabs React Native 1.2.29. CocoaPods installation and the iPhone 17 Pro / iOS 26.1 Debug build passed (zero build errors/warnings). Spotter installed, launched, and rendered its setup form; after starting the local backend with `backend/.env`, the simulator fetched `/catalog` with HTTP 200. Lint, typecheck and web export passed.

**Native launch: PASS. Stage 2 native voice / Stage 4 acceptance: PARTIAL.** Live audio, conversation restart, full workout flow, watch-panel synchronization and recovery scenarios still require simulator walkthroughs. See `docs/DEVICE_CHECKS.md` for exact commands and dependency rationale. No backend or agent implementation changed in this fix.

## Google-first landing page — October 11, 2026

User-assigned scope update: web entry now shows a responsive landing page in the existing soft-blue Spotter theme. Workout setup is gated on a backend-verified Google profile; successful sign-in shows `Welcome, <first name>` and restores saved setup/plan. Returning profile credentials are checked before opening the flow. The watch route retains session-token pairing, and native development setup is retained because native Google sign-in is not implemented. This is a client entry gate, not a new backend authorization policy for workout endpoints.

Changed files: `mobile/src/screens/landing-screen.tsx`, `mobile/src/screens/trainer-screen.tsx`, `mobile/src/auth/google-sign-in.web.tsx`, README, master plan, validation and handoff. Existing uncommitted Google profile/backend changes were preserved; no canonical contract changed in this task. Google Identity Services now renders its official popup sign-in button instead of triggering One Tap from a custom button.

Windows verification: `npm run typecheck` PASS; `npm run lint -- --no-cache` PASS; `$env:NODE_OPTIONS='--max-old-space-size=4096 --max-semi-space-size=64'; npm run export:web` PASS (four routes, existing upstream Three.js deprecation warning). React component review covered effect cleanup, callback refs, disabled/loading controls, typed props and responsive layout. Sandbox preview/lint/export processes stalled; local server and final lint/export were run with approved execution outside the sandbox. Backend logic was unchanged and its tests were not rerun for this UI task.

Browser: production export served locally using `.venv/Scripts/python.exe -m http.server 8081 --bind 127.0.0.1 --directory mobile/dist`, alongside the existing backend. Desktop 1280px and narrow 390px layouts PASS; hero, workout preview, instructions and official Google button render without clipped text. Evidence: `docs/evidence/google-landing-desktop.png`, `docs/evidence/google-landing-mobile.png`. Real Google account authentication and the resulting authenticated welcome/setup transition remain NOT RUN; no mock sign-in is counted as live evidence.

Open launch blocker: `npm run web -- --port 8081` failed to resolve `expo-modules-core/src/ts-declarations/global` in the existing installed dependency tree and warned about a missing LiveKit package export. Production export succeeds; dependency files/manifests/lockfile were not modified. Next action: verify real Google popup sign-in and welcome/setup in the production preview, then repair the local development install separately. No commit, push or deployment performed.

## Windows install repair and Mac handoff

Node 24.11.1, npm 11.6.2. Repaired mobile/package-lock.json with npm install --package-lock-only --ignore-scripts --no-audit --no-fund: PASS; package.json unchanged. npm ci accepted the repaired lock but package downloads ended in ECONNRESET. Cached retry was stopped before completion when user requested handoff to Mac. Frontend typecheck/lint/browser/audio checks remain NOT RUN on Windows; an attempted typecheck before installation finished could not find the tsc command and is not code-quality evidence. Backend local health: HTTP 200, voice_configured true. Published agent GET: HTTP 200, Mat prompt + correct omission instruction, three attached tools, authentication enabled. No secret/token/body logged. Mac owner should run install/typecheck/lint, then Stage 2 web checks and native spike; no live audio PASS is claimed here.

## Live provider authorization check, October 10, 2026

Retest after user enabled ElevenAgents Write: **PASS**. backend.voice.authorize_voice accepted the real provider response using ignored local credentials. No token/key was printed and no conversation was started. This verifies authorization only, not audio, client-tool execution, or overall Stage 2 acceptance.

Windows Python 3.13.3 / pinned backend virtual environment; ignored backend/.env loaded locally, no credentials/token/body logged. Real ElevenLabs WebRTC token request returned HTTP 401, error category missing_permissions, explicitly requiring convai_write. Backend correctly surfaced sanitized HTTP 502. Read-only ElevenAgents API-key scope is insufficient for this endpoint. Next user action: change only ElevenAgents permission to Write, keep unrelated endpoints disabled, then rerun authorization. No conversation/audio was started; Stage 2 live voice checks remain NOT RUN.

## Dashboard setup follow-up, Windows

User-authorized browser configuration of Mat's draft: attached three existing client tools; verified response waiting and LLM parameter sources; saved action enum and optional target fields. Set repository prompt/greeting, preview defaults, and authentication. These are configuration observations, not live voice acceptance. The browser session became unavailable during final navigation; no publication/audio performed. Compatibility change normalizes omitted End/Retry targets to null and rejects incomplete/stale exercise targets. `.venv/Scripts/python.exe -m pytest backend/tests -q --basetemp=.test-runs/tool-config --tb=short`: **27 passed, 1 upstream warning in 2.62s**. Frontend typecheck/lint NOT RUN: npm ci fails on existing @emnapi lockfile inconsistencies; fallback dependency installation stalled and was stopped without changing manifest/lockfile. Live Stage 2 checks remain NOT RUN.

Run: October 10, 2026 on macOS. Node 24.13.x, npm 11.x, Python 3.14.2, Expo 57.0.27, React Native 0.86.3, ElevenLabs React 1.17.0. Codex in-app browser (WebKit; browser version not exposed). API http://localhost:8000; app http://localhost:8081; demo mode uses 5-second rests. Xcode 26.1.1 and iOS/watchOS 26.1 runtimes are available; no native app was built.

Stage numbers below match MASTER_PLAN.md. PASS applies to the stated environment and evidence, not the entire stage. Windows checks and joint contract approval remain pending.

| Check | Environment | Actual result | Status | Evidence / remaining work |
|---|---|---|---|---|
| 0.1–0.2 | Mac | Backend and browser launched; three-exercise routine loaded | PASS (Mac) | README commands; clean install/Windows launch NOT RUN |
| 0.3 | Mac | CORS requests accepted; authenticated WebSocket connects | PASS | Browser Live indicator; backend CORS test |
| 0.4 | Local source/config | Provider key is backend-only; frontend env contains API URL only | PASS | Backend token endpoint; frontend config |
| 0.5 | Shared contract | Schema version 1 exported; developer approval pending | NOT RUN | contracts/ and docs/API.md ready for review |
| 1.1 | Browser + real API | Strict session starts awaiting chest press confirmation | PASS | Manual walkthrough |
| 1.2 | Browser + real API | Taken defers chest press and selects seated row | PASS | Manual walkthrough; strict-mode test |
| 1.3 | Browser + real API | Claim starts exercise; completion saves one set and starts 5s rest | PASS | Manual walkthrough; initialized countdown fixed |
| 1.4 | Browser + real API | Deferred exercise retried; full routine finishes with six sets | PASS | Trainer and separate watch tab both show six sets/three exercises |
| 1.5 | Browser + automated backend | Refresh during rest retains deadline; restart persistence tested | PASS | Browser reload; test_rest_survives_restart. Full process restart during browser rest NOT RUN |
| 1.6–1.7 | Automated backend | Duplicate, concurrent, stale, wrong-target actions rejected/deduplicated | PASS | pytest suite; no double advancement |
| 1.8 | Browser + automated backend | All remaining equipment taken enters blocked; explicit retry works | PASS | Browser watch Taken flow; all-taken test |
| 1.9 | Browser + automated backend | Substitute requires acceptance and new claim; exclusions respected | PASS | Dumbbell press accepted manually; exclusion tests |
| 1.10 | Browser + automated backend | Normal completion: six sets/three exercises. Early end: one substituted set/zero completed exercises; reload retains result | PASS | docs/evidence/web-ended-summary.jpg; ended timer test |
| 2 web.1–2 web.7 | Browser + ElevenLabs | Web voice adapter and client tools are implemented; live microphone, speech, and tool conversation not tested | NOT RUN | Agent and backend credentials needed; `npm run typecheck`, `npm run lint`, and `npm run export:web` pass. No sponsor integration claim yet. |
| Voice configuration error | Browser | Unconfigured voice reports failure; workout controls still work | PASS | POST /voice/token returns 503 without provider request |
| 2 native.1–2 native.4 | iPhone simulator | Native adapter, LiveKit dependencies, and microphone permission are implemented. `npx expo run:ios --configuration Debug` failed before app launch: LiveKit compile could not find `WebRTC/WebRTC.h`; ExpoModulesJSI build script also failed. Simulator runtime/audio checks not run. | FAIL (build) | Mac Xcode 26.1.1; Expo SDK 57 docs require Xcode 26.4+. Build output also reports CoreSimulatorService unavailable. Resolve the native toolchain/dependency build issue, then install, launch, speak, hear reply, and restart the conversation. |
| 3.1–3.3 | Windows browser, two tabs + live agent | Separate watch Taken/Got it synchronized both tabs; agent generated the correct external-action explanation | PARTIAL | State synchronization passed. Automated run observed response text and Speaking status but did not independently verify audible output. |
| 3.4–3.8 | Windows browser + live agent | Two-control race advanced once; watch hard reload recovered set 2/2; voice disconnect/reconnect retained state; one 6-set routine completed | PARTIAL | Spoken question, voice-vs-control race, audible-output confirmation and second full spoken run remain. See detailed Stage 3 section below. |
| 4 prep | Mac + Expo prebuild | Native-only LiveKit WebRTC globals now register before Expo Router; web uses a platform no-op. iOS config regenerates with the microphone permission. | PASS (setup only) | `npx expo prebuild --platform ios --no-install`, `npm run lint`, `npm run typecheck`, and `npm run export:web` pass. Native compile remains blocked by Xcode 26.1.1 (Expo SDK 57 requires 26.4+) and unavailable CoreSimulatorService. |
| 4, 5 | Native simulators | Full iPhone app and actual SwiftUI watch app not tested | NOT RUN | Browser watch panel is explicitly labeled simulation |
| 6 | Submission | Code local; no submission/publishing performed | NOT RUN | Human publication authorization and final demo required |

## Automated checks

- `python3 -m pytest backend/tests -q`: **14 passed** (0.66 seconds).
- `npm run typecheck`: PASS.
- `npm run lint`: PASS.
- `npm run export:web`: PASS; static routes `/` and `/watch` exported.
- Contracts generated using `python3 scripts/export_contracts.py`.

Dependency audit: npm reports 30 findings (19 high, 11 moderate) after adding the Stage 2 native ElevenLabs/LiveKit dependencies. Findings are in the app/toolchain dependency tree. Suggested automatic fixes change Expo/React Native major versions; no forced downgrade/upgrade applied. Resolve with compatible upstream versions before a public release. This is an open dependency check, not a clean security certification.

Physical iPhone/headphone routing, locked-phone audio, real Apple Watch pairing, native WatchConnectivity, haptics and battery: NOT RUN and outside initial acceptance scope.

## Stage 2 Windows backend — October 10, 2026

Environment: Windows, Python 3.13.3, isolated .venv installed from unchanged backend/requirements.txt: FastAPI 0.129.0, Pydantic 2.12.5, Uvicorn 0.40.0, HTTPX 0.28.1, pytest 9.0.3. No browser or native simulator run. Base URL remains http://127.0.0.1:8000. Tests use temporary SQLite and HTTPX MockTransport, with no real provider request or credentials. Mock tokens/keys are synthetic.

Commands: `.venv/Scripts/python.exe scripts/export_contracts.py` PASS; `.venv/Scripts/python.exe -m pytest backend/tests -q --basetemp=.test-runs/stage2-pinned --tb=short`: **26 passed, 1 warning in 2.24s**. Warning is the installed Starlette TestClient's deprecated AnyIO BlockingPortal alias. Earlier available-system-dependency run: 26 passed in 2.48s. Approved unsandboxed execution was used because the Windows sandbox previously stalled asyncio socketpair initialization. No frontend checks were rerun or claimed.

Post-pull integration check on macOS: `python3 -m pytest backend/tests -q`: **26 passed in 0.79s**, including generated tool definitions against `mobile/src/voice/voice-panel-shared.tsx`. In `mobile/`, `npm run typecheck` and `npm run lint` pass; `npm run export:web` passes with the shared voice component. These checks do not establish live ElevenLabs credentials, agent setup, or spoken audio behavior.

| Stage / check | Owner | Environment | Expected | Actual | Status | Evidence / blocker |
|---|---|---|---|---|---|---|
| 2 backend authorization | Windows | API + simulated provider | Session-scoped authorization before provider request | Missing, invalid and cross-session tokens rejected; finished workout rejected | PASS | test_private_authorization_scoped_and_no_cache |
| 2 backend authorization | Windows | API + simulated provider | Typed token; no caching; key stays server-side | Configured agent called with backend header; fresh response each call; no-store | PASS | test_private_authorization_scoped_and_no_cache |
| 2 backend failure handling | Windows | API + simulated provider | Provider failures preserve workout and suppress secrets | 401/429/500/redirect/timeout/missing/empty/wrong-type/invalid-JSON map to 502; progress unchanged | PASS | test_provider_errors_are_sanitized |
| 2 backend setup | Windows | API + simulated provider | Missing configuration actionable; invalid input rejected | 503 with no provider call, 422 extra/empty input | PASS | test_missing_configuration_and_schema |
| 2 tool definitions | Windows | Local canonical schemas | Names/action enums match client/backend | Generated artifacts match and client names exist; no rest_elapsed tool action | PASS | test_exported_tools_match_backend_and_client; runtime speech still NOT RUN |
| 2 web.1 | Thanmay + Windows | Browser + live ElevenLabs | Exercise introduction and spoken reply | No agent created yet | NOT RUN | User requested setup instructions |
| 2 web.2 | Thanmay | Browser + live ElevenLabs | Repeat leaves progress unchanged | Prompt rule prepared only | NOT RUN | Live tool/voice check required |
| 2 web.3 | Thanmay | Browser + live ElevenLabs | Set done acknowledged after one accepted action | Definitions and backend tested only | NOT RUN | Live tool/voice check required |
| 2 web.4 | Thanmay | Browser + live ElevenLabs | Grounded guidance, no observed-form claim | Catalog boundary/prompt documented only | NOT RUN | Live answer and content review required |
| 2 web.5 | Thanmay | Browser + live ElevenLabs | Mic denial/disconnect preserves session and buttons | Authorization failures tested only | NOT RUN | Actual mic/connection recovery required |
| 2 web.6 | Thanmay | Browser + live ElevenLabs | End releases conversation/audio resources | Finished session cannot get new token | NOT RUN | Existing connection cleanup must be verified in browser |
| 2 web.7 | Thanmay | Browser + live ElevenLabs | Two-minute idle/noise has zero transitions | No audio sample run | NOT RUN | Prompt rules are not speaker-identification evidence |
| 2 native.1–4 | Thanmay | iPhone simulator | Launch; live mic/reply; end/restart; PASS or concrete blocker | Build attempted; no app launch. Live mic/reply and end/restart not run. | FAIL (build) | `npx expo run:ios --configuration Debug` fails on missing `WebRTC/WebRTC.h` and ExpoModulesJSI; Xcode 26.1.1 is below Expo SDK 57's documented Xcode 26.4 minimum. See docs/DEVICE_CHECKS.md. |

Stage 2 overall remains open. Private agent setup instructions are in agent/README.md. Prompt and catalog guidance are developer-authored; professional content review is not certified. No provider configuration or conversation was created. Mobile voice adapter implementation is local; live voice and simulator evidence remain pending. No commit/push/deployment was performed by this validation.

## Stage 3 Windows backend — October 10, 2026

WebSocket authorization, snapshot and pong frames now have exported Pydantic contracts. Automated checks verify the initial snapshot, a watch-sourced accepted event and acknowledgment, duplicate replay acknowledgment, external-action broadcast, reconnect to the authoritative latest version, ping/pong, and close code 1008 for invalid authorization. Command: `.venv\Scripts\python.exe -m pytest backend/tests -q --basetemp=.test-runs/stage3 --tb=short`: **31 passed, 1 upstream warning in 2.57s**. A Windows browser walkthrough was attempted; `npm run web` could not start because the interrupted frontend installation left the local Expo executable unavailable.

This completes the backend-owned Stage 3 transport hardening. Browser results recorded below supersede the earlier browser-pending note.

## Stage 3 Windows browser — October 10, 2026

Environment: Windows, Expo web at `http://localhost:8081`, backend at `http://127.0.0.1:8000`, live configured ElevenLabs agent, two browser tabs. Session credentials are intentionally omitted.

| Check | Actual | Status | Evidence / limitation |
|---|---|---|---|
| 3.1 | Trainer and separate watch tab joined one live session. Taken in the watch moved both tabs from Chest press to Seated row. | PASS | Both tabs showed Live and the same next exercise/decision. |
| 3.2 | The agent connected and produced the correct Seated row explanation after an external Got it action; UI changed through Speaking to Listening. | PARTIAL | Response text and speaking status verified, but this automated run did not independently verify audible output. |
| 3.3 | Got it in the watch moved both tabs to Seated row set 1 with matching state. | PASS | Trainer received the committed snapshot and agent explanation. |
| 3.4 | Near-simultaneous Set done clicks in trainer and watch saved only one set; after rest both showed set 2/2. | PARTIAL | Two-control race passed; the competing action was not spoken voice. Automated backend concurrency coverage also passes. |
| 3.5 | Hard-reloaded the watch route; it restored credentials, fetched current state and displayed Live at set 2/2. | PASS | No stale command or old cue replay was observed. |
| 3.6 | Disconnected and reconnected live voice at set 2/2; workout state remained intact and connection returned to Listening. | PASS | No false workout advancement occurred. Backend-stop recovery was not separately exercised. |
| 3.7 | Mute listening changed to Talk to Mat and reconnect restored Listening. | PARTIAL | Actual spoken question/reply and timed listening-window closure require manual microphone input. |
| 3.8 | Completed one full strict routine with one Taken report, deferred retry, rests and normal ending: 6 sets, 3 exercises, 0 skipped. | PARTIAL | `docs/evidence/stage3-windows-summary.png`. A spoken question and second complete spoken run remain required. |

Stage 3 remains **PARTIAL**. Required manual remainder: verify audible external-action speech, ask and receive one microphone question, run voice-vs-control concurrency, and complete the scenario a second time.

## Muscle-first workout builder — October 10, 2026

Explicit scope change after the original staged demo: the fictional gym now contains 18 source-backed machines and ten selectable muscle groups. Setup supports deterministic plan preview, remove/add/approved replacement, editable sets/reps and an optional pound slider. Guidance remains `professional_review_pending`.

Automated backend command: `.venv\Scripts\python.exe -m pytest backend/tests -q --basetemp=.test-runs/muscle-builder --tb=short`: **35 passed, 1 upstream warning in 2.89s**. Coverage includes catalog/source integrity, recommendation balance/cap/de-duplication, custom-plan validation, settings bounds, replacement weight reset and all prior session/voice/stream regressions. Contract export, mobile typecheck and lint pass. Browser walkthrough is recorded separately after the implementation checks below.

Final verification: contract export PASS; backend **35 passed, 1 upstream warning in 4.94s**; `npm run typecheck`, `npm run lint` and `npm run export:web` PASS. Windows browser walkthrough selected Chest and Back, verified both front/back regions turned red, received the expected four-machine preview, removed Pec deck, replaced Chest press with Pec deck, changed it to 3 sets × 11 reps at 90 lb, approved the plan and reached a live authoritative session showing Pec deck at Floor 1 · Push zone with exactly those settings. Status: **PASS (Windows web)**. Evidence: `docs/evidence/muscle-builder-selected.png`, `docs/evidence/muscle-builder-approved.png`.

## Interactive 3D muscle model — October 10, 2026

Environment: Windows, Expo SDK 57.0.27, React 19.2.3, React Three Fiber 9.8.1, Three.js 0.186.1, browser app at `http://localhost:8081`.

| Check | Actual | Status | Evidence / limitation |
|---|---|---|---|
| Licensed asset integrity | Bundled GLB is 8,819,872 bytes; SHA-256 matches `5234472152a791baf002bed614707c33ba3ab2b278e41f41899a79a453d40785`. BodyParts3D/Z-Anatomy attribution, upstream license, and Draco notice are preserved. | PASS | `mobile/public/models/`; `mobile/public/draco/` |
| Web load and rotation | Draco-compressed anatomy loaded from the local app. Screenshots several seconds apart showed changed orientation. | PASS | `docs/evidence/interactive-3d-loaded.png` |
| Mesh selection and highlighting | A direct torso mesh click selected Core; labeled button state changed to Remove Core. Selected surfaces render bright red while non-selected anatomy uses a dimmed cool-gray palette, so deeper mapped muscles remain visible without red-on-red ambiguity. | PASS | Browser accessibility state; `docs/evidence/interactive-3d-centered-contrast.png` |
| Manual orbit and resumed rotation | The source annotation is excluded from body bounds. Horizontal canvas drag changed orientation around a vertical axis through the centered body; automatic rotation resumed. Pitch, pan, and zoom are disabled. | PASS | `docs/evidence/interactive-3d-centered-contrast.png` |
| Accessible/native fallback | Ten labeled toggle buttons remained operable alongside WebGL. Platform resolution retains the SVG schematic on native; model error boundary renders the same schematic on web failure. | PASS (web/source) | Native runtime itself NOT RUN on Windows |
| Volume threshold | A Back plan at exactly six sets showed no caution. Raising it to seven showed Back: 7 sets and Biceps: 7 sets, confirming primary and secondary counting. | PASS | `docs/evidence/interactive-3d-volume-caution.png` |
| Acknowledgment gate/reset | Approval was disabled at seven sets, enabled after checking the caution, then disabled and unchecked after changing reps while volume remained high. | PASS | Browser accessibility state |

Commands: `.venv\Scripts\python.exe -m pytest backend/tests -q --basetemp=.test-runs/interactive-3d --tb=short`: **35 passed, 1 upstream warning in 3.93s**. `npm run typecheck`: PASS. `npm run lint`: PASS. `$env:NODE_OPTIONS='--max-old-space-size=4096'; npm run export:web`: PASS; `/`, `/watch`, `/_sitemap`, and `/+not-found` exported. The final export reports Three.js's upstream CommonJS deprecation warning but no build failure.

WebGL resilience follow-up, October 11: a browser context-allocation failure was reproduced after several concurrent 3D tabs and memory pressure. The model now preflights WebGL, requests a low-power context with antialiasing disabled, renders at device-pixel ratio 1, and falls back to a user-selectable 2D map instead of mounting the WebGL canvas when no context is available. Browser validation switched from 3D to the lightweight map and selected Chest successfully; switching does not change workout selection. `npm run typecheck`, targeted Expo lint, and web export pass. The bundled Draco GLB remains 8,819,872 bytes; a materially smaller 3D runtime would require a separately reviewed decimated asset.

## Enriched catalog UI — October 11, 2026

Environment: Windows, Expo SDK 57.0.27, React Native Web 0.21.0, browser app at `http://localhost:8081`, backend at `http://127.0.0.1:8000`.

## Google profile save — October 11, 2026

Automated backend: `python -m pytest backend/tests -q --basetemp .tmp_pytest_auth`: **38 passed**. Coverage includes Google ID-token verification, name/plan persistence across sign-in, stale profile-token rejection, unverified-email rejection, and 503 when `GOOGLE_CLIENT_ID` is missing. `python scripts/export_contracts.py` PASS. `npm run typecheck` PASS. Live Google Cloud client ID and browser sign-in remain NOT RUN until the user adds the web client ID to ignored `.env` files.

The client now validates and consumes `body_regions`, `equipment_catalog`, and `exercise_metadata`. Selecting Chest and Back displayed the normalized region names and highlighted both muscle groups. The generated four-machine plan displayed movement pattern, explicit unknown difficulty, equipment type, normalized floor/zone, unknown manufacturer/model, and the configured weight range/increment. Expanding Chest press rendered preserved setup, execution cue, mistakes, troubleshooting, stop conditions, source titles/plain URLs, and the pending-review warning. After plan approval, the active Chest press screen retained the catalog-derived machine summary and guide control.

Browser walkthrough: **PASS**. Evidence: `docs/evidence/catalog-regions-wired.png`, `docs/evidence/catalog-machine-guide-wired.png`, `docs/evidence/catalog-active-workout-wired.png`.

Commands: `npm run typecheck`: **PASS**. `npm run lint -- --no-cache`: **PASS**. `$env:NODE_OPTIONS='--max-old-space-size=4096 --max-semi-space-size=64'; npm run export:web`: **PASS** with the existing upstream Three.js CommonJS deprecation warning. `python -m pytest backend/tests -q --basetemp .tmp_pytest_catalog_ui`: **35 passed**. The first browser load correctly rejected a stale pre-change catalog held by the already-running backend; restarting the local backend loaded the current JSON and the walkthrough passed.

Pre-push verification, October 11: pinned backend command .venv/Scripts/python.exe -m pytest backend/tests -q --basetemp .test-runs/pre-push-auth --tb=short PASS: 38 passed, one upstream AnyIO deprecation warning in 4.53s. Real Google browser authentication remains NOT RUN.


## Trainer persona and motivation — October 11, 2026 (macOS)

Implemented configurable name, three avatar colors/expressions/accessories, motivation text, reminder toggle, opening card/skip, speaking avatar state, completed-work celebration, and edits for future workouts. Signed-in profiles persist through the existing SQLite-backed profile API; session preferences capture the persona. Existing profiles/snapshots default to Mat. No dependency changes. Existing staged package-lock edits were preserved.

- PASS: `.venv/bin/python -m pytest backend/tests -q` — 43 passed; one upstream AnyIO deprecation warning. New tests cover profile/login/session persistence and invalid persona inputs; existing legacy session payloads still pass.
- PASS: `npm run typecheck`, `npm run lint`, `npm run export:web` in mobile. Export retains the upstream Three.js CommonJS warning.
- PASS: `node scripts/test-reminder-state.mjs` — reconnect/reload suppression, fresh-session eligibility, corrupt history, unavailable storage fallback.
- PASS (Chrome editor): renamed draft to Pip, selected mint/calm/headphones, entered sample motivation, observed matching avatar and reminder preview; start disabled while editing; Cancel restored Mat and discarded sample text. Sample data was not saved to the real profile. Evidence: `docs/evidence/trainer-persona-editor.png` (default editor left open after discarding the sample).
- Local backend restarted on the existing port to load the new additive schema. No external agent deployment, commit, or push.
- NOT RUN: native runtime, live spoken reminder/name, interrupted speech, full browser start/skip/reconnect scenario. Customized persona persistence has automated coverage. Voice request history is not audible-delivery proof. Native unsigned setup uses the current app process; signed-in web profile persistence is the supported cross-visit flow.
- Provider handoff: apply `agent/prompt.md` and neutralize the old hardcoded Mat greeting, then perform the voice checks in `agent/README.md`. Watch ignores the additive preferences object; watch UI was not changed.

- PASS (live Chrome save/reload): saved the default Mat persona with empty motivation to the existing local signed-in profile, reloaded, and observed Mat plus the unchanged Lat pulldown plan. Reopened customization for the user. No sample motivation was retained.

Opening-cue tone follow-up: replaced the read-aloud script with a request to naturally paraphrase the personal note in one or two sentences, without announcing motivation or a reminder. The on-screen greeting uses conversational encouragement; voice incorporates the saved note. Live spoken wording remains NOT RUN; the provider prompt update remains pending.

## Pull integration — October 11, 2026

Merged Rahul’s `50b4437` set-timer/confirmed-weight work with local trainer-persona commits. Preserved both prompt sections, API fields, avatar/encouragement, set tracking/history, and confirmed weight actions; regenerated contracts from merged models. PASS: backend pytest (56 tests), mobile typecheck, lint, reminder-state checks, and web export. Native/live voice checks were not repeated for this merge.

## Intentional voice disconnect popup — October 11, 2026

User requested removal of the LiveKit signal-stream error popup on Disconnect voice. The app marks the conversation before intentional disconnect (including workout completion); for ten seconds, only that room's exact signal-stream WebSocket ConnectionError is logged at info instead of error, keeping it out of Expo's error overlay. Other rooms/errors and SDK error handling remain unchanged. No console monkey-patch, global LogBox suppression, or dependency edits. End-session promise failures surface an actionable inline error.

PASS: mobile typecheck and lint; focused logger harness confirms intentional hangup is informational while other rooms, messages and error types retain error reporting. Live browser/native disconnect and reconnect NOT RUN; reload the app to pick up the logging change.


## Web 3D default and removal of 2D — October 11, 2026

Supersedes the earlier user-selectable 2D fallback. Web setup automatically attempts 3D; the unused web schematic and mode switch are removed. WebGL/model failures show an error and Retry, with muscle buttons outside the error boundary. Retry clears the GLTF loader cache and remounts the model without changing selection. Existing rotation/highlighting code and native rendering remain unchanged. No API changes.

Mac checks: `npm run typecheck`, `npm run lint -- --no-cache`, `npm run export:web`, and `git diff --check` PASS. Export retains the existing Three.js CommonJS and color-environment warnings. Chrome at localhost:8081 PASS: automatic startup reaches the explicit WebGL failure UI; no 2D map/toggle; Chest selection remains enabled and survives Retry; Retry visibly enters Starting 3D model before returning to the error. Original selection restored after checking. Successful 3D rendering, rotation, and visual highlighting remain NOT VERIFIED in this tab because canvas creation reports WebGL unavailable. No commit, push, or deployment.


### Correction: false WebGL error fixed — October 11, 2026

The preceding WebGL-unavailable observation was caused by our throwing Canvas fallback, not evidence that the browser lacked WebGL. Installed React Three Fiber 9.8.1 mounts its `fallback` as canvas DOM children even when WebGL is supported. Replaced that unconditional throw with passive text; actual renderer configuration failures already propagate to the error boundary. Preflight now requires WebGL2, matching installed Three.js. After reload, Chrome localhost:8081 successfully loaded and visibly rendered the 3D anatomy with existing muscle highlights and no error panel. Typecheck, lint, and web export PASS; existing upstream export warnings remain. Genuine renderer-failure recovery was not re-induced in this follow-up.


### Centered anatomy framing — October 11, 2026

Camera and orbit target now align with the normalized model origin (y=0); camera distance increased from 5 to 5.8 to leave head/foot margins. Chrome localhost:8081 visual PASS: full body centered and feet no longer clipped. `npm run typecheck` and `npm run lint -- --no-cache` PASS. Native rendering unchanged.

## UI polish — October 11, 2026 (macOS)

Refined shared action buttons with outlined secondary actions, readable disabled states, focus feedback, and selected accessibility state. Muscle choices now have checkmarks and 48px targets; set steppers have 44px targets and visible disabled/pressed states. Setup gains a header divider, smaller panel headings, phone spacing, a safer two-column breakpoint, wrapping summary metrics, and a trainer card that wraps without crushing its text. Weekly planning retains the left day rail with abbreviated visual labels on phones and full accessible names. No API or workout-state changes.

PASS: mobile `npm run typecheck`, `npm run lint -- --no-cache`, `npm run export:web`; `git diff --check`. Export retains existing Three.js CommonJS and color-environment warnings.
PASS: Chrome desktop visual inspection of setup and selected controls; 390px viewport trainer wrapping, weekly day selection/time field, disabled Build this day with no selection, and no document horizontal overflow. Returned to today's setup and reset viewport. Evidence: `docs/evidence/ui-polish-controls.png`.
NOT RUN: native runtime, live voice, full workout replay, landing/sign-in visual regression. Existing muscle-model and planning-document edits preserved.

UI placement follow-up: moved Create a plan (and the corresponding Today’s workout return action) into the welcome row, right-aligned on desktop and below the greeting on phones. Removed its separate row above the greeting. Mobile typecheck, lint, and diff whitespace checks PASS.

## Snowflake analytics — October 11, 2026

Explicit user selection: Snowflake for workout analytics. Added optional connector dependency, read-only local event extraction, sequential retry-safe MERGE export, equipment insights view/query, and setup/demo runbook. Existing workout engine/API unchanged. No user profiles, tokens, trainer preferences or free-form motivation are exported.

PASS (macOS): `.venv/bin/python -m pytest backend/tests -q` — 75 passed, one existing AnyIO deprecation warning. New tests cover accepted-only extraction, retry deduplication, completed exercise/set metrics, deferred equipment mapping, allowlisted fields and missing source failing without creating a DB. `.venv/bin/python -m backend.snowflake_sync --dry-run` — 44 accepted events across 11 sessions. `git diff --check` PASS.

NOT RUN: live Snowflake authentication, DDL/MERGE/view execution, repeated-sync cloud row counts and live worksheet demonstration. Account/warehouse/database/schema connection setup is pending. Local test success does not establish a working sponsor integration. Sync is operator-triggered, single-writer, and full-scan; no auto streaming or UI dashboard. No cloud data changed, commit, push or deployment.


## Vercel web deployment configuration — October 19, 2026

Changed files: root `vercel.json`, `scripts/check_web_deploy.mjs`,
`docs/DEPLOYMENT.md`, README, master plan and this record. Existing uncommitted
UI and Snowflake work preserved. No contract or backend behavior changes.
Owner: Thanmay/macOS; Node v24.13.1.

- PASS: `npm run typecheck --prefix mobile`.
- PASS: `npm run lint --prefix mobile -- --no-cache`.
- PASS: `EXPO_PUBLIC_API_URL=https://api.example.com EXPO_PUBLIC_GOOGLE_CLIENT_ID=build-check.apps.googleusercontent.com node scripts/check_web_deploy.mjs` followed by `npm run export:web --prefix mobile` with the same public variables. These are test placeholders, not a real provider or API. Export includes index, watch, sitemap and not-found HTML, model and Draco assets. Existing Three.js CommonJS and color-environment warnings remain.
- PASS: five subprocess guard cases: missing variables, HTTP localhost, HTTPS localhost and missing Google client ID reject; HTTPS API plus client ID accepts.
- PASS: `git diff --check`.
- NOT RUN: clean Vercel install/build, public deployment, hosted Google sign-in, backend volume persistence, WebSocket synchronization and live voice.

Next action: supply a persistent single-instance backend, configure its HTTPS URL
and matching Google OAuth client ID in Vercel, add exact Google/CORS frontend
origins, deploy the branch containing the root configuration, then run the hosted
checks in `docs/DEPLOYMENT.md`. No commit, push or cloud settings changed.


## Neon PostgreSQL integration — October 19, 2026

Owner: Thanmay/macOS; Python 3.14, Psycopg 3.3.3, isolated local PostgreSQL 18.
Changed: backend/database.py, store.py, app.py, requirements.txt, .env.example,
backend/migrations/001_initial.sql, migrate_sqlite.py, database/config tests,
test isolation, README, API/deployment docs, master plan and this record. Existing
UI/Snowflake work preserved. No client, tool, canonical contract or watch changes.

- PASS: `SPOTTER_TEST_DATABASE_URL=postgresql://spotter_test@127.0.0.1:55439/spotter_test .venv/bin/python -m pytest backend/tests -q` — 97 passed, one existing AnyIO deprecation warning. Actual PostgreSQL covers full/deferred workouts, alternatives/exclusions, duplicate/conflicting retries, concurrent completions, profile/login races and token rotation, schedules, restart-safe rests, timing/weight history, ended sessions, HTTP/stream synchronization, rollback and no idle polling.
- PASS: `.venv/bin/python -m pytest backend/tests -q` — 77 passed, 20 explicit local-PostgreSQL tests skipped when their test URL is absent; routine collection ignores developer/cloud DB settings.
- PASS: real SQLite-to-local-PostgreSQL migration preserves all four tables, IDs and tokens; nonempty target refuses import; a deliberately invalid text value midway through copying rolls back every inserted row.
- PASS: read-only `SELECT 1` using DATABASE_URL from ignored backend/.env against Neon. Credentials and endpoint withheld. This proves connectivity only, not cloud workflow acceptance.
- PASS: `.venv/bin/python -m backend.migrate_sqlite` — source counts: 25 sessions, 76 events, 2 users, 2 schedules. Ignored pre-Neon SQLite backup created in backend/data; source file retained.
- PASS: `git diff --check`.
- BLOCKED pending explicit owner approval: actual transfer of existing records to Neon. Automatic approval review rejected `python -m backend.migrate_sqlite --apply` because its payload includes profiles, session/event state and token hashes, and requested specific authorization for this payload/destination. No transfer occurred and no workaround was used.
- NOT RUN: live Neon schema initialization/import, live Neon profile/session/voice/browser walkthrough, hosted deployment and native tests. Local database tests do not prove those gates.

Next action: obtain explicit approval to copy the listed records to the Neon
database configured in backend/.env, then run the tested migration and verify
cloud counts/workflows. A clean empty-cloud start is also available if the owner
chooses it. No commit, push, deployment or external provider changes.

Handoff: PostgreSQL uses transaction-scoped serialization across all store
operations. No idle half-second expiry worker runs for PostgreSQL; active streams
and server reads/actions reconcile persisted rest deadlines. SQLite retains its
local worker. Snowflake export is currently SQLite-only and does not export new
Neon events; no claim of cloud analytics support. Backend run commands now load
backend/.env without overriding hosting environment variables.


## Vercel npm lockfile discovery — October 19, 2026

Owner: Thanmay/macOS; Node 24.13.1, npm 11.8.0. User-provided Vercel
log for ede7842 fails at `npm ci --prefix mobile` with EUSAGE. The same
commit contains mobile/package-lock.json (version 3); local dry-run accepts
the manifest/lockfile. Exact Vercel npm version/root-directory environment
was unavailable, so the hosted root cause is not fully reproduced.

Changed root vercel.json to explicitly enter mobile for install/export:
`cd mobile && npm ci` and
`node scripts/check_web_deploy.mjs && cd mobile && npm run export:web`.
Updated deployment troubleshooting; no dependencies or lockfile changes.

PASS: copied only package.json/package-lock.json to an isolated temporary
mobile directory, then ran `npm ci --offline --no-audit --no-fund` from that
directory (clean install; no existing node_modules from the app).
PASS: exact new build command with explicitly supplied placeholder HTTPS API
and Google client ID exported index/watch/sitemap/not-found routes. This
checks bundling only; no network/API/provider acceptance. Existing Three.js
CommonJS warning remains.
PASS: git diff --check. NOT RUN: Vercel redeployment.
Next: publish the changed config/docs through the user's normal Git flow,
keep Vercel Root Directory at repository root and redeploy. If install still
fails, capture effective working directory/npm version and lockfile presence
from the hosted environment. No commit, push, deployment or cloud-data changes.


## Vercel backend configuration correction — October 19

Human clarified backend-only target. Replaced Expo/npm root vercel.json with FastAPI, Python dependency install, empty build command and default output directory. Added root requirements.txt forwarding to pinned backend requirements. Existing pyproject entrypoint retained. Updated deployment runbook, README and plan. No API behavior/contract changes.

PASS: JSON/TOML configuration parsing and git diff --check. NOT RUN: Vercel hosted build, API/Neon/voice/WebSocket acceptance. Next: clear Vercel Root Directory to repository root, remove saved frontend overrides, publish these changes through the human Git workflow and deploy the new commit. No commit/push/deployment or personal-data transfer performed.


## Separate Vercel configurations — October 19

Restored root vercel.json byte-for-byte to the checked-in frontend configuration. Added backend/vercel.json as an alternate FastAPI config for CLI selection from repository root; retained root pyproject entrypoint and requirements forwarding. Updated README/deployment/plan to document separate projects and explicit backend config selection. No runtime code, client contracts, data or provider changes.

PASS: root config matches HEAD; JSON/TOML parsing, dependency include paths and git diff --check. NOT RUN: actual Vercel backend/frontend deployments. Root frontend install/export was validated earlier; unchanged commands were not repeated. Backend project uses --local-config backend/vercel.json from repo root, not backend/ as root. Nested config alone does not configure Git deployments. No commit, push or deploy.


## Independent Vercel application roots — October 19, 2026

Human approved the clean monorepo structure for frontend and backend on separate
Vercel projects. This supersedes all prior root/alternate-config/staging guidance.
Owner: Thanmay/macOS, Node 24.13.1, Python 3.14, local PostgreSQL 18.

Changes: moved frontend config and environment guard into mobile/; moved backend
pyproject into backend/ with app:app entrypoint; removed root deployment files.
Backend runtime is now backend/spotter with relative imports, catalog lives in
backend/catalog, migration SQL in backend/spotter/migrations. backend/app.py
retains the repository import facade and provides the standalone entrypoint.
Updated test/export imports and affected runbooks/ownership paths; added per-app
.vercelignore files. Existing ignored .env/SQLite files and backup remain intact.

- PASS: `SPOTTER_TEST_DATABASE_URL=postgresql://spotter_test@127.0.0.1:55439/spotter_test .venv/bin/python -m pytest backend/tests -q` — 98 passed, one existing AnyIO deprecation warning. Includes all PostgreSQL rules, migration/rollback, concurrency and the new isolated deployment-root test.
- PASS: isolated root subprocess uses only copied backend app/package/catalog/config files; -I excludes repository import paths. Validated /health, /catalog (18 entries), /openapi.json, real session events/WebSocket updates, migration initialization, restart persistence and server rest expiry using temporary SQLite. The test compares equivalent UTC timestamps as datetimes.
- PASS: mobile `npm run typecheck`, `npm run lint -- --no-cache`.
- PASS: from mobile/, `node scripts/check_web_deploy.mjs && npm run export:web` with explicit placeholder HTTPS API/Google client ID. Export includes /, /watch, sitemap and not-found. Existing Three.js CommonJS warning remains; placeholders do not validate live services.
- PASS: `DATABASE_URL='' SPOTTER_DATABASE=/private/tmp/spotter-contract-export.sqlite3 .venv/bin/python scripts/export_contracts.py`; generated contracts/tool definitions have no diff.
- PASS: catalog/migration SQL byte comparison against pre-move Git versions; config JSON/TOML checks; per-app ignore checks exclude Pods/native output, local data, secrets and caches while preserving runtime assets and required manifests.
- PASS: git diff --check.
- NOT RUN: hosted Vercel builds, production API/Neon workflows, cross-origin Google sign-in, live voice and native runtime. Local WebSocket success does not establish Vercel WebSocket acceptance. No personal records copied to Neon.

Next: commit all moves/configs together, configure frontend Root Directory mobile
and backend Root Directory backend, clear old npm/Expo overrides on backend,
connect both projects to the same Git branch and deploy that new commit. Use
frontend/public and backend/private environment settings in docs/DEPLOYMENT.md.
No commit, push, deployment or external configuration changes performed here.


## Backend empty Vercel deployment — October 19

Read-only CLI inspection confirmed spotter-backend has Root Directory backend,
FastAPI preset, and production domain spotter-backend-seven.vercel.app assigned
to dpl_2rAGoseNxyBpB1vyP6WRibQ4Gmst. Its build listing contains only '.' [0ms]
and no Python function. No remote settings or deployments changed.

Removed backend/vercel.json's explicit empty buildCommand and null outputDirectory;
backend/pyproject.toml now selects spotter.app:app directly instead of the conditional
compatibility facade. Updated isolated deployment-root test to import the exact
configured module/instance. Frontend configuration is unchanged.

Next: publish the new commit, clear backend dashboard build/output overrides,
redeploy without cache, then verify a Python function and /health JSON. Exact
cause of the previous empty remote build has not been reproduced locally; this
configuration correction still needs hosted verification. No cloud data copied.


## Public privacy policy — October 20, 2026

Owner: Thanmay / macOS. User authorized page creation and deployment and supplied
mdasthanmay@gmail.com as the privacy/deletion contact.

- PASS: inspected current Google identity, profile/session storage, voice-context
  payloads, persistence and optional Snowflake export before drafting disclosures.
- PASS: Python HTMLParser/static assertions verified eight policy sections,
  contact/date, identical root and /privacy content, and no scripts.
- PASS: mobile `npm run typecheck` after adding the policy link to sign-in.
- PASS: Sites access set to public; version 1 deployment returned succeeded at
  https://spotter-privacy.mellowcabin4.chatgpt.site
  Site source commit: 468dd886d4174792a33f90a205228b90e2ed6f8a.
- NOT RUN: rendered browser/responsive checks; local Google Chrome launch was
  unavailable. Sites success verifies deployment, not Google OAuth approval.
- NOT RUN: frontend Vercel deployment; the new sign-in policy link is local only.

Handoff: page source and hosting identity live in sites/spotter-privacy/. That
subdirectory has its own Sites source repository; application repository changes
were not committed or pushed. Use the public root URL as the privacy policy URL.
For Google brand verification, separately confirm homepage linkage and domain
ownership requirements. ElevenLabs retention/training settings were not inspected
in the provider dashboard; the policy makes no zero-retention guarantee.
Next: deploy the frontend link with the next app release and update the policy
when actual retention or provider settings change. No user records were changed.


## Public Terms of Service — October 20, 2026

Owner: Thanmay / macOS. Added sites/spotter-privacy/dist/terms/index.html with
matching styling, account and acceptable-use terms, fitness/AI limitations,
privacy/deletion links, service availability and contact details. Added navigation
between public legal pages and a local sign-in Terms of Service link.

- PASS: Python HTMLParser assertions: ten terms sections, contact, no scripts,
  matching root/privacy policy copies, legal page navigation.
- PASS: mobile `npm run typecheck`; `git diff --check`.
- PASS: public Sites version 2 returned deployment succeeded; pushed source
  commit 46f6fd519f2182bd034b115ba583037b224b4761.
  Terms URL: https://spotter-privacy.mellowcabin4.chatgpt.site/terms/
- NOT RUN: rendered browser QA, Google brand approval, frontend Vercel deployment.

Next: paste the terms URL in Google’s Application terms of service link field.
The mobile sign-in link remains local until the next frontend deployment.
Application repo changes were not committed/pushed; only the separate Sites
source repository was published. No contract or backend changes.
