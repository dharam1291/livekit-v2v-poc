"""Process-env config helpers (no .env file reads)."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AgentConfig:
    agent_name: str
    openai_model: str
    speaches_base_url: str
    whisper_model: str
    kokoro_model: str
    kokoro_voice: str
    agent_join_timeout_sec: float = 30.0


def load_agent_config() -> AgentConfig:
    """Load config from process environment variables only."""
    return AgentConfig(
        agent_name=os.getenv("AGENT_NAME", "v2v-poc-agent"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        speaches_base_url=os.getenv("SPEACHES_BASE_URL", "http://localhost:8000/v1"),
        whisper_model=os.getenv("WHISPER_MODEL", "Systran/faster-whisper-small"),
        kokoro_model=os.getenv(
            "KOKORO_MODEL", "speaches-ai/Kokoro-82M-v1.0-ONNX"
        ),
        kokoro_voice=os.getenv("KOKORO_VOICE", "af_heart"),
        agent_join_timeout_sec=float(os.getenv("AGENT_JOIN_TIMEOUT_SEC", "30")),
    )
