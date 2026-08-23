import os

from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
BHASHINI_API_KEY = os.getenv("BHASHINI_API_KEY", "")

# Model routing per README section 2.1. Overridable via env vars so a
# retired/renamed Groq model ID doesn't require a code change.
ORCHESTRATOR_MODEL = os.getenv("ORCHESTRATOR_MODEL", "openai/gpt-oss-20b")
INTAKE_MODEL = os.getenv("INTAKE_MODEL", "openai/gpt-oss-120b")
CONVERSATION_MODEL = os.getenv("CONVERSATION_MODEL", "openai/gpt-oss-120b")
SAFETY_MODEL = os.getenv("SAFETY_MODEL", "openai/gpt-oss-safeguard-20b")
NOTE_MODEL = os.getenv("NOTE_MODEL", "openai/gpt-oss-20b")
KNOWLEDGE_MODEL = os.getenv("KNOWLEDGE_MODEL", "openai/gpt-oss-120b")

# stt_router.py sends English audio to Groq's Whisper instead of Bhashini -
# Bhashini was chosen for its Indic/code-mixed strength (README 2.1), which
# English doesn't need, and Groq is faster/cheaper for it. Confirmed live:
# "distil-whisper-large-v3-en" is decommissioned as of this writing, so this
# defaults to the turbo model instead of the (dead) English-distilled one.
GROQ_STT_MODEL = os.getenv("GROQ_STT_MODEL", "whisper-large-v3-turbo")

# bhashini_client.py talks to Bhashini's pipeline-compute inference API
# directly over HTTP (no official Python SDK) - endpoint is overridable in
# case a deployment is pinned to a region/version-specific URL.
BHASHINI_ENDPOINT = os.getenv(
    "BHASHINI_ENDPOINT", "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"
)

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


def require_bhashini_key() -> str:
    if not BHASHINI_API_KEY:
        raise RuntimeError(
            "BHASHINI_API_KEY is not set. Add it to backend/.env (copy from .env.example) "
            "to enable speech-to-text / text-to-speech."
        )
    return BHASHINI_API_KEY
