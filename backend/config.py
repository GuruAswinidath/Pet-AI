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

SARVAM_STT_URL = os.getenv("SARVAM_STT_URL", "https://api.sarvam.ai/speech-to-text")
SARVAM_TTS_URL = os.getenv("SARVAM_TTS_URL", "https://api.sarvam.ai/text-to-speech")
SARVAM_TTS_SPEAKER = os.getenv("SARVAM_TTS_SPEAKER", "meera")
SARVAM_TTS_MODEL = os.getenv("SARVAM_TTS_MODEL", "bulbul:v1")

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5500,http://127.0.0.1:5500",
    ).split(",")
    if origin.strip()
]

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
