#!/usr/bin/env bash
# start_app.sh — single entrypoint for the LiveKit V2V POC
# Starts: Docker (LiveKit + Speaches), Python agent, Next.js UI
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

LOG_DIR="$ROOT_DIR/.run"
PID_FILE="$LOG_DIR/pids"
AGENT_LOG="$LOG_DIR/agent.log"
WEB_LOG="$LOG_DIR/web.log"

# Host ports this POC needs (Docker publishes LiveKit/Speaches; Next uses 3000)
PORTS_TO_FREE=(3000 7880 7881 7882 8000)

AGENT_PID=""
WEB_PID=""
AGENT_TAIL_PID=""
WEB_TAIL_PID=""

log() { printf '[start_app] %s\n' "$*"; }
err() { printf '[start_app] ERROR: %s\n' "$*" >&2; }

# Read KEY=value from an env file without failing under `set -o pipefail` when missing.
env_get() {
  local file="$1"
  local key="$2"
  local line
  line="$(grep -E "^${key}=" "$file" 2>/dev/null | head -1 || true)"
  if [[ -z "$line" ]]; then
    printf ''
    return 0
  fi
  printf '%s' "${line#*=}" | tr -d '"' | tr -d "'"
}

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    err "Missing required command: $1"
    exit 1
  fi
}

# Gracefully free a TCP port: SIGTERM, wait, then SIGKILL if needed.
# Skips Docker Desktop / docker-proxy PIDs (killing those breaks the daemon socket).
free_port() {
  local port="$1"
  local pids pid cmd keep="" kill_list=""
  pids="$(lsof -nP -iTCP:"$port" -sTCP:LISTEN -t 2>/dev/null || true)"
  if [[ -z "$pids" ]]; then
    return 0
  fi

  for pid in $pids; do
    cmd="$(ps -p "$pid" -o comm= 2>/dev/null || true)"
    case "$cmd" in
      *docker*|*com.docker*|docker-proxy|VPNKit*|vpnkit*)
        keep="${keep} ${pid}"
        ;;
      *)
        kill_list="${kill_list} ${pid}"
        ;;
    esac
  done

  if [[ -n "$keep" ]]; then
    log "Port $port held by Docker (PIDs:${keep}) — will release via docker compose, not kill."
  fi

  kill_list="${kill_list## }"
  if [[ -z "$kill_list" ]]; then
    return 0
  fi

  log "Port $port is in use (PIDs: ${kill_list}). Stopping non-Docker listeners…"
  # shellcheck disable=SC2086
  kill -TERM $kill_list 2>/dev/null || true

  local waited=0
  while [[ $waited -lt 5 ]]; do
    local still=""
    for pid in $kill_list; do
      if kill -0 "$pid" 2>/dev/null; then
        still="${still} ${pid}"
      fi
    done
    [[ -z "$still" ]] && break
    sleep 1
    waited=$((waited + 1))
  done

  for pid in $kill_list; do
    if kill -0 "$pid" 2>/dev/null; then
      kill -KILL "$pid" 2>/dev/null || true
    fi
  done
}

require_docker() {
  local attempts="${1:-30}"
  local i=0
  while [[ $i -lt $attempts ]]; do
    if docker info >/dev/null 2>&1; then
      return 0
    fi
    if [[ $i -eq 0 ]]; then
      log "Waiting for Docker Desktop daemon…"
    fi
    sleep 2
    i=$((i + 1))
  done
  err "Cannot connect to Docker daemon at docker.sock."
  err "Open Docker Desktop, wait until it shows Running, then retry: ./start_app.sh"
  exit 1
}

ensure_env_files() {
  if [[ ! -f "$ROOT_DIR/agent/.env.local" ]]; then
    if [[ -f "$ROOT_DIR/agent/.env.example" ]]; then
      cp "$ROOT_DIR/agent/.env.example" "$ROOT_DIR/agent/.env.local"
      log "Created agent/.env.local from agent/.env.example — set OPENAI_API_KEY before using GPT."
    else
      err "Missing agent/.env.local and agent/.env.example"
      exit 1
    fi
  fi

  if [[ ! -f "$ROOT_DIR/web/.env.local" ]]; then
    if [[ -f "$ROOT_DIR/web/.env.example" ]]; then
      cp "$ROOT_DIR/web/.env.example" "$ROOT_DIR/web/.env.local"
      log "Created web/.env.local from web/.env.example"
    else
      err "Missing web/.env.local and web/.env.example"
      exit 1
    fi
  fi
}

check_openai_key() {
  # Accept standard OpenAI key OR Azure/PowerProxy key (do not print values).
  local key azure_key azure_endpoint effective
  key="$(env_get "$ROOT_DIR/agent/.env.local" OPENAI_API_KEY)"
  azure_key="$(env_get "$ROOT_DIR/agent/.env.local" AZURE_OPENAI_API_KEY)"
  azure_endpoint="$(env_get "$ROOT_DIR/agent/.env.local" AZURE_OPENAI_ENDPOINT)"

  effective="${azure_key:-$key}"
  if [[ -z "$effective" \
    || "$effective" == "sk-..." \
    || "$effective" == "sk-your-key-here" \
    || "$effective" == "replace-with-your-api-key" ]]; then
    err "Set OPENAI_API_KEY or AZURE_OPENAI_API_KEY in agent/.env.local (not a placeholder)."
    exit 1
  fi
  if [[ -n "$azure_endpoint" ]]; then
    local api_version
    api_version="$(env_get "$ROOT_DIR/agent/.env.local" OPENAI_API_VERSION)"
    if [[ -z "$api_version" ]]; then
      err "AZURE_OPENAI_ENDPOINT is set but OPENAI_API_VERSION is missing in agent/.env.local"
      exit 1
    fi
    log "Detected AZURE_OPENAI_ENDPOINT — agent will use Azure/PowerProxy LLM mode."
  fi
}

ensure_speaches_models() {
  local whisper_model kokoro_model
  whisper_model="$(env_get "$ROOT_DIR/agent/.env.local" WHISPER_MODEL)"
  kokoro_model="$(env_get "$ROOT_DIR/agent/.env.local" KOKORO_MODEL)"
  whisper_model="${whisper_model:-Systran/faster-whisper-small}"
  kokoro_model="${kokoro_model:-speaches-ai/Kokoro-82M-v1.0-ONNX}"

  # Speaches install API: POST /v1/models/{model_id}  (model_id may contain '/')
  # Docs: https://speaches.ai/usage/model-discovery/
  ensure_one_model() {
    local model_id="$1"
    local listed http_code body_file
    listed="$(curl -fsS --max-time 10 http://localhost:8000/v1/models 2>/dev/null || true)"
    if echo "$listed" | grep -Fq "$model_id"; then
      log "Speaches model already present: $model_id"
      return 0
    fi

    log "Downloading Speaches model (first run can take several minutes): $model_id"
    body_file="$(mktemp)"
    # IMPORTANT: do not POST JSON to /v1/models — use path form below.
    http_code="$(
      curl -sS -o "$body_file" -w '%{http_code}' --max-time 600 \
        -X POST "http://localhost:8000/v1/models/${model_id}" \
        || true
    )"

    if [[ "$http_code" == "200" || "$http_code" == "201" ]]; then
      log "Downloaded: $model_id"
      rm -f "$body_file"
      return 0
    fi

    # Fallback: some builds accept aliases like whisper-1 / tts-1
    local alias=""
    case "$model_id" in
      Systran/*whisper*|*/faster-whisper*) alias="whisper-1" ;;
      *Kokoro*) alias="tts-1" ;;
    esac
    if [[ -n "$alias" ]]; then
      log "Retrying download via alias: $alias"
      http_code="$(
        curl -sS -o "$body_file" -w '%{http_code}' --max-time 600 \
          -X POST "http://localhost:8000/v1/models/${alias}" \
          || true
      )"
      if [[ "$http_code" == "200" || "$http_code" == "201" ]]; then
        log "Downloaded via alias $alias"
        rm -f "$body_file"
        return 0
      fi
    fi

    err "Failed to download Speaches model '$model_id' (HTTP ${http_code:-000})."
    if [[ -s "$body_file" ]]; then
      err "Response: $(head -c 400 "$body_file")"
    fi
    err "Check: curl -s http://localhost:8000/v1/registry | head"
    err "Or: docker compose logs -f speaches"
    rm -f "$body_file"
    return 1
  }

  ensure_one_model "$whisper_model" || true
  ensure_one_model "$kokoro_model" || true
  log "Installed Speaches models now:"
  curl -fsS --max-time 10 http://localhost:8000/v1/models 2>/dev/null | head -c 800 || true
  printf '\n'
}

wait_http() {
  local url="$1"
  local name="$2"
  local attempts="${3:-60}"
  local i=0
  log "Waiting for $name ($url)…"
  while [[ $i -lt $attempts ]]; do
    if curl -fsS -o /dev/null "$url" 2>/dev/null \
      || curl -fsS -o /dev/null --max-time 2 "$url" 2>/dev/null; then
      log "$name is up."
      return 0
    fi
    # LiveKit may return non-JSON on / ; treat any HTTP response as up.
    local code
    code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 2 "$url" 2>/dev/null || true)"
    if [[ -n "$code" && "$code" != "000" ]]; then
      log "$name is up (HTTP $code)."
      return 0
    fi
    sleep 2
    i=$((i + 1))
  done
  err "$name did not become ready in time"
  return 1
}

STARTED=0

cleanup() {
  # Only tear down processes we actually launched (avoid scary message on early config errors).
  if [[ "${STARTED}" -ne 1 && -z "${AGENT_PID}" && -z "${WEB_PID}" ]]; then
    return 0
  fi
  log "Shutting down agent and web…"
  for pid in "${AGENT_TAIL_PID}" "${WEB_TAIL_PID}"; do
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      kill -TERM "$pid" 2>/dev/null || true
    fi
  done
  if [[ -n "${AGENT_PID}" ]] && kill -0 "$AGENT_PID" 2>/dev/null; then
    kill -TERM "$AGENT_PID" 2>/dev/null || true
  fi
  if [[ -n "${WEB_PID}" ]] && kill -0 "$WEB_PID" 2>/dev/null; then
    kill -TERM "$WEB_PID" 2>/dev/null || true
  fi
  if [[ -f "$PID_FILE" ]]; then
    while read -r pid; do
      [[ -n "$pid" ]] && kill -TERM "$pid" 2>/dev/null || true
    done <"$PID_FILE"
  fi
  sleep 1
  if [[ -n "${AGENT_PID}" ]] && kill -0 "$AGENT_PID" 2>/dev/null; then
    kill -KILL "$AGENT_PID" 2>/dev/null || true
  fi
  if [[ -n "${WEB_PID}" ]] && kill -0 "$WEB_PID" 2>/dev/null; then
    kill -KILL "$WEB_PID" 2>/dev/null || true
  fi
  rm -f "$PID_FILE"
  log "Stopped. Docker services are still running (use: docker compose down)."
}

trap cleanup EXIT INT TERM

mkdir -p "$LOG_DIR"

log "Checking prerequisites…"
need_cmd docker
need_cmd curl
need_cmd lsof
need_cmd uv
need_cmd npm
need_cmd node

require_docker 5

ensure_env_files
check_openai_key

# Release LiveKit/Speaches ports cleanly via Compose (do not kill docker-proxy).
log "Stopping any previous Compose stack for this project…"
docker compose down --remove-orphans >/dev/null 2>&1 || true

require_docker 30

log "Freeing non-Docker listeners on: ${PORTS_TO_FREE[*]}"
for port in "${PORTS_TO_FREE[@]}"; do
  free_port "$port"
done

log "Starting Docker stack (LiveKit + Speaches)…"
require_docker 5
if ! docker compose up -d; then
  err "docker compose up failed. Is Docker Desktop running?"
  err "Start Docker Desktop, wait for it to be healthy, then run ./start_app.sh again."
  exit 1
fi

wait_http "http://localhost:7880" "LiveKit" 45 || true
# Speaches health endpoints vary; accept /health or /v1/models
if ! wait_http "http://localhost:8000/health" "Speaches" 90; then
  wait_http "http://localhost:8000/v1/models" "Speaches" 30
fi

ensure_speaches_models

log "Syncing agent dependencies (uv)…"
(
  cd "$ROOT_DIR/agent"
  uv sync --all-groups
)

log "Installing web dependencies (npm) if needed…"
(
  cd "$ROOT_DIR/web"
  if [[ ! -d node_modules ]]; then
    npm install
  fi
)

: >"$AGENT_LOG"
: >"$WEB_LOG"

log "Starting agent (live log below + $AGENT_LOG)…"
(
  cd "$ROOT_DIR/agent"
  # Prefer .env.local already loaded by agent; keep cwd correct for dotenv.
  uv run python src/agent.py dev
) >>"$AGENT_LOG" 2>&1 &
AGENT_PID=$!
STARTED=1

log "Starting web UI (live log below + $WEB_LOG)…"
(
  cd "$ROOT_DIR/web"
  npm run dev -- --port 3000
) >>"$WEB_LOG" 2>&1 &
WEB_PID=$!

printf '%s\n%s\n' "$AGENT_PID" "$WEB_PID" >"$PID_FILE"

# Mirror logs into this terminal so TTS/LLM errors are visible without another window.
(
  printf '\n---------- agent.log ----------\n'
  tail -n +1 -F "$AGENT_LOG"
) &
AGENT_TAIL_PID=$!
(
  printf '\n---------- web.log ----------\n'
  # Keep web quieter: only stream after Ready / errors; still follow the file.
  tail -n +1 -F "$WEB_LOG"
) &
WEB_TAIL_PID=$!

wait_http "http://localhost:3000" "Web UI" 60

cat <<EOF

========================================
  LiveKit V2V POC is running
========================================
  UI:     http://localhost:3000
  LiveKit ws://localhost:7880
  Speaches http://localhost:8000

  Agent + web logs stream in this terminal.
  Files: $AGENT_LOG
         $WEB_LOG

  Test: open UI → Connect → allow mic → speak → End call
  Press Ctrl+C to stop agent + web.
  Docker keeps running until: docker compose down
========================================

EOF

# Keep script alive while children run; EXIT trap cleans up.
wait "$AGENT_PID" "$WEB_PID"
