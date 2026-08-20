"""STT / TTS / LLM factory wiring for Speaches + OpenAI/Azure-compatible LLM."""

from __future__ import annotations

import logging

from livekit.agents import APIConnectOptions, tts
from livekit.agents.types import DEFAULT_API_CONNECT_OPTIONS
from livekit.plugins import openai
from livekit.plugins.openai.tts import AudioChunkedStream

from adapters.config import AgentConfig

logger = logging.getLogger("agent.speech_llm")


class SpeachesTTS(openai.TTS):
    """OpenAI-compatible TTS forced onto LiveKit's binary audio stream path.

    LiveKit's openai.TTS uses SSE streaming for every model except tts-1 / tts-1-hd.
    Speaches (Kokoro) returns raw audio bytes, not SSE events, which otherwise yields
    ``no audio frames were pushed``. Always use AudioChunkedStream for Speaches.
    """

    def synthesize(
        self,
        text: str,
        *,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> tts.ChunkedStream:
        return AudioChunkedStream(tts=self, input_text=text, conn_options=conn_options)


def build_stt(config: AgentConfig):
    return openai.STT(
        model=config.whisper_model,
        base_url=config.speaches_base_url,
        api_key="not-needed",
    )


def build_llm(config: AgentConfig):
    """
    Build LLM client.

    - LLM_PROVIDER=azure (or AZURE_OPENAI_ENDPOINT set): Azure OpenAI / PowerProxy style
      (api-key header + deployments path via AsyncAzureOpenAI).
    - Otherwise: standard OpenAI or OpenAI-compatible base_url.
    """
    if config.llm_provider == "azure":
        if not config.azure_endpoint:
            raise RuntimeError(
                "LLM_PROVIDER=azure requires AZURE_OPENAI_ENDPOINT "
                "(e.g. https://powerproxy.example.com)"
            )
        if not config.openai_api_version:
            raise RuntimeError(
                "LLM_PROVIDER=azure requires OPENAI_API_VERSION "
                "(query api-version from your working curl)"
            )
        logger.info(
            "Using Azure-compatible LLM endpoint=%s deployment=%s api_version=%s",
            config.azure_endpoint,
            config.azure_deployment,
            config.openai_api_version,
        )
        return openai.LLM.with_azure(
            model=config.openai_model,
            azure_endpoint=config.azure_endpoint,
            azure_deployment=config.azure_deployment,
            api_version=config.openai_api_version,
            api_key=config.openai_api_key,
        )

    kwargs: dict = {"model": config.openai_model}
    if config.openai_api_key:
        kwargs["api_key"] = config.openai_api_key
    if config.openai_base_url:
        kwargs["base_url"] = config.openai_base_url
    logger.info(
        "Using OpenAI-compatible LLM model=%s base_url=%s",
        config.openai_model,
        config.openai_base_url or "default",
    )
    return openai.LLM(**kwargs)


def build_tts(config: AgentConfig, *, voice: str | None = None):
    """Build Speaches Kokoro TTS. ``voice`` overrides ``config.kokoro_voice`` when set."""
    resolved_voice = voice or config.kokoro_voice
    logger.info(
        "Using Speaches TTS model=%s voice=%s base_url=%s",
        config.kokoro_model,
        resolved_voice,
        config.speaches_base_url,
    )
    return SpeachesTTS(
        model=config.kokoro_model,
        voice=resolved_voice,
        base_url=config.speaches_base_url,
        api_key="not-needed",
        response_format="wav",
    )
