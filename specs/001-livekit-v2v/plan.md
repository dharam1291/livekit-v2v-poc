# Implementation Plan: LiveKit Voice-to-Voice Agent Testing POC

**Branch**: `001-livekit-v2v` | **Date**: 2026-08-20 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-livekit-v2v/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Deliver a production-structured local POC where a human tester uses a small web UI to join a LiveKit voice room, converse with an agent (automatic greeting, multi-turn context, barge-in), see live transcripts, exercise one demo tool by voice, and get clear fail-fast errors (network drop, agent missing within ~30s). Technical approach: keep LiveKit as realtime transport (rooms, tracks, Agents SDK session I/O); introduce LangGraph + LangChain for agent reasoning/tools behind a clean adapter boundary; keep Speaches for STT/TTS and OpenAI GPT for LLM; evolve the existing `agent/` + `web/` + Docker stack rather than replacing it.

## Technical Context

**Language/Version**: Python 3.10–3.14 (agent via `uv`); TypeScript / Node 20+ (web via npm/pnpm); Docker for LiveKit + Speaches

**Primary Dependencies**: LiveKit Agents SDK, LiveKit React components, LangGraph, LangChain, OpenAI API (LLM), Speaches OpenAI-compatible STT/TTS, Next.js

**Storage**: N/A for POC (in-session conversation state only; no durable DB)

**Testing**: `pytest` / `pytest-asyncio` for agent/graph units; manual UI validation via quickstart scenarios; optional lightweight web lint

**Target Platform**: Local macOS/Linux developer machine; desktop browser (same host as Docker stack)

**Project Type**: Split app — Python realtime agent worker + Next.js testing UI + Docker infra

**Performance Goals**: First agent greeting audible within 30s after connect on healthy local setup; barge-in yield within ~1s; transcript visible by end of turn

**Constraints**: Constitution v1.1.0 — LiveKit-first voice, LangGraph-first orchestration, no reading `.env`/secrets in agent workflows, human approval before privileged ops, small test-focused UI; fail-fast on network drop (no auto-recover); agent-join timeout ~30s; at least one demo tool required

**Scale/Scope**: Single tester + single agent per session; local POC quality (clear lifecycle/errors), not multi-tenant production SaaS

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Evidence in plan |
|------|--------|------------------|
| I. LiveKit Voice-to-Voice First | PASS | LiveKit rooms + Agents session for audio; STT/TTS/LLM via adapters |
| II. LangGraph Architecture First | PASS | Explicit graph state for turns/tools; LiveKit session delegates reasoning to graph adapter |
| III. Clean Python Design Patterns | PASS | Proposed modules: transport session, graph orchestration, tools, adapters |
| IV. Safe Secrets Handling | PASS | Docs reference `.env.example` / var names only; no secret file reads in automation |
| V. Human-Gated Operations | PASS | Quickstart assumes operator-run commands; agent work asks before privileged access |
| VI. Small UI, Real Workflow Validation | PASS | UI scope = connect/disconnect, status, transcripts, agent presence — no product chrome |

**Post-design re-check**: PASS — contracts and data model keep transport vs orchestration separated; UI contract limited to testing controls.

## Project Structure

### Documentation (this feature)

```text
specs/001-livekit-v2v/
├── plan.md              # This file
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/           # Phase 1
│   ├── session-token-api.md
│   ├── voice-session-events.md
│   └── ui-session-controls.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
livekit-v2v-poc/
├── docker-compose.yml          # LiveKit server + Speaches
├── .env.example                # Documented env var names only
├── README.md                   # Runbook + specs index
├── specs/                      # Spec Kit feature docs (+ README index)
│   └── 001-livekit-v2v/
├── agent/
│   ├── pyproject.toml
│   ├── src/
│   │   ├── agent.py            # LiveKit Agents entrypoint (thin)
│   │   ├── graph/              # LangGraph state, nodes, edges
│   │   ├── tools/              # Demo tools (e.g. weather)
│   │   └── adapters/           # STT/TTS/LLM/LiveKit bridge helpers
│   └── tests/
│       ├── unit/
│       └── integration/
└── web/
    ├── app/                    # Next.js routes + token API
    ├── components/app/         # Welcome + session views
    ├── hooks/                  # Session/status/error helpers
    └── lib/                    # Token/session utilities
```

**Structure Decision**: Keep the existing monorepo layout (`agent/` + `web/` + Docker).

**Current (as of implement)**:
- `agent/src/agent.py` — LiveKit Agents entrypoint
- `agent/src/graph/` — LangGraph state, nodes, prompts, compiled greeting graph
- `agent/src/tools/` — demo weather tool
- `agent/src/adapters/` — config, STT/TTS/LLM factories, LiveKit↔graph bridge
- `web/` — Next.js testing UI (status, fail-fast, transcripts overlay)

Refactor goal remains: thin entrypoint + modular graph/tools/adapters; evolve UI rather than replacing it.

## Complexity Tracking

> No constitution violations requiring justification.
