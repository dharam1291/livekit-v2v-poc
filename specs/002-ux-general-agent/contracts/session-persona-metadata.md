# Contract: Session Persona Metadata

**Feature**: `002-ux-general-agent`  
**Surface**: UI → `POST /api/token` → LiveKit agent dispatch → agent TTS voice

## Purpose

Carry avatar gender and session language from the tester UI into the agent job so the greeting and subsequent speech use the correct Kokoro voice.

## Request (token API extension)

`POST /api/token` body MAY include (alongside any existing `room_config`):

```json
{
  "persona": {
    "avatarGender": "female",
    "sessionLanguage": "en"
  }
}
```

| Field | Required | Values | Default |
|-------|----------|--------|---------|
| `persona.avatarGender` | recommended | `male` \| `female` | `female` |
| `persona.sessionLanguage` | optional | language code string | `en` |

Invalid gender → `400` with clear error, or coerce to default `female` (implementation MUST pick one and document it; prefer coerce for POC resilience).

## Agent job metadata

Token route MUST attach persona fields to agent dispatch metadata (or equivalent LiveKit job metadata) so the worker can read them at session start without a second HTTP call.

Suggested metadata keys:

| Key | Example |
|-----|---------|
| `avatar_gender` | `male` |
| `session_language` | `en` |

## Agent behavior

1. Read metadata at job/session start.
2. Resolve Kokoro voice via voice map (see research R3).
3. Configure TTS before `generate_reply` greeting.
4. If metadata missing, use defaults (`female` + `en` → current `af_heart` path).

## Non-goals

- No authenticated user profiles.
- No persistence of persona on the server.
- Changing voice mid-utterance is not required.

## Acceptance mapping

| Spec | Proof |
|------|-------|
| FR-007, FR-009 | Male vs female connect → audible voice differs; matches selection |
| SC-004 related | Avatar gender choice applied for session |
