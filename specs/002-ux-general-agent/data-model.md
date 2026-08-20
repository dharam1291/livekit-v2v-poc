# Data Model: Conversation UX and General Agent Answers

**Feature**: `002-ux-general-agent`  
**Date**: 2026-08-20

## Entities

### VoiceSession (runtime)

In-memory for an active call (UI + agent job).

| Field | Type | Notes |
|-------|------|-------|
| roomName | string | LiveKit room id |
| connectionStatus | enum | `disconnected` \| `connecting` \| `connected` \| `failed` |
| agentState | enum | `listening` \| `thinking` \| `speaking` \| … (as exposed by Agents UI) |
| avatarGender | `male` \| `female` | Chosen before connect |
| sessionLanguage | string | e.g. `en` |
| kokoroVoice | string | Resolved on agent from gender+language |
| liveTurns | TranscriptTurn[] | From LiveKit session messages |

**Transitions**: `disconnected` → `connecting` → `connected` → `disconnected` \| `failed`. Agent speaking/thinking drives avatar + wait feedback only while `connected`.

### TranscriptTurn

| Field | Type | Notes |
|-------|------|-------|
| id | string | Stable client id |
| role | `user` \| `agent` | Tester vs agent |
| text | string | Plain transcript text |
| createdAt | string (ISO-8601) | Ordering / display |

**Validation**: `text` non-empty after trim for persisted turns; ignore empty/noise finals for history.

### ConversationRecord (persisted)

| Field | Type | Notes |
|-------|------|-------|
| id | string | UUID |
| startedAt | string (ISO-8601) | |
| endedAt | string (ISO-8601) | |
| label | string | Short preview (first user or agent line, truncated) |
| avatarGender | `male` \| `female` | Snapshot |
| sessionLanguage | string | Snapshot |
| turns | TranscriptTurn[] | Full transcript for detail view |

**Validation**: Persist only if `turns.length >= 1`. Cap store at 50 records (drop oldest). Corrupt JSON → treat as empty list + surface recoverable UI error for that open attempt.

### AgentAvatar (UI)

| Field | Type | Notes |
|-------|------|-------|
| gender | `male` \| `female` | |
| visualState | `idle` \| `listening` \| `thinking` \| `speaking` | Mapped from agentState |
| assetKey | string | Illustration key per gender |

### WaitFeedback (UI runtime)

| Field | Type | Notes |
|-------|------|-------|
| active | boolean | True while thinking / awaiting first speech of reply |
| mode | `visual` \| `visual+audio` | Audio optional if autoplay allowed |
| startedAt | number | For min-duration / skip-flash logic |

### KnowledgeBoundaryResponse (policy, not stored)

Logical behavior encoded in prompts: when the agent cannot help, spoken text must clearly apologize and state lack of knowledge (or equivalent). Not a separate persisted entity.

### SessionPersonaMetadata (transport)

Passed UI → token API → agent job (see contracts).

| Field | Type | Notes |
|-------|------|-------|
| avatarGender | `male` \| `female` | Required for new sessions |
| sessionLanguage | string | Default `en` |

## Relationships

```text
ConversationRecord 1──* TranscriptTurn
VoiceSession (live) 1──* TranscriptTurn  ──on end──▶ ConversationRecord
VoiceSession ──has──▶ AgentAvatar + WaitFeedback
SessionPersonaMetadata ──configures──▶ VoiceSession.kokoroVoice + prompts language
```

## State notes

- Mid-call gender change (if UI allows): apply to avatar immediately; voice change applies from next agent utterance (agent may ignore mid-utterance swaps).
- History is device-local only; clearing site data clears conversations.
