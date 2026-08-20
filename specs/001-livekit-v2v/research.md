# Research: LiveKit Voice-to-Voice Agent Testing POC

**Feature**: `001-livekit-v2v`  
**Date**: 2026-08-20

## R1. Realtime transport

**Decision**: Use LiveKit (local Docker server) + LiveKit Agents Python SDK for room join, audio publish/subscribe, VAD, and session I/O.

**Rationale**: Spec and constitution mandate LiveKit for voice-to-voice. The repo already runs `livekit/livekit-server` and an Agents-based worker; replacing transport would add risk without POC value.

**Alternatives considered**:
- Custom WebRTC / websockets — rejected (constitution forbids custom socket hacks for media).
- LiveKit Cloud only — rejected for local POC runbook (Cloud remains optional later).

## R2. Agent orchestration

**Decision**: Introduce LangGraph (with LangChain tools/prompts/models) as the reasoning layer. LiveKit `AgentSession` remains the voice runtime; a thin adapter maps transcripts / tool requests into graph state and maps graph outputs back to spoken replies.

**Rationale**: Constitution requires LangGraph-first orchestration with deterministic state, retries, and failure handling. Current code uses LiveKit Agents `Agent` + `@function_tool` inline; that works for demos but does not satisfy governance for inspectable graph workflows.

**Alternatives considered**:
- Keep LiveKit Agents tools only — rejected (fails LangGraph gate).
- Replace LiveKit Agents entirely with a custom audio loop + LangGraph — rejected (reinvents VAD/STT/TTS room I/O).

## R3. Speech + LLM providers

**Decision**: Keep Speaches (OpenAI-compatible Whisper STT + Kokoro TTS) in Docker; keep OpenAI GPT via API for LLM (`OPENAI_MODEL`, e.g. `gpt-4o-mini`).

**Rationale**: Matches existing stack and README; separates transport from model vendors via adapters.

**Alternatives considered**:
- Ollama local LLM — rejected for this POC (README explicitly uses OpenAI GPT).
- Cloud STT/TTS only — rejected; local Speaches already validates offline-ish speech path.

## R4. Testing UI

**Decision**: Evolve existing Next.js + `@livekit/components-react` app: explicit connect/disconnect, status labels (disconnected/connecting/connected/failed), agent presence, live transcripts for both sides, clear errors, manual reconnect after failure.

**Rationale**: Spec requires a small testing UI with transcripts and fail-fast behavior; starter UI already has welcome/session views and token route.

**Alternatives considered**:
- Build a new minimal UI from scratch — rejected (duplicate work; existing components sufficient).
- Product-style dashboard — rejected (constitution: small UI).

## R5. Failure semantics

**Decision**:
- Mid-call network drop → immediate fail + user-visible error; no silent auto-recover; manual reconnect.
- Agent missing after connect → fail within ~30 seconds.
- Mic denied → clear error; not “connected”.

**Rationale**: Locked by clarification session 2026-08-20; simplifies acceptance tests vs opportunistic reconnect logic.

**Alternatives considered**: Brief auto-recover then fail — rejected by product owner (chose fail-immediate).

## R6. Demo tool

**Decision**: Require at least one voice-invokable demo tool (keep weather lookup as default). Tool lives in a dedicated tools module and is registered into the LangGraph/tool node path; spoken + transcript answers must reflect tool results.

**Rationale**: Clarification made tool use mandatory for acceptance; weather tool already exists in starter agent.

**Alternatives considered**: Conversation-only MVP — rejected by clarification answer A.

## R7. Greeting + barge-in

**Decision**: Keep automatic short greeting on agent ready (`generate_reply` / graph-driven greeting node). Rely on LiveKit Agents VAD + session interruption semantics for barge-in; validate yield ~1s in manual tests.

**Rationale**: Spec FR-013 / SC-005; starter already greets on connect.

**Alternatives considered**: Wait-for-user-first — rejected in clarification.

## R8. Secrets and config

**Decision**: Document only `.env.example` variable names in docs/plans. Runtime continues to load local env files via existing app conventions, but agents/automation MUST NOT open or print secret files unless the user explicitly grants access.

**Rationale**: Constitution Safe Secrets Handling.

**Alternatives considered**: Commit real env files — rejected.

## R9. Documentation / specs index

**Decision**: Maintain `specs/README.md` as the feature index and link it from the root README so operators can find active specs/plans quickly.

**Rationale**: Explicit user request during `/speckit-plan`; supports Spec Kit workflow discoverability.

**Alternatives considered**: Specs only under git without index — rejected (harder navigation).
