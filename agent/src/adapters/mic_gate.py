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
    On mute: discard any in-progress user turn so a half-spoken phrase is not
    committed once the track goes silent.

    Do **not** call ``session.input.set_audio_enabled(False)`` here. Detaching
    input and relying on ``track_unmuted`` to re-attach is unreliable (unmute
    may republish instead of unmute), which left sessions deaf after mute→unmute.
    A muted LiveKit mic already stops media; clearing the turn is enough.
    """
    if muted:
        with contextlib.suppress(RuntimeError):
            session.clear_user_turn()
        logger.info("User mic muted — cleared in-progress user turn")
    else:
        logger.info("User mic unmuted — listening resumed via published audio")


def wire_user_mic_gate(session: AgentSession, room: rtc.Room) -> None:
    """Listen for LiveKit track mute/unmute and clear partial turns on mute."""

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
