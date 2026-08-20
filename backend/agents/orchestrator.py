"""Orchestrator agent - README section 2: light LLM routing, no medical
judgment. Its only job is deciding which agent handles this turn; it owns
conversation flow, not medical content.
"""

from typing import Any

import config
from groq_client import chat_json

_SYSTEM_PROMPT = """You are the routing layer for a pet-health triage assistant. \
You do not give medical advice and you never decide urgency. For each user \
message, decide whether it belongs to:

- "triage": the user is describing (or continuing to describe) a symptom, \
problem, or concern about a specific pet that needs an urgency assessment. \
This includes answers to a clarifying question the assistant just asked.
- "knowledge": the user is asking a general, non-urgent informational \
question (breed facts, nutrition, general care, "what is X condition") \
that does NOT describe an active symptom happening to their pet right now.

If a message could be read either way, prefer "triage" - it is safer to \
run the deterministic triage check than to skip it.

Respond with strict JSON: {"route": "triage" | "knowledge", "reasoning": "<one short phrase>"}"""


def route_turn(session: dict[str, Any], user_message: str) -> dict[str, str]:
    # Fast path: if we're mid clarifying-question loop, stay in triage
    # without spending an LLM call - the Conversation Agent already framed
    # the last assistant turn as a triage question.
    if session.get("status") == "awaiting_clarification":
        return {"route": "triage", "reasoning": "session awaiting clarification"}

    user_prompt = (
        f"Species on file: {session.get('species') or 'unknown'}\n"
        f"Session status: {session.get('status')}\n"
        f"User message: {user_message}"
    )

    try:
        result = chat_json(config.ORCHESTRATOR_MODEL, _SYSTEM_PROMPT, user_prompt)
        route = result.get("route")
        if route not in ("triage", "knowledge"):
            route = "triage"
        return {"route": route, "reasoning": result.get("reasoning", "")}
    except Exception:
        # When in doubt, route to the safety-checked triage path rather
        # than letting an unclassified message slip to the Knowledge Agent.
        return {"route": "triage", "reasoning": "routing failed, defaulted to triage"}
