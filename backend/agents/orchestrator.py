"""Orchestrator agent - README section 2: light LLM routing, no medical
judgment. Its only job is deciding which agent handles this turn; it owns
conversation flow, not medical content.
"""

import logging
from typing import Any

import config
from groq_client import chat_json

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are the routing layer for a cat-health triage assistant. \
You do not give medical advice and you never decide urgency. For each user \
message, decide whether it belongs to:

- "triage": the user is describing (or continuing to describe) a symptom, \
problem, or concern about a specific cat that needs an urgency assessment. \
This includes answers to a clarifying question the assistant just asked.
- "knowledge": the user is asking a general, non-urgent informational \
question (breed facts, nutrition, general care, "what is X condition") \
that does NOT describe an active symptom happening to their cat right now.

If a message could be read either way, prefer "triage" - it is safer to \
run the deterministic triage check than to skip it.

Respond with strict JSON: {"route": "triage" | "knowledge", "reasoning": "<one short phrase>"}"""

# A short reply (yes/no/a number/"a bit more"/etc.) is essentially never
# how a genuine new general-knowledge question is phrased - those come as
# full sentences. Below this word count, treat it as a continuation of
# existing symptom context rather than asking the LLM to guess.
_SHORT_REPLY_WORD_LIMIT = 4


def route_turn(session: dict[str, Any], user_message: str) -> dict[str, str]:
    # Fast path: if we're mid clarifying-question loop, stay in triage
    # without spending an LLM call - the Conversation Agent already framed
    # the last assistant turn as a triage question.
    if session.get("status") == "awaiting_clarification":
        return {"route": "triage", "reasoning": "session awaiting clarification"}

    # Fast path #2: a session's status flips to "complete" after every
    # final reply, even an underspecified one the user might still add
    # detail to - so the *next* message can be a bare "yes" confirming
    # something safety-relevant (e.g. a fever) with no awaiting_clarification
    # flag protecting it. The Orchestrator LLM sees only bare text with no
    # view of the assistant's last question, and demonstrably misroutes
    # short continuations like "yes" to "knowledge" - which then replies
    # "I don't have that in the knowledge base" instead of ever triaging the
    # detail. A message this short with any prior symptom context is almost
    # certainly a continuation, not a new topic, so skip the LLM guess -
    # unless it's phrased as an actual question ("?"), which the LLM should
    # still get a chance to route properly.
    if (
        session.get("extracted_symptoms")
        and "?" not in user_message
        and len(user_message.split()) <= _SHORT_REPLY_WORD_LIMIT
    ):
        return {"route": "triage", "reasoning": "short reply with existing symptom context"}

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
        logger.exception("route_turn: Groq call failed, defaulting to triage")
        return {"route": "triage", "reasoning": "routing failed, defaulted to triage"}
