# Pet AI - Cat Vet Triage Assistant

An AI-assisted symptom triage chatbot for **cats**: a cat owner describes what's
going on, a small pipeline of LLM agents plus one **deterministic** rules engine
decides how urgent it is (`emergency` / `soon` / `home`), and a SOAP-format
consultation note + transcript are saved at the end of the conversation. Text and
voice (Sarvam STT/TTS), multilingual (English + 10 Indic languages), plus a
separate RAG-backed knowledge base for general (non-urgent) cat-care questions.

This prototype supports cats only - every prompt, the triage knowledge base, and
the RAG corpus are written and reviewed for feline presentation specifically (see
`flow.md` §10 for the research behind that). A message that clearly describes a
different animal gets a polite out-of-scope reply instead of being triaged.

Full architecture spec: [`flow.md`](flow.md). Short version below.

## How it works

1. **Orchestrator** (light LLM call) - routes each message to the triage flow or
   the general-knowledge flow.
2. **Intake Agent** (LLM) - extracts structured fields (species, symptom, duration,
   severity cues) from free text; flags species as out-of-scope if the message
   clearly describes a non-cat animal.
3. **Triage Engine** (`backend/triage_engine.py`) - a **plain deterministic Python
   function**, not an LLM. It looks the symptom up in a vet-reviewed static
   knowledge base (`backend/triage_kb.py`, cat-only) and returns an urgency level.
   This is the safety-critical decision, and it's intentionally never left to an
   LLM's judgment - the agents only ever report what this function decided.
4. **Conversation Agent** (LLM) - either asks one clarifying question (max 3 per
   session, drawing on each symptom's vet-reviewed `questions_to_ask`, then falls
   back to a cautious urgency) or phrases the final reply.
5. **Safety Agent** (LLM) - reviews the draft reply for drug names/dosages/overreach
   before it goes out; failing replies get regenerated or replaced with a canned
   safe message.
6. **Note Agent** (LLM) - writes a **SOAP-format** consultation note (Subjective /
   Objective / Assessment / Plan) at session end; the raw transcript is also saved
   to `backend/results/`.
7. **Knowledge Agent** + RAG (`backend/rag_store.py`) - answers general questions
   ("is it normal for kittens to lose baby teeth?") grounded in documents you
   upload - seed it with the cat health docs in `backend/knowledge_docs/` via
   `python scripts/seed_kb.py` - completely separate from the triage knowledge base.

All LLM agents run on Groq; Sarvam handles speech-to-text/text-to-speech.

## Project layout

```
Pet AI/
  flow.md             - full architecture spec (source of truth for design decisions)
  Readme.md           - this file (setup + quick reference)
  backend/            - FastAPI service (Python)
  frontend/           - Next.js app (TypeScript, Tailwind, App Router)
```

## Prerequisites

- Python 3.11+ (developed on 3.12)
- Node.js 20.9+ and npm
- A [Groq](https://console.groq.com) API key (for the LLM agents)
- A [Sarvam](https://www.sarvam.ai) API key (only needed for voice - the app runs
  fine without it, voice requests just return a clear error)

## Clone and set up

```bash
git clone <your-fork-or-repo-url> "Pet AI"
cd "Pet AI"
```

### 1. Backend (FastAPI)

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt

copy .env.example .env        # Windows
# cp .env.example .env        # macOS/Linux
```

Open `backend/.env` and set:

```
GROQ_API_KEY=your-groq-key
SARVAM_API_KEY=your-sarvam-key   # optional, only for voice
```

Run it:

```bash
python app.py
```

The API is now at `http://127.0.0.1:8000` (interactive docs at `/docs`). Without
`GROQ_API_KEY`/`SARVAM_API_KEY` set, the deterministic parts (triage engine, RAG
upload/retrieval, session flow) still work - LLM/voice calls just return a clear
503 instead of crashing.

Optionally, seed the RAG knowledge base with the cat health documents in
`backend/knowledge_docs/` (no API key needed - embedding runs locally):

```bash
python scripts/seed_kb.py
```

### 2. Frontend (Next.js)

In a second terminal:

```bash
cd frontend
npm install
copy .env.local.example .env.local   # Windows
# cp .env.local.example .env.local   # macOS/Linux
npm run dev
```

Open `http://localhost:3000`. `frontend/.env.local` sets `NEXT_PUBLIC_API_BASE_URL`
(defaults to `http://127.0.0.1:8000`) - change it if the backend runs elsewhere.

### Running both together

You need both processes running at the same time, in separate terminals: the
backend on port 8000, the frontend on port 3000. The backend's `CORS_ORIGINS`
(in `backend/.env`) already allows `http://localhost:3000` by default.

## Key environment variables

| File | Variable | Purpose |
|---|---|---|
| `backend/.env` | `GROQ_API_KEY` | Required for all LLM agents (Orchestrator, Intake, Conversation, Safety, Note, Knowledge) |
| `backend/.env` | `SARVAM_API_KEY` | Required only for voice input/output |
| `backend/.env` | `CORS_ORIGINS` | Comma-separated origins allowed to call the API |
| `backend/.env` | `*_MODEL` | Override any agent's Groq model ID (see comments in `.env.example`) |
| `frontend/.env.local` | `NEXT_PUBLIC_API_BASE_URL` | Where the frontend sends API requests |

## Testing

```bash
cd backend
python -m unittest tests.test_triage_engine -v
```

This exercises the deterministic triage engine in isolation (red-flag detection,
yellow-flag detection, missing-info handling, clarify-cap fallback) with no API
keys required.
