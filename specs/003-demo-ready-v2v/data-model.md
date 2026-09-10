# Data Model: Demo-Ready Voice Experience

**Feature**: `003-demo-ready-v2v`  
**Date**: 2026-09-09

## Entities

### VoiceSession

One LiveKit room call between tester and agent.

| Field | Type | Notes |
|-------|------|-------|
| `room_name` | string | LiveKit room id |
| `started_at` / `ended_at` | datetime | Session bounds |
| `reply_mode` | enum | `standard` \| `voice_to_voice` — fixed at start |
| `persona` | PersonaSelection | Applied (possibly defaulted) persona |
| `trace_id` / `session_id` | string | Correlates timeline events |

**Relationships**: has many `ConversationTurn`; has many `TraceEvent`; has one `WaitFeedback` policy for the UI.

### PersonaSelection

| Field | Type | Allowed | Default |
|-------|------|---------|---------|
| `avatar_gender` | enum | `male` \| `female` | `female` |
| `session_language` | string | `en` \| `hi` \| `es` (existing UI set) | `en` |
| `applied_voice_id` | string | Kokoro id (standard) or Realtime voice id (V2V) | from map |
| `defaults_used` | boolean | true if metadata missing/invalid | false |

**Validation**:
- Invalid gender → coerce to `female` and set `defaults_used=true` (or reject at token API—prefer coerce for POC resilience; record in traces).
- Unsupported language → coerce to `en` + `defaults_used=true`.
- UI-displayed persona MUST equal applied persona unless `defaults_used` is surfaced to the operator.

### ReplyModeFlag

| Field | Type | Notes |
|-------|------|-------|
| `source` | enum | `env` \| `token_metadata` \| `ui` |
| `value` | enum | `standard` \| `voice_to_voice` |
| `resolved_at` | datetime | Job/session start |

**Validation**: Unknown value → `standard` + warn in traces. Immutable after `session_start`.

### ConversationTurn

| Field | Type | Notes |
|-------|------|-------|
| `turn_index` | int | 0-based order |
| `user_text` | string \| null | May lag in V2V if transcript is parallel |
| `agent_text` | string \| null | From chat/realtime text channel when available |
| `user_speech_ended_at` | datetime | EOU commit |
| `agent_reply_started_at` | datetime | First agent audio |
| `agent_reply_ended_at` | datetime \| null | |
| `latency_ms` | int \| null | `agent_reply_started_at - user_speech_ended_at` |

**Relationships**: belongs to `VoiceSession`; prior turns form multiturn context for the agent.

### EndOfUtteranceDecision

| Field | Type | Notes |
|-------|------|-------|
| `min_endpointing_delay_ms` | int | Configured pause tolerance |
| `committed_at` | datetime | When silence threshold crossed |
| `interrupted` | boolean | Barge-in path |

**State transitions (user speech)**:
`idle` → `speaking` → (`paused_brief` → `speaking`)* → `ended` (EOU) → agent reply cycle

Brief pauses below threshold stay in `speaking`/`paused_brief` without committing.

### WaitFeedback

UI-only entity (not persisted server-side).

| Field | Type | Notes |
|-------|------|-------|
| `visual_active` | boolean | Required while thinking |
| `audio_active` | boolean | Asset playback |
| `asset_path` | string | e.g. `/wait-cue.mp3` |
| `start_delay_ms` | int | Default ~450 |

**Transitions**: inactive → (delay) → active while agent thinking → inactive on agent speaking or disconnect.

### TraceEvent (Session Trace)

| Field | Type | Notes |
|-------|------|-------|
| `session_id` | string | |
| `ts` | datetime | |
| `event` | string | See contracts/session-traces.md |
| `turn_index` | int \| null | |
| `attrs` | object | persona, mode, timings, defaults_used, errors |

**Validation**: Missing sink MUST NOT fail the call; emit best-effort.

## State overview

```text
Connect → resolve ReplyMode + Persona → session_start (trace)
  → greeting
  → loop:
       user speaking / brief pause
       → EOU commit (trace)
       → wait feedback (UI)
       → agent reply start (trace) … end (trace)
  → disconnect → session_end (trace)
```

## Persistence

| Data | Where |
|------|--------|
| Live transcript / history | Existing UI message stream + `localStorage` (002) |
| Applied persona / mode | In-memory agent session state + traces |
| Trace timeline | Local JSONL / logs; optional UI view |
| Secrets | Env only — never in traces payloads |
