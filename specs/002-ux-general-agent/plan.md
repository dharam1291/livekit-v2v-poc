# Implementation Plan: Conversation UX and General Agent Answers

**Branch**: `002-ux-general-agent` | **Date**: 2026-08-20 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-ux-general-agent/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Extend the existing LiveKit voice POC so testers get a clearer call stage (right-side live transcript, gendered speaking avatar, wait fillers while the agent thinks), a creative home with device-local previous conversations, and an agent that answers general questions instead of advertising weather-only—refusing clearly when it cannot help while keeping the weather demo tool. Approach: evolve `web/` session layout and localStorage history; pass avatar gender (+ session language) into the agent job via token/dispatch metadata; select Kokoro TTS voice by gender/language; update LangGraph/LiveKit assistant prompts for general answers + knowledge-boundary refusals.

## Technical Context

**Language/Version**: Python 3.10–3.14 (agent via `uv`); TypeScript / Node 20+ (Next.js web); Docker for LiveKit + Speaches

**Primary Dependencies**: LiveKit Agents SDK, LiveKit React components / Agents UI blocks, LangGraph, LangChain, OpenAI/Azure LLM, Speaches (Whisper STT + Kokoro TTS), Next.js App Router

**Storage**: Browser `localStorage` for conversation history on the tester device; in-session LiveKit transcription streams for live turns (no server DB)

**Testing**: `pytest` for prompt/voice-mapping/agent behavior; manual UI validation via [quickstart.md](./quickstart.md); existing agent unit tests extended

**Target Platform**: Local macOS/Linux developer machine; desktop browser (primary layout target)

**Project Type**: Split app — Python realtime agent worker + Next.js testing UI + Docker infra (existing monorepo)

**Performance Goals**: Wait feedback perceptible when reply start > ~1.5s; avatar speaking state within ~1s of agent speech; greeting still within existing ~30s agent-join budget

**Constraints**: Constitution v1.1.0 (LiveKit-first, LangGraph-first, safe secrets, human-gated ops, validation-focused UI); no cross-device account sync; no photoreal lip-sync; keep connect/disconnect/barge-in/weather tool working

**Scale/Scope**: Single tester + single agent per session; UI additions limited to home + call-stage UX and local history; one existing demo tool retained

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Evidence in plan |
|------|--------|------------------|
| I. LiveKit Voice-to-Voice First | PASS | Audio remains LiveKit rooms + Agents session; avatar/fillers/transcript are UI/session metadata, not custom sockets |
| II. LangGraph Architecture First | PASS | Prompt/policy and session persona (gender/language) flow through graph/adapter state; no ad hoc reply orchestration outside existing bridge |
| III. Clean Python Design Patterns | PASS | Voice selection + prompt updates in adapters/graph modules; tools stay isolated |
| IV. Safe Secrets Handling | PASS | Docs/contracts use env var names only; no `.env` reads in automation |
| V. Human-Gated Operations | PASS | Quickstart is operator-run; no privileged path automation |
| VI. Small UI, Real Workflow Validation | PASS (scoped expansion) | Creative home, avatar, fillers, and history stay tied to validating call flow, diagnostics, and repeat testing (see Complexity Tracking) |

**Post-design re-check**: PASS — contracts keep transport (LiveKit) vs orchestration (prompts/tools/voice map) vs UI (layout/history) separated; no new backend DB or product shell.

## Project Structure

### Documentation (this feature)

```text
specs/002-ux-general-agent/
├── plan.md              # This file
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/           # Phase 1
│   ├── session-persona-metadata.md
│   ├── conversation-history-storage.md
│   └── ui-call-stage.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
livekit-v2v-poc/
├── docker-compose.yml
├── README.md
├── specs/002-ux-general-agent/
├── agent/
│   ├── src/
│   │   ├── agent.py                 # Entrypoint; read job/session metadata → voice
│   │   ├── graph/
│   │   │   ├── prompts.py           # General-answer + refusal + non-weather-only greeting
│   │   │   ├── state.py             # Optional persona fields (gender, language, voice)
│   │   │   └── ...
│   │   ├── adapters/
│   │   │   ├── config.py
│   │   │   ├── speech_llm.py        # TTS voice selection
│   │   │   ├── voice_map.py         # NEW: gender+language → Kokoro voice id
│   │   │   └── livekit_bridge.py
│   │   └── tools/weather.py         # Keep demo tool
│   └── tests/
└── web/
    ├── app/
    │   ├── page.tsx
    │   └── api/token/route.ts       # Accept persona metadata for agent dispatch
    ├── components/app/
    │   ├── welcome-view.tsx         # Creative home + history list
    │   ├── conversation-history.*   # NEW: list + detail drawer/modal
    │   ├── transcript-panel.tsx     # Wire/reuse for side panel
    │   └── view-controller.tsx
    ├── components/agents-ui/blocks/agent-session-view-01/
    │   └── ...                      # Call stage: avatar tile + right transcript + fillers
    └── lib/
        ├── transcript.ts            # Extend for persistence shapes
        └── conversation-store.ts    # NEW: localStorage CRUD
```

**Structure Decision**: Keep the existing `agent/` + `web/` + Docker monorepo. Extend prompts, TTS voice mapping, token metadata, and call/home UI; do not add a new service or database.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| UI beyond minimal connect chrome (creative home, avatar, history, fillers) | Spec FR-007–FR-015; improves diagnosability and demo clarity for the same voice workflow | Bare connect + overlay chat only — fails side transcript, speaking avatar, wait feedback, and prior-conversation review |
