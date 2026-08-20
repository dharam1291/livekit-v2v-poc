"""LiveKit Agents entrypoint for the local voice-to-voice POC."""

from __future__ import annotations

import logging

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


@server.rtc_session(agent_name=AGENT_NAME)
async def my_agent(ctx: JobContext) -> None:
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    assistant = create_assistant()
    session = AgentSession(
        vad=ctx.proc.userdata["vad"],
        stt=build_stt(config),
        llm=build_llm(config),
        tts=build_tts(config),
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
