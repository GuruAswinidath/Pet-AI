"""Knowledge Agent - README section 2 & 8: answers general informational
questions that are NOT urgent triage. It never assigns an urgency to an
active session - that hard boundary is enforced by this module never
writing to session state and never being reachable from turn_processor.py's
triage route (only from the standalone /kb/ask endpoint).

Three answer modes, selectable from the Settings panel's /kb/ask switch:
- "kb"  - a plain, deterministic dictionary lookup against the same
  TRIAGE_KB the Triage Engine uses (triage_engine.normalize_symptom + an
  exact/alias key match). No AI call, no fuzzy matching - this is the
  "current case" / rule-based mode, here purely for side-by-side
  comparison against the two AI modes below. It surfaces the KB entry as
  reference material, not as an urgency verdict for a specific cat.
- "llm" - answered directly from the model, no retrieval.
- "rag" - grounds the answer in retrieved chunks from rag_store.py and is
  instructed to say "I don't have that information" rather than guess
  when retrieval is empty/irrelevant.
"""

import logging
from typing import Any

import config
from groq_client import chat
from rag_store import retrieve
from triage_engine import normalize_symptom
from triage_kb import TRIAGE_KB

logger = logging.getLogger(__name__)

_FALLBACK_ANSWER = (
    "Sorry, I couldn't reach the knowledge model just now. Please try asking again in a moment."
)

_LLM_ONLY_SYSTEM_PROMPT = """You are the Knowledge Agent for a cat-care assistant. \
Answer general, non-urgent informational questions about cat care, breeds, and \
common feline conditions in plain language. Reply in the language matching the given \
language_code where possible.

You must NEVER issue an urgency classification or tell the user whether their \
specific cat's active symptom is an emergency - if the question actually describes \
a current symptom happening to their cat right now, say this needs a proper triage \
conversation instead of answering it here, and suggest they describe the symptom \
directly so it can be assessed.

Never mention specific drug names or dosages. Keep answers concise (3-6 sentences)."""

_RAG_SYSTEM_PROMPT = """You are the Knowledge Agent for a cat-care assistant, answering \
using ONLY the provided reference excerpts - do not use outside knowledge. Reply in the \
language matching the given language_code where possible.

If the excerpts don't contain the answer, say plainly that you don't have that \
information in the knowledge base - do not guess or fill gaps from general knowledge.

You must NEVER issue an urgency classification for an active symptom - if the question \
describes a current symptom happening to their cat right now, say this needs a proper \
triage conversation instead, and suggest they describe the symptom directly.

Never mention specific drug names or dosages. Keep answers concise (3-6 sentences)."""


def answer_from_kb(query: str) -> dict[str, Any]:
    """The "current case" mode: an exact/alias dictionary lookup against
    TRIAGE_KB, same as the live Triage Engine uses - no model call, no
    embeddings, no fuzzy matching. Returns a plain "no match" answer if the
    query doesn't resolve to a known symptom key, rather than guessing."""
    key = normalize_symptom(query)
    entry = TRIAGE_KB.get(key) if key else None
    if not entry:
        return {
            "answer": (
                "No exact match for that in the triage knowledge base. This mode only does a direct "
                "lookup by known symptom name (e.g. \"vomiting\", \"urinary obstruction\") - try the "
                "LLM or RAG modes for a free-form question."
            ),
            "sources": [],
        }
    answer = (
        f"{entry['label']}\n\n"
        f"Typical triage level: {entry['typical_triage_level']}\n\n"
        f"Questions to ask: {' / '.join(entry['questions_to_ask'])}\n\n"
        f"Red flags: {' / '.join(entry['red_flags'])}\n\n"
        f"Owner guidance: {entry['owner_guidance']}"
    )
    return {"answer": answer, "sources": []}


def generate_llm_only_answer(query: str, language_code: str | None) -> str:
    user_prompt = f"language_code: {language_code or 'en-IN'}\nQuestion: {query}"
    try:
        return chat(config.KNOWLEDGE_MODEL, _LLM_ONLY_SYSTEM_PROMPT, user_prompt, temperature=0.3, max_tokens=400)
    except Exception:
        logger.exception("generate_llm_only_answer: Groq call failed")
        return _FALLBACK_ANSWER


def generate_rag_answer(query: str, language_code: str | None) -> dict[str, Any]:
    chunks = retrieve(query, top_k=config.RAG_TOP_K)
    if not chunks:
        excerpts_text = "(no matching excerpts found in the knowledge base)"
    else:
        excerpts_text = "\n\n".join(
            f"[Source: {c['filename']}, score={c['score']:.2f}]\n{c['text']}" for c in chunks
        )
    user_prompt = (
        f"language_code: {language_code or 'en-IN'}\n"
        f"Question: {query}\n\nReference excerpts:\n{excerpts_text}"
    )
    try:
        answer = chat(config.KNOWLEDGE_MODEL, _RAG_SYSTEM_PROMPT, user_prompt, temperature=0.2, max_tokens=400)
    except Exception:
        logger.exception("generate_rag_answer: Groq call failed")
        return {"answer": _FALLBACK_ANSWER, "sources": chunks}
    return {"answer": answer, "sources": chunks}


def answer_general_question(query: str, mode: str, language_code: str | None) -> dict[str, Any]:
    if mode == "kb":
        return answer_from_kb(query)
    if mode == "llm":
        return {"answer": generate_llm_only_answer(query, language_code), "sources": []}
    return generate_rag_answer(query, language_code)
