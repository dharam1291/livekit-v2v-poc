"""Map avatar gender + session language to Kokoro TTS voice ids."""

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
