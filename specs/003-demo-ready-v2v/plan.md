# Implementation Plan: Demo-Ready Voice Experience

**Branch**: `003-demo-ready-v2v` | **Date**: 2026-09-09 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-demo-ready-v2v/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Make the existing LiveKit voice POC demo-ready by (1) fixing persona delivery so avatar gender and language actually drive spoken behavior (not UI-only / voice-id-only), (2) replacing the unsatisfactory wait cue, (3) adding a **feature-flag dual reply mode**—**standard** (improved Speaches STT → chat LLM → Kokoro TTS with transcript off the spoken critical path) and **low-latency voice-to-voice** (LiveKit Agents + OpenAI/Azure Realtime speech path with parallel transcript), (4) enabling operator-visible session traces (persona, mode, EOU, stage timings), and (5) documenting/tuning end-of-utterance pause behavior while keeping multiturn session context in both modes. LangGraph remains the session supervisor (persona, mode, prompts/policy, inspectable state); realtime speech is an adapter, not a bypass of orchestration boundaries.

## Technical Context

**Language/Version**: Python 3.10–3.14 (agent via `uv`); TypeScript / Node 20+ (Next.js web); Docker for LiveKit + Speaches

**Primary Dependencies**: LiveKit Agents SDK, LiveKit React / Agents UI, LangGraph, LangChain, OpenAI/Azure chat LLM, LiveKit OpenAI Realtime plugin (`openai.realtime.RealtimeModel`) for V2V mode, Speaches (Whisper STT + Kokoro TTS) for standard mode + parallel transcript, Silero VAD, Next.js App Router

**Storage**: Browser `localStorage` for conversation history (unchanged); in-session LiveKit messages for live transcript; new session trace sink as local JSONL / in-memory timeline exposed to operator (no production DB)

**Testing**: `pytest` for persona/voice map/language instructions/mode factory/EOU config; manual dual-mode + latency validation via [quickstart.md](./quickstart.md); lightweight trace fixture checks

**Target Platform**: Local macOS/Linux developer machine; desktop browser (primary demo target)

**Project Type**: Split app — Python realtime agent worker + Next.js testing UI + Docker infra (existing monorepo)

**Performance Goals**: Per [spec.md](./spec.md) SC-003 — V2V mode median ≤2.5s EOU→first agent audio (90% ≤4s); standard mode median ≤4s (90% ≤6s) under normal local demo conditions

**Constraints**: Constitution v1.1.0 (LiveKit-first transport, LangGraph-first orchestration boundaries, safe secrets, human-gated ops, small validation UI); reply mode fixed at session start; no mid-call mode switch; secrets via env templates only; wait cue must not overlap agent speech

**Scale/Scope**: Single tester + single agent per session; dual reply modes behind `REPLY_MODE` (env + optional UI/token metadata); shared persona, wait feedback, EOU, multiturn context, and traces; no new product surfaces beyond call-stage status/trace visibility

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Evidence in plan |
|------|--------|------------------|
| I. LiveKit Voice-to-Voice First | PASS | Both modes stay in LiveKit rooms + `AgentSession`; media via WebRTC join/publish/subscribe; Realtime and Speaches are speech adapters, not custom sockets |
| II. LangGraph Architecture First | PASS (with justified adapter) | Session persona, reply mode, language policy, greeting/refusal policy, and inspectable state remain LangGraph/adapter-owned; V2V uses Realtime as speech I/O adapter under the same session supervisor (see Complexity Tracking) |
| III. Clean Python Design Patterns | PASS | Mode factory, persona resolver, EOU config, trace emitter, and speech adapters in distinct modules; UI wait/trace viewers thin |
| IV. Safe Secrets Handling | PASS | Docs/contracts use env var names only; no automation reading `.env` secrets |
| V. Human-Gated Operations | PASS | Quickstart is operator-run; mode/trace toggles are explicit config |
| VI. Small UI, Real Workflow Validation | PASS | UI changes limited to wait cue, mode visibility, persona correctness, and optional trace panel—tied to demo validation |

**Post-design re-check**: PASS — contracts separate transport (LiveKit), reply-mode adapters (standard vs realtime), persona/EOU/trace schemas, and thin UI surfaces; LangGraph remains supervisor for policy/state even when Realtime owns low-level speech tokens.

## Project Structure

### Documentation (this feature)

```text
specs/003-demo-ready-v2v/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── session-persona-and-mode.md
│   ├── reply-modes.md
│   ├── session-traces.md
│   └── wait-feedback.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
livekit-v2v-poc/
├── docker-compose.yml
├── README.md
├── agent/
│   ├── .env.example                 # REPLY_MODE, EOU knobs, TRACE_*, realtime model vars
│   ├── src/
│   │   ├── agent.py                 # Mode factory; persona+mode from job metadata; EOU; traces
│   │   ├── graph/
│   │   │   ├── prompts.py           # Language-aware system + greeting instructions
│   │   │   ├── state.py             # Persona, reply_mode, applied voice, defaults_used
│   │   │   └── ...
│   │   ├── adapters/
│   │   │   ├── config.py            # REPLY_MODE, endpointing, tracing flags
│   │   │   ├── speech_llm.py        # Standard STT/LLM/TTS builders
│   │   │   ├── realtime_speech.py   # NEW: RealtimeModel session builder (V2V mode)
│   │   │   ├── voice_map.py         # Kokoro map (standard) + realtime voice map (V2V)
│   │   │   ├── persona.py           # NEW: resolve + ack applied persona (fail-visible defaults)
│   │   │   ├── eou.py               # NEW: endpointing / pause tolerance config
│   │   │   ├── tracing.py           # NEW: session timeline events → sink
│   │   │   └── livekit_bridge.py    # Assistant + tools; language-aware instructions
│   │   └── tools/weather.py
│   └── tests/
└── web/
    ├── public/                      # NEW: wait-cue audio asset (replace oscillator)
    ├── app/api/token/route.ts       # Persona + reply_mode in agent dispatch metadata
    ├── components/app/
    │   ├── welcome-view.tsx         # Optional mode chooser (or env-driven)
    │   ├── wait-feedback.tsx        # New asset + stop-on-speaking
    │   ├── agent-avatar.tsx
    │   └── session-trace-panel.tsx  # NEW (optional): operator timeline view
    └── lib/
        ├── session-persona.ts       # Extend with replyMode
        ├── wait-sound.ts            # Asset-backed cue
        └── session-traces.ts        # NEW: consume/display trace events if exposed to UI
```

**Structure Decision**: Evolve the existing `agent/` + `web/` split. Add adapters for realtime speech, persona ack, EOU, and tracing rather than a new service. Speaches remains for standard mode and as the parallel transcript STT path in V2V mode where needed.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| V2V mode uses OpenAI/Azure Realtime speech path instead of LangGraph-per-token orchestration | Spec requires dual-mode low-latency demos (SC-003); Realtime is the supported LiveKit Agents pattern for native speech-to-speech | Keeping only Speaches STT→chat→TTS cannot reliably hit V2V latency targets; graph-on-every-audio-frame would add latency and fight the Realtime SDK |
| Dual reply-mode factories in one agent worker | Feature flag dual-mode is an explicit product decision | Two separate agent processes doubles ops burden for a local POC and fragments persona/trace code |
| Optional operator trace UI | FR-011/SC-006 need diagnosability for demos | Logs-only is insufficient for “identify persona vs EOU vs latency in 2 minutes” without structured timeline |
