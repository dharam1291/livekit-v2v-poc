"""End-of-utterance / endpointing helpers for AgentSession turn_handling."""

from __future__ import annotations

from typing import Any

from adapters.config import AgentConfig


def endpointing_delays_seconds(config: AgentConfig) -> tuple[float, float]:
    """Return (min_delay_sec, max_delay_sec) from ms env knobs."""
    min_s = max(0.05, config.min_endpointing_delay_ms / 1000.0)
    max_s = max(min_s, config.max_endpointing_delay_ms / 1000.0)
    return min_s, max_s


def build_turn_handling(config: AgentConfig) -> dict[str, Any]:
    """
    LiveKit Agents TurnHandlingOptions for local Docker POC.

    IMPORTANT: Always set ``turn_detection="vad"``. Omitting it makes AgentSession
    default to ``inference.TurnDetector()`` (LiveKit Cloud), which 401s locally and
    can break turn-taking / reply playback.
    """
    min_delay, max_delay = endpointing_delays_seconds(config)
    return {
        "turn_detection": "vad",
        "endpointing": {
            "min_delay": min_delay,
            "max_delay": max_delay,
        },
        "interruption": {
            "enabled": True,
            "mode": "vad",
        },
    }
