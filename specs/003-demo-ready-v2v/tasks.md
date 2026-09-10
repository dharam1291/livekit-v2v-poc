# Tasks: Demo-Ready Voice Experience

**Input**: Design documents from `/specs/003-demo-ready-v2v/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Not required by the feature spec for TDD; recommended agent unit checks appear in Polish. Manual validation via `specs/003-demo-ready-v2v/quickstart.md`.

**Organization**: Tasks are grouped by user story (US1–US4) to enable independent implementation and testing. Paths reflect the existing `agent/` + `web/` + Docker monorepo.

**Clarification note**: Spec clarify Q4 resolved as **Option B**—best-effort tools in V2V; clear limit if unavailable; full tools in standard (see `spec.md` Clarifications + FR-015). T030 implements this.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Agent: `agent/src/`, `agent/tests/`
- Web: `web/app/`, `web/components/`, `web/lib/`, `web/public/`
- Specs/docs: `specs/003-demo-ready-v2v/`, `README.md`, `specs/README.md`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Align workspace and env knobs without changing runtime behavior yet

- [x] T001 Confirm active feature pointer is `specs/003-demo-ready-v2v` in `.specify/feature.json` and `specs/README.md`
- [x] T002 [P] Document env var names only for `REPLY_MODE`, endpointing delay, and trace sink path in `agent/.env.example` (no secret values)
- [x] T003 [P] Extend session types with optional `replyMode` in `web/lib/session-persona.ts` (or sibling `web/lib/session-reply-mode.ts`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared persona/mode/EOU/trace plumbing that all stories rely on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Extend `POST /api/token` to accept optional `replyMode` and attach `reply_mode` to agent dispatch metadata per `specs/003-demo-ready-v2v/contracts/session-persona-and-mode.md` in `web/app/api/token/route.ts`
- [x] T005 [P] Add `REPLY_MODE`, endpointing, and tracing config fields with safe defaults in `agent/src/adapters/config.py`
- [x] T006 [P] Create persona resolver with applied ack (`gender`, `language`, `voice_id`, `defaults_used`) in `agent/src/adapters/persona.py`
- [x] T007 [P] Create EOU / endpointing config helper (e.g. `MIN_ENDPOINTING_DELAY_MS`) in `agent/src/adapters/eou.py`
- [x] T008 [P] Create session timeline emitter (JSONL/logger sink, soft-fail) per `specs/003-demo-ready-v2v/contracts/session-traces.md` in `agent/src/adapters/tracing.py`
- [x] T009 Extend LangGraph/session state with `reply_mode`, `requested_reply_mode`, `defaults_used`, and applied persona fields in `agent/src/graph/state.py`
- [x] T010 Wire `agent/src/agent.py` to resolve persona + mode from job metadata/env, emit `session_start` / `persona_applied` / `reply_mode_selected` traces, and apply EOU settings into `AgentSession` turn handling

**Checkpoint**: Foundation ready — token carries persona+mode; agent resolves and traces them; stories can proceed

---

## Phase 3: User Story 1 - Persona Matches What the Tester Chose (Priority: P1) 🎯 MVP

**Goal**: Avatar gender + language drive spoken behavior (instructions + voice), not UI-only / voice-id-only mismatches

**Independent Test**: Male/female × supported languages → greeting and replies match avatar + language; traces show `persona_applied` (`quickstart.md` Scenario A)

### Implementation for User Story 1

- [x] T011 [US1] Make system and greeting instructions language-aware (respond/greet in selected language) in `agent/src/graph/prompts.py`
- [x] T012 [US1] Apply language-aware instructions when creating the assistant in `agent/src/adapters/livekit_bridge.py`
- [x] T013 [US1] Pass STT language hint (when supported) from resolved persona in `agent/src/adapters/speech_llm.py`
- [x] T014 [US1] Ensure Kokoro voice resolution still matches gender+language and logs/traces applied voice in `agent/src/adapters/voice_map.py` and `agent/src/agent.py`
- [x] T015 [US1] Surface applied persona (or `defaults_used`) in call-stage status UI so UI cannot silently disagree with agent in `web/components/agents-ui/blocks/agent-session-view-01/components/agent-session-block.tsx` (or related status component)

**Checkpoint**: US1 persona/language correctness works without requiring dual-mode or new wait asset

---

## Phase 4: User Story 2 - Comfortable Wait Feedback During Thinking (Priority: P1)

**Goal**: Replace unsatisfactory wait sound; stop cleanly when agent speaks; visual fallback remains

**Independent Test**: Induce thinking → new cue plays/shows → stops on speech (`quickstart.md` Scenario B)

### Implementation for User Story 2

- [x] T016 [P] [US2] Add short soft looped wait-cue audio asset under `web/public/` (path referenced by wait-sound helper)
- [x] T017 [US2] Replace Web Audio oscillator with asset playback (keep ~450ms delay, low volume, loop) in `web/lib/wait-sound.ts`
- [x] T018 [US2] Confirm `WaitFeedback` starts on thinking, stops on speaking, and keeps visual fallback per `specs/003-demo-ready-v2v/contracts/wait-feedback.md` in `web/components/app/wait-feedback.tsx` and `agent-session-block.tsx`

**Checkpoint**: US2 wait cue acceptable independently of V2V/traces

---

## Phase 5: User Story 3 - Faster, Demo-Acceptable Response Latency (Priority: P1)

**Goal**: Dual reply modes via env default + pre-connect UI toggle; standard improved; V2V Realtime path with parallel transcript; EOU pause tolerance; multiturn context; V2V→standard fallback with visible warning

**Independent Test**: Toggle/env standard vs V2V; measure EOU→audio; brief pause vs end silence; multiturn name recall; unavailable V2V falls back with warning (`quickstart.md` Scenarios C–E)

### Implementation for User Story 3

- [x] T019 [P] [US3] Add pre-connect reply-mode toggle (standard / voice_to_voice) on home, defaulting from env-exposed default when present, in `web/components/app/welcome-view.tsx` and parent state in `web/components/app/app.tsx`
- [x] T020 [US3] Pass selected `replyMode` into token/session start so dispatch metadata includes `reply_mode` from `web/components/app/app.tsx` (and `web/lib/session-persona.ts` types)
- [x] T021 [US3] Show actual (and requested, if fallback) reply mode in call-stage status in `agent-session-block.tsx` (or status chip component)
- [x] T022 [P] [US3] Implement Realtime voice map (gender → Realtime voice id) alongside Kokoro map in `agent/src/adapters/voice_map.py`
- [x] T023 [US3] Implement `voice_to_voice` session builder using LiveKit OpenAI/Azure Realtime adapter per `specs/003-demo-ready-v2v/contracts/reply-modes.md` in `agent/src/adapters/realtime_speech.py`
- [x] T024 [US3] Refactor `agent/src/agent.py` into a mode factory: build standard `AgentSession` (STT/LLM/TTS) vs Realtime session; keep LangGraph supervisor for persona/policy/state
- [x] T025 [US3] Implement auto-fallback from requested `voice_to_voice` to `standard` when credentials/service unavailable, with visible UI warning channel and trace attrs `requested_reply_mode` / `actual_reply_mode` in `agent/src/agent.py` + web status/warning UI
- [x] T026 [US3] Ensure standard-mode spoken path does not wait on UI transcript ack; prefer streaming LLM→TTS where SDK allows in `agent/src/adapters/speech_llm.py` / `agent/src/agent.py`
- [x] T027 [US3] Add parallel transcript path for V2V (Speaches STT and/or realtime text events → session messages) without blocking first audio in `agent/src/adapters/realtime_speech.py` and/or `agent/src/agent.py`
- [x] T028 [US3] Apply tunable endpointing/pause tolerance from `agent/src/adapters/eou.py` in both modes; emit `user_speech_ended` (and speech started if available) via `agent/src/adapters/tracing.py`
- [x] T029 [US3] Verify multiturn context in both modes (LiveKit chat context standard; Realtime session memory V2V) and keep language/persona policy applied for follow-ups in `agent/src/adapters/livekit_bridge.py` / `realtime_speech.py`
- [x] T030 [US3] Best-effort weather/tool registration in V2V when Realtime function tools are supported; if unavailable, clear spoken/visible limit—full tools remain in standard (`agent/src/adapters/realtime_speech.py`, `agent/src/tools/weather.py`, `livekit_bridge.py`)

**Checkpoint**: US3 dual-mode demos work; US1/US2 still intact

---

## Phase 6: User Story 4 - Inspectable Session Traces (Priority: P2)

**Goal**: Local structured timeline + simple in-app session timeline panel; soft-fail when sink degraded

**Independent Test**: Run call → see persona/mode/EOU/reply timings in panel and JSONL; break sink → call continues (`quickstart.md` Scenario F)

### Implementation for User Story 4

- [x] T031 [US4] Emit remaining required/recommended stage events (`agent_reply_started` / `ended`, standard `stt_done` / `llm_first_token` / `tts_first_audio`, V2V `realtime_response_started`) from session hooks in `agent/src/adapters/tracing.py` and `agent/src/agent.py`
- [x] T032 [P] [US4] Add client helper to consume/normalize timeline events in `web/lib/session-traces.ts`
- [x] T033 [US4] Expose a soft-fail debug feed for the current session timeline (room data message and/or lightweight debug API) that UI can read without secrets in agent and/or `web/app/` as needed
- [x] T034 [US4] Build simple in-app session timeline panel listing turn-ordered events in `web/components/app/session-trace-panel.tsx` and wire into call stage layout in `agent-session-block.tsx`
- [x] T035 [US4] Show “traces unavailable” empty/error state when sink/feed fails without ending the call in `session-trace-panel.tsx`

**Checkpoint**: US4 diagnosis path works for persona/EOU/latency issues

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Docs, baseline measurement, and small safety nets across stories

- [x] T036 [P] Update root `README.md` with dual-mode (`REPLY_MODE`), persona/language notes, wait cue, and how to view traces
- [x] T037 [P] Align `specs/003-demo-ready-v2v/quickstart.md` commands/env names with final implementation
- [x] T038 [P] Add unit tests for persona resolver + language prompt helpers + voice maps in `agent/tests/`
- [x] T039 Measure baseline EOU→first-audio for standard and V2V under local demo conditions; record results in `specs/003-demo-ready-v2v/quickstart.md` or a short notes section
- [x] T040 Run full `specs/003-demo-ready-v2v/quickstart.md` validation (Scenarios A–F) and fix any blockers

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — **BLOCKS** all user stories
- **US1 (Phase 3)**: After Foundational — MVP persona fix
- **US2 (Phase 4)**: After Foundational — can parallel with US1 (different files)
- **US3 (Phase 5)**: After Foundational; benefits from US1 language/persona correctness; uses mode UI + fallback
- **US4 (Phase 6)**: After Foundational; richest when US3 emits stage timings, but panel can start earlier against core events from T010
- **Polish (Phase 7)**: After desired stories complete

### User Story Dependencies

- **US1 (P1)**: No dependency on US2–US4
- **US2 (P1)**: Independent of US1/US3/US4
- **US3 (P1)**: Should follow US1 for language-aware prompts; mode UI independent of wait asset
- **US4 (P2)**: Uses foundational tracer; stage events from US3 improve completeness

### Parallel Opportunities

- T002/T003 in Setup
- T005–T008 in Foundational
- After Foundational: US1 and US2 in parallel
- Within US3: T019 and T022 can start in parallel before T024 factory merge
- Within US4: T032 parallel with T031
- Polish doc tasks T036/T037 in parallel

---

## Parallel Example: After Foundational

```bash
# Persona story (US1) + wait cue (US2) in parallel:
Task: "Language-aware prompts in agent/src/graph/prompts.py"
Task: "Add wait-cue asset under web/public/"
Task: "Replace oscillator in web/lib/wait-sound.ts"
```

## Parallel Example: User Story 3 kickoff

```bash
Task: "Pre-connect reply-mode toggle in web/components/app/welcome-view.tsx"
Task: "Realtime voice map in agent/src/adapters/voice_map.py"
Task: "Realtime session builder stub in agent/src/adapters/realtime_speech.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: US1 persona/language
4. **STOP and VALIDATE** via quickstart Scenario A
5. Demo persona credibility even before latency dual-mode

### Incremental Delivery

1. Setup + Foundational
2. US1 → persona demo-ready
3. US2 → wait cue acceptable
4. US3 → dual-mode latency + EOU + fallback
5. US4 → traces panel + JSONL
6. Polish → README + quickstart pass

### Suggested MVP scope

**US1 only** (persona/language correctly applied) is the smallest demo-credibility win. For a stakeholder latency demo, complete **US1 + US3** (wait cue US2 is fast and should ship before external demos).

---

## Notes

- [P] = different files, no incomplete-task dependencies
- Do not mid-call switch `REPLY_MODE`
- Never commit secrets; env example names only
- Tools-in-V2V: best-effort per FR-015 / clarify Q4 Option B; full tools in standard
- Commit after each task or logical group when the operator requests commits
