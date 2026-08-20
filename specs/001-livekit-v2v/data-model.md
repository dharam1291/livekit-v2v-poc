# Data Model: LiveKit Voice-to-Voice Agent Testing POC

**Feature**: `001-livekit-v2v`  
**Date**: 2026-08-20

In-session concepts only. No durable database for this POC.

## Entities

### Voice Session

| Field | Type | Notes |
|-------|------|-------|
| session_id | string | Client/logical id for the call attempt |
| room_name | string | LiveKit room name |
| status | enum | `disconnected` \| `connecting` \| `connected` \| `failed` |
| failure_reason | string? | User-visible when `failed` |
| connected_at | datetime? | Set on successful connect |
| ended_at | datetime? | Set on disconnect/fail |
| agent_present | boolean | True when agent participant is detected |
| agent_join_deadline_sec | number | Default ~30 |

**Transitions**:
```text
disconnected → connecting → connected → disconnected
connecting → failed → disconnected (after user dismiss / reset)
connected → failed → disconnected (network drop, agent leave)
```

**Rules**:
- Mic denial MUST NOT leave status as `connected`.
- Network drop MUST move to `failed` immediately (no auto-recover).
- If `agent_present` remains false for ~30s after connect, MUST `failed`.

### Human Tester

| Field | Type | Notes |
|-------|------|-------|
| participant_identity | string | LiveKit participant identity |
| mic_permission | enum | `unknown` \| `granted` \| `denied` |

### Agent Participant

| Field | Type | Notes |
|-------|------|-------|
| agent_name | string | Dispatch name (e.g. `v2v-poc-agent`) |
| ready | boolean | Session started + greeting eligible |

### Conversation Turn

| Field | Type | Notes |
|-------|------|-------|
| turn_id | string | Unique within session |
| speaker | enum | `tester` \| `agent` |
| text | string | Transcript text |
| audio_complete | boolean | True when speech finished |
| interrupted | boolean | True if barge-in cut agent speech |
| tool_name | string? | Set when turn used a demo tool |
| tool_ok | boolean? | Tool success/failure |

### Transcript Entry

| Field | Type | Notes |
|-------|------|-------|
| entry_id | string | UI list key |
| turn_id | string | FK to Conversation Turn |
| speaker | enum | `tester` \| `agent` |
| text | string | Display text |
| created_at | datetime | Ordering |

### Demo Tool Invocation

| Field | Type | Notes |
|-------|------|-------|
| tool_name | string | e.g. `lookup_weather` |
| args | object | Tool arguments |
| result_summary | string | Spoken/transcript-friendly result |
| success | boolean | |

### LangGraph Session State (orchestration)

| Field | Type | Notes |
|-------|------|-------|
| messages | list | Multi-turn context for the call |
| last_user_text | string? | Latest recognized utterance |
| pending_tool | object? | Tool call in flight |
| last_agent_text | string? | Latest agent reply text |
| should_greet | boolean | True until greeting emitted |
| ended | boolean | Terminal flag |

## Relationships

```text
Voice Session 1──* Conversation Turn
Conversation Turn 1──1 Transcript Entry (when text available)
Conversation Turn 0──1 Demo Tool Invocation
Voice Session 1──1 LangGraph Session State (in-memory for call)
Voice Session 1──1 Human Tester
Voice Session 0──1 Agent Participant
```

## Validation rules (from spec)

- Multi-turn context retained for the lifetime of one Voice Session only.
- Greeting turn is an agent turn created without a prior tester utterance.
- Tool-backed replies MUST set `tool_name` and reflect `result_summary` in agent text.
- Idle silence does not end the session; only tester disconnect or failure does.
