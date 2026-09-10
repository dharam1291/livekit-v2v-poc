# Contract: Wait Feedback

**Feature**: `003-demo-ready-v2v`  
**Surface**: Next.js call stage (`WaitFeedback`)  
**Updates**: `specs/002-ux-general-agent/contracts/ui-call-stage.md` wait-feedback row

## Behavior

| Rule | Detail |
|------|--------|
| Trigger | Agent state indicates thinking / awaiting reply (no agent speech yet) |
| Start delay | ~450ms (skip if reply starts sooner) |
| Audio | Play soft looped asset from `web/public/` (replaces oscillator) |
| Visual | Always show progress cue when waiting |
| Stop | Immediately when agent speaking begins; never overlap reply |
| Audio blocked | Visual alone still required |

## Non-goals

- Agent-side hold music on the TTS track.
- Personalized per-language wait jingles (optional later).

## Acceptance mapping

| Spec | Proof |
|------|-------|
| FR-004–005, SC-002 | New cue during think; stops on speech; observers prefer over old tone |
