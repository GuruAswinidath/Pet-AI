"""Shared error type for speech-to-text/text-to-speech provider failures.
STT is now split across two providers (stt_router.py: Groq for English,
Bhashini for Indic languages) - this lets app.py handle either provider's
failure the same way without caring which one actually failed."""

from typing import Optional


class SpeechServiceError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code
