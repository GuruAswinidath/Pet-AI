"""Safety Agent - README section 2: final guardrail with veto power over
the Conversation Agent's draft reply. Checks for drug names, dosages,
and diagnostic overreach before anything goes out to the user.
"""

from typing import Any

import config
from groq_client import chat_json

_SYSTEM_PROMPT = """You are the Safety Agent for a pet-health triage assistant. \
You review a draft reply before it is sent to a pet owner. Flag it as failing if \
it contains ANY of the following:
- a specific drug/medication name (human or veterinary)
- a specific dosage, quantity, or frequency of any substance
- a definitive diagnosis stated as fact (e.g. "your dog has parvo") rather than a \
  possibility or a reason to see a vet
- any instruction that could delay urgent care for a genuinely dangerous symptom

Respond with strict JSON: {"passed": true|false, "violations": ["<short reason>", ...]}
If there are no issues, return {"passed": true, "violations": []}."""


def run_safety_check(draft_reply: str) -> dict[str, Any]:
    try:
        result = chat_json(
            config.SAFETY_MODEL,
            _SYSTEM_PROMPT,
            f"Draft reply to review:\n{draft_reply}",
            temperature=0.0,
            max_tokens=300,
        )
        passed = bool(result.get("passed", False))
        violations = result.get("violations") or []
        return {"passed": passed, "violations": violations}
    except Exception as exc:
        # Fail closed: if the safety check itself breaks, treat the draft
        # as not-passed so the caller falls back to a canned safe message
        # rather than silently skipping the guardrail.
        return {"passed": False, "violations": [f"safety_check_error: {exc}"]}
