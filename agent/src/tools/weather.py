"""Demo weather tool for voice-triggered tool use."""

from __future__ import annotations

import logging

logger = logging.getLogger("agent.tools.weather")


def lookup_weather(location: str) -> str:
    """Return a short spoken-friendly weather summary for a location."""
    place = (location or "").strip() or "that location"
    logger.info("Looking up weather for %s", place)
    return (
        f"In {place}, it is sunny with a temperature of 70 degrees Fahrenheit."
    )


def weather_tool_failure_message(location: str) -> str:
    place = (location or "").strip() or "that location"
    return (
        f"I could not look up the weather for {place} right now. "
        "Please try again in a moment."
    )
