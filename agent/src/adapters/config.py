"""Process-env config helpers (no .env file reads)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

ReplyMode = Literal["standard", "voice_to_voice"]


@dataclass(frozen=True)
class AgentConfig:
    agent_name: str
    llm_provider: str  # "openai" | "azure"
    openai_model: str
    openai_api_key: str | None
    openai_base_url: str | None
    azure_endpoint: str | None
    azure_deployment: str | None
    openai_api_version: str | None
    speaches_base_url: str
    whisper_model: str
    kokoro_model: str
    kokoro_voice: str
    agent_join_timeout_sec: float = 30.0
    reply_mode: ReplyMode = "standard"
    min_endpointing_delay_ms: int = 500
    max_endpointing_delay_ms: int = 3000
    trace_enabled: bool = True
    trace_dir: str = "traces"
    otlp_endpoint: str = "http://localhost:4318/v1/traces"
    jaeger_ui_url: str = "http://localhost:16686"
    realtime_model: str = "gpt-realtime"
    realtime_azure_deployment: str | None = None
    realtime_api_version: str | None = None
    # Machine Y Computer-Use Agent (gRPC)
    computer_use_enabled: bool = True
    computer_use_grpc_target: str = "127.0.0.1:50051"
    computer_use_timeout_sec: float = 180.0


def normalize_reply_mode(value: str | None) -> ReplyMode:
    raw = (value or "standard").strip().lower().replace("-", "_")
    if raw in {"voice_to_voice", "v2v", "realtime"}:
        return "voice_to_voice"
    return "standard"


def normalize_otlp_traces_endpoint(value: str | None) -> str:
    """Ensure an OTLP HTTP traces URL (Jaeger collector on :4318)."""
    raw = (value or "http://localhost:4318/v1/traces").strip().rstrip("/")
    if raw.endswith("/v1/traces"):
        return raw
    return f"{raw}/v1/traces"


def load_agent_config() -> AgentConfig:
    """Load config from process environment variables only."""
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT") or os.getenv(
        "OPENAI_AZURE_ENDPOINT"
    )
    provider = (os.getenv("LLM_PROVIDER") or "").strip().lower()
    if not provider:
        provider = "azure" if azure_endpoint else "openai"

    return AgentConfig(
        agent_name=os.getenv("AGENT_NAME", "v2v-poc-agent"),
        llm_provider=provider,
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        openai_api_key=os.getenv("OPENAI_API_KEY")
        or os.getenv("AZURE_OPENAI_API_KEY"),
        openai_base_url=os.getenv("OPENAI_BASE_URL"),
        azure_endpoint=azure_endpoint,
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT")
        or os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        openai_api_version=os.getenv("OPENAI_API_VERSION")
        or os.getenv("AZURE_OPENAI_API_VERSION"),
        speaches_base_url=os.getenv("SPEACHES_BASE_URL", "http://localhost:8000/v1"),
        whisper_model=os.getenv("WHISPER_MODEL", "Systran/faster-whisper-small"),
        kokoro_model=os.getenv(
            "KOKORO_MODEL", "speaches-ai/Kokoro-82M-v1.0-ONNX"
        ),
        kokoro_voice=os.getenv("KOKORO_VOICE", "af_heart"),
        agent_join_timeout_sec=float(os.getenv("AGENT_JOIN_TIMEOUT_SEC", "30")),
        reply_mode=normalize_reply_mode(os.getenv("REPLY_MODE")),
        min_endpointing_delay_ms=int(os.getenv("MIN_ENDPOINTING_DELAY_MS", "500")),
        max_endpointing_delay_ms=int(os.getenv("MAX_ENDPOINTING_DELAY_MS", "3000")),
        trace_enabled=(os.getenv("TRACE_ENABLED", "true").strip().lower() not in {"0", "false", "no"}),
        trace_dir=os.getenv("TRACE_DIR", "traces"),
        otlp_endpoint=normalize_otlp_traces_endpoint(
            os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT")
            or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
            or "http://localhost:4318/v1/traces"
        ),
        jaeger_ui_url=os.getenv("JAEGER_UI_URL", "http://localhost:16686"),
        realtime_model=os.getenv("REALTIME_MODEL", "gpt-realtime"),
        realtime_azure_deployment=os.getenv("REALTIME_AZURE_DEPLOYMENT"),
        realtime_api_version=os.getenv("REALTIME_API_VERSION"),
        computer_use_enabled=(
            os.getenv("COMPUTER_USE_ENABLED", "true").strip().lower()
            in {"1", "true", "yes", "on"}
        ),
        computer_use_grpc_target=(
            os.getenv("COMPUTER_USE_GRPC_TARGET")
            or os.getenv("COMPUTER_USE_GRPC_URL")
            or "127.0.0.1:50051"
        ).strip(),
        computer_use_timeout_sec=float(os.getenv("COMPUTER_USE_TIMEOUT_SEC", "180")),
    )
