"""Unit tests for persona resolver and language-aware prompts (003)."""

from adapters.persona import resolve_persona, resolve_reply_mode_from_metadata
from adapters.voice_map import resolve_kokoro_voice, resolve_realtime_voice
from graph.prompts import (
    GREETING_FALLBACK_TEXT,
    GREETING_INSTRUCTIONS,
    SYSTEM_INSTRUCTIONS,
    greeting_instructions_for,
    system_instructions_for,
)


def test_greeting_not_weather_only() -> None:
    assert "livekit" in GREETING_FALLBACK_TEXT.lower()
    assert "weather" not in GREETING_INSTRUCTIONS.lower()
    assert "weather" not in GREETING_FALLBACK_TEXT.lower()
    assert "screenshot" in GREETING_FALLBACK_TEXT.lower()


def test_system_encourages_general_answers_and_refusal() -> None:
    text = SYSTEM_INSTRUCTIONS.lower()
    assert "conversational" in text
    assert "do not have knowledge" in text
    assert "lookup_weather" in text
    assert "computer_use" in text
    assert "screenshot" in text
    assert "terminal" in text
    assert "type" in text or "search" in text


def test_language_aware_instructions_include_hindi() -> None:
    text = system_instructions_for("hi").lower()
    assert "hindi" in text
    assert "always speak" in text


def test_greeting_instructions_include_language() -> None:
    assert "Spanish" in greeting_instructions_for("es")


def test_resolve_persona_from_metadata() -> None:
    persona = resolve_persona(
        '{"avatar_gender":"male","session_language":"en"}',
        kokoro_override="af_heart",
    )
    assert persona.avatar_gender == "male"
    assert persona.session_language == "en"
    assert persona.kokoro_voice == "am_adam"
    assert persona.defaults_used is False


def test_resolve_persona_defaults_when_missing() -> None:
    persona = resolve_persona(None, kokoro_override="af_heart")
    assert persona.avatar_gender == "female"
    assert persona.session_language == "en"
    assert persona.defaults_used is True
    assert persona.kokoro_voice == "af_heart"


def test_reply_mode_from_metadata_overrides_env() -> None:
    mode, from_meta = resolve_reply_mode_from_metadata(
        {"reply_mode": "voice_to_voice"}, "standard"
    )
    assert mode == "voice_to_voice"
    assert from_meta is True


def test_realtime_voice_map_by_gender() -> None:
    assert resolve_realtime_voice(gender="female") == "marin"
    assert resolve_realtime_voice(gender="male") == "ash"
    assert resolve_kokoro_voice(gender="female", language="hi") == "hf_alpha"
