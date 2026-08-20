# Tasks: LiveKit Voice-to-Voice Agent Testing POC

**Input**: Design documents from `/specs/001-livekit-v2v/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Not required by the feature spec; optional unit updates only appear in Polish where existing `agent/tests/` already covers the weather tool.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. Paths reflect the **existing** `agent/` + `web/` + Docker monorepo; new modules under `agent/src/graph|tools|adapters/` are additive refactors, not a greenfield app.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Agent: `agent/src/`, `agent/tests/`
- Web: `web/app/`, `web/components/`, `web/hooks/`, `web/lib/`
- Specs/docs: `specs/001-livekit-v2v/`, `README.md`, `specs/README.md`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Align dependencies and package layout with the plan without breaking the current runnable POC

- [x] T001 Create agent package directories `agent/src/graph/`, `agent/src/tools/`, `agent/src/adapters/` with `__init__.py` files in each
- [x] T002 [P] Add LangGraph and LangChain dependencies to `agent/pyproject.toml` and refresh the lockfile via `uv lock` / `uv sync` in `agent/`
- [x] T003 [P] Document current-vs-target agent layout in `specs/001-livekit-v2v/plan.md` Structure Decision (existing `agent.py` vs planned modules)
- [x] T004 [P] Confirm `.env.example` documents required var names only (`LIVEKIT_*`, `AGENT_NAME`, `OPENAI_*`, `SPEACHES_*`) without secret values

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared session/orchestration boundaries that all stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Define LangGraph session state TypedDict/dataclass in `agent/src/graph/state.py` per `specs/001-livekit-v2v/data-model.md`
- [x] T006 [P] Create config helper reading process env by name (no `.env` file reads in helpers) in `agent/src/adapters/config.py`
- [x] T007 [P] Extract Speaches STT/TTS + OpenAI LLM factory wiring from `agent/src/agent.py` into `agent/src/adapters/speech_llm.py`
- [x] T008 Create LiveKit session bridge stub/interface in `agent/src/adapters/livekit_bridge.py` for mapping voice turns ↔ graph invoke
- [x] T009 Slim `agent/src/agent.py` to Agents entrypoint (`AgentServer`, prewarm, `rtc_session`) that delegates reasoning to the bridge
- [x] T010 Align web token route response shape with `specs/001-livekit-v2v/contracts/session-token-api.md` in `web/app/api/token/route.ts`
- [x] T011 [P] Add shared session status enum/helpers (`disconnected|connecting|connected|failed`) in `web/lib/session-status.ts`

**Checkpoint**: Foundation ready — user story implementation can begin

---

## Phase 3: User Story 1 - Connect and Hold a Voice Conversation (Priority: P1) 🎯 MVP

**Goal**: Tester connects, hears automatic greeting, multi-turn voice replies with in-call context, and clean disconnect

**Independent Test**: Connect → hear greeting → two user turns with replies → End call (quickstart V1)

### Implementation for User Story 1

- [x] T012 [US1] Implement greeting node/path that emits short spoken greeting without waiting for user speech in `agent/src/graph/nodes.py`
- [x] T013 [US1] Implement multi-turn reply path that preserves messages in graph state for the active call in `agent/src/graph/nodes.py` and `agent/src/graph/graph.py`
- [x] T014 [US1] Wire graph compile/entry in `agent/src/graph/graph.py` and invoke from `agent/src/adapters/livekit_bridge.py`
- [x] T015 [US1] Ensure `agent/src/agent.py` starts `AgentSession` with Speaches STT/TTS + LLM adapters and triggers greeting on agent ready
- [x] T016 [US1] Keep Connect / End-call flow working in `web/components/app/view-controller.tsx` and `web/components/app/welcome-view.tsx` against LiveKit session context
- [x] T017 [US1] Verify mic grant path and connected agent presence messaging in `web/components/app/welcome-view.tsx` / session view components
- [x] T018 [US1] Confirm clean disconnect stops media and returns UI to disconnected in `web/components/app/view-controller.tsx`

**Checkpoint**: US1 MVP voice conversation works end to end

---

## Phase 4: User Story 2 - Validate Session Lifecycle in the UI (Priority: P2)

**Goal**: Clear status, actionable failures, manual reconnect, fail-fast network drop, ~30s agent-join timeout

**Independent Test**: Connect/disconnect/reconnect; induce token/backend failure; agent-down timeout; mid-call network fail (quickstart V2)

### Implementation for User Story 2

- [x] T019 [US2] Surface connecting/connected/disconnected/failed labels using `web/lib/session-status.ts` in `web/components/app/welcome-view.tsx` and `web/components/app/view-controller.tsx`
- [x] T020 [US2] Map token/connect errors to failed status with user-visible reason in `web/hooks/useAgentErrors.tsx` and session UI
- [x] T021 [US2] Implement ~30s agent-join timeout → failed status when agent never appears in `web/components/app/view-controller.tsx` (or dedicated `web/hooks/useAgentJoinTimeout.ts`)
- [x] T022 [US2] On mid-call transport loss, force failed state immediately with no silent auto-reconnect in `web/components/app/view-controller.tsx` / LiveKit session hooks
- [x] T023 [US2] Ensure Disconnect then Connect works without full page reload in `web/components/app/view-controller.tsx`
- [x] T024 [P] [US2] Document failure UX expectations against `specs/001-livekit-v2v/contracts/voice-session-events.md` in a short note under `specs/001-livekit-v2v/quickstart.md` V2 section if gaps appear

**Checkpoint**: Lifecycle and fail-fast behaviors are tester-visible and repeatable

---

## Phase 5: User Story 3 - Inspect Live Transcripts While Testing (Priority: P2)

**Goal**: Live transcript entries for tester and agent turns (including greeting)

**Independent Test**: During a call, greeting + user + agent text appear in the UI (quickstart V3)

### Implementation for User Story 3

- [x] T025 [P] [US3] Add transcript entry types/helpers in `web/lib/transcript.ts` aligned with `specs/001-livekit-v2v/data-model.md`
- [x] T026 [US3] Create compact transcript panel component in `web/components/app/transcript-panel.tsx`
- [x] T027 [US3] Subscribe to LiveKit/Agents transcription or data events and append tester/agent lines in `web/components/app/view-controller.tsx` (or `web/hooks/useLiveTranscripts.ts`)
- [x] T028 [US3] Ensure agent greeting text appears as an agent transcript entry when greeting audio plays
- [x] T029 [US3] Mount transcript panel in the active session UI without expanding into a product dashboard (`web/components/app/view-controller.tsx`)

**Checkpoint**: Transcripts make voice turns diagnosable in-browser

---

## Phase 6: User Story 5 - Exercise One Demo Tool by Voice (Priority: P2)

**Goal**: At least one demo tool callable by spoken request; spoken + transcript answers reflect tool result

**Independent Test**: Ask weather (or documented phrase) → spoken + transcript tool-backed answer (quickstart V4)

### Implementation for User Story 5

- [x] T030 [P] [US5] Move weather demo tool from inline `Assistant` into `agent/src/tools/weather.py`
- [x] T031 [US5] Register tool node/binding in LangGraph tool path in `agent/src/graph/nodes.py` and `agent/src/graph/graph.py`
- [x] T032 [US5] Update agent instructions/prompts so weather questions invoke the tool and spoken summary stays plain text in `agent/src/graph/prompts.py` (new) or graph node config
- [x] T033 [US5] Ensure tool-backed replies can annotate transcript/tool metadata when UI shows the turn (`web/lib/transcript.ts` + transcript panel)
- [x] T034 [US5] Add tool-failure spoken fallback that keeps the session usable in `agent/src/graph/nodes.py`
- [x] T035 [P] [US5] Update `agent/tests/test_agent.py` imports/paths for the moved weather tool

**Checkpoint**: Demo tool is required-path ready for acceptance

---

## Phase 7: User Story 4 - Interrupt and Recover During Agent Speech (Priority: P3)

**Goal**: Barge-in yields agent audio promptly; conversation continues

**Independent Test**: Speak over a long agent reply → yield within ~1s → continue (quickstart V5)

### Implementation for User Story 4

- [x] T036 [US4] Confirm LiveKit Agents session interruption/VAD settings allow barge-in in `agent/src/agent.py` and `agent/src/adapters/livekit_bridge.py`
- [x] T037 [US4] On barge-in, mark interrupted turn in graph state and cancel/ignore stale agent speech generation in `agent/src/graph/state.py` / `agent/src/graph/nodes.py`
- [x] T038 [US4] Verify UI remains connected and transcripts continue after interrupt in `web/components/app/view-controller.tsx`
- [x] T039 [US4] Capture barge-in validation steps already listed in `specs/001-livekit-v2v/quickstart.md` V5 during manual check

**Checkpoint**: Interrupt path does not brick the call

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Docs, consistency, and full quickstart pass

- [x] T040 [P] Update `specs/README.md` task column to link `001-livekit-v2v/tasks.md`
- [x] T041 [P] Sync root `README.md` notes with LangGraph module layout and quickstart link (no secret values)
- [x] T042 Run full validation scenarios in `specs/001-livekit-v2v/quickstart.md` (V1–V5) and record any gaps as checklist notes in `specs/001-livekit-v2v/checklists/requirements.md`
- [x] T043 [P] Run `uv run ruff check` / `uv run pytest` in `agent/` after refactors
- [x] T044 Remove dead inline `Assistant` duplication from `agent/src/agent.py` if fully superseded by graph/tools modules

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup — **BLOCKS** all user stories
- **US1 (Phase 3)**: After Foundational — MVP
- **US2 (Phase 4)**: After Foundational; ideally after US1 connect path exists
- **US3 (Phase 5)**: After Foundational; needs active session (US1) for meaningful validation
- **US5 (Phase 6)**: After Foundational; needs conversation path (US1); transcripts (US3) improve acceptance but spoken tool reply can be validated with audio alone
- **US4 (Phase 7)**: After US1 conversation path (needs agent speech to interrupt)
- **Polish (Phase 8)**: After desired stories complete

### User Story Dependencies

- **US1 (P1)**: No story dependencies — MVP
- **US2 (P2)**: Soft dependency on US1 connect/disconnect controls
- **US3 (P2)**: Soft dependency on US1 turns existing
- **US5 (P2)**: Soft dependency on US1; optional US3 for transcript assertion
- **US4 (P3)**: Soft dependency on US1 agent speech

### Parallel Opportunities

- T002, T003, T004 in Setup
- T006, T007 in Foundational (after T005 started/defined)
- T025 parallel with early US3 work
- T030, T035 in US5
- T040, T041, T043 in Polish

---

## Parallel Example: User Story 3

```bash
# Different files — can proceed together after US1 session works:
Task: "Add transcript helpers in web/lib/transcript.ts"
Task: "Create transcript panel in web/components/app/transcript-panel.tsx"
# Then integrate in view-controller / hook (sequential):
Task: "Subscribe and append live transcript lines"
```

---

## Parallel Example: User Story 5

```bash
Task: "Move weather tool to agent/src/tools/weather.py"
Task: "Update agent/tests/test_agent.py imports"
# Then sequential graph wiring:
Task: "Register tool in LangGraph nodes/graph"
Task: "Prompts + failure fallback"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 Setup
2. Complete Phase 2 Foundational
3. Complete Phase 3 US1
4. **STOP and VALIDATE** quickstart V1
5. Demo connect → greet → talk → disconnect

### Incremental Delivery

1. Setup + Foundational
2. US1 → MVP demo
3. US2 fail-fast lifecycle
4. US3 transcripts
5. US5 demo tool (acceptance-required)
6. US4 barge-in polish
7. Phase 8 docs + full quickstart

### Parallel Team Strategy

1. Shared Setup + Foundational
2. Dev A: US1 then US4
3. Dev B: US2 + US3 (web-heavy)
4. Dev C: US5 tools/graph after T005–T009 land

---

## Notes

- Do not read or commit `.env.local` secrets; use `.env.example` names only
- Ask before running privileged/destructive commands per constitution
- Prefer evolving existing LiveKit Agents + Next.js starter over rewriting
- [P] = different files, no incomplete blockers
- Commit after each task or logical group when requested
