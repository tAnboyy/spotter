# Configure Mat — Stage 2 Windows owner

Backend and agent assets are ready for configuration. A real ElevenLabs agent has not been created or tested by this work. Thanmay owns browser handlers and the native audio spike; automated checks do not certify live audio.

## ElevenLabs dashboard setup

1. Create an agent named Mat. Choose an available conversational model and English voice in your account. Keep ElevenLabs as the only conversation system.
2. Paste `agent/prompt.md` into the system prompt. Set first message to: “Hi {{user_name}}, I’m Mat. Let me check your workout.” Do not introduce an exercise before the state tool returns.
3. Configure dynamic variables `workout_context`, `coaching_style`, `user_name`. The app supplies these at connection. Dashboard preview placeholders may be empty context, standard, and Demo. Actual workout tools require the real app's handlers, which are absent in dashboard preview.
4. Add exactly three tools of type **Client** using `agent/tools.json`. Names and arguments are case-sensitive. Enable **Wait for response** for every tool. This file is a generated dashboard specification, not an API create-agent request body. Its JSON Schema `anyOf` fields mean nullable string/integer arguments. No webhook URL or backend credential belongs in a client tool.
5. Keep agent authentication enabled. Backend obtains a WebRTC conversation token using its API key; browser receives only `conversation_token`. Review provider recording/retention settings for the demo. Local code does not log raw audio/transcripts by default.
6. Save the agent and copy its ID. Create an API key with permissions for that agent's conversation authorization. Keep both values in ignored `backend/.env` only, never in frontend public configuration, chat, screenshots or commits.

## Local setup

Verified permission: the API key needs **ElevenAgents Write** (`convai_write`) to request a conversation token. Read-only was rejected by the live provider. Leave unrelated endpoint permissions disabled.

From repository root, Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
# First setup only; preserve an existing backend/.env.
Copy-Item backend/.env.example backend/.env
# Edit backend/.env locally: fill ELEVENLABS_API_KEY and ELEVENLABS_AGENT_ID.
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --env-file backend/.env
```

macOS equivalents:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
# First setup only.
cp -n backend/.env.example backend/.env
# Edit backend/.env locally.
.venv/bin/python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --env-file backend/.env
```

`scripts/run_backend.py` does not load `.env`; use the explicit command above for voice. Start Thanmay's app with `cd mobile`, `npm ci`, `npm run web`. Start a workout on localhost:8081, choose Connect Mat's voice and grant microphone permission. `/health` reports configuration presence, not valid credentials or a live connection.

## Contract and curated content

`backend/tool_contract.py` defines canonical agent arguments. `python scripts/export_contracts.py` regenerates `agent/tools.json`, `contracts/client-tools.json`, HTTP schemas and OpenAPI. Existing frontend names and arguments are preserved. Map `current.instance_id` to action argument `exercise_instance_id`; map `current.id` to guidance argument `exercise_id`. Dashboard target parameters are optional: omit them for end/retry; the handler normalizes omitted values to null. Exercise actions still require both current targets. Read-only tools return state/catalog data; submit returns `{success:true,snapshot}` or `{success:false,error}` as JSON strings from the browser handler.

`backend/catalog/demo.json` is the runtime guidance source for 18 configured machines: setup, cue, mistake, troubleshooting, stop conditions, muscles, approved alternatives, equipment, location and source URLs. Avoid a second coaching catalog or provider knowledge-base copy that can drift. Content is source-backed and developer-paraphrased but remains pending professional review. Mat must admit when a question exceeds that content. See `agent/GUIDANCE.md` for the review checklist.

## Live acceptance

Record Stage 2 web checks 1–7 separately in docs/VALIDATION.md: introduction/spoken question; Repeat without mutation; Set done acknowledged after one accepted event; grounded muscle/guidance answer; denied microphone/disconnect preserves buttons; ending releases audio; two-minute idle/noise sample has zero transitions. Compare version/completed count before and after Set done; ambiguous “done” should request clarification. Simulated provider responses do not prove live speech.

Thanmay records native spike checks 1–4 on Mac: development build launch, actual microphone/reply, end/restart, PASS or concrete blocker. Expo Go and Windows browser tests cannot satisfy those checks.

Troubleshooting: 401 means session access mismatch; 409 means workout finished; 503 means missing configuration; 502 means provider authorization failed. Provider bodies are suppressed. Check key permissions, private-agent ID and connectivity locally. Reconnect with a newly issued token; never cache or log it. Provider tokens authorize an agent conversation; separate backend session tokens authorize workout access. Frontend ending cleanup stops existing conversations; issuing a token is not provider-side revocation.

References checked October 10, 2026: [WebRTC token](https://elevenlabs.io/docs/eleven-agents/api-reference/conversations/get-webrtc-token), [client tools and Wait for response](https://elevenlabs.io/docs/eleven-agents/customization/tools/client-tools), [dynamic variables](https://elevenlabs.io/docs/eleven-agents/customization/personalization/dynamic-variables).


### Personalized trainer / opening motivation

The existing `workout_context` now includes `preferences.trainer`. Apply the updated `agent/prompt.md` to the configured provider agent before claiming live persona support. Replace any dashboard first message that hardcodes Mat with a neutral greeting such as “Welcome back. Let’s get ready for your workout.” No new dynamic-variable configuration is needed. The app sends the display name as context and one explicit read-only opening-reminder request on the first successful connection, unless disabled/skipped/already requested. The app does not provision or publish agent changes. The live provider may still use its old Mat greeting until this team-owned setup is updated.

Validation: verify the chosen name, audible motivation, no workout mutation, quiet-style brevity, skip/disabled behavior, and reconnect without repeating. A client request marker records requested speech, not proof the user heard it; interrupted speech is not automatically replayed.

## Timer and weight tool update — October 11

Before live testing, replace the published prompt with `agent/prompt.md` and update the existing `submit_workout_action` client tool: include `weight_updated` in its enum and add optional numeric `weight_lb` / `weight_increase_lb` arguments, LLM-supplied, in pounds. Exactly one is used only for weight_updated. Existing target fields and Wait for response remain required as described above. Generated canonical definitions are in `agent/tools.json`; updating local files alone does not publish this provider change.

Acceptance: say “found the machine” from awaiting_equipment; verify one accepted equipment claim, hear “Okay” after success, and see the set timer. Say “set done”; verify it stops and a duration/weight record is saved. With another set remaining at 50 lb and 10 planned reps, verify the conditional 5 lb suggestion; say “yes, increase by 5 lb” and verify 55 lb after one backend acknowledgment, while the previous record remains 50 lb. Repeat must not mutate progress. Ask with unknown weight, stale target, difficult set or pain and verify clarification/rejection/suppression. Live microphone/speech checks remain separate from backend tests.

## English / Spanish trainer language — October 11, 2026

The app saves `preferences.trainer.language` (`en` or `es`, default `en`) in profiles and workout snapshots. The shared web/native connection passes `overrides.agent.language` and a localized `overrides.agent.firstMessage` on every connection. Existing workouts retain their original preference; edits during a workout apply to the next workout. App menus remain English. No new dynamic variables or client tools are needed.

Before live use, the agent owner must enable Spanish as an additional language, choose a speech model/voice supporting English and Spanish, enable **Language** and **First message** overrides in the agent Security settings, and apply `agent/prompt.md`. Both overrides are sent for English too. Overrides are disabled by default at the provider; updating these local files does not activate them. Do not override the system prompt from the client. See [provider override setup](https://elevenlabs.io/docs/eleven-agents/customization/personalization/overrides).

Live acceptance (NOT RUN): select Español, save, reload profile, start workout and connect; hear Spanish from the first greeting, ask for guidance and say “repite” without mutation; say “serie terminada” and verify exactly one accepted completion; test “la máquina está ocupada”, ambiguous “terminé”, end confirmation, rest/watch announcements and reconnect. Check that numbers, pounds, exercise targets and stop conditions retain their meaning. Repeat the English flow to check regression. Dashboard activation and real speech remain unverified.
