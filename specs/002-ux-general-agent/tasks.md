# Tasks: Conversation UX and General Agent Answers

**Input**: Design documents from `/specs/002-ux-general-agent/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Not required by the feature spec; recommended agent unit checks appear in Polish (prompts + voice map). Manual validation via `specs/002-ux-general-agent/quickstart.md`.

**Organization**: Tasks are grouped by user story (US1–US5) to enable independent implementation and testing. Paths reflect the existing `agent/` + `web/` + Docker monorepo.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Agent: `agent/src/`, `agent/tests/`
- Web: `web/app/`, `web/components/`, `web/hooks/`, `web/lib/`
- Specs/docs: `specs/002-ux-general-agent/`, `README.md`, `specs/README.md`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Align the feature workspace without changing runtime behavior yet

- [x] T001 Confirm active feature pointer is `specs/002-ux-general-agent` in `.specify/feature.json` and `specs/README.md`
- [x] T002 [P] Add comments for optional persona/voice-related env var names only (`KOKORO_VOICE` override note) in `agent/.env.example` (no secret values)
- [x] T003 [P] Sketch shared web types stubs for `SessionPersona` and persistence-ready `TranscriptTurn` in `web/lib/session-persona.ts` and extend `web/lib/transcript.ts` as needed

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared contracts and plumbing that later stories rely on (persona metadata path + agent state hooks)

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Implement `avatarGender` + `sessionLanguage` parse/defaults for `POST /api/token` body `persona` per `specs/002-ux-general-agent/contracts/session-persona-metadata.md` in `web/app/api/token/route.ts`
- [x] T005 Attach `avatar_gender` and `session_language` to LiveKit agent dispatch metadata in `web/app/api/token/route.ts`
- [x] T006 [P] Add optional persona fields (`avatar_gender`, `session_language`, `kokoro_voice`) to LangGraph session state in `agent/src/graph/state.py`
- [x] T007 [P] Create Kokoro voice map module `gender` + `language` → voice id with English male/female defaults and fallbacks in `agent/src/adapters/voice_map.py`
- [x] T008 Wire agent entrypoint to read job/dispatch metadata, resolve voice via `voice_map`, and pass voice into TTS factory in `agent/src/agent.py` and `agent/src/adapters/speech_llm.py`

**Checkpoint**: Foundation ready — token can carry persona; agent can select TTS voice from metadata; user stories can proceed

---

## Phase 3: User Story 1 - Ask General Questions and Get Clear Limits (Priority: P1) 🎯 MVP

**Goal**: Non-weather-only welcome; answer general questions; clear spoken refusal when unable; keep weather tool

**Independent Test**: Connect → hear greeting (no weather-only claim) → one answerable general Q → one refusal Q → one weather Q still works (`quickstart.md` scenario 1)

### Implementation for User Story 1

- [x] T009 [US1] Rewrite `SYSTEM_INSTRUCTIONS` for short spoken general answers, tool use for weather, and explicit knowledge-boundary refusal wording in `agent/src/graph/prompts.py`
- [x] T010 [US1] Rewrite `GREETING_INSTRUCTIONS` and `GREETING_FALLBACK_TEXT` so welcome does not claim weather-only capability in `agent/src/graph/prompts.py`
- [x] T011 [US1] Ensure `GraphBackedAssistant` / bridge still registers `lookup_weather` and uses updated system instructions in `agent/src/adapters/livekit_bridge.py`
- [x] T012 [US1] Smoke-check greeting generation path still runs on session start with new instructions in `agent/src/agent.py`

**Checkpoint**: US1 MVP agent behavior works without requiring new home/avatar/history UI

---

## Phase 4: User Story 2 - Follow the Live Transcript in a Side Panel (Priority: P1)

**Goal**: Dedicated transcript panel separate from main call stage (right side on desktop)

**Independent Test**: Connect → complete greeting + one exchange → turns visible in dedicated side panel (`quickstart.md` scenario 2)

### Implementation for User Story 2

- [x] T013 [US2] Adapt or wire `web/components/app/transcript-panel.tsx` (or equivalent) to render ordered user/agent turns from LiveKit session messages
- [x] T014 [US2] Restructure call layout so main stage and a dedicated transcript column coexist in `web/components/agents-ui/blocks/agent-session-view-01/components/agent-session-block.tsx` (right panel on desktop-width)
- [x] T015 [US2] Ensure transcript updates live from `useSessionMessages` (or current session message hook) without being the only surface as a hidden overlay in `agent-session-block.tsx` / related transcript components
- [x] T016 [US2] Add empty-state copy when connected but no turns yet and keep panel scrollable for long transcripts in the transcript panel component

**Checkpoint**: US2 side transcript works independently of avatar/history polish

---

## Phase 5: User Story 3 - Speaking Avatar Matched to Gender and Language (Priority: P2)

**Goal**: Male/female avatar choice; speaking vs idle animation; TTS voice matches gender + session language

**Independent Test**: Select each gender → Connect → avatar animates while agent speaks; male vs female voices differ (`quickstart.md` scenario 3)

### Implementation for User Story 3

- [x] T017 [US3] Add avatar gender + session language selectors on home and hold selection in session UI state in `web/components/app/welcome-view.tsx` (and parent state in `web/components/app/app.tsx` / `view-controller.tsx` as needed)
- [x] T018 [US3] Pass selected `persona` into token/session start so `POST /api/token` receives `avatarGender` + `sessionLanguage` from `web/components/app/app.tsx` (or token source wrapper)
- [x] T019 [P] [US3] Create gendered avatar visuals (idle/listening/thinking/speaking states) under `web/components/app/agent-avatar.tsx` (or `web/components/agents-ui/...`)
- [x] T020 [US3] Replace/augment center tile visualizer with `AgentAvatar` driven by LiveKit agent state (`speaking` / `listening` / `thinking`) in `web/components/agents-ui/blocks/agent-session-view-01/components/` (e.g. `tile-view.tsx` / `agent-session-block.tsx`)
- [x] T021 [US3] Verify agent applies metadata voice before greeting (male/female English mapping) via `agent/src/adapters/voice_map.py` + `agent/src/agent.py`; document fallbacks in `agent/.env.example`

**Checkpoint**: US3 avatar + gendered voice work; US1/US2 still intact

---

## Phase 6: User Story 4 - Wait Feedback While Agent Is Thinking (Priority: P2)

**Goal**: Perceptible visual (and optional audio) filler while processing; stops when speech starts

**Independent Test**: Ask a question with >1.5s think time → filler visible/audible → stops on agent speech (`quickstart.md` scenario 4)

### Implementation for User Story 4

- [x] T022 [US4] Add wait-feedback UI (avatar/stage pulse or shimmer) when agent state is `thinking` in `web/components/app/wait-feedback.tsx` and integrate into call stage components
- [x] T023 [P] [US4] Add optional short waiting sound asset + play/stop helpers with autoplay-failure fallback (visual-only) in `web/lib/wait-sound.ts` and `web/public/` (or equivalent static path)
- [x] T024 [US4] Start filler on thinking / awaiting reply and stop immediately on `speaking` or disconnect; skip/flash-guard for sub-~500ms thinks in call stage integration (`agent-session-block.tsx` or wrapper)

**Checkpoint**: US4 wait feedback works without requiring conversation history

---

## Phase 7: User Story 5 - Creative Home and Previous Conversations (Priority: P3)

**Goal**: Engaging home with Start CTA; list prior conversations; open read-only transcript; persist on call end

**Independent Test**: Complete a call with turns → see it on home → open transcript; empty state when none (`quickstart.md` scenario 5)

### Implementation for User Story 5

- [x] T025 [US5] Implement localStorage conversation CRUD (`version`, max 50, newest-first) per `specs/002-ux-general-agent/contracts/conversation-history-storage.md` in `web/lib/conversation-store.ts`
- [x] T026 [US5] On End call / disconnect, upsert a `ConversationRecord` when live turns exist (label, persona snapshot, turns) from session view / `web/components/app/view-controller.tsx` (or session end hook)
- [x] T027 [P] [US5] Build previous-conversations list + read-only detail view in `web/components/app/conversation-history.tsx`
- [x] T028 [US5] Redesign creative home composition (brand presence, short support line, primary Connect CTA, persona selectors, history section + empty state) in `web/components/app/welcome-view.tsx`
- [x] T029 [US5] Handle storage parse/quota failures without blocking Connect (non-blocking error) in `web/lib/conversation-store.ts` and home/history UI

**Checkpoint**: US5 home history complete; full feature stories independently demonstrable

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Docs, regression, and recommended agent unit coverage

- [x] T030 [P] Add/extend unit tests for prompt policy (greeting not weather-only; refusal guidance present) in `agent/tests/` (e.g. `test_prompts.py`)
- [x] T031 [P] Add unit tests for `voice_map` gender/language → voice id and fallbacks in `agent/tests/test_voice_map.py`
- [x] T032 [P] Update root `README.md` and/or `specs/002-ux-general-agent/quickstart.md` with avatar/language selectors and history validation notes
- [x] T033 Mark `specs/README.md` tasks column for `002-ux-general-agent` and confirm feature status
- [x] T034 Run `uv run pytest` in `agent/` and execute manual scenarios in `specs/002-ux-general-agent/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — **BLOCKS** all user stories
- **US1 (Phase 3)**: After Foundational — MVP; no dependency on US2–US5
- **US2 (Phase 4)**: After Foundational — independent of US1 agent copy (can parallel with US1 if staffed)
- **US3 (Phase 5)**: After Foundational — uses persona token + voice_map; integrates with home selectors (welcome-view)
- **US4 (Phase 6)**: After Foundational — best after US3 avatar exists (can use stage-only filler if US3 deferred)
- **US5 (Phase 7)**: After Foundational — best after US2 so persisted turns match side-panel transcript shape; can stub turns from session messages alone
- **Polish (Phase 8)**: After desired stories complete

### User Story Dependencies

| Story | Depends on | Notes |
|-------|------------|-------|
| US1 General answers | Foundational | Prompt-only MVP |
| US2 Side transcript | Foundational | Layout-only; no history required |
| US3 Avatar + voice | Foundational (T004–T008) | Soft preference: after US2 for calmer layout merge |
| US4 Wait feedback | Foundational | Soft preference: after US3 for avatar-tied filler |
| US5 Home history | Foundational | Soft preference: after US2 for shared turn shaping |

### Parallel Opportunities

- T002 ∥ T003 (Setup)
- T006 ∥ T007 (Foundational)
- After Foundational: **US1 ∥ US2** strongly parallelizable (agent vs web layout)
- T019 ∥ T017 within US3 once token wiring planned
- T022 ∥ T023 within US4
- T027 ∥ T025 within US5 (store then UI, or types-first)
- T030 ∥ T031 ∥ T032 in Polish

---

## Parallel Example: After Foundational

```bash
# Developer A — US1 agent prompts
Task: "Rewrite SYSTEM_INSTRUCTIONS in agent/src/graph/prompts.py"
Task: "Rewrite GREETING_* in agent/src/graph/prompts.py"
Task: "Confirm weather tool still registered in agent/src/adapters/livekit_bridge.py"

# Developer B — US2 side transcript
Task: "Wire transcript panel in web/components/app/transcript-panel.tsx"
Task: "Restructure call layout in agent-session-block.tsx"
```

---

## Parallel Example: User Story 3

```bash
Task: "Create agent-avatar.tsx with gendered idle/speaking states"
Task: "Add gender/language selectors in welcome-view.tsx"
# Then sequentially: pass persona into token → tile integration → verify voice_map
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup  
2. Complete Phase 2: Foundational (persona/voice plumbing — needed later; still finish before stories)  
3. Complete Phase 3: US1 prompts + tool retention  
4. **STOP and VALIDATE** with quickstart scenario 1  
5. Demo improved agent answers/refusals even before UX polish  

### Incremental Delivery

1. Setup + Foundational → foundation ready  
2. US1 → general agent MVP  
3. US2 → diagnosable side transcript  
4. US3 → avatar + gendered voice  
5. US4 → wait fillers  
6. US5 → creative home + history  
7. Polish → tests/docs/quickstart pass  

### Parallel Team Strategy

1. Team finishes Setup + Foundational together  
2. Then: A → US1, B → US2; later C → US3/US4, A/B → US5  
3. Integrate on shared call-stage files carefully (prefer sequential commits on `agent-session-block.tsx`)

---

## Notes

- [P] = different files, no incomplete-task dependencies  
- Do not keep overlay chat as the only transcript surface after US2  
- Do not read `.env` files in helpers; process env / examples only  
- Preserve 001 behaviors: connect/disconnect, barge-in, ~30s agent-join fail, weather tool  
- Commit after each task or logical group; validate at every checkpoint  
