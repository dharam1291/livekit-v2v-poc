"""Process-env config helpers (no .env file reads)."""

from __future__ import annotations

import os
from dataclasses import dataclass


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
    )
