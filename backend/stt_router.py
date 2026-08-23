"""Speech-to-text provider routing.

English goes through Groq's Whisper - fast and cheap, and English doesn't
need the Indic/code-mixed strength Bhashini was specifically chosen for
(README 2.1). Every other supported language goes through Bhashini.
"""

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Optional

import groq_client
from bhashini_client import transcribe_audio as _bhashini_transcribe
from speech_errors import SpeechServiceError


def _normalize_audio(file_bytes: bytes, filename: str) -> tuple[bytes, str]:
    if not file_bytes:
        raise SpeechServiceError("Uploaded audio is empty.", status_code=422)

    with tempfile.TemporaryDirectory() as temp_dir:
        source_path = Path(temp_dir) / (Path(filename).name or "recording.webm")
        output_path = Path(temp_dir) / "recording_infer_ready.wav"
        source_path.write_bytes(file_bytes)

        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-i",
                    str(source_path),
                    "-vn",
                    "-ac",
                    "1",
                    "-ar",
                    "16000",
                    str(output_path),
                    "-y",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError as exc:
            raise RuntimeError("ffmpeg is not installed or is not available on PATH.") from exc
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or "audio conversion failed").strip()
            logging.error("Audio conversion failed: %s", detail)
            raise SpeechServiceError(f"Audio conversion failed: {detail}", status_code=422) from exc

        normalized_bytes = output_path.read_bytes()
        if not normalized_bytes:
            raise SpeechServiceError("Audio conversion produced an empty file.", status_code=422)
        return normalized_bytes, "recording.wav"


def transcribe_audio(file_bytes: bytes, filename: str, language_code: Optional[str] = None) -> dict[str, Any]:
    normalized_bytes, normalized_filename = _normalize_audio(file_bytes, filename)
    bare_lang = (language_code or "en-IN").split("-")[0].lower()
    if bare_lang == "en":
        return groq_client.transcribe_audio(normalized_bytes, normalized_filename, language_code)
    return _bhashini_transcribe(normalized_bytes, normalized_filename, language_code)
