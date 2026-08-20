# Specs Index

Feature specifications for this repository live under `specs/`.  
Governance: [`.specify/memory/constitution.md`](../.specify/memory/constitution.md)

| ID | Feature | Status | Spec | Plan | Tasks |
|----|---------|--------|------|------|-------|
| `001-livekit-v2v` | LiveKit voice-to-voice agent testing POC | Draft / planned | [spec.md](./001-livekit-v2v/spec.md) | [plan.md](./001-livekit-v2v/plan.md) | [tasks.md](./001-livekit-v2v/tasks.md) |
| `002-ux-general-agent` | Conversation UX and general agent answers | Implemented | [spec.md](./002-ux-general-agent/spec.md) | [plan.md](./002-ux-general-agent/plan.md) | [tasks.md](./002-ux-general-agent/tasks.md) |

## Active feature

Configured in [`.specify/feature.json`](../.specify/feature.json):

- **Directory**: `specs/002-ux-general-agent`
- **Branch**: `002-ux-general-agent` (optional; create when planning/implementing)

## Artifact map (per feature)

```text
specs/<id>-<name>/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
├── checklists/
└── tasks.md          # created by /speckit-tasks
```

## How to add a feature

1. `/speckit-specify` — create `spec.md`
2. `/speckit-clarify` — optional decisions
3. `/speckit-plan` — plan + design artifacts
4. `/speckit-tasks` — implementation task breakdown
5. `/speckit-implement` — execute tasks
