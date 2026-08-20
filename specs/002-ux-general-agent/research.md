# Research: Conversation UX and General Agent Answers

**Feature**: `002-ux-general-agent`  
**Date**: 2026-08-20

## R1 — Agent answering policy (general knowledge vs tools-only)

**Decision**: Instruct the LLM to answer ordinary conversational / general-knowledge questions in short spoken form; use `lookup_weather` when weather is asked; refuse with a clear spoken apology when it cannot help (no applicable knowledge, unsafe professional advice, or missing live data without a tool). Do **not** advertise weather-only in the greeting.

**Rationale**: Matches FR-001–FR-004 and the user’s “answer all human queries” + honest refusal. Keeps the existing demo tool. Avoids a brittle tools-only agent that refuses everything except weather.

**Alternatives considered**:
- Tools-only + refuse otherwise — contradicts “answer all” and makes the POC feel broken for normal chat.
- Add many new tools before general chat — out of POC scope and delays UX value.

## R2 — Passing avatar gender and language to the agent

**Decision**: On Connect, the UI sends `avatarGender` (`male` | `female`) and `sessionLanguage` (BCP-47-ish code, default `en`) into the token request. The token route attaches these as **agent dispatch metadata** (and/or room/participant attributes). The agent reads metadata at session start, maps to a Kokoro voice id, and configures TTS before the greeting.

**Rationale**: Persona must affect the first greeting voice. Dispatch metadata is the natural LiveKit Agents path for per-job config without a new API service.

**Alternatives considered**:
- Env-only `KOKORO_VOICE` — cannot honor per-tester avatar choice.
- Data-channel message after connect — races the automatic greeting.
- Separate HTTP voice API — unnecessary complexity for a POC.

## R3 — Kokoro voice mapping (gender + language)

**Decision**: Add `agent/src/adapters/voice_map.py` with an explicit table, e.g.:

| Gender | Language | Kokoro voice (initial) |
|--------|----------|------------------------|
| female | `en` (default) | `af_heart` (current default) |
| male | `en` | `am_adam` (or nearest available male English voice in Speaches) |
| female/male | other listed langs | Best available Kokoro voice for that lang+gender; fall back to English same-gender if missing |

Document fallbacks in `.env.example` comments. Keep `KOKORO_VOICE` as optional override for debugging (wins over map when set for the process — document clearly; prefer metadata for normal UI flow).

**Rationale**: Speaches/Kokoro already supports gendered voice ids; mapping keeps UI simple (gender + language) without exposing raw voice ids to testers.

**Alternatives considered**:
- Single voice forever — fails FR-009.
- Client-side TTS — breaks LiveKit agent audio path and constitution LiveKit-first voice output.

## R4 — Speaking avatar UI (no video track)

**Decision**: Replace/augment the center audio-visualizer-only tile with a **static gendered avatar illustration** plus CSS/animation for idle vs speaking. Drive speaking state from existing LiveKit agent state (`speaking` / `listening` / `thinking`) already surfaced in the session view.

**Rationale**: Agent does not publish video today; photoreal lip-sync is out of scope. Spec assumes illustration + speaking state, not filmed video.

**Alternatives considered**:
- Publish avatar video from agent — heavy and unnecessary for POC.
- Keep bar visualizer only — fails FR-007/FR-008.

## R5 — Live transcript side panel

**Decision**: Restructure the call stage so the main column holds avatar + controls, and a **dedicated right transcript panel** shows ordered user/agent turns (desktop). Reuse LiveKit `useSessionMessages` as the live source; optionally adapt unused `TranscriptPanel` / `transcript.ts` shapes for display consistency with history.

**Rationale**: Overlay chat fails FR-005 side-panel requirement. Messages already flow via Agents transcription streams—no custom data channel needed for live text.

**Alternatives considered**:
- Keep overlay toggle only — does not meet side-panel acceptance.
- Custom transcript WebSocket — duplicates LiveKit streams.

## R6 — Wait fillers while thinking

**Decision**: When agent state is `thinking` (and optionally after user final transcript until `speaking`), show a visible filler (pulse/shimmer on avatar or stage) and play a short, quiet waiting loop/tone if audio output is allowed. Stop filler immediately on `speaking` or session end. Skip or cap filler if thinking ends under ~300–500ms to avoid flash.

**Rationale**: UI already labels “Thinking…”; extending that state into perceptible multimodal feedback satisfies FR-010/FR-011 without agent changes. Visual-only fallback if autoplay is blocked.

**Alternatives considered**:
- Agent-generated filler speech (“One moment…”) — adds latency and can interrupt barge-in semantics.
- No audio cue — weaker for “nothing happening” complaint; keep visual minimum.

## R7 — Previous conversations persistence

**Decision**: Persist `ConversationRecord` JSON in `localStorage` (keyed namespace e.g. `livekit-v2v-poc:conversations`). On End call / disconnect, if there is at least one transcript turn, upsert a record (id, startedAt, endedAt, label/preview, avatarGender, language, turns[]). Home lists newest first; click opens read-only transcript view. Cap list size (e.g. 50) with FIFO eviction.

**Rationale**: Spec assumes same-browser/device storage; no auth or DB in POC.

**Alternatives considered**:
- Server DB — out of scope.
- sessionStorage only — lost on tab close; worse for “previous conversations.”
- IndexedDB — fine later; localStorage is enough for small transcript POC volumes.

## R8 — Creative home within “small UI”

**Decision**: Redesign `welcome-view` as a single composition: brand/product presence, short supporting line, primary Start/Connect CTA, avatar + language chooser, and a previous-conversations section (empty state when none). Avoid marketing dashboards, stats strips, or multi-card clutter.

**Rationale**: Meets FR-012–FR-014 while staying validation-focused (constitution VI scoped expansion).

**Alternatives considered**:
- Multi-route marketing site — out of scope.
- Leave bare Connect button — fails creative home + history stories.

## R9 — Session language (minimal)

**Decision**: Ship a small language selector on home (at least `en`; add 1–2 more only if Speaches/Kokoro voices are confirmed available in the local stack). Pass selection with avatar metadata. STT language hint: set when the Agents/STT adapter supports it; otherwise English STT remains acceptable for POC with documented limitation.

**Rationale**: FR-009 ties voice to language; full i18n STT matrix is not required for acceptance if English works and mapping/fallbacks are documented.

**Alternatives considered**:
- Auto-detect language from first utterance — nice-to-have; unreliable for greeting voice selection.
- Hardcode English only — weaker vs “speak as per language,” but acceptable fallback if only English voices work locally.

## Resolved clarifications

All Technical Context items resolved; no remaining NEEDS CLARIFICATION blockers for planning.
