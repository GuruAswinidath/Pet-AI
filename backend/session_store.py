"""In-memory session state store.

README section 4's session object, passed between agent "nodes". A plain
process-local dict is enough for the MVP - the transcript itself is what
gets persisted to disk (results/, via save_conversation in transcript.py).
Swap this for a real store (Redis, a DB) later without touching the
agents, which only ever see the dict shape defined here.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

_SESSIONS: dict[str, dict[str, Any]] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_session(language_code: str = "en-IN") -> dict[str, Any]:
    session_id = str(uuid.uuid4())
    session = {
        "session_id": session_id,
        "language_code": language_code or "en-IN",
        "species": None,
        "breed": None,
        "age": None,
        "turns": [],
        "extracted_symptoms": [],
        "urgency": None,
        "matched_kb_entries": [],
        "missing_info": [],
        "safety_flags": [],
        "status": "in_progress",
        "clarify_count": 0,
        "followup_note": None,
        "transcript_path": None,
    }
    _SESSIONS[session_id] = session
    return session


def get_session(session_id: str) -> Optional[dict[str, Any]]:
    return _SESSIONS.get(session_id)


def get_or_create_session(session_id: Optional[str], language_code: str = "en-IN") -> dict[str, Any]:
    if session_id:
        existing = _SESSIONS.get(session_id)
        if existing is not None:
            return existing
    return create_session(language_code)


def save_session(session: dict[str, Any]) -> None:
    _SESSIONS[session["session_id"]] = session


def append_turn(session: dict[str, Any], role: str, text: str) -> None:
    session["turns"].append({"role": role, "text": text, "timestamp": _now()})


def list_sessions() -> list[dict[str, Any]]:
    return list(_SESSIONS.values())
