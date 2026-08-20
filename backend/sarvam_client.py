"""Sarvam client - Indic speech-to-text and text-to-speech (README section
2.1). Kept as one small separate integration since it's the one piece not
served through Groq: its own API key, its own client.

Endpoint/payload shapes follow Sarvam's public Speech APIs as documented
at https://docs.sarvam.ai at the time this was written. Sarvam's API
surface has changed before - if a call here starts failing with an
unexpected shape, check that doc first.
"""

import base64
from typing import Any, Optional

import httpx

import config


def transcribe_audio(file_bytes: bytes, filename: str, language_code: Optional[str] = None) -> dict[str, Any]:
    """POST multipart audio to Sarvam's speech-to-text endpoint.
    Returns {"transcript": str, "language_code": str | None}."""
    config.require_sarvam_key()

    data = {}
    if language_code:
        data["language_code"] = language_code

    files = {"file": (filename, file_bytes)}
    headers = {"api-subscription-key": config.SARVAM_API_KEY}

    with httpx.Client(timeout=30.0) as client:
        response = client.post(config.SARVAM_STT_URL, headers=headers, data=data, files=files)
        response.raise_for_status()
        payload = response.json()

    return {
        "transcript": payload.get("transcript", ""),
        "language_code": payload.get("language_code", language_code),
    }


def synthesize_speech(
    text: str,
    language_code: str = "en-IN",
    speaker: Optional[str] = None,
) -> dict[str, str]:
    """POST text to Sarvam's text-to-speech endpoint.
    Returns {"audio_base64": str, "audio_mime_type": str}."""
    config.require_sarvam_key()

    headers = {
        "api-subscription-key": config.SARVAM_API_KEY,
        "Content-Type": "application/json",
    }
    body = {
        "inputs": [text],
        "target_language_code": language_code,
        "speaker": speaker or config.SARVAM_TTS_SPEAKER,
        "model": config.SARVAM_TTS_MODEL,
        "pitch": 0,
        "pace": 1.0,
        "loudness": 1.0,
        "speech_sample_rate": 16000,
        "enable_preprocessing": True,
    }

    with httpx.Client(timeout=30.0) as client:
        response = client.post(config.SARVAM_TTS_URL, headers=headers, json=body)
        response.raise_for_status()
        payload = response.json()

    audios = payload.get("audios") or []
    if not audios:
        raise RuntimeError("Sarvam TTS returned no audio.")

    # Validate it's actually base64 rather than trusting the API blindly.
    base64.b64decode(audios[0], validate=True)

    return {"audio_base64": audios[0], "audio_mime_type": "audio/wav"}
