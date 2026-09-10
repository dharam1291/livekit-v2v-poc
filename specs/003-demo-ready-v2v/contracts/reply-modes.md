# Contract: Dual Reply Modes

**Feature**: `003-demo-ready-v2v`  
**Surface**: Agent `AgentSession` factory + operator feature flag

## Flag

| Name | Where | Values | Session rule |
|------|-------|--------|--------------|
| `REPLY_MODE` | `agent/.env.local` | `standard` (default) \| `voice_to_voice` | Fixed at job start |
| `reply_mode` | token/job metadata | same | Overrides env for that session |

## Mode: `standard`

```text
mic → LiveKit → VAD → Speaches STT → chat LLM → Kokoro TTS → room audio
                         ↘ transcript / UI messages
```

**Requirements**:
- Transcript MUST NOT gate TTS start.
- Language-aware instructions + Kokoro voice from persona.
- Multiturn via LiveKit Agents chat context.
- Emit stage timings when practical: `stt_done`, `llm_first_token`, `tts_first_audio`.

**Latency target**: SC-003 standard band (median ≤4s, 90% ≤6s).

## Mode: `voice_to_voice`

```text
mic → LiveKit → VAD / Realtime input → OpenAI or Azure RealtimeModel → room audio
                         ↘ parallel transcript (Speaches STT and/or realtime text) → UI
```

**Requirements**:
- Spoken path MUST NOT wait on Speaches STT completion.
- Same persona language policy; Realtime voice mapped from gender (and language preference where applicable).
- Multiturn via Realtime session conversation state; shared system/greeting policy from LangGraph/adapter supervisor.
- Tools (e.g. weather): best-effort via Realtime function tools when supported; otherwise document limitation and keep weather reliable in `standard`.
- Emit `realtime_response_started` / reply end events.

**Latency target**: SC-003 V2V band (median ≤2.5s, 90% ≤4s).

## Shared

- LiveKit room lifecycle unchanged.
- Wait feedback UI while agent thinking / before first audio.
- EOU / barge-in behavior (see env knobs in tracing/EOU docs).
- Session traces include `reply_mode`.

## Non-goals

- Mid-call mode switching.
- Dual simultaneous spoken pipelines in one session.
- Replacing LiveKit transport with direct browser↔OpenAI WebRTC.
