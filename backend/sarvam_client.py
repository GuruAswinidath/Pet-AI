"""Sarvam client - Indic speech-to-text and text-to-speech (README section
2.1). Kept as one small separate integration since it's the one piece not
served through Groq: its own API key, its own client.

Uses the official `sarvamai` SDK rather than hand-rolled HTTP calls - a
previous hand-rolled version silently drifted from Sarvam's actual API
(retired speaker/model defaults causing live 400s, and STT calls that never
specified a model at all), which the typed SDK surfaces at call time instead
of guessing a payload shape.
"""

import io
from typing import Any, Optional

from sarvamai import SarvamAI
from sarvamai.core.api_error import ApiError

import config

_client: Optional[SarvamAI] = None


def _get_client() -> SarvamAI:
    global _client
    if _client is None:
        config.require_sarvam_key()
        _client = SarvamAI(api_subscription_key=config.SARVAM_API_KEY)
    return _client


def transcribe_audio(file_bytes: bytes, filename: str, language_code: Optional[str] = None) -> dict[str, Any]:
    """Speech-to-text via Sarvam's saaras model.
    Returns {"transcript": str, "language_code": str | None}."""
    client = _get_client()

    kwargs: dict[str, Any] = {
        "file": (filename, io.BytesIO(file_bytes)),
        "model": config.SARVAM_STT_MODEL,
        "mode": "transcribe",
    }
    # "unknown" tells Sarvam to auto-detect rather than being pinned to a
    # hint that might be wrong (e.g. a session's default en-IN when the
    # user actually spoke Hindi).
    if language_code and language_code != "unknown":
        kwargs["language_code"] = language_code

    response = client.speech_to_text.transcribe(**kwargs)
    return {
        "transcript": response.transcript or "",
        "language_code": response.language_code or language_code,
    }


def synthesize_speech(
    text: str,
    language_code: str = "en-IN",
    speaker: Optional[str] = None,
) -> dict[str, str]:
    """Text-to-speech via Sarvam's bulbul model.
    Returns {"audio_base64": str, "audio_mime_type": str}."""
    client = _get_client()

    response = client.text_to_speech.convert(
        model=config.SARVAM_TTS_MODEL,
        text=text,
        language_code=language_code,
        speaker=speaker or config.SARVAM_TTS_SPEAKER,
    )

    if not response.audios:
        raise RuntimeError("Sarvam TTS returned no audio.")

    return {"audio_base64": response.audios[0], "audio_mime_type": "audio/wav"}


def describe_api_error(exc: ApiError) -> str:
    """Pulls Sarvam's own error message out of an ApiError's body, falling
    back to the raw body if it isn't the usual {"error": {"message": ...}}
    shape - used by app.py to turn a 429/402/etc. into a useful HTTP detail
    instead of just str(exc)'s headers dump."""
    body = exc.body
    if isinstance(body, dict):
        message = (body.get("error") or {}).get("message") if isinstance(body.get("error"), dict) else None
        if message:
            return message
    return str(body) if body is not None else str(exc)
