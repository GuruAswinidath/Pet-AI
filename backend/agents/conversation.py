"""Conversation Agent - README section 2: owns tone, clarity, and
language. It never invents an urgency level or KB guidance - it only
phrases what the deterministic Triage Engine already decided, or asks
one clarifying question when the Triage Engine says information is
missing.
"""

import json
import logging
from typing import Any

import config
from groq_client import chat
from triage_kb import TRIAGE_KB

logger = logging.getLogger(__name__)

_BASE_RULES = """You are the Conversation Agent for a cat-health triage assistant. \
Rules that never change:
- Reply in the language for this session's language_code (e.g. hi-IN means Hindi, \
ta-IN means Tamil, en-IN means English). If unsure of the exact code's language, \
default to simple, clear English.
- Never mention a specific drug name or dosage.
- Never state a diagnosis as fact - describe possibilities and next steps, not certainty.
- Keep replies short: 2-5 sentences, warm and plain-spoken, no medical jargon.
- Never contradict the urgency level or KB guidance you are given - phrase it naturally, don't invent your own."""


def _suggested_questions(missing_info: list[str]) -> dict[str, list[str]]:
    """Looks up each missing_info entry (e.g. "duration_or_severity:vomiting")
    against TRIAGE_KB's per-symptom questions_to_ask, so the Conversation
    Agent has vet-reviewed phrasing to draw from instead of inventing a
    generic question from scratch."""
    hints: dict[str, list[str]] = {}
    for item in missing_info:
        _, _, key = item.partition(":")
        entry = TRIAGE_KB.get(key)
        if entry and entry.get("questions_to_ask"):
            hints[key] = entry["questions_to_ask"]
    return hints


def ask_clarifying_question(session: dict[str, Any], missing_info: list[str]) -> str:
    system_prompt = _BASE_RULES + "\n\nYour job right now: ask exactly ONE short clarifying question " \
        "to fill in the most important missing piece of information. Do not ask multiple questions. " \
        "Do not give any guidance yet - just ask the question. If suggested_questions below has an " \
        "entry for the relevant symptom, prefer asking one of those (in your own natural phrasing) " \
        "over inventing an unrelated question."
    user_prompt = json.dumps(
        {
            "language_code": session.get("language_code"),
            "species": session.get("species"),
            "known_symptoms": session.get("extracted_symptoms"),
            "missing_info": missing_info,
            "suggested_questions": _suggested_questions(missing_info),
        },
        ensure_ascii=False,
    )
    try:
        return chat(config.CONVERSATION_MODEL, system_prompt, user_prompt, temperature=0.4, max_tokens=200)
    except Exception:
        logger.exception("ask_clarifying_question: Groq call failed, using canned fallback")
        return _fallback_clarifying_question(session.get("language_code"))


def draft_reply(session: dict[str, Any], urgency: str, matched_kb_entries: list[str]) -> str:
    kb_context = [
        {
            "symptom": key,
            "label": TRIAGE_KB[key]["label"],
            "owner_guidance": TRIAGE_KB[key]["owner_guidance"],
        }
        for key in matched_kb_entries
        if key in TRIAGE_KB
    ]
    system_prompt = _BASE_RULES + f"""

Your job right now: phrase the final reply for this turn. You are given the \
urgency level ("{urgency}") and matched guidance below - ground your reply in \
these, do not add your own medical judgment.

Urgency meanings:
- emergency: tell them to go to a vet or emergency clinic now.
- soon: tell them to schedule a vet visit within the next day or two, and give the \
relevant owner_guidance as interim guidance.
- home: reassure them it's likely fine to monitor at home for now, give the relevant \
owner_guidance, and mention what would be a reason to seek a vet if it changes."""
    user_prompt = json.dumps(
        {
            "language_code": session.get("language_code"),
            "species": session.get("species"),
            "urgency": urgency,
            "matched_guidance": kb_context,
            "extracted_symptoms": session.get("extracted_symptoms"),
        },
        ensure_ascii=False,
    )
    try:
        return chat(config.CONVERSATION_MODEL, system_prompt, user_prompt, temperature=0.4, max_tokens=350)
    except Exception:
        logger.exception("draft_reply: Groq call failed, using canned fallback")
        return _fallback_reply(urgency, session.get("language_code"))


def regenerate_with_flag(session: dict[str, Any], draft: str, violations: list[str]) -> str:
    system_prompt = _BASE_RULES + f"""

Your previous draft reply failed a safety review for these reasons: {violations}. \
Rewrite the reply so it no longer contains those issues, while keeping the same \
urgency level and guidance. Do not mention the safety review to the user."""
    user_prompt = json.dumps(
        {
            "language_code": session.get("language_code"),
            "previous_draft": draft,
            "violations": violations,
            "urgency": session.get("urgency"),
        },
        ensure_ascii=False,
    )
    try:
        return chat(config.CONVERSATION_MODEL, system_prompt, user_prompt, temperature=0.3, max_tokens=350)
    except Exception:
        logger.exception("regenerate_with_flag: Groq call failed, using canned fallback")
        return _fallback_reply(session.get("urgency") or "soon", session.get("language_code"))


def _fallback_clarifying_question(language_code: str | None) -> str:
    return "Could you tell me how long this has been going on, and whether you've noticed anything else unusual?"


def _fallback_reply(urgency: str, language_code: str | None) -> str:
    if urgency == "emergency":
        return "Based on what you've described, please take your cat to a vet or emergency clinic right away."
    if urgency == "soon":
        return "Based on what you've described, it's best to schedule a vet visit within the next day or two. Keep an eye on your cat in the meantime."
    return "Based on what you've described, it's likely okay to monitor your cat at home for now. If things get worse or don't improve, please see a vet."
