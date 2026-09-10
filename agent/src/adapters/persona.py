"""Resolve session persona from job metadata with fail-visible defaults."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from adapters.voice_map import (
    normalize_gender,
    normalize_language,
    resolve_kokoro_voice,
    resolve_realtime_voice,
)

logger = logging.getLogger("agent.persona")


@dataclass(frozen=True)
class AppliedPersona:
    avatar_gender: str
    session_language: str
    kokoro_voice: str
    realtime_voice: str
    defaults_used: bool
    raw_metadata: dict[str, Any]


def parse_job_metadata(metadata: str | None) -> dict[str, Any]:
    if not metadata or not metadata.strip():
        return {}
    try:
        data = json.loads(metadata)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        logger.warning("Ignoring non-JSON job metadata")
        return {}


def resolve_persona(
    metadata: str | None,
    *,
    kokoro_override: str | None = None,
) -> AppliedPersona:
    """
    Resolve avatar gender + language + voices from job metadata.

    Missing/invalid fields coerce to female/en and set defaults_used=True.
    """
    raw = parse_job_metadata(metadata)
    had_gender = bool(raw.get("avatar_gender") or raw.get("avatarGender"))
    had_language = bool(raw.get("session_language") or raw.get("sessionLanguage"))

    gender_raw = raw.get("avatar_gender") or raw.get("avatarGender")
    language_raw = raw.get("session_language") or raw.get("sessionLanguage")

    gender = normalize_gender(str(gender_raw) if gender_raw is not None else None)
    language = normalize_language(str(language_raw) if language_raw is not None else None)

    defaults_used = not (had_gender and had_language)
    if gender_raw is not None and normalize_gender(str(gender_raw)) != str(gender_raw).strip().lower():
        # coerced from invalid
        if str(gender_raw).strip().lower() not in {"male", "female"}:
            defaults_used = True
    if language_raw is not None:
        code = str(language_raw).strip().lower().split("-")[0]
        if code not in {"en", "hi", "es"}:
            defaults_used = True

    has_persona = had_gender or had_language
    kokoro = resolve_kokoro_voice(
        gender=gender,
        language=language,
        override=None if has_persona else kokoro_override,
    )
    realtime = resolve_realtime_voice(gender=gender, language=language)

    return AppliedPersona(
        avatar_gender=gender,
        session_language=language,
        kokoro_voice=kokoro,
        realtime_voice=realtime,
        defaults_used=defaults_used,
        raw_metadata=raw,
    )


def resolve_reply_mode_from_metadata(
    metadata: dict[str, Any],
    env_default: str,
) -> tuple[str, bool]:
    """Return (requested_mode, from_metadata)."""
    from adapters.config import normalize_reply_mode

    raw = metadata.get("reply_mode") or metadata.get("replyMode")
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return normalize_reply_mode(env_default), False
    return normalize_reply_mode(str(raw)), True
