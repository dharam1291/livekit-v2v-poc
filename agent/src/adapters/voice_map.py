"""Map avatar gender + session language to Kokoro / Realtime TTS voice ids."""

from __future__ import annotations

from typing import Literal

AvatarGender = Literal["male", "female"]

# Primary English voices available via Speaches Kokoro.
_VOICE_TABLE: dict[tuple[str, str], str] = {
    ("female", "en"): "af_heart",
    ("male", "en"): "am_adam",
    ("female", "hi"): "hf_alpha",
    ("male", "hi"): "hm_omega",
    ("female", "es"): "ef_dora",
    ("male", "es"): "em_alex",
}

_FALLBACK_BY_GENDER: dict[str, str] = {
    "female": "af_heart",
    "male": "am_adam",
}

# OpenAI Realtime built-in voices (gender-oriented mapping for demos).
_REALTIME_BY_GENDER: dict[str, str] = {
    "female": "marin",
    "male": "ash",
}


def normalize_gender(value: str | None) -> AvatarGender:
    return "male" if (value or "").strip().lower() == "male" else "female"


def normalize_language(value: str | None) -> str:
    code = (value or "en").strip().lower().split("-")[0]
    if code in {"en", "hi", "es"}:
        return code
    return "en"


def resolve_kokoro_voice(
    *,
    gender: str | None = None,
    language: str | None = None,
    override: str | None = None,
) -> str:
    """
    Resolve a Kokoro voice id.

    - ``override`` (e.g. process ``KOKORO_VOICE`` when forcing) wins when non-empty.
    - Otherwise map gender+language; unknown language falls back to English same gender;
      unknown pair falls back to ``af_heart`` / ``am_adam``.
    """
    if override and override.strip():
        return override.strip()

    g = normalize_gender(gender)
    lang = normalize_language(language)
    if (g, lang) in _VOICE_TABLE:
        return _VOICE_TABLE[(g, lang)]
    if (g, "en") in _VOICE_TABLE:
        return _VOICE_TABLE[(g, "en")]
    return _FALLBACK_BY_GENDER[g]


def resolve_realtime_voice(
    *,
    gender: str | None = None,
    language: str | None = None,
) -> str:
    """Resolve an OpenAI/Azure Realtime voice id from avatar gender."""
    del language  # language is enforced via instructions; Realtime voice set is gender-first
    g = normalize_gender(gender)
    return _REALTIME_BY_GENDER[g]
