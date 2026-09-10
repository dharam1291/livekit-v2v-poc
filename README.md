# LiveKit Voice-to-Voice POC

Local POC for **human ↔ agent voice calls** over **LiveKit**, with **LangGraph** orchestration, Speaches (Whisper STT + Kokoro TTS) in Docker, OpenAI GPT for the LLM, and a small Next.js UI for testing.

## One command to run

```bash
cd /Users/dharmendrasingh/DTDL_CODEBASE/POC/livekit-v2v-poc
chmod +x start_app.sh   # once
./start_app.sh
```

That script:

1. Checks Docker, `uv`, and Node/npm
2. Creates `agent/.env.local` / `web/.env.local` from examples if missing
3. Requires a real `OPENAI_API_KEY` in `agent/.env.local`
4. Frees busy ports (**3000**, **7880**, **7881**, **7882**, **8000**, **16686**, **4317**, **4318**) if something is already listening (SIGTERM, then SIGKILL)
5. Starts Docker: LiveKit + Speaches + Jaeger
6. Starts the Python agent and the Next.js UI
7. Prints **http://localhost:3000** (and Jaeger at **http://localhost:16686**)

Press **Ctrl+C** to stop the agent and web UI. Docker stays up until you run `docker compose down`.

### First-time API key / LLM

Edit `agent/.env.local` (created from `agent/.env.example` on first run).

**Azure / PowerProxy** (matches a curl like  
`.../openai/deployments/gpt-5.4/chat/completions?api-version=...` with `api-key` header):

```bash
LLM_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=https://powerproxy.dev.oneai.yo-digital.com
AZURE_OPENAI_DEPLOYMENT=gpt-5.4
OPENAI_MODEL=gpt-5.4
OPENAI_API_VERSION=<your-api-version>
AZURE_OPENAI_API_KEY=<your-api-key>
```

**Public OpenAI** instead:

```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

Do not commit real keys. Templates:

- `agent/.env.example` — LiveKit, Speaches, LLM
- `web/.env.example` — LiveKit + `AGENT_NAME` only

---

## What runs

| Piece | How | Port |
|-------|-----|------|
| LiveKit server | Docker (`livekit/livekit-server`) | 7880 / 7881 / 7882 |
| Whisper STT + Kokoro TTS | Docker Speaches | 8000 |
| Jaeger (traces UI + OTLP) | Docker (`jaegertracing/all-in-one`) | 16686 / 4317 / 4318 |
| LLM | OpenAI GPT via `OPENAI_API_KEY` | — |
| Agent (LangGraph + LiveKit Agents) | `uv` on host | — |
| Web testing UI | Next.js on host | **3000** |

Whisper is **not** installed with pip/brew. Speaches downloads model weights into a Docker volume on first use (can take several minutes).

---

## Prerequisites

- **Docker Desktop** running (`docker info` succeeds)
- [uv](https://docs.astral.sh/uv/)
- Node.js 20+ / npm
- OpenAI API key in `agent/.env.local`

---

## Test the call

1. Open **http://localhost:3000** in your browser (Chrome/Safari/Firefox on this machine)
   - Mic/WebRTC only work on **localhost** or **HTTPS**. Do **not** use a LAN URL like `http://192.168.x.x:3000` — the browser will block `mediaDevices`.
2. Choose **avatar**, **language**, and **reply mode** (Standard or Voice-to-voice), then **Connect** (allow microphone)
3. Hear the agent greeting in the selected language; speak; watch the **right-side transcript**, speaking avatar, and **session traces** panel
4. While the agent thinks, you should see wait feedback and hear the soft `/wait-cue.wav` loop (visual still works if audio is blocked)
5. Optional: “What’s the weather in London?” works in **standard** mode; in voice-to-voice tools are best-effort
6. If voice-to-voice credentials are missing **or the Realtime WebSocket is blocked (e.g. PowerProxy 403)**, the agent **falls back to standard** with a visible warning
7. **End call** → conversation appears under **Previous conversations** on the home page

Voice-to-voice on Azure needs a Realtime-capable deployment (`REALTIME_AZURE_DEPLOYMENT`) and usually `REALTIME_API_VERSION=2024-10-01-preview` (do not reuse chat-only `OPENAI_API_VERSION`). Many chat proxies reject Realtime WS; the agent probes and falls back.

### Dual-mode / traces (agent env)

See `agent/.env.example` for:

- `REPLY_MODE=standard|voice_to_voice`
- `MIN_ENDPOINTING_DELAY_MS` / `MAX_ENDPOINTING_DELAY_MS`
- `TRACE_ENABLED` / `TRACE_DIR` / `OTEL_EXPORTER_OTLP_*` / `JAEGER_UI_URL` (Jaeger via docker compose + JSONL + UI topic)
- `REALTIME_MODEL` (OpenAI) or `REALTIME_AZURE_DEPLOYMENT` (Azure Realtime)

More scenarios: [specs/003-demo-ready-v2v/quickstart.md](./specs/003-demo-ready-v2v/quickstart.md) · [specs/002-ux-general-agent/quickstart.md](./specs/002-ux-general-agent/quickstart.md)

---

## Stop / reset

```bash
# Stop agent + web: Ctrl+C in the start_app.sh terminal

docker compose down          # stop LiveKit + Speaches
docker compose down -v       # also clear Speaches/Whisper cache
```

Logs while running stream in the `./start_app.sh` terminal and are also written to `.run/agent.log` / `.run/web.log`.

---

## Project layout

E2E architecture diagram: **[docs/architecture.md](./docs/architecture.md)**

```
livekit-v2v-poc/
  start_app.sh           # ← only command you need to start everything
  docker-compose.yml     # LiveKit + Speaches + Jaeger
  docs/                  # Architecture diagram + notes
  agent/                 # LiveKit Agents + LangGraph (see agent/README.md)
    .env.example         # agent env template
    src/agent.py
    src/graph/
    src/tools/
    src/adapters/
  web/                   # Next.js testing UI
    .env.example         # web env template
  specs/                 # Spec Kit feature docs
  .specify/              # Constitution + Spec Kit
```

---

## Specs index

| ID | Feature | Spec | Plan | Tasks |
|----|---------|------|------|-------|
| `001-livekit-v2v` | LiveKit voice-to-voice agent testing POC | [spec.md](./specs/001-livekit-v2v/spec.md) | [plan.md](./specs/001-livekit-v2v/plan.md) | [tasks.md](./specs/001-livekit-v2v/tasks.md) |
| `002-ux-general-agent` | Conversation UX and general agent answers | [spec.md](./specs/002-ux-general-agent/spec.md) | [plan.md](./specs/002-ux-general-agent/plan.md) | [tasks.md](./specs/002-ux-general-agent/tasks.md) |
| `003-demo-ready-v2v` | Demo-ready voice (persona, wait cue, dual-mode, traces) | [spec.md](./specs/003-demo-ready-v2v/spec.md) | [plan.md](./specs/003-demo-ready-v2v/plan.md) | [tasks.md](./specs/003-demo-ready-v2v/tasks.md) |

Full index: **[specs/README.md](./specs/README.md)**  
Governance: [`.specify/memory/constitution.md`](./.specify/memory/constitution.md)

---

## Notes

- No LiveKit Cloud, no Ollama for this POC.
- `--node-ip 127.0.0.1` on LiveKit makes browser WebRTC work on the same machine.
- `start_app.sh` is the supported way to run; avoid starting agent/web/docker in separate terminals unless debugging.
- Speaches models install with `POST /v1/models/<model_id>` (not a JSON body). If downloads fail, run manually:

```bash
curl -X POST "http://localhost:8000/v1/models/Systran/faster-whisper-small"
curl -X POST "http://localhost:8000/v1/models/speaches-ai/Kokoro-82M-v1.0-ONNX"
curl -s "http://localhost:8000/v1/models"
```
