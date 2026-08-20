# Contract: Conversation History Storage

**Feature**: `002-ux-general-agent`  
**Surface**: Browser localStorage (tester device)

## Purpose

Persist completed call transcripts so the home page can list and reopen previous conversations.

## Storage key

`livekit-v2v-poc:conversations` (single JSON document)

## Document schema

```json
{
  "version": 1,
  "conversations": [
    {
      "id": "uuid",
      "startedAt": "2026-08-20T12:00:00.000Z",
      "endedAt": "2026-08-20T12:05:00.000Z",
      "label": "What's the weather in Paris?",
      "avatarGender": "female",
      "sessionLanguage": "en",
      "turns": [
        { "id": "t1", "role": "agent", "text": "Hi…", "createdAt": "…" },
        { "id": "t2", "role": "user", "text": "…", "createdAt": "…" }
      ]
    }
  ]
}
```

## Operations

| Op | Behavior |
|----|----------|
| List | Return conversations newest-first |
| Get by id | Return one record or not-found |
| Upsert on call end | If `turns.length >= 1`, insert/update; enforce max 50 |
| Clear (optional) | Not required for v1 UI |

## Failure handling

- Quota / write failure: keep the live call usable; show a non-blocking toast/banner that history was not saved.
- Parse failure on read: treat as empty list; do not crash home.
- Missing conversation on open: show clear error; home remains usable.

## Non-goals

- No server sync, encryption-at-rest beyond browser defaults, or multi-tab merge protocol (last write wins is acceptable).

## Acceptance mapping

| Spec | Proof |
|------|-------|
| FR-013–FR-015 | End call with turns → appears on home → open transcript |
| SC-006 | Open prior transcript in under 30s |
