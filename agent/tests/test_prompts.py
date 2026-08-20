"""Unit tests for prompt policy (002-ux-general-agent)."""

from graph.prompts import (
    GREETING_FALLBACK_TEXT,
    GREETING_INSTRUCTIONS,
    SYSTEM_INSTRUCTIONS,
)


def test_greeting_not_weather_only() -> None:
    assert "livekit" in GREETING_FALLBACK_TEXT.lower()
    assert "weather" not in GREETING_INSTRUCTIONS.lower()
    assert "weather" not in GREETING_FALLBACK_TEXT.lower()


def test_system_encourages_general_answers_and_refusal() -> None:
    text = SYSTEM_INSTRUCTIONS.lower()
    assert "conversational" in text
    assert "do not have knowledge" in text
    assert "lookup_weather" in text
