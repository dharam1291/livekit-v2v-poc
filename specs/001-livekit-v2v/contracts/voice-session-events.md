# Contract: Voice Session Events

**Feature**: `001-livekit-v2v`  
**Participants**: Web UI ↔ LiveKit room ↔ Agent worker

## Purpose

Define the observable session events the UI and agent must honor for acceptance testing.

## Lifecycle events (logical)

| Event | Direction | UI effect |
|-------|-----------|-----------|
| `session.connecting` | local | Status = connecting |
| `session.connected` | room | Status = connected; start agent-join timer (~30s) |
| `agent.joined` | room participant | `agent_present=true`; cancel join timer; allow greeting |
| `agent.greeting` | agent → room audio + text | Play audio; append agent transcript |
| `tester.speech_final` | STT → agent/UI | Append tester transcript |
| `agent.reply` | agent → room | Play audio; append agent transcript |
| `agent.tool_result` | agent internal → reply | Reply text reflects tool; optional transcript annotation |
| `barge_in` | tester speech during agent TTS | Agent audio yields; new tester turn handled |
| `session.network_failed` | transport | Status = failed immediately; no auto-recover |
| `session.agent_timeout` | local timer | Status = failed if no agent in ~30s |
| `session.disconnected` | local/user | Status = disconnected; mic stopped |

## Fail-fast rules

1. Any mid-call transport loss → `session.network_failed` (not silent reconnect).
2. Agent absent past deadline → `session.agent_timeout`.
3. Mic permission denied → error before `session.connected`.

## Transcript payload (logical)

```json
{
  "speaker": "tester | agent",
  "text": "string",
  "turnId": "string",
  "toolName": "string | null"
}
```

Delivery mechanism may use LiveKit data messages, agent transcription events, or UI hooks from the Agents components stack—implementation choice—as long as both speakers appear live in the UI.
