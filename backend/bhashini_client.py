"""Bhashini client - Indic speech-to-text and text-to-speech (README section
2.1). Kept as one small separate integration since it's the one piece not
served through Groq: its own API key, its own endpoint.

Talks to Bhashini's pipeline-compute inference API directly over HTTP (the
service has no official Python SDK), selecting an ASR/TTS serviceId per
language the way Bhashini's own examples do.
"""

import base64
import logging
from typing import Any, Optional

import requests

import config
from speech_errors import SpeechServiceError

# The rest of the app (frontend, models.py, session state) uses BCP-47-ish
# codes like "hi-IN" throughout, but Bhashini's pipeline expects bare
# ISO-639-1 codes ("hi"). "od" (Odia, as used by the frontend's language
# picker) isn't actually ISO-639-1 - the real code is "or", so it needs an
# explicit remap rather than just stripping the "-IN" suffix.
_LANGUAGE_OVERRIDES = {"od": "or"}


def _to_bhashini_lang(language_code: Optional[str]) -> str:
    if not language_code:
        return "en"
    bare = language_code.split("-")[0].lower()
    return _LANGUAGE_OVERRIDES.get(bare, bare)


def _headers() -> dict[str, str]:
    config.require_bhashini_key()
    return {
        "Content-Type": "application/json",
        "Authorization": config.BHASHINI_API_KEY,
    }


def _stt_service_id(source_lang: str) -> str:
    if source_lang == "en":
        return "ai4bharat/whisper-medium-en--gpu--t4"
    if source_lang in ("te", "ml", "ta", "kn"):
        return "ai4bharat/conformer-multilingual-dravidian-gpu--t4"
    if source_lang in ("hi", "bn", "mr", "pa", "gu", "or", "as"):
        return "ai4bharat/conformer-multilingual-indo_aryan-gpu--t4"
    raise SpeechServiceError(f"Unsupported source language for STT: {source_lang}")


def transcribe_audio(file_bytes: bytes, filename: str, language_code: Optional[str] = None) -> dict[str, Any]:
    """Speech-to-text via Bhashini's ASR pipeline.
    Returns {"transcript": str, "language_code": str | None}."""
    source_lang = _to_bhashini_lang(language_code)
    service_id = _stt_service_id(source_lang)
    logging.info(f"Bhashini STT call: language={source_lang}, service={service_id}, audio_bytes={len(file_bytes)}")

    audio_b64 = base64.b64encode(file_bytes).decode("utf-8")
    payload = {
        "pipelineTasks": [
            {
                "taskType": "asr",
                "config": {"language": {"sourceLanguage": source_lang}, "serviceId": service_id},
            }
        ],
        "inputData": {"audio": [{"audioContent": audio_b64}]},
    }

    try:
        response = requests.post(url=config.BHASHINI_ENDPOINT, headers=_headers(), json=payload, timeout=90)
        response.raise_for_status()
        out = response.json()
        transcript = out["pipelineResponse"][0]["output"][0]["source"]
    except RuntimeError as exc:
        logging.error(f"Bhashini STT config error: {exc}")
        raise
    except requests.RequestException as exc:
        status_code = exc.response.status_code if exc.response is not None else None
        body = exc.response.text if exc.response is not None else None
        logging.error(f"Bhashini STT API error (status={status_code}): {exc}; body={body}")
        raise SpeechServiceError(f"Bhashini STT request failed: {exc}", status_code=status_code) from exc
    except (KeyError, IndexError) as exc:
        logging.error(f"Bhashini STT parsing failed: {exc}")
        raise SpeechServiceError("Bhashini STT returned an unexpected response shape.") from exc

    logging.info(f"Bhashini STT succeeded: transcript_length={len(transcript or '')}")
    return {"transcript": transcript or "", "language_code": language_code}


def synthesize_speech(
    text: str,
    language_code: str = "en-IN",
    speaker: Optional[str] = None,
) -> dict[str, str]:
    """Text-to-speech via Bhashini's TTS pipeline.
    Returns {"audio_base64": str, "audio_mime_type": str}."""
    target_lang = _to_bhashini_lang(language_code)
    if target_lang not in ("hi", "gu", "bn", "mr", "pa", "or", "as", "ta", "te", "ml", "kn", "en"):
        raise SpeechServiceError(f"Unsupported target language for TTS: {target_lang}")

    logging.info(f"Bhashini TTS call: language={target_lang}, text_length={len(text)}")

    payload = {
        "pipelineTasks": [
            {
                "taskType": "tts",
                "config": {
                    "language": {"sourceLanguage": target_lang},
                    "serviceId": "Bhashini/IITM/TTS",
                    "gender": speaker or "female",
                    "speed": 1.0,
                    "samplingRate": 22050,
                },
            }
        ],
        "inputData": {"input": [{"source": text}]},
    }

    try:
        response = requests.post(url=config.BHASHINI_ENDPOINT, headers=_headers(), json=payload, timeout=90)
        response.raise_for_status()
        out = response.json()
        audio_content = out["pipelineResponse"][0]["audio"][0]["audioContent"]
        audio_format = out["pipelineResponse"][0]["config"]["audioFormat"]
    except RuntimeError as exc:
        logging.error(f"Bhashini TTS config error: {exc}")
        raise
    except requests.RequestException as exc:
        status_code = exc.response.status_code if exc.response is not None else None
        body = exc.response.text if exc.response is not None else None
        logging.error(f"Bhashini TTS API error (status={status_code}): {exc}; body={body}")
        raise SpeechServiceError(f"Bhashini TTS request failed: {exc}", status_code=status_code) from exc
    except (KeyError, IndexError) as exc:
        logging.error(f"Bhashini TTS parsing failed: {exc}")
        raise SpeechServiceError("Bhashini TTS returned an unexpected response shape.") from exc

    if not audio_content:
        logging.error("Bhashini TTS returned an empty audioContent field.")
        raise SpeechServiceError("Bhashini TTS returned no audio.")

    logging.info(f"Bhashini TTS succeeded: audio_format={audio_format}, audio_base64_length={len(audio_content)}")
    return {"audio_base64": audio_content, "audio_mime_type": f"audio/{audio_format}"}


def describe_api_error(exc: SpeechServiceError) -> str:
    """Mirrors sarvam_client's describe_api_error signature so app.py's
    error-handling call sites didn't need to change shape."""
    return str(exc)
