# Quickstart: Demo-Ready Voice Experience

**Feature**: `003-demo-ready-v2v`  
**Purpose**: Operator validation of persona, wait cue, dual reply modes, EOU/pauses, multiturn context, and traces.

## Prerequisites

- Docker Desktop running; `uv` and Node 20+ installed
- `agent/.env.local` configured (see `agent/.env.example`) with LLM credentials
- For `voice_to_voice`: Realtime-capable credentials (OpenAI and/or Azure Realtime as documented in env example after implementation)
- Repo root: `/Users/dharmendrasingh/DTDL_CODEBASE/POC/livekit-v2v-poc`

## Start stack

```bash
cd /Users/dharmendrasingh/DTDL_CODEBASE/POC/livekit-v2v-poc
./start_app.sh
```

Open http://localhost:3000

## Config knobs (names only)

| Variable | Purpose |
|----------|---------|
| `REPLY_MODE` | `standard` \| `voice_to_voice` (env default; UI can override per session) |
| `NEXT_PUBLIC_DEFAULT_REPLY_MODE` | Optional UI default for the home toggle |
| `MIN_ENDPOINTING_DELAY_MS` / `MAX_ENDPOINTING_DELAY_MS` | Pause tolerance before EOU |
| `TRACE_ENABLED` / `TRACE_DIR` | Local JSONL timeline (also LiveKit topic `session.trace`) |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Jaeger OTLP HTTP base (`http://localhost:4318`) |
| `JAEGER_UI_URL` / `NEXT_PUBLIC_JAEGER_UI_URL` | Jaeger UI (`http://localhost:16686`) |
| `REALTIME_MODEL` | OpenAI Realtime model id |
| `REALTIME_AZURE_DEPLOYMENT` | Required for Azure voice-to-voice; if unset, V2V falls back to standard |

Do not commit real secrets.

---

## Scenario A — Persona match (P1)

1. On home, select **male** + language `en`; connect.
2. Hear greeting: male voice presentation; avatar male; English.
3. End call; select **female** + `hi` (or `es`); connect.
4. Confirm voice + avatar + **spoken language** match selection (not English-only with foreign voice id).
5. Check traces: `persona_applied` attrs match UI; `defaults_used` false.

**Pass**: SC-001 style checks; no UI/agent mismatch.

## Scenario B — Wait cue (P1)

1. `REPLY_MODE=standard` (easier to induce think time).
2. Ask a longer question; while thinking, confirm **new** wait sound/visual (not old beep).
3. When agent speaks, cue stops with no overlap.

**Pass**: FR-004–005 / SC-002.

## Scenario C — Standard mode latency + transcript (P1)

1. Set `REPLY_MODE=standard`; restart agent if needed.
2. Status/traces show `standard`.
3. Ask 3 short clear questions; note EOU→first audio (stopwatch or trace timestamps).
4. Confirm side transcript updates without blocking speech.

**Pass**: Median/feel within standard SC-003 band; FR-007/013.

## Scenario D — Voice-to-voice mode (P1)

1. Set `REPLY_MODE=voice_to_voice` (or UI toggle if present); new session.
2. Traces/status show `voice_to_voice`.
3. Short Q&A; confirm faster first audio vs standard (informal compare OK).
4. Confirm transcript still appears (may lag slightly).
5. Multiturn: “My name is Ada.” → later “What is my name?” → agent recalls.

**Pass**: V2V SC-003 band under good network; SC-004 context.

## Scenario E — Pause vs end-of-speech (P1/P2)

1. Speak a sentence with a **brief** mid-thought pause, then continue—agent should wait.
2. Finish a sentence and stay silent—agent should reply after threshold.
3. Optionally lower/raise endpointing delay and re-check.

**Pass**: SC-005 qualitative; events `user_speech_ended` align with intent.

## Scenario F — Traces soft-fail (P2)

1. Run a normal call with traces enabled; locate timeline (`persona_applied`, EOU, reply start/end, `reply_mode`).
2. Simulate sink failure if supported (invalid path); confirm call still works.

**Pass**: FR-011–012 / SC-006 readiness.

---

## Suggested measurement sheet

| Turn | Mode | EOU→audio (ms) | Persona OK? | Context OK? | Notes |
|------|------|----------------|-------------|-------------|-------|
| 1 | | | | | |
| 2 | | | | | |

## Related artifacts

- [spec.md](./spec.md)
- [plan.md](./plan.md)
- [research.md](./research.md)
- [data-model.md](./data-model.md)
- [contracts/](./contracts/)
