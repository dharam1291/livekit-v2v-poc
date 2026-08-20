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

log() { printf '[start_app] %s\n' "$*"; }
err() { printf '[start_app] ERROR: %s\n' "$*" >&2; }

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    err "Missing required command: $1"
    exit 1
  fi
}

# Gracefully free a TCP port: SIGTERM, wait, then SIGKILL if needed.
free_port() {
  local port="$1"
  local pids
  pids="$(lsof -nP -iTCP:"$port" -sTCP:LISTEN -t 2>/dev/null || true)"
  if [[ -z "$pids" ]]; then
    return 0
  fi

  log "Port $port is in use (PIDs: $(echo "$pids" | tr '\n' ' ')). Stopping listeners…"
  # shellcheck disable=SC2086
  kill -TERM $pids 2>/dev/null || true

  local waited=0
  while [[ $waited -lt 5 ]]; do
    pids="$(lsof -nP -iTCP:"$port" -sTCP:LISTEN -t 2>/dev/null || true)"
    [[ -z "$pids" ]] && break
    sleep 1
    waited=$((waited + 1))
  done

  pids="$(lsof -nP -iTCP:"$port" -sTCP:LISTEN -t 2>/dev/null || true)"
  if [[ -n "$pids" ]]; then
    log "Port $port still busy — force killing…"
    # shellcheck disable=SC2086
    kill -KILL $pids 2>/dev/null || true
    sleep 1
  fi

  if lsof -nP -iTCP:"$port" -sTCP:LISTEN -t >/dev/null 2>&1; then
    err "Could not free port $port"
    exit 1
  fi
  log "Port $port is free."
}

ensure_env_files() {
  if [[ ! -f "$ROOT_DIR/agent/.env.local" ]]; then
    if [[ -f "$ROOT_DIR/.env.example" ]]; then
      cp "$ROOT_DIR/.env.example" "$ROOT_DIR/agent/.env.local"
      log "Created agent/.env.local from .env.example — set OPENAI_API_KEY before using GPT."
    else
      err "Missing agent/.env.local and .env.example"
      exit 1
    fi
  fi

  if [[ ! -f "$ROOT_DIR/web/.env.local" ]]; then
    if [[ -f "$ROOT_DIR/web/.env.example" ]]; then
      cp "$ROOT_DIR/web/.env.example" "$ROOT_DIR/web/.env.local"
      log "Created web/.env.local from web/.env.example"
    elif [[ -f "$ROOT_DIR/.env.example" ]]; then
      cp "$ROOT_DIR/.env.example" "$ROOT_DIR/web/.env.local"
      log "Created web/.env.local from .env.example"
    fi
  fi
}

check_openai_key() {
  # Do not print the key; only verify it looks configured.
  local key
  key="$(
    grep -E '^OPENAI_API_KEY=' "$ROOT_DIR/agent/.env.local" 2>/dev/null \
      | head -1 \
      | cut -d= -f2- \
      | tr -d '"' \
      | tr -d "'"
  )"
  if [[ -z "$key" || "$key" == "sk-..." || "$key" == "sk-your-key-here" ]]; then
    err "Set a real OPENAI_API_KEY in agent/.env.local (replace the placeholder)."
    exit 1
  fi
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

cleanup() {
  log "Shutting down agent and web…"
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

if ! docker info >/dev/null 2>&1; then
  err "Docker is not running. Start Docker Desktop and retry."
  exit 1
fi

ensure_env_files
check_openai_key

log "Freeing ports if already in use: ${PORTS_TO_FREE[*]}"
for port in "${PORTS_TO_FREE[@]}"; do
  free_port "$port"
done

log "Starting Docker stack (LiveKit + Speaches)…"
docker compose up -d

wait_http "http://localhost:7880" "LiveKit" 45 || true
# Speaches health endpoints vary; accept /health or /v1/models
if ! wait_http "http://localhost:8000/health" "Speaches" 90; then
  wait_http "http://localhost:8000/v1/models" "Speaches" 30
fi

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

log "Starting agent (logs: $AGENT_LOG)…"
(
  cd "$ROOT_DIR/agent"
  # Prefer .env.local already loaded by agent; keep cwd correct for dotenv.
  uv run python src/agent.py dev
) >"$AGENT_LOG" 2>&1 &
AGENT_PID=$!

log "Starting web UI (logs: $WEB_LOG)…"
(
  cd "$ROOT_DIR/web"
  npm run dev -- --port 3000
) >"$WEB_LOG" 2>&1 &
WEB_PID=$!

printf '%s\n%s\n' "$AGENT_PID" "$WEB_PID" >"$PID_FILE"

wait_http "http://localhost:3000" "Web UI" 60

cat <<EOF

========================================
  LiveKit V2V POC is running
========================================
  UI:     http://localhost:3000
  LiveKit ws://localhost:7880
  Speaches http://localhost:8000

  Agent log: $AGENT_LOG
  Web log:   $WEB_LOG

  Press Ctrl+C to stop agent + web.
  Docker keeps running until: docker compose down
========================================

EOF

# Keep script alive while children run; EXIT trap cleans up.
wait "$AGENT_PID" "$WEB_PID"
