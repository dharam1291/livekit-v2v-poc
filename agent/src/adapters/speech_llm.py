"""STT / TTS / LLM factory wiring for Speaches + OpenAI."""

from __future__ import annotations

from livekit.plugins import openai

from adapters.config import AgentConfig


def build_stt(config: AgentConfig):
    return openai.STT(
        model=config.whisper_model,
        base_url=config.speaches_base_url,
        api_key="not-needed",
    )


def build_llm(config: AgentConfig):
    return openai.LLM(model=config.openai_model)


def build_tts(config: AgentConfig):
    return openai.TTS(
        model=config.kokoro_model,
        voice=config.kokoro_voice,
        base_url=config.speaches_base_url,
        api_key="not-needed",
        response_format="wav",
    )
