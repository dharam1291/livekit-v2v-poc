"""LiveKit Agents entrypoint for the local voice-to-voice POC."""

from __future__ import annotations

import json
import logging
from typing import Any

from dotenv import load_dotenv
from livekit.agents import (
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    room_io,
)
from livekit.plugins import silero

from adapters.config import load_agent_config
from adapters.livekit_bridge import create_assistant
from adapters.speech_llm import build_llm, build_stt, build_tts
from adapters.voice_map import normalize_gender, normalize_language, resolve_kokoro_voice
from graph.prompts import GREETING_INSTRUCTIONS

logger = logging.getLogger("agent")

# Runtime local env load for the operator process (not for automation/secret scraping).
load_dotenv(".env.local")

config = load_agent_config()
AGENT_NAME = config.agent_name

server = AgentServer()


def prewarm(proc: JobProcess) -> None:
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


def _parse_job_persona(metadata: str | None) -> dict[str, Any]:
    if not metadata or not metadata.strip():
        return {}
    try:
        data = json.loads(metadata)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        logger.warning("Ignoring non-JSON job metadata")
        return {}


def _resolve_session_voice(ctx: JobContext) -> tuple[str, str, str]:
    """Return (gender, language, kokoro_voice) for this job."""
    persona = _parse_job_persona(getattr(ctx.job, "metadata", None) or "")
    gender = normalize_gender(
        persona.get("avatar_gender") or persona.get("avatarGender")
    )
    language = normalize_language(
        persona.get("session_language") or persona.get("sessionLanguage")
    )
    # UI metadata maps to a voice; env KOKORO_VOICE is only the no-metadata default.
    has_persona = bool(
        persona.get("avatar_gender")
        or persona.get("avatarGender")
        or persona.get("session_language")
        or persona.get("sessionLanguage")
    )
    voice = resolve_kokoro_voice(
        gender=gender,
        language=language,
        override=None if has_persona else config.kokoro_voice,
    )
    return gender, language, voice


@server.rtc_session(agent_name=AGENT_NAME)
async def my_agent(ctx: JobContext) -> None:
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    gender, language, voice = _resolve_session_voice(ctx)
    logger.info(
        "Session persona gender=%s language=%s voice=%s",
        gender,
        language,
        voice,
    )

    assistant = create_assistant()
    assistant.apply_update(
        {
            "avatar_gender": gender,
            "session_language": language,
            "kokoro_voice": voice,
        }
    )

    session = AgentSession(
        vad=ctx.proc.userdata["vad"],
        stt=build_stt(config),
        llm=build_llm(config),
        tts=build_tts(config, voice=voice),
        # Barge-in enabled for local POC (VAD mode; no LiveKit Cloud inference required).
        turn_handling={
            "interruption": {"enabled": True, "mode": "vad"},
        },
    )

    await session.start(
        agent=assistant,
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(),
        ),
    )

    await ctx.connect()

    # Seed LangGraph greeting state, then speak via the session.
    greeting = assistant.greeting_message()
    logger.info("Greeting ready: %s", greeting[:80])
    await session.generate_reply(instructions=GREETING_INSTRUCTIONS)


if __name__ == "__main__":
    cli.run_app(server)
