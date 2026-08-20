# Contract: Session Token API

**Feature**: `001-livekit-v2v`  
**Consumer**: Web UI  
**Provider**: Next.js `app/api/token` (or equivalent)

## Purpose

Issue short-lived LiveKit connection details so the tester can join a room without embedding API secrets in the browser.

## Request

- **Method**: `GET` or `POST` (keep existing project convention)
- **Auth**: Local POC — no end-user login (developer/local access)
- **Body/Query**: optional room name override; otherwise server generates

## Success response (shape)

```json
{
  "serverUrl": "ws://localhost:7880",
  "participantToken": "<jwt>",
  "roomName": "<room>",
  "participantName": "<identity>"
}
```

## Error response (shape)

```json
{
  "error": "<user-safe message>"
}
```

- HTTP 4xx/5xx when LiveKit credentials/config missing or token mint fails.
- UI MUST map this to session status `failed` with visible message.

## Notes

- Documented env var names only: `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, `AGENT_NAME`.
- Do not return API secrets to the client.
