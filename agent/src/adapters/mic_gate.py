"""Pause agent listening when the user mutes their microphone."""

from __future__ import annotations

import contextlib
import logging

import livekit.rtc as rtc
from livekit.agents import AgentSession

logger = logging.getLogger("agent.mic_gate")


def _is_user_microphone(
    room: rtc.Room, participant: rtc.Participant, publication: rtc.TrackPublication
) -> bool:
    """True for a remote human mic publication (not the agent's own tracks)."""
    local = room.local_participant
    if local is not None and participant.identity == local.identity:
        return False
    source = getattr(publication, "source", None)
    return source == rtc.TrackSource.SOURCE_MICROPHONE


def apply_user_mic_muted(session: AgentSession, *, muted: bool) -> None:
    """
    When muted: discard any in-progress user turn and detach audio input so the
    agent neither hears nor replies to audio captured while the mic is off.
    When unmuted: re-attach audio input.
    """
    if muted:
        with contextlib.suppress(RuntimeError):
            session.clear_user_turn()
        session.input.set_audio_enabled(False)
        logger.info("User mic muted — audio input paused and user turn cleared")
    else:
        session.input.set_audio_enabled(True)
        logger.info("User mic unmuted — audio input resumed")


def wire_user_mic_gate(session: AgentSession, room: rtc.Room) -> None:
    """Listen for LiveKit track mute/unmute and gate AgentSession audio input."""

    def on_muted(participant: rtc.Participant, publication: rtc.TrackPublication) -> None:
        if not _is_user_microphone(room, participant, publication):
            return
        apply_user_mic_muted(session, muted=True)

    def on_unmuted(participant: rtc.Participant, publication: rtc.TrackPublication) -> None:
        if not _is_user_microphone(room, participant, publication):
            return
        apply_user_mic_muted(session, muted=False)

    room.on("track_muted", on_muted)
    room.on("track_unmuted", on_unmuted)

    # If the user already joined muted, honour that before the greeting reply path.
    for participant in room.remote_participants.values():
        for publication in participant.track_publications.values():
            if (
                _is_user_microphone(room, participant, publication)
                and getattr(publication, "muted", False)
            ):
                apply_user_mic_muted(session, muted=True)
                return
