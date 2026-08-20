"""FastAPI app - README section 7's tool surface, exposed as HTTP endpoints.

/consult, /consult/audio  - the triage flow (README section 3)
/consult/{session_id}     - read back session state
/tts                      - standalone text-to-speech (e.g. "replay" button)
/kb/*                     - the RAG knowledge store (README section 8)

Run directly with `python app.py` - no separate uvicorn command needed.
"""

import logging

import httpx
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

import config
from agents import knowledge as knowledge_agent
from models import (
    ConsultTurnRequest,
    ConsultTurnResponse,
    KBAskRequest,
    KBAskResponse,
    KBDocument,
    KBUploadResponse,
    SessionStateResponse,
    TTSRequest,
    TTSResponse,
)
from sarvam_client import synthesize_speech, transcribe_audio
from session_store import get_session
from transcript import save_conversation
from turn_processor import process_turn

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(title="Pet AI Vet Triage", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "groq_key_configured": bool(config.GROQ_API_KEY),
        "sarvam_key_configured": bool(config.SARVAM_API_KEY),
    }


@app.post("/consult", response_model=ConsultTurnResponse)
def consult(payload: ConsultTurnRequest) -> ConsultTurnResponse:
    try:
        result = process_turn(payload.session_id, payload.message, payload.language_code, payload.want_audio)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return ConsultTurnResponse(**result)


@app.post("/consult/audio", response_model=ConsultTurnResponse)
async def consult_audio(
    audio: UploadFile = File(...),
    session_id: str | None = Form(None),
    language_code: str | None = Form("en-IN"),
    want_audio: bool = Form(True),
) -> ConsultTurnResponse:
    try:
        audio_bytes = await audio.read()
        stt_result = transcribe_audio(audio_bytes, audio.filename or "audio.wav", language_code)
        transcript = stt_result["transcript"]
        if not transcript:
            raise HTTPException(status_code=422, detail="Could not transcribe any speech from the audio.")
        effective_language = stt_result.get("language_code") or language_code
        result = process_turn(session_id, transcript, effective_language, want_audio)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Speech-to-text service error: {exc}") from exc
    return ConsultTurnResponse(**result)


@app.get("/consult/{session_id}", response_model=SessionStateResponse)
def get_consult_session(session_id: str) -> SessionStateResponse:
    session = get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionStateResponse(**session)


@app.post("/consult/{session_id}/end", response_model=SessionStateResponse)
def end_consult_session(session_id: str) -> SessionStateResponse:
    session = get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session["status"] != "complete":
        session["status"] = "complete"
        session["transcript_path"] = save_conversation(session)
    return SessionStateResponse(**session)


@app.post("/tts", response_model=TTSResponse)
def tts(payload: TTSRequest) -> TTSResponse:
    try:
        result = synthesize_speech(payload.text, payload.language_code)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Text-to-speech service error: {exc}") from exc
    return TTSResponse(audio_base64=result["audio_base64"], audio_mime_type=result["audio_mime_type"])


@app.post("/kb/upload", response_model=KBUploadResponse)
async def kb_upload(file: UploadFile = File(...)) -> KBUploadResponse:
    from rag_store import ingest_document

    file_bytes = await file.read()
    try:
        result = ingest_document(file.filename or "document", file_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return KBUploadResponse(**result)


@app.get("/kb/documents", response_model=list[KBDocument])
def kb_documents() -> list[KBDocument]:
    from rag_store import list_documents

    return [KBDocument(**doc) for doc in list_documents()]


@app.delete("/kb/documents/{doc_id}")
def kb_delete_document(doc_id: str) -> dict:
    from rag_store import delete_document

    deleted = delete_document(doc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"deleted": True, "doc_id": doc_id}


@app.post("/kb/ask", response_model=KBAskResponse)
def kb_ask(payload: KBAskRequest) -> KBAskResponse:
    try:
        result = knowledge_agent.answer_general_question(payload.query, payload.mode, payload.language_code)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return KBAskResponse(answer=result["answer"], mode=payload.mode, sources=result.get("sources", []))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
