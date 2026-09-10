# Voice agent (LiveKit + LangGraph)

Python agent for the local **LiveKit voice-to-voice POC**. It joins a LiveKit room, greets in the UI-selected language, and answers by voice.

Prefer starting the full stack from the repo root: `./start_app.sh`. This folder is the agent process only.

## Capabilities

| Mode | Pipeline |
|------|----------|
| **Standard** (default) | Speaches Whisper STT → chat LLM (OpenAI or Azure/PowerProxy) → Speaches Kokoro TTS |
| **Voice-to-voice** | OpenAI/Azure Realtime speech path; falls back to standard if Realtime WS fails or credentials are missing |

Also:

- **Persona** — avatar gender + language from UI metadata map to a Kokoro voice
- **LangGraph** — session state, greeting, turn tracking
- **Tool** — `lookup_weather` in standard mode (best-effort / limited in voice-to-voice)
- **EOU** — configurable endpointing delays (`MIN_` / `MAX_ENDPOINTING_DELAY_MS`)
- **Mic gate** — reduces barge-in while the agent speaks
- **Traces** — JSONL under `TRACE_DIR` plus OTLP → Jaeger when enabled

No LiveKit Cloud or LiveKit Inference in this POC. Speech is local Speaches; LLM is remote OpenAI/Azure.

## Layout

```
agent/
  .env.example          # env template (copy → .env.local)
  src/agent.py          # LiveKit Agents entrypoint
  src/graph/            # LangGraph state, nodes, prompts
  src/adapters/         # STT/TTS/LLM, Realtime, persona, EOU, tracing
  src/tools/            # function tools (weather)
  tests/
```

## Setup

```bash
cd agent
cp .env.example .env.local   # if missing
# set OPENAI / Azure keys — see .env.example
uv sync
```

Required for chat: `OPENAI_API_KEY` or `AZURE_OPENAI_API_KEY` (and Azure endpoint/deployment when `LLM_PROVIDER=azure`).

LiveKit + Speaches + Jaeger are started by root `docker-compose.yml` / `start_app.sh`, not from this directory alone.

## Run

From the **repo root** (recommended):

```bash
./start_app.sh
```

Agent-only (Docker LiveKit already up, `.env.local` configured):

```bash
cd agent
uv run python src/agent.py dev
```

Console mode (terminal only, no web UI):

```bash
uv run python src/agent.py console
```

Agent name defaults to `v2v-poc-agent` (`AGENT_NAME`); must match `web/.env.local`.

## Tests

```bash
cd agent
uv run pytest
uv run ruff check src tests
```

## Related docs

- Repo overview: [../README.md](../README.md)
- Architecture: [../docs/architecture.md](../docs/architecture.md)
- Feature specs: [../specs/README.md](../specs/README.md)
