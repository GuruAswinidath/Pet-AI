from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

Urgency = Literal["emergency", "soon", "home"]
Route = Literal["triage", "knowledge"]
KBMode = Literal["kb", "llm", "rag"]


class ConsultTurnRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    language_code: Optional[str] = "en-IN"
    want_audio: bool = False


class ConsultTurnResponse(BaseModel):
    session_id: str
    route: Route
    reply: str
    status: str
    urgency: Optional[Urgency] = None
    matched_kb_entries: list[str] = Field(default_factory=list)
    missing_info: list[str] = Field(default_factory=list)
    safety_flags: list[str] = Field(default_factory=list)
    is_final: bool
    audio_base64: Optional[str] = None
    audio_mime_type: Optional[str] = None
    followup_note: Optional[dict[str, Any]] = None
    transcript_path: Optional[str] = None
    sources: list[dict[str, Any]] = Field(default_factory=list)
    tts_error: Optional[str] = None


class SessionStateResponse(BaseModel):
    session_id: str
    language_code: str
    species: Optional[str] = None
    breed: Optional[str] = None
    age: Optional[str] = None
    turns: list[dict[str, Any]]
    extracted_symptoms: list[dict[str, Any]]
    urgency: Optional[Urgency] = None
    matched_kb_entries: list[str]
    missing_info: list[str]
    safety_flags: list[str]
    status: str
    followup_note: Optional[dict[str, Any]] = None
    transcript_path: Optional[str] = None


class TTSRequest(BaseModel):
    text: str
    language_code: str = "en-IN"


class TTSResponse(BaseModel):
    audio_base64: str
    audio_mime_type: str = "audio/wav"


class KBDocument(BaseModel):
    doc_id: str
    filename: str
    chunk_count: int
    uploaded_at: str


class KBUploadResponse(BaseModel):
    doc_id: str
    filename: str
    chunk_count: int


class KBAskRequest(BaseModel):
    query: str
    mode: KBMode = "rag"
    language_code: Optional[str] = "en-IN"


class KBAskSource(BaseModel):
    doc_id: str
    filename: str
    score: float
    text: str


class KBAskResponse(BaseModel):
    answer: str
    mode: KBMode
    sources: list[KBAskSource] = Field(default_factory=list)
