"""Note Agent - README section 2: at session end, compiles the full
transcript + urgency + guidance into a structured follow-up note. Owns
the document, not the live conversation.

The note is written in SOAP format (Subjective / Objective / Assessment /
Plan) - the standard veterinary consultation note structure - so it reads
naturally to both the cat owner and any vet it's shared with.
"""

import json
import logging
from typing import Any

import config
from groq_client import chat_json
from triage_kb import TRIAGE_KB

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are the Note Agent for a cat-health triage assistant. \
Given a completed session's structured state, write a veterinary consultation \
note in SOAP format that a cat owner could save or share with a vet. Do not add \
any new medical judgment beyond what's already in the session state - organize \
and summarize it faithfully. You are documenting this conversation, not \
diagnosing anything.

What each SOAP section means here:
- Subjective: what the owner reported in their own words - the symptom(s), \
duration, severity cues, and any relevant history (age, indoor/outdoor, prior \
episodes) mentioned in the conversation.
- Objective: observable details reported during the conversation only (e.g. \
frequency counts, described appearance of vomit/stool/urine, breathing pattern). \
No physical exam or vitals were performed - say plainly that this is based on \
owner report, not an in-person exam, rather than inventing exam findings.
- Assessment: the triage impression - the matched concern(s) and urgency level, \
phrased as a possibility or a reason to seek care, never as a definitive diagnosis.
- Plan: the recommended action matching the urgency level, home-care guidance for \
the interim, and the specific signs that mean the owner should seek care \
immediately rather than continue waiting.

Respond with strict JSON:
{
  "subjective": "<2-4 sentences>",
  "objective": "<1-3 sentences, explicitly based on owner report, not an exam>",
  "assessment": "<1-3 sentences: urgency + matched concern(s), non-diagnostic>",
  "plan": "<2-4 sentences: recommended action + home care + red flags to watch for>",
  "urgency": "<the urgency level, unchanged>",
  "key_symptoms": ["<short phrase>", ...]
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
            max_tokens=1000,
        )
    except Exception:
        logger.exception("generate_followup_note: Groq call failed, using fallback note")
        note = _fallback_note(session)

    note.setdefault("urgency", session.get("urgency"))
    note.setdefault("key_symptoms", session.get("matched_kb_entries", []))
    return note


def _fallback_note(session: dict[str, Any]) -> dict[str, Any]:
    urgency = session.get("urgency") or "soon"
    symptoms = [s.get("symptom") for s in session.get("extracted_symptoms", []) if s.get("symptom")]
    matched = session.get("matched_kb_entries") or []
    symptom_text = ", ".join(symptoms) if symptoms else "unspecified symptoms"

    action = {
        "emergency": "Seek emergency veterinary care now.",
        "soon": "Schedule a vet visit within the next day or two.",
        "home": "Monitor at home; see a vet if things worsen.",
    }.get(urgency, "See a vet if symptoms persist or worsen.")
    guidance = " ".join(TRIAGE_KB[k]["owner_guidance"] for k in matched if k in TRIAGE_KB)

    return {
        "subjective": f"Owner reported: {symptom_text}.",
        "objective": "Based on the owner's description in this conversation only; no in-person exam was performed.",
        "assessment": f"Triage urgency: {urgency}."
        + (f" Matched concern(s): {', '.join(matched)}." if matched else ""),
        "plan": f"{action} {guidance}".strip(),
        "urgency": urgency,
        "key_symptoms": symptoms,
    }
