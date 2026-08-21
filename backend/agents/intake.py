"""Intake Agent - README section 2: turns messy human speech into
structured data. Never decides urgency itself; that's the Triage Engine's
job. Runs on the larger Groq model since clean structured extraction is
the entire point of this agent (README section 2.1).
"""

import json
import logging
from typing import Any

import config
from groq_client import chat_json
from triage_kb import TRIAGE_KB

logger = logging.getLogger(__name__)

_KNOWN_SYMPTOMS = "\n".join(f"- {key}: {entry['label']}" for key, entry in TRIAGE_KB.items())

_SYSTEM_PROMPT = f"""You are the Intake Agent for a cat-health triage assistant. \
This assistant only triages cats. Extract structured fields from the user's \
free-text message about their cat. You do not diagnose anything and you do not \
decide urgency - you only extract what was said.

Known symptom categories (use the key on the left whenever the message clearly \
matches one of these; otherwise put the user's own words in "symptom" and leave \
it unmatched):
{_KNOWN_SYMPTOMS}

Return strict JSON with this exact shape:
{{
  "species": "cat" | "other" | null,
  "breed": "<string or null>",
  "age": "<string or null>",
  "symptoms": [
    {{
      "symptom": "<one of the known keys above, or the user's own short phrase>",
      "duration": "<string or null, e.g. 'since this morning', '2 days'>",
      "severity_cues": ["<short phrases describing severity/red-flag signs mentioned>"]
    }}
  ],
  "additional_notes": "<anything else relevant, or null>"
}}

For "species": set it to "other" ONLY if the message clearly describes a \
different kind of animal (e.g. a dog, bird, or rabbit) rather than a cat - and \
put the animal name in "additional_notes" when you do. Otherwise leave it null; \
the session already assumes "cat" by default, so you don't need to confirm it.

Only extract what the user actually said. Do not invent details. If this message \
answers a previous clarifying question, merge that answer into the appropriate \
field(s) rather than creating an unrelated new symptom entry unless a new one was \
genuinely mentioned."""


def extract_fields(session: dict[str, Any], user_message: str) -> dict[str, Any]:
    context = {
        "species_on_file": session.get("species"),
        "breed_on_file": session.get("breed"),
        "age_on_file": session.get("age"),
        "existing_symptoms": session.get("extracted_symptoms", []),
        "last_assistant_question": _last_assistant_text(session),
    }
    user_prompt = f"Session context:\n{json.dumps(context, ensure_ascii=False)}\n\nNew user message:\n{user_message}"

    try:
        result = chat_json(config.INTAKE_MODEL, _SYSTEM_PROMPT, user_prompt)
    except Exception:
        # Fail safe: no structured extraction, but don't crash the turn -
        # the Triage Engine will see an empty symptom list and respond
        # with a cautious "soon" + missing_info, not silence.
        logger.exception("extract_fields: Groq call failed, returning empty extraction")
        result = {"species": None, "breed": None, "age": None, "symptoms": [], "additional_notes": None}

    result.setdefault("species", None)
    result.setdefault("breed", None)
    result.setdefault("age", None)
    result.setdefault("symptoms", [])
    result.setdefault("additional_notes", None)
    return result


def _last_assistant_text(session: dict[str, Any]) -> str | None:
    for turn in reversed(session.get("turns", [])):
        if turn["role"] == "assistant":
            return turn["text"]
    return None


def merge_into_session(session: dict[str, Any], extracted: dict[str, Any]) -> None:
    if extracted.get("species") == "other":
        # Explicit out-of-scope flag - turn_processor short-circuits the
        # rest of the triage flow when it sees this. Every session already
        # defaults to "cat" (session_store.create_session), so this is the
        # only species value worth writing back.
        session["species"] = "other"
    if extracted.get("breed") and not session.get("breed"):
        session["breed"] = extracted["breed"]
    if extracted.get("age") and not session.get("age"):
        session["age"] = extracted["age"]

    existing = session.setdefault("extracted_symptoms", [])
    existing_keys = {s.get("symptom") for s in existing}
    for symptom in extracted.get("symptoms", []):
        key = symptom.get("symptom")
        if not key:
            continue
        if key in existing_keys:
            # Merge new duration/severity info into the existing entry.
            for existing_symptom in existing:
                if existing_symptom.get("symptom") == key:
                    if symptom.get("duration") and not existing_symptom.get("duration"):
                        existing_symptom["duration"] = symptom["duration"]
                    cues = set(existing_symptom.get("severity_cues") or [])
                    cues.update(symptom.get("severity_cues") or [])
                    existing_symptom["severity_cues"] = list(cues)
        else:
            existing.append(symptom)
            existing_keys.add(key)
