# Quickstart: Validate Conversation UX and General Agent Answers

**Feature**: `002-ux-general-agent`  
**Date**: 2026-08-20

## Prerequisites

- Docker Desktop running
- `uv` and Node 20+ installed
- LLM configured in `agent/.env.local` (see root README; do not commit secrets)
- Stack startable via `./start_app.sh`

## Setup

```bash
cd /Users/dharmendrasingh/DTDL_CODEBASE/POC/livekit-v2v-poc
./start_app.sh
```

Open **http://localhost:3000**

## Validation scenarios

### 1. General answers and clear refusal (P1)

1. On home, pick an avatar (and language if desired) and Connect.
2. Hear the greeting — it must **not** claim weather-only capability.
3. Ask a general question (e.g. “What is the capital of France?”) → relevant spoken + transcript answer.
4. Ask something the agent should refuse (e.g. detailed medical dosing advice, or nonsense the policy refuses) → clear spoken “can’t answer / no knowledge” style reply.
5. Ask weather for a city → still uses the weather tool and answers.

**Pass**: SC-001/SC-002 style behavior observable; FR-001–FR-004.

### 2. Side transcript panel (P1)

1. During the same call, confirm turns appear in a **dedicated** transcript panel (right on desktop), not only a hidden overlay.
2. Complete 2+ turns; panel stays ordered and scrollable.

**Pass**: FR-005, FR-006, SC-003.

### 3. Avatar gender and speaking state (P2)

1. End call. Choose the **other** gender. Connect again.
2. Confirm avatar art matches gender and animates while the agent speaks; idle/listening when not.
3. Confirm voice presentation differs appropriately for male vs female (English session).

**Pass**: FR-007–FR-009, SC-004.

### 4. Wait feedback (P2)

1. Ask a longer question so the agent takes >1.5s before speaking.
2. Confirm visual filler (and optional waiting sound) during thinking.
3. Confirm filler stops when the agent starts speaking.

**Pass**: FR-010, FR-011, SC-005.

### 5. Home history (P3)

1. End a call that had at least one transcript turn.
2. On home, see the conversation listed.
3. Open it and verify the prior transcript.
4. With cleared site data / fresh profile, confirm empty state does not block Connect.

**Pass**: FR-012–FR-015, SC-006.

## Agent unit checks (optional but recommended)

```bash
cd agent
uv run pytest
```

After implementation, prefer tests covering prompt policy (no weather-only greeting text; refusal language) and `voice_map` gender/language → voice id.

## Related artifacts

- [spec.md](./spec.md)
- [data-model.md](./data-model.md)
- [contracts/session-persona-metadata.md](./contracts/session-persona-metadata.md)
- [contracts/conversation-history-storage.md](./contracts/conversation-history-storage.md)
- [contracts/ui-call-stage.md](./contracts/ui-call-stage.md)
