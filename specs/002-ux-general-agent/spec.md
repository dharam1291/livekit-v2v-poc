# Feature Specification: Conversation UX and General Agent Answers

**Feature Branch**: `002-ux-general-agent`

**Created**: 2026-08-20

**Status**: Draft

**Input**: User description: "Extend the application with UI improvements (separate transcript panel, gendered speaking avatar matched to language, wait-time fillers while the agent is thinking, creative home page with previous conversations and reopenable transcripts) and backend improvement so the agent answers general human queries rather than advertising weather-only; if it cannot help, it clearly says it does not have knowledge for that request."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ask General Questions and Get Clear Limits (Priority: P1)

A tester starts a voice call, hears a welcome that does not claim the agent is weather-only, asks everyday questions, and receives spoken answers when the agent can help. When the agent cannot help, it clearly says it does not have knowledge for that request instead of inventing an answer or staying silent.

**Why this priority**: The core agent behavior change unblocks useful testing beyond a single demo capability and sets honest expectations when help is unavailable.

**Independent Test**: Connect, hear the welcome, ask one answerable general question and one question the agent cannot help with; verify a helpful spoken reply for the first and a clear spoken refusal for the second—without needing the new home page or avatar.

**Acceptance Scenarios**:

1. **Given** a newly connected session with the agent present, **When** the agent greets the tester, **Then** the welcome does not state that the agent only provides weather (or similar single-capability claims).
2. **Given** a connected session, **When** the tester asks a clear general question the agent can answer, **Then** the agent responds with a relevant spoken answer.
3. **Given** a connected session, **When** the tester asks something the agent cannot help with, **Then** the agent speaks a clear apology that it cannot answer because it does not have knowledge about that request.
4. **Given** a connected session, **When** the tester asks a question that needs a specialized capability the agent does have (for example a live lookup the product already supports), **Then** the agent still uses that capability and answers correctly.
5. **Given** a connected session, **When** the tester follows up after a refusal, **Then** the conversation continues normally and the agent can still answer later questions it can help with.

---

### User Story 2 - Follow the Live Transcript in a Side Panel (Priority: P1)

During an active call, a tester sees the conversation transcript in a dedicated panel (typically on the right) separate from the main call controls and avatar area, so speech and text can be reviewed side by side.

**Why this priority**: Separating transcript from the call stage makes testing diagnosable and matches the requested layout for ongoing validation.

**Independent Test**: Start a call, complete at least one exchange (including greeting), and confirm user and agent turns appear in a distinct transcript panel without relying on conversation history or fillers.

**Acceptance Scenarios**:

1. **Given** a connected session, **When** the agent or tester produces recognizable speech, **Then** the corresponding text appears in a dedicated transcript panel separate from the primary call stage.
2. **Given** an active call with multiple turns, **When** new turns arrive, **Then** the transcript panel updates in order and remains readable while the call continues.
3. **Given** a connected session on a typical desktop-width layout, **When** the tester views the call screen, **Then** the transcript panel is positioned to the side (right preferred) so the main call area stays uncluttered.

---

### User Story 3 - See a Speaking Avatar Matched to Gender and Language (Priority: P2)

A tester chooses a male or female agent avatar. While the agent speaks, the avatar visibly “speaks” (animated speaking state). The spoken voice presentation aligns with the selected gender and the language in use for the session.

**Why this priority**: A gendered speaking avatar makes the voice session feel present and clearer during demos, without blocking core call success.

**Independent Test**: Select each avatar option, start a call, trigger agent speech in the session language, and confirm speaking animation plus gender-appropriate voice presentation—without needing conversation history.

**Acceptance Scenarios**:

1. **Given** the tester is preparing or starting a call, **When** they choose a male or female avatar, **Then** that choice is clearly applied for the session.
2. **Given** a selected avatar and a connected session, **When** the agent is speaking, **Then** the avatar shows an active speaking state.
3. **Given** a selected avatar and a connected session, **When** the agent is not speaking, **Then** the avatar returns to a non-speaking (idle/listening) state.
4. **Given** a male or female avatar selection and a session language, **When** the agent speaks, **Then** the voice presentation matches the selected gender and the language in use for that session.

---

### User Story 4 - Hear or See Wait Feedback While the Agent Is Thinking (Priority: P2)

While the agent is processing and has not yet started its spoken reply, the tester is not left in a silent “nothing is happening” state: the UI (and optionally light audio) provides fillers such as a short waiting tune, animation, or other clear in-progress cue until the response begins.

**Why this priority**: Perceived dead air is a frequent POC complaint; wait feedback improves trust that the session is still working.

**Independent Test**: Ask a question that takes noticeable processing time and confirm filler feedback appears before the reply starts, then stops when speech begins—without needing history or avatar gender changes.

**Acceptance Scenarios**:

1. **Given** a connected session, **When** the tester finishes a question and the agent is still preparing a reply (no agent speech yet), **Then** the UI shows or plays clear wait feedback (visual filler and/or a short waiting sound).
2. **Given** wait feedback is active, **When** the agent begins speaking its reply, **Then** the wait feedback stops so it does not overlap the reply.
3. **Given** a very fast reply, **When** the agent starts speaking almost immediately, **Then** wait feedback is brief or skipped so it does not feel artificial or delay the answer.

---

### User Story 5 - Browse Previous Conversations from a Creative Home Page (Priority: P3)

From a more engaging home page, a tester sees a list of previous conversations, opens one, and reviews that conversation’s transcript without needing to reconstruct it from memory.

**Why this priority**: History improves repeat testing and demos, but the live call and agent behavior deliver more immediate POC value.

**Independent Test**: Complete at least one call that produces a transcript, return to the home page, open that conversation, and verify the prior transcript is visible—without needing avatar or filler behavior.

**Acceptance Scenarios**:

1. **Given** the tester opens the application home, **When** the home page loads, **Then** it presents a creative, inviting entry experience (not only a bare connect button) and a clear path to start a new call.
2. **Given** the tester has completed at least one prior conversation that produced a transcript, **When** they view the home page, **Then** they see that conversation listed among previous conversations.
3. **Given** a listed previous conversation, **When** the tester selects it, **Then** they can view that conversation’s transcript.
4. **Given** no previous conversations exist, **When** the tester views the home page, **Then** the history area shows an empty state and does not block starting a new call.

---

### Edge Cases

- What happens if the transcript panel has no turns yet (connected but silent)? Show an empty state in the panel without looking broken.
- How does the system handle avatar selection changing mid-call? Apply the new avatar (and matching voice presentation) from the next agent utterance, or defer change until the current utterance finishes—without crashing the session.
- What happens if wait feedback fails to play (e.g., sound blocked)? Visual filler alone MUST still indicate processing.
- How does the system handle a very long transcript during a live call? The panel remains usable (scrollable) and does not hide essential call controls.
- What happens if a previous conversation’s transcript cannot be loaded? Show a clear error for that item and keep the rest of the home page usable.
- How does the agent handle ambiguous or empty speech input? Do not treat silence/noise as a knowledge refusal; stay ready for the next clear utterance.
- What happens when a question is partly answerable? Prefer a partial helpful answer plus an honest limit, rather than a full refusal or a fabricated completion.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The agent MUST welcome the tester without claiming that weather (or any single demo capability) is its only purpose.
- **FR-002**: The agent MUST attempt to answer general human questions it can help with during a voice session.
- **FR-003**: When the agent cannot help with a request, it MUST speak a clear apology that it cannot answer because it does not have knowledge about that request (or equivalent clear wording).
- **FR-004**: Existing specialized capabilities the agent already has MUST remain usable when a question needs them.
- **FR-005**: The call experience MUST show live conversation transcript in a dedicated panel separate from the main call stage (right-side placement preferred on desktop-width layouts).
- **FR-006**: The transcript panel MUST show both tester and agent turns in conversational order during an active session.
- **FR-007**: Users MUST be able to choose a male or female agent avatar before or at the start of a session.
- **FR-008**: While the agent is speaking, the selected avatar MUST show a speaking state; when the agent is not speaking, it MUST show a non-speaking state.
- **FR-009**: Agent voice presentation MUST align with the selected avatar gender and the language in use for the session.
- **FR-010**: While the agent is preparing a reply and has not started speaking, the experience MUST provide perceptible wait feedback (visual filler and/or a short waiting sound).
- **FR-011**: Wait feedback MUST stop when the agent’s spoken reply begins.
- **FR-012**: The home experience MUST be more creative and engaging than a minimal connect-only screen while still making “start a new conversation” obvious.
- **FR-013**: The home experience MUST list previous conversations available to the tester.
- **FR-014**: Selecting a previous conversation MUST let the tester view that conversation’s transcript.
- **FR-015**: Completing a conversation that produced transcript content MUST make that conversation available in the previous-conversations list for later review.
- **FR-016**: The enhancements MUST preserve the existing ability to connect, converse by voice, and disconnect for POC validation.

### Key Entities

- **Voice Session**: An active human–agent call with connection state, language in use, avatar selection, and live turns.
- **Transcript Turn**: One spoken contribution from the tester or the agent, with role, text, and ordering within a conversation.
- **Conversation Record**: A saved prior session summary for the home list (identity, time or label, and its transcript turns).
- **Agent Avatar**: Male or female visual persona with idle and speaking states, paired with gender-aligned voice presentation.
- **Wait Feedback**: Temporary visual and/or audio cue shown while a reply is being prepared.
- **Knowledge Boundary Response**: The spoken refusal used when the agent cannot help with a request.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In a scripted test of 5 general questions the agent can help with, at least 4 receive relevant spoken answers (80%+).
- **SC-002**: In a scripted test of 5 questions the agent cannot help with, 100% receive a clear spoken “cannot answer / no knowledge” style refusal rather than a fabricated answer or silence.
- **SC-003**: After connect, testers can locate the live transcript in a dedicated side panel within 5 seconds without hunting through unrelated controls.
- **SC-004**: During agent speech, observers can tell the avatar is in a speaking state within 1 second of speech start in at least 9 of 10 trials.
- **SC-005**: For replies that take longer than about 1.5 seconds to start, wait feedback is perceptible before speech begins in at least 90% of trials.
- **SC-006**: After at least one completed conversation, testers can open the home page and view that conversation’s transcript in under 30 seconds.
- **SC-007**: At least 8 of 10 first-time testers correctly identify how to start a new call and how to open a previous transcript from the home page without coaching.

## Assumptions

- This feature extends the existing voice-to-voice testing POC; it does not introduce multi-user accounts, billing, or a full customer-facing product shell.
- “General human queries” means ordinary conversational and knowledge-style questions suitable for a demo agent, not domain-expert professional advice (medical, legal, financial advice remains out of scope and may be refused).
- When a specialized live capability exists (for example weather-style lookup already in the POC), the agent continues to use it for matching questions; refusals apply when the agent truly cannot help.
- Avatar gender is an explicit tester choice (male or female), not inferred from the microphone.
- “Avatar speaks as per language” means speaking animation plus voice presentation consistent with the selected gender and the session’s language—not photoreal lip-sync or filmed video.
- Wait feedback may be visual-only if sound is blocked; a short waiting sound is preferred when audio output is available but must not drown out the eventual reply.
- Previous conversations for this POC are stored for the tester on the same browser/device used for testing (no cross-device account sync required).
- Creative home-page treatment stays within a focused testing UI: atmosphere and history are allowed; large unrelated marketing modules are not.
- Desktop-width layout is the primary validation target for the right-side transcript panel; smaller widths may stack the transcript below or in an accessible alternate layout while keeping it separate from the main call stage.
- Constitution principle “small UI” is interpreted as keeping the UI validation-focused; the requested creative home, avatar, fillers, and history are in scope because they directly improve workflow validation and demo clarity.
