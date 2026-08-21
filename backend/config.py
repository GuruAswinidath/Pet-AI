import os

from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")

# Model routing per README section 2.1. Overridable via env vars so a
# retired/renamed Groq model ID doesn't require a code change.
ORCHESTRATOR_MODEL = os.getenv("ORCHESTRATOR_MODEL", "openai/gpt-oss-20b")
INTAKE_MODEL = os.getenv("INTAKE_MODEL", "openai/gpt-oss-120b")
CONVERSATION_MODEL = os.getenv("CONVERSATION_MODEL", "openai/gpt-oss-120b")
SAFETY_MODEL = os.getenv("SAFETY_MODEL", "openai/gpt-oss-safeguard-20b")
NOTE_MODEL = os.getenv("NOTE_MODEL", "openai/gpt-oss-20b")
KNOWLEDGE_MODEL = os.getenv("KNOWLEDGE_MODEL", "openai/gpt-oss-120b")

# sarvam_client.py uses the official `sarvamai` SDK, which manages its own
# base URL - no endpoint URL config needed here.
#
# Model/speaker compatibility is stricter than it looks: each TTS model
# version has its own speaker roster (a live call 400s with "Speaker 'X' is
# not compatible with model Y" listing the valid ones), and STT/TTS model
# IDs get retired over time (found via real end-to-end testing - "meera"
# and "bulbul:v1", both defaults at one point, are dead now). "shubh" is
# confirmed valid for bulbul:v3 as of this writing.
SARVAM_STT_MODEL = os.getenv("SARVAM_STT_MODEL", "saaras:v3")
SARVAM_TTS_MODEL = os.getenv("SARVAM_TTS_MODEL", "bulbul:v3")
SARVAM_TTS_SPEAKER = os.getenv("SARVAM_TTS_SPEAKER", "shubh")

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5500,http://127.0.0.1:5500",
    ).split(",")
    if origin.strip()
]

# Railway (and most PaaS hosts) inject PORT and require binding to 0.0.0.0
# to accept external traffic - 127.0.0.1 only accepts local-loopback
# connections, which is safe for local dev but silently unreachable once
# deployed (this is what actually caused a 404 on Railway, not a routing
# or CORS issue). Presence of PORT is used as the "we're deployed" signal
# so local `python app.py` behavior is unchanged unless overridden.
PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0" if os.getenv("PORT") else "127.0.0.1")
RELOAD = os.getenv("RELOAD", "false" if os.getenv("PORT") else "true").lower() == "true"

RESULTS_DIR = os.getenv("RESULTS_DIR", "results")
KB_STORE_DIR = os.getenv("KB_STORE_DIR", "kb_store")

# Clarifying-question loop cap - README section 3. After this many
# clarifying questions in one session, stop asking and fall back to the
# most cautious applicable urgency level instead.
MAX_CLARIFYING_QUESTIONS = int(os.getenv("MAX_CLARIFYING_QUESTIONS", "3"))

EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "4"))
RAG_CHUNK_WORDS = int(os.getenv("RAG_CHUNK_WORDS", "220"))
RAG_CHUNK_OVERLAP_WORDS = int(os.getenv("RAG_CHUNK_OVERLAP_WORDS", "40"))


def require_groq_key() -> str:
    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Add it to backend/.env (copy from .env.example) "
            "to enable the LLM agents."
        )
    return GROQ_API_KEY


def require_sarvam_key() -> str:
    if not SARVAM_API_KEY:
        raise RuntimeError(
            "SARVAM_API_KEY is not set. Add it to backend/.env (copy from .env.example) "
            "to enable speech-to-text / text-to-speech."
        )
    return SARVAM_API_KEY
