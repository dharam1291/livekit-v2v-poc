# Contract: Session Persona and Reply Mode Metadata

**Feature**: `003-demo-ready-v2v`  
**Surface**: UI → `POST /api/token` → LiveKit agent dispatch metadata → agent session  
**Extends**: `specs/002-ux-general-agent/contracts/session-persona-metadata.md`

## Purpose

Deliver avatar gender, session language, and reply mode to the agent so spoken behavior and traces match the operator’s selection.

## Request (token API)

```json
{
  "persona": {
    "avatarGender": "female",
    "sessionLanguage": "en"
  },
  "replyMode": "standard"
}
```

| Field | Required | Values | Default |
|-------|----------|--------|---------|
| `persona.avatarGender` | recommended | `male` \| `female` | `female` |
| `persona.sessionLanguage` | recommended | `en` \| `hi` \| `es` | `en` |
| `replyMode` | optional | `standard` \| `voice_to_voice` | env `REPLY_MODE` or `standard` |

## Agent job metadata keys

| Key | Example |
|-----|---------|
| `avatar_gender` | `male` |
| `session_language` | `hi` |
| `reply_mode` | `voice_to_voice` |

## Agent behavior

1. Resolve persona + mode at job start (metadata overrides env for mode when present).
2. Apply language to system/greeting instructions (“respond in {language}”).
3. Select voice: Kokoro map for `standard`; Realtime voice map for `voice_to_voice`.
4. Apply STT language hint in `standard` when Speaches/Whisper supports it.
5. Emit `persona_applied` and `reply_mode_selected` trace events with `defaults_used` if coercion occurred.
6. Do not change `reply_mode` mid-session.

## Fail-visible defaults

| Missing/invalid | Behavior |
|-----------------|----------|
| gender | `female`, `defaults_used=true` |
| language | `en`, `defaults_used=true` |
| reply mode | `standard`, warn in traces |

## Acceptance mapping

| Spec | Proof |
|------|-------|
| FR-001–003 | Male/female + language match UI and speech |
| FR-006, FR-008 | Mode from flag/metadata visible in status/traces |
| SC-001 | Persona matrix |
