"""Wires one conversation turn through the flow in README section 3:

Orchestrator -> (Knowledge Agent) or (Intake Agent -> Triage Engine ->
Conversation Agent -> Safety Agent) -> optional TTS -> Note Agent +
save_conversation once the session reaches a final, non-clarifying reply.

This assistant is cat-only: if the Intake Agent flags species as "other"
(a different animal was clearly described), the triage route short-circuits
with a polite out-of-scope reply instead of running it through the Triage
Engine, which is only vet-reviewed for cats (triage_kb.py).

Shared by the /consult and /consult/audio endpoints in main.py.
"""

from typing import Any, Optional

import config
from agents import conversation as conversation_agent
from agents import knowledge as knowledge_agent
from agents import note as note_agent
from agents import orchestrator as orchestrator_agent
from agents import safety as safety_agent
from agents.intake import extract_fields, merge_into_session
from session_store import append_turn, get_or_create_session, save_session
from transcript import save_conversation
from triage_engine import apply_clarify_cap_fallback, classify_urgency

_CANNED_SAFE_MESSAGE = {
    "emergency": "Please take your cat to a vet or emergency clinic as soon as possible.",
    "soon": "Please schedule a vet visit within the next day or two to have this looked at.",
    "home": "It's likely okay to keep an eye on your cat at home for now, but please see a vet if things don't improve.",
}

_OUT_OF_SCOPE_MESSAGE = (
    "I'm built specifically to help with cats right now, so I can't safely triage a different "
    "animal here. Please contact your vet directly, or start a new chat to ask about a cat."
)


def process_turn(
    session_id: Optional[str],
    user_text: str,
    language_code: Optional[str],
    want_audio: bool = False,
) -> dict[str, Any]:
    session = get_or_create_session(session_id, language_code or "en-IN")
    if language_code:
        session["language_code"] = language_code
    append_turn(session, "user", user_text)

    routing = orchestrator_agent.route_turn(session, user_text)
    route = routing["route"]

    if route == "knowledge":
        result = knowledge_agent.answer_general_question(user_text, "rag", session["language_code"])
        reply_text = result["answer"]
        append_turn(session, "assistant", reply_text)
        save_session(session)
        response = _build_response(session, route, reply_text, is_final=True, sources=result.get("sources", []))
        _maybe_attach_audio(response, reply_text, session["language_code"], want_audio)
        return response

    # --- triage route ---
    extracted = extract_fields(session, user_text)
    merge_into_session(session, extracted)

    if session.get("species") == "other":
        session["status"] = "complete"
        session["urgency"] = None
        session["matched_kb_entries"] = []
        session["missing_info"] = []
        append_turn(session, "assistant", _OUT_OF_SCOPE_MESSAGE)
        transcript_path = save_conversation(session)
        session["transcript_path"] = transcript_path
        save_session(session)
        response = _build_response(
            session, route, _OUT_OF_SCOPE_MESSAGE, is_final=True, transcript_path=transcript_path
        )
        _maybe_attach_audio(response, _OUT_OF_SCOPE_MESSAGE, session["language_code"], want_audio)
        return response

    triage_result = classify_urgency(session["extracted_symptoms"], session.get("species"))
    session["urgency"] = triage_result["urgency"]
    session["matched_kb_entries"] = triage_result["matched_kb_entries"]
    session["missing_info"] = triage_result["missing_info"]

    cap_hit = session["clarify_count"] >= config.MAX_CLARIFYING_QUESTIONS
    needs_clarification = bool(triage_result["missing_info"]) and triage_result["urgency"] != "emergency"

    if needs_clarification and not cap_hit:
        question = conversation_agent.ask_clarifying_question(session, triage_result["missing_info"])
        session["clarify_count"] += 1
        session["status"] = "awaiting_clarification"
        append_turn(session, "assistant", question)
        save_session(session)
        response = _build_response(session, route, question, is_final=False)
        _maybe_attach_audio(response, question, session["language_code"], want_audio)
        return response

    if needs_clarification and cap_hit:
        triage_result = apply_clarify_cap_fallback(triage_result)
        session["urgency"] = triage_result["urgency"]

    draft = conversation_agent.draft_reply(session, session["urgency"], session["matched_kb_entries"])
    safety_result = safety_agent.run_safety_check(draft)

    if not safety_result["passed"]:
        draft = conversation_agent.regenerate_with_flag(session, draft, safety_result["violations"])
        safety_result_2 = safety_agent.run_safety_check(draft)
        if not safety_result_2["passed"]:
            draft = _CANNED_SAFE_MESSAGE.get(session["urgency"], _CANNED_SAFE_MESSAGE["soon"])
            safety_result_2["violations"].append("fell_back_to_canned_message")
        session["safety_flags"] = safety_result["violations"] + safety_result_2["violations"]
    else:
        session["safety_flags"] = []

    session["status"] = "complete"
    append_turn(session, "assistant", draft)

    note = note_agent.generate_followup_note(session)
    transcript_path = save_conversation(session)
    session["followup_note"] = note
    session["transcript_path"] = transcript_path
    save_session(session)

    response = _build_response(
        session,
        route,
        draft,
        is_final=True,
        followup_note=note,
        transcript_path=transcript_path,
    )
    _maybe_attach_audio(response, draft, session["language_code"], want_audio)
    return response


def _build_response(
    session: dict[str, Any],
    route: str,
    reply: str,
    *,
    is_final: bool,
    sources: Optional[list[dict[str, Any]]] = None,
    followup_note: Optional[dict[str, Any]] = None,
    transcript_path: Optional[str] = None,
) -> dict[str, Any]:
    return {
        "session_id": session["session_id"],
        "route": route,
        "reply": reply,
        "status": session["status"],
        "urgency": session.get("urgency") if route == "triage" else None,
        "matched_kb_entries": session.get("matched_kb_entries", []) if route == "triage" else [],
        "missing_info": session.get("missing_info", []) if route == "triage" else [],
        "safety_flags": session.get("safety_flags", []),
        "is_final": is_final,
        "audio_base64": None,
        "audio_mime_type": None,
        "followup_note": followup_note,
        "transcript_path": transcript_path,
        "sources": sources or [],
    }


def _maybe_attach_audio(response: dict[str, Any], text: str, language_code: str, want_audio: bool) -> None:
    if not want_audio:
        return
    try:
        from sarvam_client import synthesize_speech

        tts = synthesize_speech(text, language_code)
        response["audio_base64"] = tts["audio_base64"]
        response["audio_mime_type"] = tts["audio_mime_type"]
    except Exception as exc:
        # Voice is a nice-to-have on top of the text reply, which the user
        # already has - don't fail the whole turn if TTS is unavailable.
        response.setdefault("safety_flags", [])
        response["tts_error"] = str(exc)
