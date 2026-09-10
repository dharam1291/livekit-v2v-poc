# Feature Specification: Demo-Ready Voice Experience

**Feature Branch**: `003-demo-ready-v2v`

**Created**: 2026-09-09

**Status**: Draft

**Input**: User description: "The basic POC is fine but it's not production ready and demoable. Challenges: (1) Agent persona [avatar and language] is not working properly—may not be correctly fed to the agent; (2) waiting sound needs to change; (3) improve latency—consider transcript-only path for current STT stack and voice-to-voice with the LLM so speech can go more directly to the model while transcript remains separate; (4) enable traces for visibility. Open question: how does the system decide speech is finished when the user pauses mid-thought, and in a voice-to-voice multiturn call how does the agent keep prior conversation context?"

## Clarifications

### Session 2026-09-09

- Q: How should operators choose between standard and low-latency voice-to-voice reply modes for a demo call? → A: Env default + optional UI toggle before connect; mode fixed for that session
- Q: Where should operators view session traces during or after a demo call? → A: Local structured timeline (JSONL/logs) + simple in-app session timeline panel
- Q: What should happen if the operator selects low-latency voice-to-voice mode but the required credentials or service are unavailable? → A: Auto-fallback to standard mode with a visible warning that fallback occurred
- Q: In low-latency voice-to-voice mode, how should existing demo tools (such as weather lookup) behave? → A: Best-effort tools in V2V; clear spoken/visible limit if unavailable; full tools guaranteed in standard mode

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Persona Matches What the Tester Chose (Priority: P1)

A demo operator selects an agent avatar (male/female) and a session language, starts a call, and hears the agent speak in a voice and language that match that selection. The avatar on screen reflects the same persona. The choice is reliably applied for the whole session—not ignored, defaulted away, or only shown in the UI while the spoken agent behaves differently.

**Why this priority**: A mismatched persona breaks demo credibility immediately; stakeholders judge the product on whether the chosen agent “is who they picked.”

**Independent Test**: Pick male then female (and each supported language), start a call, trigger agent speech, and verify spoken voice, language, and on-screen avatar all match the selection—without needing latency changes or traces.

**Acceptance Scenarios**:

1. **Given** the tester selects a male avatar and a supported language before joining, **When** the agent greets or replies, **Then** the spoken voice presents as male and in that language, and the on-screen avatar is the male persona.
2. **Given** the tester selects a female avatar and a supported language before joining, **When** the agent greets or replies, **Then** the spoken voice presents as female and in that language, and the on-screen avatar is the female persona.
3. **Given** a selected persona and language, **When** the session runs for multiple turns, **Then** persona and language remain consistent for every agent utterance unless the tester explicitly changes them.
4. **Given** the UI shows a selected persona/language, **When** the agent speaks, **Then** the spoken behavior MUST match what the UI shows (no “UI only” persona).

---

### User Story 2 - Comfortable Wait Feedback During Thinking (Priority: P1)

While the agent is preparing a reply and has not started speaking, the tester hears (and/or sees) wait feedback that feels appropriate for a demo—not the current unsatisfactory waiting sound. Feedback stops cleanly when the agent starts talking and does not overlap the reply.

**Why this priority**: Awkward or wrong waiting audio is highly noticeable in live demos and undermines “production-ready” perception even when answers are correct.

**Independent Test**: Ask a question that needs noticeable processing; confirm the new wait cue plays/shows, then stops when speech starts—without needing persona or pipeline changes.

**Acceptance Scenarios**:

1. **Given** a connected session, **When** the tester finishes speaking and the agent has not yet started its reply, **Then** the experience plays/shows the updated wait feedback (not the previous unsatisfactory waiting sound).
2. **Given** wait feedback is active, **When** the agent begins speaking, **Then** wait feedback stops immediately and does not overlap the reply.
3. **Given** a very fast reply, **When** the agent starts speaking almost immediately, **Then** wait feedback is brief or skipped so it does not delay or interrupt the answer.
4. **Given** audio wait feedback cannot play (e.g., blocked), **When** the agent is still thinking, **Then** a visual wait cue still indicates progress.

---

### User Story 3 - Faster, Demo-Acceptable Response Latency (Priority: P1)

A demo operator has a multi-turn voice conversation that feels responsive enough for stakeholder demos: after the user finishes an utterance, the agent begins a useful spoken reply within an acceptable time. The operator may keep a readable transcript of the call, but transcript generation MUST NOT be what makes the spoken reply feel slow.

**Why this priority**: Latency is the main barrier between “POC works” and “demoable.” Pipeline choice directly determines whether demos feel production-like.

**Independent Test**: Run a scripted multi-turn call (greeting + 3 follow-ups) and measure time from end of user speech to start of agent speech against success criteria; confirm transcript still appears for review.

**Acceptance Scenarios**:

1. **Given** a quiet room and a clear short question, **When** the tester finishes speaking, **Then** the agent begins its spoken reply within the target latency in Success Criteria under normal local demo conditions.
2. **Given** an active multi-turn call, **When** the tester asks a follow-up that depends on earlier turns, **Then** the agent answers with awareness of that prior context (not as if each turn were a brand-new conversation).
3. **Given** either reply mode is active, **When** the call produces speech turns, **Then** a readable transcript of user and agent turns is still available for the operator (live and/or after the call as already supported by the product).
4. **Given** the operator enables the standard reply mode via env default and/or the pre-connect UI toggle, **When** they run a call, **Then** the session uses the improved speech→reason→speech path with transcript kept off the critical path for starting spoken replies.
5. **Given** the operator enables the low-latency voice-to-voice mode via env default and/or the pre-connect UI toggle, **When** they run a call and voice-to-voice is available, **Then** speech goes more directly to the voice-capable model path while transcript remains a parallel/side channel.
6. **Given** the operator selected voice-to-voice but required credentials or service are unavailable, **When** the session starts, **Then** the system falls back to standard mode, shows a clear visible warning that fallback occurred, and records the fallback in traces (requested vs actual mode).
7. **Given** the user pauses briefly mid-sentence then continues, **When** they resume within the configured pause tolerance, **Then** the system does not treat the pause as end-of-turn and does not send a partial thought to the agent as a finished utterance.
8. **Given** the user finishes a thought and remains silent past the end-of-speech threshold, **When** that silence elapses, **Then** the system treats the utterance as complete and proceeds to generate the agent reply.
9. **Given** voice-to-voice mode is active and a demo tool (e.g. weather) is supported on that path, **When** the tester asks a tool-backed question, **Then** the agent attempts the tool and answers from the result when possible.
10. **Given** voice-to-voice mode is active but a demo tool cannot run on that path, **When** the tester asks a tool-backed question, **Then** the agent gives a clear spoken (and/or visible) limit that the tool is unavailable in this mode—without inventing tool results—while standard mode continues to guarantee full tool behavior.

---

### User Story 4 - Inspectable Session Traces for Debugging Demos (Priority: P2)

A demo operator or developer can open traces for a session—both as a local structured timeline (e.g. JSONL/logs) and in a simple in-app session timeline panel—and see what happened: when the user spoke, when end-of-utterance was decided, what persona/language were applied, major processing stages, and when the agent started/finished speaking. This makes persona bugs, latency, and “why did it cut me off?” diagnosable without guessing.

**Why this priority**: Without traces, persona and latency issues cannot be verified or fixed confidently before a demo.

**Independent Test**: Run one call, open the session’s traces, and confirm turn boundaries, persona/language, and stage timings are visible—without changing wait sound assets.

**Acceptance Scenarios**:

1. **Given** a completed or in-progress session, **When** the operator opens the in-app session timeline (or the local structured timeline for that session), **Then** they can see ordered events for user speech end, agent reply start, and agent reply end (at minimum).
2. **Given** a session with a selected persona and language, **When** viewing traces in-app or in the local timeline, **Then** the applied persona and language for agent turns are visible.
3. **Given** a multi-turn session, **When** viewing traces, **Then** turns are distinguishable so the operator can relate a spoken exchange to a specific turn.
4. **Given** traces are enabled, **When** a normal demo call runs, **Then** tracing does not prevent the call from completing or make the experience unusable for demo purposes.
5. **Given** the operator selected a reply mode via env default or the pre-connect UI toggle, **When** the call is connected, **Then** the active (actual) mode is visible in session status and/or traces and does not change mid-call; if fallback occurred, requested vs actual mode are both visible.
6. **Given** the local timeline sink is unavailable, **When** the operator still uses the call, **Then** the call continues and the in-app panel (if present) shows that traces are unavailable rather than failing the session.

---

### Edge Cases

- What if voice-to-voice mode is selected but credentials or the voice service are unavailable? Auto-fallback to standard mode; show a clear visible warning; record requested vs actual mode in traces—do not silently run a different path.
- What if persona or language metadata is missing when the agent joins? Use a documented safe default and surface the default clearly in traces; do not silently mix UI persona with a different spoken persona.
- What if the user changes avatar/language mid-call? Apply from the next agent utterance (or after the current utterance finishes) without dropping the call; prior context remains.
- What if the user makes a long mid-thought pause (longer than pause tolerance)? The system may finalize the partial utterance; the agent should handle a short/incomplete prompt gracefully and stay ready for the next turn.
- What if the user interrupts (barge-in) while the agent is speaking? Stop or yield agent speech per existing call behavior and accept the new user utterance; context should include what was already said as appropriate for a natural conversation.
- What if transcript generation fails while voice replies still work? Spoken conversation continues; show a clear transcript error/empty state without failing the call.
- What if tracing backend is unavailable? Call continues; operator sees that traces are unavailable (in-app and/or status) rather than a hard call failure; local sink failure MUST NOT drop the call.
- What if a demo tool (e.g. weather) cannot run in voice-to-voice mode? Speak/show a clear limit; do not invent results; full tool behavior remains guaranteed in standard mode.
- What if network or model latency spikes during a demo? Wait feedback remains active until speech starts; traces record the elongated stage so post-demo diagnosis is possible.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST apply the tester-selected agent avatar gender to both on-screen persona and spoken voice presentation for the session.
- **FR-002**: The system MUST apply the tester-selected session language to agent speech for the session.
- **FR-003**: Persona and language selection MUST be successfully delivered to the agent side of the call (not UI-only); if delivery fails, the system MUST fail visibly (clear status/error or documented default recorded in traces)—not silently mismatch.
- **FR-004**: The waiting experience during agent “thinking” MUST use an updated wait cue that replaces the current unsatisfactory waiting sound.
- **FR-005**: Wait feedback MUST stop when agent speech starts and MUST NOT overlap the reply.
- **FR-006**: The product MUST support dual spoken-reply modes selected by an env/feature-flag default plus an optional pre-connect UI toggle: (1) **standard mode** — improved speech→reason→speech with transcript kept off the critical path for starting spoken replies; (2) **low-latency voice-to-voice mode** — speech goes more directly to a voice-capable model path while transcript remains a parallel/side channel. Mode MUST be fixed for the session once the call starts (no mid-call switch), except that an unavailable voice-to-voice path MUST auto-fallback to standard with a visible warning and traced requested vs actual mode.
- **FR-007**: In both modes, producing a transcript MUST NOT be what blocks the start of agent speech on the critical path.
- **FR-008**: The active reply mode MUST be visible to operators (pre-connect selection and/or in-call session status and/or traces) so demos and debugging know which path ran; if fallback occurred, both requested and actual mode MUST be visible.
- **FR-009**: Across multiple turns in one session, in both modes, the agent MUST retain prior conversation context so follow-ups refer to earlier user and agent content correctly.
- **FR-010**: The system MUST distinguish brief mid-utterance pauses from end-of-utterance using a defined silence/end-of-speech behavior so partial thoughts are not routinely sent as finished turns (behavior applies in both modes).
- **FR-011**: Operators MUST be able to view session traces via a local structured timeline (e.g. JSONL/logs) and a simple in-app session timeline panel; traces MUST include turn boundaries, applied persona/language, active reply mode, and timing of major stages (user finished speaking → agent started speaking at minimum).
- **FR-012**: Enabling traces MUST NOT block core call connect/speak/disconnect for demos when tracing is degraded; if the local sink or in-app feed fails, the operator MUST see that traces are unavailable rather than a hard call failure.
- **FR-013**: A readable transcript of the conversation MUST remain available for operator review in both reply modes.
- **FR-014**: The feature MUST remain a focused LiveKit room voice call with a small testing UI; it MUST NOT expand into unrelated product surfaces.
- **FR-015**: In voice-to-voice mode, existing demo tools (e.g. weather lookup) MUST be best-effort: attempt them when the voice path supports them; if a tool cannot run, the agent MUST give a clear spoken and/or visible limit and MUST NOT invent tool results. Standard mode MUST continue to provide full tool behavior for those demo tools.

### Key Entities

- **Voice Session**: One connected call between tester and agent; has persona, language, reply mode, start/end, and ordered turns.
- **Persona Selection**: Avatar gender plus language chosen for the session; must match both UI and spoken agent behavior.
- **Reply Mode Flag**: Env/feature-flag default plus optional pre-connect UI choice between standard speech→reason→speech and low-latency voice-to-voice; fixed for a session once the call starts. If voice-to-voice cannot start, actual mode may be standard after explicit fallback warning (requested mode still recorded).
- **Conversation Turn**: One user utterance and the corresponding agent reply (or refusal), including timing and context linkage to prior turns.
- **End-of-Utterance Decision**: The moment the system decides the user has finished speaking (after silence beyond pause tolerance), distinct from brief mid-thought pauses.
- **Wait Feedback**: Visual and/or audio cue shown/played while the agent is preparing a reply.
- **Session Trace**: Operator-visible record of session events and stage timings for diagnosis and demo readiness, available as a local structured timeline and a simple in-app session timeline panel.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In 10 scripted persona checks (5 male / 5 female across supported languages), at least 9 of 10 show matching on-screen avatar, spoken gender presentation, and language—with no silent UI/agent mismatch.
- **SC-002**: In demo dry-runs, at least 9 of 10 observers rate the waiting cue as acceptable (not distracting or “wrong sound”) compared with the previous waiting sound.
- **SC-003**: Under normal local demo conditions, for clear short questions in **low-latency voice-to-voice mode**, median time from user end-of-speech to agent start-of-speech is at most 2.5 seconds, and at least 90% of such turns start within 4 seconds. **Standard mode** MUST still feel demo-usable: median at most 4 seconds, and at least 90% of such turns start within 6 seconds.
- **SC-004**: In a 5-turn scripted multiturn dialog that requires remembering earlier facts, the agent correctly uses prior context on at least 4 of 5 follow-ups.
- **SC-005**: In pause tests, brief mid-sentence pauses under the configured tolerance do not finalize the turn in at least 9 of 10 trials; intentional end-of-turn silence does finalize within the expected window in at least 9 of 10 trials.
- **SC-006**: After any failed demo call investigation, an operator can identify from traces whether the issue was persona delivery, end-of-utterance timing, or reply-path delay within 2 minutes, for at least 9 of 10 injected fault scenarios.

## Assumptions

- Demo readiness means reliable persona, acceptable wait feedback, multiturn context, inspectable traces, and latency good enough for stakeholder demos—not full enterprise hardening (auth productization, multi-tenant ops, etc.).
- Supported languages and avatar options remain those already exposed by the existing UX feature unless explicitly expanded later.
- The updated waiting sound will be a short, non-jarring ambient/progress cue suitable for demos; exact creative asset can be chosen during planning/implementation.
- Traces are for operators/developers validating demos (session timeline and stage timings), exposed as local structured timeline files/logs plus a simple in-app panel—not a full customer-facing analytics product.
- **Speech finish detection (addresses open question)**: Real-time voice sessions typically treat “user finished speaking” as sustained silence after speech activity (end-of-utterance / turn-taking), not as the first short pause. Brief hesitations stay inside the same user turn; longer silence commits the turn and triggers the agent reply. Exact silence thresholds are tuning parameters validated against SC-005.
- **Multiturn context (addresses open question)**: Regardless of whether replies are produced by a staged speech→reason→speech flow or a native voice-to-voice model path, the session MUST keep a conversation memory/context across turns so the agent can refer to earlier user and agent content. Transcript may be a parallel artifact for humans; context for the agent is a first-class session concern, not “whatever the last audio chunk was.”
- LiveKit remains the realtime room/transport foundation for the call (join, publish, subscribe, disconnect).
- **Dual-mode (resolved)**: Operators choose reply path via env/feature-flag default and an optional pre-connect UI toggle—standard (reliable / closer to today’s POC, improved) vs low-latency voice-to-voice (speech more direct to the model; transcript parallel). Both modes share persona delivery, wait feedback, end-of-utterance behavior, multiturn context, and traces.
- Reply mode is selected before connect (env default and/or UI) and remains stable for that session to avoid mid-call path switching surprises during demos.
- If voice-to-voice is requested but unavailable, the session MUST auto-fallback to standard with a visible warning and traced requested vs actual mode (not a silent path change).
- Improving latency may change how reasoning and speech generation are staged, but orchestration and session behavior MUST stay inspectable and consistent with project governance (explicit agent behavior and testable boundaries).
- Existing general-answer behavior and honest “I don’t know” limits from the prior UX feature remain in effect unless this feature explicitly changes them.
- **Tools in V2V (resolved)**: Demo tools are best-effort in voice-to-voice mode with a clear limit when unavailable; full tool behavior is guaranteed in standard mode. Full tool parity in V2V is not required for demo readiness.

## Out of Scope

- Redesigning the home page or conversation history browser (already specified elsewhere), except where persona/language/trace fixes touch the live call path.
- New agent domains, tools, or knowledge bases beyond what is needed to demo reliable voice conversation.
- Production deployment topology, SSO, billing, or multi-region operations.
- Perfect human-level barge-in and overlapping speech handling beyond practical demo behavior.
