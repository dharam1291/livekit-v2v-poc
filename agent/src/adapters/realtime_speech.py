"""Realtime speech-to-speech session builder (OpenAI / Azure Realtime)."""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlencode

import aiohttp
from livekit.plugins import openai

from adapters.config import AgentConfig

logger = logging.getLogger("agent.realtime")

# Chat api-versions (e.g. 2024-10-21) are often rejected by Azure Realtime WS.
_DEFAULT_REALTIME_API_VERSION = "2024-10-01-preview"


def realtime_api_version(config: AgentConfig) -> str:
    return (config.realtime_api_version or _DEFAULT_REALTIME_API_VERSION).strip()


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


def _realtime_ws_url(config: AgentConfig) -> str:
    """Build the Azure/OpenAI Realtime WebSocket URL used by the LiveKit plugin."""
    if config.llm_provider == "azure":
        endpoint = (config.azure_endpoint or "").rstrip("/")
        deployment = config.realtime_azure_deployment or config.azure_deployment or ""
        api_version = realtime_api_version(config)
        query = urlencode({"api-version": api_version, "deployment": deployment})
        # Match livekit.plugins.openai.realtime path for legacy api_version URLs.
        return f"{endpoint.replace('https://', 'wss://').replace('http://', 'ws://')}/openai/realtime?{query}"
    model = config.realtime_model
    return f"wss://api.openai.com/v1/realtime?model={model}"


async def probe_realtime_connection(config: AgentConfig) -> tuple[bool, str | None]:
    """
    Best-effort WebSocket handshake probe.

    PowerProxy and many Azure gateways return 403 on Realtime WS even when chat
    completions work. Fail fast so the session can fall back to standard mode.
    """
    url = _realtime_ws_url(config)
    headers: dict[str, str] = {}
    if config.llm_provider == "azure":
        headers["api-key"] = config.openai_api_key or ""
        headers["OpenAI-Beta"] = "realtime=v1"
    else:
        headers["Authorization"] = f"Bearer {config.openai_api_key or ''}"
        headers["OpenAI-Beta"] = "realtime=v1"

    timeout = aiohttp.ClientTimeout(total=8)
    try:
        async with (
            aiohttp.ClientSession(timeout=timeout) as http,
            http.ws_connect(url, headers=headers, heartbeat=30) as ws,
        ):
            await ws.close()
        logger.info("Realtime WS probe ok url=%s", url.split("?")[0])
        return True, None
    except aiohttp.WSServerHandshakeError as exc:
        reason = (
            f"Realtime WebSocket handshake failed ({exc.status}) at {url.split('?')[0]}; "
            "PowerProxy/chat gateways often block Realtime — use a Realtime-capable "
            "Azure deployment or OpenAI, or stay on standard mode"
        )
        logger.warning("%s", reason)
        return False, reason
    except Exception as exc:
        reason = f"Realtime WebSocket probe failed: {exc}"
        logger.warning("%s", reason)
        return False, reason


def build_realtime_model(config: AgentConfig, *, voice: str) -> Any:
    """Build LiveKit OpenAI RealtimeModel for voice-to-voice mode."""
    # Enable input transcription so the UI can show parallel transcript text.
    transcription = {"model": "gpt-4o-mini-transcribe"}

    if config.llm_provider == "azure":
        deployment = config.realtime_azure_deployment or config.azure_deployment
        if not deployment:
            raise RuntimeError("Azure Realtime requires REALTIME_AZURE_DEPLOYMENT")
        api_version = realtime_api_version(config)
        logger.info(
            "Using Azure Realtime deployment=%s voice=%s endpoint=%s api_version=%s",
            deployment,
            voice,
            config.azure_endpoint,
            api_version,
        )
        return openai.realtime.RealtimeModel.with_azure(
            azure_deployment=deployment,
            azure_endpoint=config.azure_endpoint,
            api_key=config.openai_api_key,
            api_version=api_version,
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
