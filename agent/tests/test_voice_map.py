"""Unit tests for Kokoro voice mapping."""

from adapters.voice_map import resolve_kokoro_voice


def test_english_female_default() -> None:
    assert resolve_kokoro_voice(gender="female", language="en") == "af_heart"


def test_english_male() -> None:
    assert resolve_kokoro_voice(gender="male", language="en") == "am_adam"


def test_unknown_language_falls_back_to_english_gender() -> None:
    assert resolve_kokoro_voice(gender="male", language="zz") == "am_adam"
    assert resolve_kokoro_voice(gender="female", language="zz") == "af_heart"


def test_override_wins() -> None:
    assert (
        resolve_kokoro_voice(gender="male", language="en", override="af_heart")
        == "af_heart"
    )


def test_normalize_male_case() -> None:
    assert resolve_kokoro_voice(gender="MALE", language="EN") == "am_adam"
