"""STT / TTS / LLM factory wiring for Speaches + OpenAI/Azure-compatible LLM."""

from __future__ import annotations

import logging
from dataclasses import replace

import httpx
import openai as openai_sdk
from livekit.agents import APIConnectOptions, utils
from livekit.agents import tts as tts_mod
from livekit.agents._exceptions import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
)
from livekit.agents.types import DEFAULT_API_CONNECT_OPTIONS
from livekit.plugins import openai
from livekit.plugins.openai.tts import NUM_CHANNELS, SAMPLE_RATE
from livekit.plugins.openai.tts import TTS as OpenAITTS  # noqa: N811

from adapters.config import AgentConfig

logger = logging.getLogger("agent.speech_llm")


class SpeachesAudioChunkedStream(tts_mod.ChunkedStream):
    """Binary PCM stream for Speaches/Kokoro with a guaranteed request_id.

    Uses ``audio/pcm`` so LiveKit can emit frames as bytes arrive (WAV/MP3
    decoding buffers and delays first audio vs the transcript panel).
    """

    def __init__(
        self, *, tts: OpenAITTS, input_text: str, conn_options: APIConnectOptions
    ) -> None:
        super().__init__(tts=tts, input_text=input_text, conn_options=conn_options)
        self._tts = tts
        self._opts = replace(tts._opts)

    async def _run(self, output_emitter: tts_mod.AudioEmitter) -> None:
        oai_stream = self._tts._client.audio.speech.with_streaming_response.create(
            input=self.input_text,
            model=self._opts.model,
            voice=self._opts.voice,
            response_format="pcm",
            speed=self._opts.speed,
            instructions=self._opts.instructions or openai_sdk.omit,
            stream_format="audio",
            timeout=httpx.Timeout(30, connect=self._conn_options.timeout),
        )

        try:
            async with oai_stream as stream:
                request_id = getattr(stream, "request_id", None) or utils.shortuuid()
                output_emitter.initialize(
                    request_id=request_id,
                    sample_rate=SAMPLE_RATE,
                    num_channels=NUM_CHANNELS,
                    mime_type="audio/pcm",
                    frame_size_ms=50,
                )

                async for data in stream.iter_bytes():
                    if data:
                        output_emitter.push(data)

            output_emitter.flush()

        except openai_sdk.APITimeoutError:
            raise APITimeoutError() from None
        except openai_sdk.APIStatusError as e:
            raise APIStatusError(
                e.message, status_code=e.status_code, request_id=e.request_id, body=e.body
            ) from None
        except Exception as e:
            raise APIConnectionError() from e


class SpeachesTTS(OpenAITTS):
    """OpenAI-compatible TTS forced onto LiveKit's binary PCM stream path.

    LiveKit's openai.TTS uses SSE streaming for every model except tts-1 / tts-1-hd.
    Speaches (Kokoro) returns raw audio bytes, not SSE events, which otherwise yields
    ``no audio frames were pushed``. Always use SpeachesAudioChunkedStream for Speaches.
    """

    def synthesize(
        self,
        text: str,
        *,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> tts_mod.ChunkedStream:
        return SpeachesAudioChunkedStream(
            tts=self, input_text=text, conn_options=conn_options
        )


def build_stt(config: AgentConfig, *, language: str | None = None):
    lang = (language or "en").strip().lower().split("-")[0] or "en"
    return openai.STT(
        model=config.whisper_model,
        base_url=config.speaches_base_url,
        api_key="not-needed",
        language=lang,
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
        "Using Speaches TTS model=%s voice=%s base_url=%s format=pcm",
        config.kokoro_model,
        resolved_voice,
        config.speaches_base_url,
    )
    return SpeachesTTS(
        model=config.kokoro_model,
        voice=resolved_voice,
        base_url=config.speaches_base_url,
        api_key="not-needed",
        response_format="pcm",
    )
