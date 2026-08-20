# Feature Specification: LiveKit Voice-to-Voice Agent Testing POC

**Feature Branch**: `001-livekit-v2v`

**Created**: 2026-08-20

**Status**: Draft

**Input**: User description: "I would like to do POC to use Livekit for voice to voice communication bitween human and agent and it should be production ready and it also has UI application while use this User can do testing"

## Clarifications

### Session 2026-08-20

- Q: Should the agent speak a short greeting automatically when the call connects, or wait until the tester speaks first? → A: Agent greets automatically soon after connect
- Q: Should the testing UI show live conversation text (what the tester said and what the agent replied), or only connection controls and audio? → A: Show live transcripts for tester and agent turns
- Q: If the network drops briefly during an active call, should the session try to recover automatically, or fail immediately with a clear error so the tester can reconnect? → A: Fail immediately with a clear error and require manual reconnect
- Q: If the agent never joins after the tester connects, how long should the UI wait before showing a clear failure? → A: Fail within about 30 seconds if the agent never joins
- Q: For this POC feature, must the agent be able to use at least one demo tool during a call (for example answering a lookup-style question), or is plain conversational voice enough for acceptance? → A: At least one demo tool is required for acceptance

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Connect and Hold a Voice Conversation (Priority: P1)

A tester opens the UI, connects to a voice session, speaks to an agent with their microphone, and hears spoken replies in a continuous conversation until they end the call.

**Why this priority**: This is the core POC value—proving human↔agent voice-to-voice interaction works end to end.

**Independent Test**: Can be fully tested by connecting once, receiving the automatic greeting, speaking a follow-up, receiving an audible agent reply, continuing for at least two user turns, then ending the call—without needing multi-user features.

**Acceptance Scenarios**:

1. **Given** the tester is on the UI in a disconnected state, **When** they start a call and grant microphone access, **Then** the UI shows a connected session and an agent is present in the call.
2. **Given** the tester has connected successfully, **When** no agent joins within about 30 seconds, **Then** the UI shows a clear failure and the session is not left hanging indefinitely.
3. **Given** a newly connected session with an agent present, **When** the agent is ready, **Then** the agent speaks a short greeting automatically without requiring the tester to speak first.
4. **Given** a connected session with an agent present, **When** the tester speaks a clear utterance and finishes speaking, **Then** the agent produces an audible spoken response related to what was said.
5. **Given** a connected multi-turn conversation, **When** the tester asks a follow-up that depends on prior context in the same call, **Then** the agent’s reply reflects that prior context.
6. **Given** a connected session, **When** the tester ends the call, **Then** the UI returns to a disconnected state and media capture stops.

---

### User Story 2 - Validate Session Lifecycle in the UI (Priority: P2)

A tester uses the UI as a control surface to observe connection status, reconnect after ending a call, and confirm the session is healthy enough for repeated testing.

**Why this priority**: Testers need reliable connect/disconnect and status visibility to run the POC repeatedly without guessing what failed.

**Independent Test**: Can be tested by connecting, verifying status, ending the call, reconnecting, and confirming a second successful session—without requiring a long conversation.

**Acceptance Scenarios**:

1. **Given** the tester is disconnected, **When** they connect, **Then** the UI clearly shows connecting and then connected (or a clear failure reason if connection fails).
2. **Given** the tester is connected, **When** they disconnect, **Then** the UI shows disconnected and they can connect again without restarting the application.
3. **Given** a connection attempt fails (for example, backend unavailable), **When** the failure occurs, **Then** the UI shows an actionable error and remains safe to retry.
4. **Given** a connected session, **When** the network drops during the call, **Then** the UI immediately shows a clear failure state and requires the tester to reconnect manually (no silent auto-recover).

---

### User Story 3 - Inspect Live Transcripts While Testing (Priority: P2)

A tester watches live conversation text for both their speech and the agent’s replies so they can confirm what was understood during a call.

**Why this priority**: Transcripts make voice testing diagnosable without external tooling while keeping the UI focused on validation.

**Independent Test**: Can be tested by connecting, completing at least one spoken exchange (including the greeting), and confirming both sides’ text appear in the UI.

**Acceptance Scenarios**:

1. **Given** a connected session, **When** the agent speaks its automatic greeting, **Then** the UI shows the greeting text as an agent turn.
2. **Given** a connected session, **When** the tester speaks a clear utterance that is recognized, **Then** the UI shows the tester’s transcript for that turn.
3. **Given** a connected session, **When** the agent replies, **Then** the UI shows the agent’s reply text for that turn.

---

### User Story 4 - Interrupt and Recover During Agent Speech (Priority: P3)

A tester can interrupt the agent while it is speaking, then continue the conversation naturally so the call does not get stuck.

**Why this priority**: Real voice conversations need barge-in; without it, testing feels unnatural and can appear broken.

**Independent Test**: Can be tested by prompting a longer agent reply, speaking over it, and confirming the agent stops or yields and then responds to the new utterance.

**Acceptance Scenarios**:

1. **Given** the agent is speaking, **When** the tester starts speaking over the agent, **Then** the agent speech stops or yields promptly and the new user utterance is handled.
2. **Given** an interrupted turn, **When** the conversation continues, **Then** the session remains connected and subsequent turns still work.

---

### User Story 5 - Exercise One Demo Tool by Voice (Priority: P2)

A tester asks a spoken question that requires the agent to use at least one demo tool, then hears a spoken answer that reflects the tool result (and sees related transcript text).

**Why this priority**: Tool use is required for acceptance to prove the agent can act during a live voice call, not only chat.

**Independent Test**: Can be tested by connecting, asking one known tool-triggering question, and confirming the spoken (and transcribed) reply includes the tool-backed answer.

**Acceptance Scenarios**:

1. **Given** a connected session with agent ready, **When** the tester asks a clear spoken question that requires the demo tool, **Then** the agent uses the tool and returns a spoken answer that reflects the tool result.
2. **Given** a successful tool-backed turn, **When** the reply is delivered, **Then** the UI transcript shows the tester question and the agent’s tool-informed answer.

---

### Edge Cases

- What happens when the tester denies microphone permission? The UI MUST show a clear error and MUST NOT appear connected.
- What happens if the agent never joins or leaves mid-call? If the agent never joins within about 30 seconds after the tester connects, the UI MUST show a clear failure. If the agent leaves mid-call, the UI MUST show a clear failure and require manual reconnect.
- What happens on temporary network interruption during a call? The session MUST fail immediately with a clear user-visible error and require manual reconnect (no automatic recovery).
- What happens if the tester remains silent for a long period after connecting? The session stays open until the tester disconnects or another failure occurs (no idle auto-hangup in this POC).
- What happens if the tester rapidly connects and disconnects repeatedly? Each cycle MUST still end in a clean disconnected state without requiring an app restart.
- How does the system behave when speech is unintelligible or mostly noise? The agent MUST NOT crash the session; it MAY ask the tester to repeat, and no false tool call is required.
- What happens if the demo tool fails? The agent MUST give a clear spoken failure/fallback response and the session MUST remain usable for further conversation.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST enable realtime voice-to-voice communication between one human tester and one agent in a shared voice session.
- **FR-002**: Testers MUST be able to start a voice session from a web UI and grant microphone access as part of joining.
- **FR-003**: Testers MUST be able to end a voice session from the UI, after which microphone capture stops and the session is closed cleanly.
- **FR-004**: The system MUST deliver the tester’s spoken audio to the agent path and return the agent’s spoken audio to the tester with conversational turn-taking.
- **FR-005**: The system MUST support multi-turn conversation within a single session so later replies can use earlier context from that same call.
- **FR-006**: The UI MUST show clear session status at least for disconnected, connecting, connected, and failed states.
- **FR-007**: The UI MUST allow reconnect after a normal disconnect without requiring an application restart.
- **FR-008**: When join, media, or agent readiness fails, the system MUST surface a clear, user-visible error suitable for testing diagnosis.
- **FR-009**: The system MUST support barge-in so the tester can interrupt agent speech and continue the conversation.
- **FR-010**: The system MUST keep transport (realtime voice session) concerns separable from agent reasoning so session lifecycle remains predictable and testable.
- **FR-011**: The POC MUST be structured for production-ready quality: explicit failure handling, deterministic session lifecycle, and boundaries that can be validated independently—even though feature breadth remains POC-scoped.
- **FR-012**: The UI MUST remain intentionally small and focused on test controls and session visibility needed to validate the voice workflow (not a full product surface).
- **FR-013**: After a successful connect with agent ready, the agent MUST speak a short greeting automatically without waiting for the tester’s first utterance.
- **FR-014**: The UI MUST show live transcripts for both tester utterances and agent replies during an active session.
- **FR-015**: If the network drops during an active call, the system MUST fail the session immediately with a clear user-visible error and MUST NOT auto-recover; the tester MUST reconnect manually.
- **FR-016**: If no agent joins within about 30 seconds after the tester connects, the system MUST fail the session with a clear user-visible error (no indefinite wait).
- **FR-017**: The agent MUST expose at least one demo tool that a tester can invoke by spoken request during a call, and the spoken reply MUST reflect the tool result when the tool succeeds.

### Key Entities

- **Voice Session**: A single timed connection between tester and agent, with status (disconnected, connecting, connected, failed) and start/end lifecycle.
- **Human Tester**: The person using the UI, providing microphone audio and listening to agent replies.
- **Agent Participant**: The automated conversational counterpart that listens, reasons, and speaks within the same session.
- **Conversation Turn**: A unit of exchange (user utterance → agent response) within a session, including interruptible agent speech and associated transcript text when available.
- **Session Status Event**: A user-visible change in connection or readiness used for testing and diagnosis.
- **Transcript Entry**: A user-visible text line for a turn, attributed to either the tester or the agent.
- **Demo Tool**: A single callable agent capability used during voice testing to prove tool-backed answers (for example a simple lookup).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A tester can go from opening the UI to hearing the agent’s automatic greeting in under 30 seconds on a healthy local setup (excluding first-time environment bootstrap), without speaking first.
- **SC-002**: In at least 9 of 10 healthy test runs, a tester can complete a 2-turn voice conversation (user speaks twice; agent replies twice) without needing to restart the app.
- **SC-003**: After ending a call, 100% of successful disconnects return the UI to a disconnected state with microphone capture stopped, and a subsequent reconnect succeeds without app restart in at least 9 of 10 attempts.
- **SC-004**: When microphone permission is denied or the backend is unavailable, 100% of such failures show a clear on-screen error instead of a silent hang.
- **SC-005**: When a tester interrupts agent speech, agent audio yields within 1 second in at least 8 of 10 interruption attempts, and the conversation remains usable afterward.
- **SC-006**: Testers report they can validate the core voice workflow using only the provided UI controls (connect, disconnect, speak/listen, status, transcripts) without needing developer tooling for the happy path.
- **SC-007**: In at least 9 of 10 healthy successful turns, the corresponding transcript entry for that speaker appears in the UI by the time the turn’s audio completes.
- **SC-008**: When a mid-call network drop is induced in testing, 100% of runs show a failed/disconnected error state without silent recovery, and a manual reconnect remains possible afterward.
- **SC-009**: When the agent is unavailable after connect, 100% of runs show a clear failure within about 30 seconds rather than hanging indefinitely.
- **SC-010**: In at least 9 of 10 healthy runs, a tester can trigger the demo tool by voice and receive a spoken answer that reflects the tool result without restarting the app.

## Assumptions

- This POC targets a single human tester and a single agent in one session at a time (no multi-party conferencing).
- Realtime voice rooms are the mandated transport for this POC (human and agent join the same session for audio), using LiveKit as specified by the product owner.
- Agent reasoning follows an explicit stateful workflow consistent with project governance and remains separable from the voice transport.
- The UI is a lightweight local web app for testing, not a polished consumer product.
- “Production ready” for this POC means reliable session lifecycle, clear errors, clean media teardown, barge-in, and maintainable structure—not enterprise multi-tenancy, SSO, or large-scale concurrency.
- Speech understanding and synthesis services are available in the local test environment; exact vendor choices are an implementation concern.
- At least one demo tool is required for feature acceptance; exact tool topic is an implementation concern as long as testers can trigger it by a clear spoken request.
- Desktop browser testing on the same machine as the local stack is the primary validation path for this POC.
- Authentication for the POC remains developer/local-access oriented; end-user account systems are out of scope.
- Idle sessions do not auto-hang up; the tester ends the call explicitly.
- Multi-party calls, mobile-native apps, SSO, and persistent cross-session memory are out of scope for this feature.
