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
from adapters.eou import build_turn_handling
from adapters.livekit_bridge import create_assistant
from adapters.mic_gate import wire_user_mic_gate
from adapters.otel_setup import setup_jaeger_tracing
from adapters.persona import resolve_persona, resolve_reply_mode_from_metadata
from adapters.realtime_speech import (
    build_realtime_model,
    probe_realtime_connection,
    voice_to_voice_availability,
)
from adapters.speech_llm import build_llm, build_stt, build_tts
from adapters.tracing import SessionTracer
from graph.prompts import greeting_instructions_for

logger = logging.getLogger("agent")

# Runtime local env load for the operator process (not for automation/secret scraping).
load_dotenv(".env.local")

config = load_agent_config()
AGENT_NAME = config.agent_name

setup_jaeger_tracing(
    service_name=AGENT_NAME,
    otlp_endpoint=config.otlp_endpoint,
    enabled=config.trace_enabled,
)

server = AgentServer()


def prewarm(proc: JobProcess) -> None:
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


def _wire_session_traces(session: AgentSession, tracer: SessionTracer) -> None:
    """Best-effort hooks for reply timing / EOU (SDK event names vary by version)."""

    def _on(name: str, handler):  # type: ignore[no-untyped-def]
        try:
            session.on(name, handler)
        except Exception:
            logger.debug("Session event %s not available", name)

    turn = {"index": 0}

    def user_end(*_a, **_k):  # type: ignore[no-untyped-def]
        turn["index"] += 1
        tracer.set_turn_index(turn["index"])
        tracer.emit("user_speech_ended", turn_index=turn["index"])

    def agent_start(*_a, **_k):  # type: ignore[no-untyped-def]
        tracer.emit("agent_reply_started", turn_index=tracer.turn_index)

    def agent_end(*_a, **_k):  # type: ignore[no-untyped-def]
        tracer.emit("agent_reply_ended", turn_index=tracer.turn_index)

    _on("user_input_transcribed", user_end)

    def on_agent_state(ev):  # type: ignore[no-untyped-def]
        state = getattr(ev, "new_state", None) or getattr(ev, "state", None)
        if state == "speaking":
            agent_start()
        elif state in {"listening", "idle", "thinking"}:
            # ended speaking when leaving speaking is harder; emit on thinking->speaking start only
            pass

    _on("agent_state_changed", on_agent_state)

    def on_conversation_item(ev):  # type: ignore[no-untyped-def]
        item = getattr(ev, "item", None)
        role = getattr(item, "role", None) if item is not None else None
        if role == "assistant":
            agent_end()

    _on("conversation_item_added", on_conversation_item)


@server.rtc_session(agent_name=AGENT_NAME)
async def my_agent(ctx: JobContext) -> None:
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    room_name = ctx.room.name or "unknown-room"
    tracer = SessionTracer(
        session_id=room_name,
        enabled=config.trace_enabled,
        trace_dir=config.trace_dir,
    )
    tracer.set_room(ctx.room)
    tracer.emit("session_start", room=room_name)

    persona = resolve_persona(
        getattr(ctx.job, "metadata", None) or "",
        kokoro_override=config.kokoro_voice,
    )
    meta = persona.raw_metadata
    requested_mode, _from_meta = resolve_reply_mode_from_metadata(
        meta, config.reply_mode
    )

    actual_mode = requested_mode
    fallback_reason: str | None = None
    if requested_mode == "voice_to_voice":
        ok, reason = voice_to_voice_availability(config)
        if ok:
            ok, reason = await probe_realtime_connection(config)
        if not ok:
            actual_mode = "standard"
            fallback_reason = reason or "voice_to_voice unavailable"

    tracer.emit(
        "persona_applied",
        avatar_gender=persona.avatar_gender,
        session_language=persona.session_language,
        voice_id=(
            persona.realtime_voice
            if actual_mode == "voice_to_voice"
            else persona.kokoro_voice
        ),
        defaults_used=persona.defaults_used,
        reply_mode=actual_mode,
    )
    tracer.emit(
        "reply_mode_selected",
        requested_reply_mode=requested_mode,
        actual_reply_mode=actual_mode,
        fallback_reason=fallback_reason,
    )

    logger.info(
        "Session persona gender=%s language=%s kokoro=%s realtime=%s "
        "requested_mode=%s actual_mode=%s defaults_used=%s fallback=%s",
        persona.avatar_gender,
        persona.session_language,
        persona.kokoro_voice,
        persona.realtime_voice,
        requested_mode,
        actual_mode,
        persona.defaults_used,
        fallback_reason,
    )

    # Best-effort tools in V2V (FR-015); full tools in standard.
    tools_enabled = True
    assistant = create_assistant(
        language=persona.session_language,
        tools_enabled=tools_enabled,
    )
    assistant.apply_update(
        {
            "avatar_gender": persona.avatar_gender,
            "session_language": persona.session_language,
            "kokoro_voice": persona.kokoro_voice,
            "realtime_voice": persona.realtime_voice,
            "reply_mode": actual_mode,
            "requested_reply_mode": requested_mode,
            "defaults_used": persona.defaults_used,
        }
    )

    turn_handling = build_turn_handling(config)
    vad = ctx.proc.userdata["vad"]

    if actual_mode == "voice_to_voice":
        try:
            realtime_llm = build_realtime_model(
                config, voice=persona.realtime_voice
            )
            session = AgentSession(
                vad=vad,
                llm=realtime_llm,
                turn_handling=turn_handling,
            )
            tracer.emit("realtime_response_started", note="session_built")
        except Exception as exc:
            logger.exception("Realtime session build failed; falling back to standard")
            fallback_reason = f"realtime build failed: {exc}"
            actual_mode = "standard"
            assistant.apply_update({"reply_mode": actual_mode})
            tracer.emit(
                "reply_mode_selected",
                requested_reply_mode=requested_mode,
                actual_reply_mode=actual_mode,
                fallback_reason=fallback_reason,
            )
            session = AgentSession(
                vad=vad,
                stt=build_stt(config, language=persona.session_language),
                llm=build_llm(config),
                tts=build_tts(config, voice=persona.kokoro_voice),
                turn_handling=turn_handling,
            )
    else:
        session = AgentSession(
            vad=vad,
            stt=build_stt(config, language=persona.session_language),
            llm=build_llm(config),
            tts=build_tts(config, voice=persona.kokoro_voice),
            turn_handling=turn_handling,
        )

    _wire_session_traces(session, tracer)

    await session.start(
        agent=assistant,
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(),
            # Emit transcripts as soon as text is available so the UI panel updates
            # even if browser autoplay blocks audio until "Start Audio".
            text_output=room_io.TextOutputOptions(sync_transcription=False),
        ),
    )

    await ctx.connect()
    tracer.set_room(ctx.room)
    # Mute must stop listening + discard in-progress STT (UI mute alone is not enough).
    wire_user_mic_gate(session, ctx.room)

    # Publish mode/persona ack for UI (attributes + trace already emitted).
    try:
        await ctx.room.local_participant.set_attributes(
            {
                "avatar_gender": persona.avatar_gender,
                "session_language": persona.session_language,
                "reply_mode": actual_mode,
                "requested_reply_mode": requested_mode,
                "defaults_used": "true" if persona.defaults_used else "false",
                "fallback_reason": fallback_reason or "",
                "voice_id": (
                    persona.realtime_voice
                    if actual_mode == "voice_to_voice"
                    else persona.kokoro_voice
                ),
            }
        )
    except Exception:
        logger.debug("Could not set participant attributes", exc_info=True)

    greeting = assistant.greeting_message()
    logger.info("Greeting ready: %s", greeting[:80])
    await session.generate_reply(
        instructions=greeting_instructions_for(persona.session_language)
    )

    tracer.emit("session_ready", actual_reply_mode=actual_mode)


if __name__ == "__main__":
    cli.run_app(server)
