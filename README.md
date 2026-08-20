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
4. Frees busy ports (**3000**, **7880**, **7881**, **7882**, **8000**) if something is already listening (SIGTERM, then SIGKILL)
5. Starts Docker: LiveKit + Speaches
6. Starts the Python agent and the Next.js UI
7. Prints **http://localhost:3000**

Press **Ctrl+C** to stop the agent and web UI. Docker stays up until you run `docker compose down`.

### First-time API key

```bash
cp .env.example agent/.env.local
# edit agent/.env.local and set OPENAI_API_KEY=sk-...
```

Do not commit real keys. `.env.local` files are gitignored.

---

## What runs

| Piece | How | Port |
|-------|-----|------|
| LiveKit server | Docker (`livekit/livekit-server`) | 7880 / 7881 / 7882 |
| Whisper STT + Kokoro TTS | Docker Speaches | 8000 |
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

1. Open **http://localhost:3000**
2. Status **Disconnected** → **Connect** (allow microphone)
3. Hear the agent greeting; speak; check live transcripts
4. Optional: “What’s the weather in London?”
5. **End call** → **Disconnected**; connect again without restarting the app

More scenarios: [specs/001-livekit-v2v/quickstart.md](./specs/001-livekit-v2v/quickstart.md)

---

## Stop / reset

```bash
# Stop agent + web: Ctrl+C in the start_app.sh terminal

docker compose down          # stop LiveKit + Speaches
docker compose down -v       # also clear Speaches/Whisper cache
```

Logs while running: `.run/agent.log`, `.run/web.log`

---

## Project layout

```
livekit-v2v-poc/
  start_app.sh           # ← only command you need to start everything
  docker-compose.yml     # LiveKit + Speaches
  .env.example           # documented env names (no secrets)
  agent/                 # LiveKit Agents + LangGraph
    src/agent.py
    src/graph/
    src/tools/
    src/adapters/
  web/                   # Next.js testing UI
  specs/                 # Spec Kit feature docs
  .specify/              # Constitution + Spec Kit
```

---

## Specs index

| ID | Feature | Spec | Plan | Tasks |
|----|---------|------|------|-------|
| `001-livekit-v2v` | LiveKit voice-to-voice agent testing POC | [spec.md](./specs/001-livekit-v2v/spec.md) | [plan.md](./specs/001-livekit-v2v/plan.md) | [tasks.md](./specs/001-livekit-v2v/tasks.md) |

Full index: **[specs/README.md](./specs/README.md)**  
Governance: [`.specify/memory/constitution.md`](./.specify/memory/constitution.md)

---

## Notes

- No LiveKit Cloud, no Ollama for this POC.
- `--node-ip 127.0.0.1` on LiveKit makes browser WebRTC work on the same machine.
- `start_app.sh` is the supported way to run; avoid starting agent/web/docker in separate terminals unless debugging.
