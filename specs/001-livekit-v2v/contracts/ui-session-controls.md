# Contract: UI Session Controls

**Feature**: `001-livekit-v2v`  
**Surface**: Small web testing UI

## Required controls

| Control | Behavior |
|---------|----------|
| Connect | Starts token fetch + room join; status → connecting → connected/failed |
| Disconnect / End call | Leaves room; stops mic; status → disconnected; reconnect allowed without app restart |
| Status display | Shows at least: Disconnected, Connecting, Connected, Failed (+ short reason) |
| Transcript panel | Lists live tester and agent text turns in order |
| Mic permission | Browser prompt on connect; denial shows clear error |

## Explicit non-goals (UI)

- No multi-room console, analytics dashboard, or account settings.
- No auto-reconnect after network failure (user must Connect again).
- No requirement for mobile-native chrome.

## Acceptance mapping

| Spec story | UI proof |
|------------|----------|
| P1 conversation | Connect → hear greeting → speak → hear reply → End call |
| P2 lifecycle | Status labels + reconnect without reload |
| P2 transcripts | Both speakers visible during call |
| P2 demo tool | Ask weather (or documented phrase) → spoken + transcript answer |
| P3 barge-in | Speak over agent → audio yields → conversation continues |
