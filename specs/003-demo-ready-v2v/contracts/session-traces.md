# Contract: Session Traces

**Feature**: `003-demo-ready-v2v`  
**Surface**: Agent trace emitter → local sink; optional UI timeline

## Purpose

Give operators a turn-ordered timeline to diagnose persona mismatches, premature EOU, and reply-path latency within ~2 minutes (SC-006).

## Event schema

```json
{
  "session_id": "room-or-job-id",
  "ts": "2026-09-09T08:30:00.123Z",
  "event": "persona_applied",
  "turn_index": null,
  "attrs": {
    "avatar_gender": "male",
    "session_language": "en",
    "voice_id": "am_adam",
    "defaults_used": false,
    "reply_mode": "standard"
  }
}
```

## Required events

| Event | When |
|-------|------|
| `session_start` | Agent session started |
| `persona_applied` | After persona resolution |
| `reply_mode_selected` | After mode resolution |
| `user_speech_ended` | EOU committed |
| `agent_reply_started` | First agent audio (or realtime response audio start) |
| `agent_reply_ended` | Agent finished speaking turn |
| `session_end` | Disconnect / job end |

## Recommended events

| Event | Mode |
|-------|------|
| `stt_done` | standard |
| `llm_first_token` | standard |
| `tts_first_audio` | standard |
| `realtime_response_started` | voice_to_voice |
| `wait_feedback_shown` | UI (optional) |
| `trace_sink_error` | any (soft fail) |

## Sink behavior

- **Primary**: OpenTelemetry spans exported over OTLP HTTP to **Jaeger** (`docker compose` service `jaeger`, UI `http://localhost:16686`).
- Also: JSON lines to a local traces path and/or structured logger.
- Also: LiveKit data topic `session.trace` for the in-app timeline panel.
- On sink/Jaeger failure: continue call; record `trace_sink_error` / disable Jaeger export for the session if possible (FR-012).
- Never log API keys or raw `.env` contents.

## Operator view

- **Jaeger UI**: open `http://localhost:16686`, select service `v2v-poc-agent` (or `AGENT_NAME`), inspect `voice.*` spans (`session.id`, persona, reply mode, turn index).
- In-app panel: chronological live events for the current call, with a link to Jaeger.
- Optional: inspect JSONL under `TRACE_DIR` and compute `latency_ms = agent_reply_started - user_speech_ended` per turn.

## Acceptance mapping

| Spec | Proof |
|------|-------|
| FR-011–012 | Timeline visible; call survives sink failure |
| SC-006 | Injected faults (wrong persona meta, long STT, short EOU) identifiable from events |
