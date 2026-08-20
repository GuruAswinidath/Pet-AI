"""README section 6 - save the raw turn-by-turn transcript to disk at
session end. Separate from the structured follow-up note; this is the
plain-text debugging/audit trail."""

import os
from datetime import datetime
from typing import Any

from config import RESULTS_DIR


def save_conversation(session_state: dict[str, Any]) -> str:
    os.makedirs(RESULTS_DIR, exist_ok=True)
    session_id = session_state.get("session_id", "session")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(RESULTS_DIR, f"{session_id}_{timestamp}.txt")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"Session ID: {session_id}\n")
        f.write(f"Language: {session_state.get('language_code', 'unknown')}\n")
        f.write(f"Species: {session_state.get('species', 'unknown')}\n")
        f.write(f"Urgency: {session_state.get('urgency', 'unclassified')}\n")
        f.write("-" * 50 + "\n\n")
        for turn in session_state.get("turns", []):
            role = "You" if turn["role"] == "user" else "Assistant"
            f.write(f"[{turn.get('timestamp', '')}] {role}: {turn['text']}\n\n")
    return filepath
