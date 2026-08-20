<!--
Sync Impact Report
Version change: 1.0.0 -> 1.1.0
Modified principles:
- I. LangGraph Architecture First -> II. LangGraph Architecture First (renumbered)
- II. Clean Python Design Patterns -> III. Clean Python Design Patterns (renumbered)
- III. Safe Secrets Handling -> IV. Safe Secrets Handling (renumbered)
- IV. Human-Gated Operations -> V. Human-Gated Operations (renumbered)
- V. Small UI, Real Workflow Validation -> VI. Small UI, Real Workflow Validation (expanded for voice)
Added sections:
- I. LiveKit Voice-to-Voice First (new principle)
Removed sections:
- None
Follow-up TODOs:
- None
-->
# Livekit V2V POC Constitution

## Core Principles

### I. LiveKit Voice-to-Voice First
Real-time voice communication MUST be built on LiveKit rooms, participants, audio tracks, and
WebRTC lifecycle semantics. Agent and browser clients MUST connect through explicit join, publish,
subscribe, and disconnect flows rather than custom socket hacks. Speech input and output MUST be
treated as first-class media paths: STT ingestion, LLM reasoning, and TTS playback MUST remain
decoupled from transport concerns via adapters. Rationale: this POC validates voice-to-voice agent
behavior; LiveKit is the non-negotiable realtime foundation.

### II. LangGraph Architecture First
All agent behavior MUST be modeled as explicit LangGraph state, nodes, edges, and termination
rules rather than ad hoc control flow scattered across files. LangChain components MAY be used for
prompts, tools, models, and memory adapters, but orchestration MUST remain production-ready
LangGraph usage with deterministic state transitions, well-defined retries, and clear failure
handling. Voice events (transcripts, tool calls, response chunks) MUST map cleanly into graph state
without bypassing the orchestration layer. Rationale: LangGraph provides inspectable, extensible
agent logic that complements LiveKit's realtime transport.

### III. Clean Python Design Patterns
Python code MUST follow clear production-oriented design patterns: separation of domain logic,
orchestration, infrastructure adapters, and interface code; dependency injection at module or
object boundaries; and single-responsibility classes or functions. Business logic MUST NOT be
hidden inside scripts, route handlers, or UI glue code. LiveKit agent handlers, STT/TTS
adapters, and LangGraph nodes MUST live in distinct, testable modules. Rationale: even in a POC,
maintainable boundaries reduce rework when promoting experiments into durable systems.

### IV. Safe Secrets Handling
Secrets and critical files MUST be treated as off-limits unless the user explicitly grants access
for a specific action. The project MUST NOT read `.env` files, credentials, tokens, or equivalent
sensitive artifacts during normal implementation, review, or debugging flows. Configuration
examples, env templates, and documented variable names MAY be referenced instead of real secret
values. Rationale: POC speed does not justify accidental exposure of credentials or hidden
configuration.

### V. Human-Gated Operations
Before executing commands, opening unfamiliar folders, or accessing files beyond the minimum
required scope, the operator MUST ask for user approval and wait for confirmation. Once approval
is granted, work MUST stay within the approved scope and MUST re-ask if the scope changes
materially. Rationale: this project prioritizes explicit operator control over automation
convenience.

### VI. Small UI, Real Workflow Validation
The UI MUST remain intentionally small and focused on validating the voice-to-voice agent workflow
end to end: connect/disconnect, mic permission, room status, agent presence, transcript or state
visibility when useful, and outcome checks. Visual complexity, styling churn, or speculative
product features MUST NOT outrank the POC's core validation goals. Rationale: the interface exists
to test LiveKit + LangGraph orchestration in a real call flow, not to become a parallel product
effort.

## Delivery Constraints

This project is a POC for LiveKit voice-to-voice communication orchestrated with LangGraph and
LangChain, with a lightweight UI for testing. New work MUST preserve that scope. Prefer thin
adapters around LiveKit SDKs, LLM providers, STT/TTS services, tools, and UI events so transport
and orchestration logic remain portable. Production readiness in this constitution means
predictable structure, explicit errors, testable boundaries, and documented assumptions; it does
not require enterprise-scale feature breadth.

## Development Workflow

Changes MUST begin by identifying the target voice workflow, the LiveKit room/participant
lifecycle, the LangGraph state shape, and the UI touchpoints needed to validate it.
Implementations SHOULD reuse existing project patterns before introducing new abstractions.
Verification MUST focus on the highest-value checks for the affected behavior—connect/disconnect,
audio path integrity, graph state transitions—with targeted tests added when they materially
reduce regression risk. When secrets, external systems, or privileged paths are involved, use
mocks, stubs, sample data, or user-provided confirmation instead of direct access.

## Governance

This constitution overrides conflicting local habits for this repository. Amendments MUST be
documented in `.specify/memory/constitution.md`, include a short rationale, and update the
version according to semantic intent: MAJOR for incompatible governance changes, MINOR for new
or materially expanded principles, and PATCH for clarifications only. Every review of specs,
plans, tasks, or implementation MUST check compliance with these principles, especially
LiveKit-first voice transport, LangGraph-first orchestration, secure secret handling, and human
approval gates.

**Version**: 1.1.0 | **Ratified**: 2026-08-19 | **Last Amended**: 2026-08-19
