# Contract: UI Call Stage and Home

**Feature**: `002-ux-general-agent`  
**Surface**: Next.js testing UI (welcome + active session)

## Home (disconnected)

| Element | Behavior |
|---------|----------|
| Creative entry | Brand/product presence + short supporting line (not connect-only chrome) |
| Avatar chooser | Male / female before connect |
| Language chooser | At least `en`; additional langs only if voices available |
| Start / Connect | Starts token fetch + room join with selected persona |
| Previous conversations | List or empty state; select → read-only transcript view |
| Status | Disconnected / Connecting / Failed as today |

## Call stage (connected)

| Region | Behavior |
|--------|----------|
| Main stage | Gendered avatar with idle / thinking / speaking visual states |
| Transcript panel | Dedicated panel separate from stage; right side on desktop-width; ordered user+agent turns |
| Wait feedback | Visible (required) + optional short waiting sound while `thinking` / awaiting reply; stops on agent `speaking` |
| Controls | Mic, End call, status; preserve barge-in / disconnect behavior from 001 |
| Overlay chat | Optional secondary; MUST NOT be the only transcript surface |

## Explicit non-goals

- No multi-user accounts, analytics dashboard, or marketing modules.
- No photoreal lip-sync video avatar.
- No auto-reconnect after network failure (unchanged from 001).

## Acceptance mapping

| Spec story | UI proof |
|------------|----------|
| P1 general answers | Hear non-weather-only greeting; Q&A + refusal (agent-side; UI shows transcript) |
| P1 side transcript | Turns visible in right/dedicated panel during call |
| P2 avatar | Gender choice + speaking animation |
| P2 wait feedback | Filler during thinking |
| P3 home history | List + open prior transcript |
