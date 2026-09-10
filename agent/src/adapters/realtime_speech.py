"""Realtime speech-to-speech session builder (OpenAI / Azure Realtime)."""

from __future__ import annotations

import logging
from typing import Any

from livekit.plugins import openai

from adapters.config import AgentConfig

logger = logging.getLogger("agent.realtime")


def voice_to_voice_availability(config: AgentConfig) -> tuple[bool, str | None]:
    """
    Return (available, reason_if_not).

    Azure Realtime requires an explicit REALTIME_AZURE_DEPLOYMENT for this POC,
    because chat deployments (e.g. PowerProxy GPT) often are not Realtime-capable.
    """
    if not config.openai_api_key:
        return False, "missing API key for Realtime"
    if config.llm_provider == "azure":
        if not config.azure_endpoint:
            return False, "missing AZURE_OPENAI_ENDPOINT for Realtime"
        if not config.realtime_azure_deployment:
            return (
                False,
                "REALTIME_AZURE_DEPLOYMENT not set; Azure chat deployment may not support Realtime",
            )
    return True, None


def build_realtime_model(config: AgentConfig, *, voice: str) -> Any:
    """Build LiveKit OpenAI RealtimeModel for voice-to-voice mode."""
    # Enable input transcription so the UI can show parallel transcript text.
    transcription = {"model": "gpt-4o-mini-transcribe"}

    if config.llm_provider == "azure":
        deployment = config.realtime_azure_deployment or config.azure_deployment
        if not deployment:
            raise RuntimeError("Azure Realtime requires REALTIME_AZURE_DEPLOYMENT")
        logger.info(
            "Using Azure Realtime deployment=%s voice=%s endpoint=%s",
            deployment,
            voice,
            config.azure_endpoint,
        )
        return openai.realtime.RealtimeModel.with_azure(
            azure_deployment=deployment,
            azure_endpoint=config.azure_endpoint,
            api_key=config.openai_api_key,
            voice=voice,
            modalities=["text", "audio"],
            input_audio_transcription=transcription,
        )

    logger.info(
        "Using OpenAI Realtime model=%s voice=%s",
        config.realtime_model,
        voice,
    )
    return openai.realtime.RealtimeModel(
        model=config.realtime_model,
        voice=voice,
        api_key=config.openai_api_key,
        modalities=["text", "audio"],
        input_audio_transcription=transcription,
    )
