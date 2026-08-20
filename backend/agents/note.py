"""Note Agent - README section 2: at session end, compiles the full
transcript + urgency + guidance into a structured follow-up note. Owns
the document, not the live conversation.
"""

import json
from typing import Any

import config
from groq_client import chat_json

_SYSTEM_PROMPT = """You are the Note Agent for a pet-health triage assistant. \
Given a completed session's structured state, write a short follow-up note a \
pet owner could save or share with a vet. Do not add any new medical judgment \
beyond what's in the session state - summarize it faithfully.

Respond with strict JSON:
{
  "summary": "<2-4 sentence plain-language summary of the concern and outcome>",
  "urgency": "<the urgency level, unchanged>",
  "key_symptoms": ["<short phrase>", ...],
  "recommended_action": "<one sentence, matching the urgency level>",
  "notes_for_vet": "<optional short line useful if this is shown to a vet, or empty string>"
}"""


def generate_followup_note(session: dict[str, Any]) -> dict[str, Any]:
    context = {
        "species": session.get("species"),
        "breed": session.get("breed"),
        "age": session.get("age"),
        "urgency": session.get("urgency"),
        "matched_kb_entries": session.get("matched_kb_entries"),
        "extracted_symptoms": session.get("extracted_symptoms"),
        "safety_flags": session.get("safety_flags"),
        "turns": session.get("turns"),
    }
    try:
        note = chat_json(
            config.NOTE_MODEL,
            _SYSTEM_PROMPT,
            json.dumps(context, ensure_ascii=False),
            temperature=0.2,
            max_tokens=500,
        )
    except Exception:
        note = _fallback_note(session)

    note.setdefault("urgency", session.get("urgency"))
    note.setdefault("key_symptoms", session.get("matched_kb_entries", []))
    return note


def _fallback_note(session: dict[str, Any]) -> dict[str, Any]:
    urgency = session.get("urgency") or "soon"
    symptoms = [s.get("symptom") for s in session.get("extracted_symptoms", []) if s.get("symptom")]
    action = {
        "emergency": "Seek emergency veterinary care now.",
        "soon": "Schedule a vet visit within the next day or two.",
        "home": "Monitor at home; see a vet if things worsen.",
    }.get(urgency, "See a vet if symptoms persist or worsen.")
    return {
        "summary": f"Pet owner reported: {', '.join(symptoms) or 'unspecified symptoms'}.",
        "urgency": urgency,
        "key_symptoms": symptoms,
        "recommended_action": action,
        "notes_for_vet": "",
    }
