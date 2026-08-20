# Quickstart: Validate LiveKit V2V POC

**Feature**: `001-livekit-v2v`  
**Date**: 2026-08-20

Use this guide to prove the feature end to end. Prefer documented env **names** from `agent/.env.example` and `web/.env.example`; do not commit secret values.

## Prerequisites

- Docker Desktop running
- `uv` and Node.js 20+ / npm (or pnpm)
- OpenAI API key available to the operator for the agent LLM
- Local ports free: `7880` (LiveKit), `8000` (Speaches), `3000` (web)

## Setup (operator-run)

```bash
cd /Users/dharmendrasingh/DTDL_CODEBASE/POC/livekit-v2v-poc
docker compose up -d
docker compose ps
```

Configure local env files from examples (edit secrets yourself; agents should not open them unless you grant access):

```bash
cp agent/.env.example agent/.env.local
cp web/.env.example web/.env.local
# Set OPENAI_API_KEY in agent/.env.local
```

```bash
# Terminal A
cd agent && uv sync && uv run python src/agent.py dev

# Terminal B
cd web && npm install && npm run dev
```

Open `http://localhost:3000`.

## Validation scenarios

### V1 — Connect, greeting, multi-turn, disconnect (P1)

1. Status shows **Disconnected**.
2. Click **Connect**; grant mic.
3. Within ~30s hear automatic agent greeting; greeting text appears in transcripts.
4. Speak a short follow-up; hear reply; see both transcripts.
5. Ask a context follow-up; reply reflects prior turn.
6. **End call** → **Disconnected**; mic stops.
7. Connect again without restarting the browser app.

**Pass**: SC-001, SC-002, SC-003 core path.

### V2 — Failures (P2)

1. Deny mic (or revoke) → clear error; not stuck “Connected”.
2. Stop agent process, Connect → within ~30s clear failure (agent missing).
3. With a live call, simulate network drop (offline / kill LiveKit briefly) → UI should move through reconnect then fail with a clear message and **no silent recover**; manual Connect works after stack is back.

**Pass**: SC-004, SC-008, SC-009.

> Note: Mid-call drop is treated as fail-fast after reconnect attempts surface a disconnect (see `voice-session-events.md`). User-initiated End call must return to Disconnected without a false network-failure banner.

### V3 — Transcripts (P2)

1. During a healthy call, confirm tester and agent lines appear by end of each turn.

**Pass**: SC-007.

### V4 — Demo tool (P2)

1. Ask a clear weather question for a city (or the documented trigger phrase).
2. Hear spoken answer reflecting tool result; see matching transcript.

**Pass**: SC-010 / FR-017.

### V5 — Barge-in (P3)

1. Prompt a longer agent reply; speak over it.
2. Agent audio yields within ~1s; conversation continues.

**Pass**: SC-005.

## Related artifacts

- Spec: [spec.md](./spec.md)
- Data model: [data-model.md](./data-model.md)
- Contracts: [contracts/](./contracts/)
- Research: [research.md](./research.md)
