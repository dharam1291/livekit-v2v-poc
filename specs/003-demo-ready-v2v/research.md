# Research: Demo-Ready Voice Experience

**Feature**: `003-demo-ready-v2v`  
**Date**: 2026-09-09

## R1 — Persona delivery and language application

**Decision**: Keep UI → `POST /api/token` → agent job metadata (`avatar_gender`, `session_language`) as the delivery path. Extend agent behavior so language affects **instructions + greeting + STT language hint (when supported) + TTS voice**, not only Kokoro voice id. Emit an **applied-persona ack** into session state and traces (`gender`, `language`, `voice_id`, `defaults_used`). If metadata is missing/invalid, coerce to documented defaults (`female` / `en`) and mark `defaults_used=true` (visible)—never silently mismatch UI without a recorded default.

**Rationale**: Current code already maps gender+language to Kokoro voices in `voice_map.py`, but prompts/greeting stay English and STT has no language hint—so Hindi/Spanish selection feels broken. Spec FR-001–003 require UI and spoken agent to match.

**Alternatives considered**:
- Participant attributes instead of job metadata — redundant with working dispatch path; keep metadata, optionally mirror attributes later.
- Separate HTTP “persona config” call — violates LiveKit-first join flow and adds race conditions.

## R2 — Wait feedback asset

**Decision**: Replace the Web Audio 392 Hz oscillator in `web/lib/wait-sound.ts` with a short, soft looped audio asset under `web/public/` (e.g. gentle ambient loop ≤2s, low volume). Keep ~450ms delay before start, stop immediately on agent `speaking`, and keep visual filler as required fallback.

**Rationale**: Spec FR-004/SC-002 call out the current cue as unsatisfactory; a file asset is easier to swap for demos than tuning oscillator parameters.

**Alternatives considered**:
- Server-side hold music via agent TTS — couples wait cue to agent audio path and risks overlap with reply.
- Silence + visual only — fails demo “something is happening” expectation when audio is expected.

## R3 — Dual reply modes and feature flag

**Decision**: Introduce `REPLY_MODE=standard|voice_to_voice` (env default `standard`). Optionally allow UI/token metadata `reply_mode` to override for a session. Mode is resolved once at job start and fixed for the session. Surface active mode in UI status and traces (FR-008).

| Mode | Spoken critical path | Transcript |
|------|----------------------|------------|
| `standard` | Silero VAD → Speaches Whisper STT → chat LLM (Azure/OpenAI) → Kokoro TTS | LiveKit session messages from same STT/LLM text path; ensure UI transcript subscription is not what gates TTS start |
| `voice_to_voice` | Silero/VAD + LiveKit `openai.realtime.RealtimeModel` (OpenAI or Azure Realtime) for speech-in/speech-out | Parallel/side-channel: keep Speaches STT (and/or realtime text transcripts if available) feeding the UI transcript only—must not block first audio |

**Rationale**: Matches user choice (dual-mode + feature flag). LiveKit documents Realtime as a first-class `AgentSession(llm=RealtimeModel(...))` path for low-latency speech-to-speech.

**Alternatives considered**:
- Standard-only with Whisper/model tuning — insufficient for SC-003 V2V targets.
- V2V-only — loses reliable local Speaches demo path and weather-tool familiarity.
- Separate agent binaries per mode — higher ops cost for POC.

## R4 — LangGraph vs Realtime (constitution)

**Decision**: Treat LangGraph as **session supervisor** in both modes: persona resolution, reply-mode selection, language-aware system/greeting policy, tool policy, and inspectable state updates. In `voice_to_voice`, do **not** run LangGraph on every audio frame; Realtime owns low-level speech I/O. In `standard`, keep today’s LiveKit pipeline; strengthen language instructions; optionally mirror turns into graph state for inspectability.

**Rationale**: Constitution II requires LangGraph-first orchestration, not that every sample passes through a graph node. Justified in plan Complexity Tracking.

**Alternatives considered**:
- Force STT text through LangGraph every turn in V2V — reintroduces latency the mode exists to remove.
- Drop LangGraph in V2V — fails constitution and loses shared policy/persona surface.

## R5 — Multiturn context

**Decision**:
- **Standard**: Continue relying on LiveKit Agents session chat context for LLM multiturn; ensure language/system instructions are set once at session start; mirror key turns into graph state when useful for traces.
- **Voice-to-voice**: Rely on Realtime session conversation state for in-call memory; on session start, apply the same language/persona/system policy. If history must be seeded, prefer **text history** injection per LiveKit/OpenAI guidance (realtime models handle text history better than raw audio history). UI `localStorage` history remains human review only—not agent memory.

**Rationale**: Spec FR-009/SC-004 and user open question: context is a first-class session concern in both modes.

**Alternatives considered**:
- Rebuild context only from UI transcript — racey and not authoritative for the agent.
- Audio-only memory across turns — unsupported/fragile for Realtime history reload.

## R6 — End-of-utterance / pause handling

**Decision**: Keep Silero VAD + LiveKit Agents turn handling with barge-in (`interruption.mode=vad`). Expose tunable env knobs documented in contracts (e.g. `MIN_ENDPOINTING_DELAY_MS`, and any supported max/endpointing settings available in the installed Agents SDK version). Defaults chosen to tolerate brief mid-sentence pauses; validate with SC-005 scripts. Emit `user_speech_started`, `user_speech_ended` (EOU committed) into traces.

**Rationale**: Spec FR-010; current code uses VAD interruption but no documented pause tolerance—operators cannot tune “cut off while thinking.”

**Alternatives considered**:
- LiveKit Cloud turn-detector model — not assumed for local Docker POC.
- Fixed push-to-talk — hurts demo naturalness.

## R7 — Session traces

**Decision**: Implement a lightweight **session timeline** (structured events) rather than full APM. Events at minimum: `session_start`, `persona_applied`, `reply_mode_selected`, `user_speech_ended`, `agent_reply_started`, `agent_reply_ended`, plus optional stage marks (`stt_done`, `llm_first_token`, `tts_first_audio` in standard; `realtime_response_started` in V2V). Sink: rotating JSONL under a local traces directory and/or logger JSON lines; optional thin UI panel reading a debug endpoint or in-room data messages. If sink fails, log warning and continue the call (FR-012).

**Rationale**: SC-006 needs operator diagnosis in ≤2 minutes; OTEL is available transitively but heavier than needed for POC.

**Alternatives considered**:
- LangSmith-only — couples to one vendor and may not cover EOU/persona/UI wait.
- Full OpenTelemetry from day one — overkill for local demo; can be a follow-up.

## R8 — Standard-mode latency improvements (non-V2V)

**Decision**: For `standard` mode, prioritize: (1) ensure TTS can start from streaming LLM tokens without waiting for full utterance synthesis where the SDK allows, (2) avoid any intentional “wait for transcript UI ack,” (3) document Whisper model size tradeoff (`faster-whisper-small` default), (4) measure baseline EOU→first audio before claiming SC-003. Optional later: smaller/faster STT model for demos.

**Rationale**: Spec requires standard mode to remain demo-usable (≤4s median) even when V2V is off.

**Alternatives considered**:
- Replace Speaches in standard mode with cloud STT — changes local POC economics; defer unless measurements fail.

## R9 — Realtime provider and voice mapping

**Decision**: Prefer **OpenAI Realtime via LiveKit plugin** when `LLM_PROVIDER=openai`; prefer **Azure OpenAI Realtime** when Azure is the configured provider **if** the installed plugin supports it—otherwise document OpenAI Realtime as the V2V path and keep Azure for standard chat LLM. Map avatar gender (+ language preference) to Realtime voice ids (e.g. male/female voices from the provider set) separately from Kokoro ids. Session language still drives instructions (“respond in Hindi/Spanish/English”).

**Rationale**: Aligns with existing `LLM_PROVIDER` split; LiveKit documents both OpenAI and Azure Realtime plugins.

**Alternatives considered**:
- Gemini Live / other realtime vendors — extra integration surface for this POC.
- Realtime text-only + Kokoro TTS — lower latency than full STT pipeline but not true speech-to-speech; keep as fallback only if audio Realtime is blocked by credentials.

## R10 — Feature-flag UX

**Decision**: Env `REPLY_MODE` is source of truth for local demos. Optional welcome-view toggle writes `reply_mode` into token/agent metadata for the next session only. Do not switch mode mid-call.

**Rationale**: Spec assumes session-stable mode; env-only is enough for operators; UI toggle improves stakeholder demos.

---

## Resolved clarifications

| Topic | Resolution |
|-------|------------|
| Dual vs single pipeline | Dual-mode via `REPLY_MODE` |
| Pause vs EOU | Sustained silence commits turn; tunable delay |
| Multiturn in V2V | Realtime session memory + shared language/persona policy; text history if seeding needed |
| Traces | Lightweight session timeline, soft-fail |
| Wait sound | Replace oscillator with public asset |
| Persona bug | Language in prompts/STT/voice; applied-persona ack in traces |
