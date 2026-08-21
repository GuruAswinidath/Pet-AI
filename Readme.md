# AI Vet Triage Chatbot — Multi-Agent Architecture Spec

**Scope: cats only.** This prototype supports cats exclusively - every prompt, the
triage knowledge base, and the test suite are written and reviewed for feline
presentation specifically. See §10 for why that's not just a wording choice (several
symptoms mean something meaningfully different in a cat than in a dog), and
`turn_processor.py` for the out-of-scope redirect that fires if a message clearly
describes a different animal.

High-level flow (see §3 for the full multi-agent breakdown this simplifies):

```
Cat Parent Voice/Text
   |
   v
Speech-to-Text (if voice)
   |
   v
AI Veterinary Assistant (Orchestrator -> Intake -> Triage Engine -> Conversation -> Safety)
   |
   v
Cat Health Knowledge Retrieval (RAG, for general questions - see §5)
   |
   v
Triage Decision (deterministic, never an LLM judgment call - see §1)
   |
   v
Guidance Response
   |
   v
SOAP Consultation Note (see §11)
```

## 1. Design principle before anything else

In an agent framework it's tempting to make everything "an agent." Don't.
**Only the conversational/reasoning parts should be LLM agents. The urgency
decision must stay a deterministic function**, called *by* an agent as a
tool, not decided *by* an agent's judgment. This is the same rule from the
earlier plan — an agent framework doesn't change it, it just gives you a
cleaner way to enforce it (the rules engine becomes a tool with a fixed
output schema that no agent can talk its way around).

---

## 2. Agent roster

| Agent | Type | Job | Owns |
|---|---|---|---|
| **Orchestrator** | LLM agent (light) | Routes the conversation turn to the right agent, tracks session state | Conversation flow, not medical content |
| **Intake Agent** | LLM agent | Extracts structured fields from free-text/voice transcript: species, symptom(s), duration, severity cues, breed/age if mentioned | Turning messy human speech into structured data |
| **Triage Engine** | Deterministic tool (not an LLM) | Takes structured fields → checks against KB (in-prompt, see §4) → returns urgency classification + matched guidance | The safety-critical decision |
| **Conversation Agent** | LLM agent | Takes urgency + KB guidance → asks a clarifying follow-up question OR phrases the final reply naturally, in the user's language | Tone, clarity, language |
| **Safety Agent** | LLM agent (or classifier) | Reviews the Conversation Agent's draft reply before it goes out — checks for drug names, dosages, diagnostic overreach | Final guardrail, veto power |
| **Note Agent** | LLM agent | At end of session, compiles the full transcript + urgency + guidance into a structured follow-up note, and triggers saving the raw transcript to disk (see §8) | The document, not the live conversation |
| **Knowledge Agent** *(optional, see §5)* | LLM agent + RAG | Answers general informational questions that aren't urgent triage ("is this breed prone to X", "what does hip dysplasia mean") | Background info, explicitly not urgency decisions |

This is 5–7 nodes, which is plenty. Resist adding more agents than this for an MVP — each additional agent is another place a conversation can go subtly wrong.

---

## 2.1 Which model for which agent, and where it's served

Your available model catalog is on Groq, plus Sarvam for Indic speech. Map them like this:

| Agent | Model | Source | Why this one |
|---|---|---|---|
| **Orchestrator** | GPT OSS 20B | Groq | Light routing logic — doesn't need your biggest model, keep it fast/cheap |
| **Intake Agent** (extraction) | GPT OSS 120B | Groq | Function-calling/tool-use is where the 120B is listed as strong — this agent's whole job is producing clean structured output, worth the larger model |
| **Triage Engine** | *(not a model)* | — | Plain deterministic Python function, no LLM call at all |
| **Conversation Agent** (reply generation, in-language) | Llama 3.3 70B **or** GPT OSS 120B | Groq | Both are tagged multilingual — test both on real Hindi/regional-language output for tone and pick whichever sounds more natural; Llama 3.3 70B is often the stronger multilingual generator, GPT OSS 120B the stronger instruction-follower for staying inside guardrails. Worth A/B-ing early. |
| **Safety Agent** | Safety GPT OSS 20B | Groq | Purpose-built for exactly this — moderation/guardrail pass on the draft reply before it goes out |
| **Note Agent** | GPT OSS 20B | Groq | Summarization from structured state, doesn't need the largest model |
| **Knowledge Agent** *(optional)* | GPT OSS 120B or Llama 3.3 70B | Groq | Same multilingual generation task as the Conversation Agent, just grounded in RAG context instead of the KB |
| **Vision** *(Phase 3, photo triage)* | Qwen 3.6 27B | Groq | Only model in your set tagged for vision |
| **Speech-to-text** | Sarvam ASR | Sarvam | Chosen over Groq's Whisper specifically for stronger Indic-language and code-mixed speech handling |
| **Text-to-speech** | Sarvam TTS | Sarvam | Groq's Orpheus only covers English/Arabic — no Indic voice output, so Sarvam fills this gap entirely |

Practical note: since Orchestrator, Intake, Conversation, Safety, and Note agents are all on Groq, you can run them through one client/SDK with just the model name changing per call — keeps your code simple. Sarvam is the one separate integration (its own API key, its own client) purely for STT/TTS.

---

## 3. Turn-by-turn flow

```
User speaks
   │
   ▼
[STT: Sarvam] → transcript + language_code
   │
   ▼
Orchestrator: is this a new complaint or a follow-up in an existing session?
   │
   ▼
Intake Agent: extract {species, symptom, duration, severity_cues, additional_notes}
   │
   ▼
Triage Engine (tool call, deterministic):
   input: extracted fields
   output: {urgency: emergency|soon|home, matched_kb_entry, missing_info: [...]}
   │
   ├── if missing_info is non-empty and urgency isn't already "emergency":
   │      → Conversation Agent asks ONE clarifying question, loop back to user
   │
   └── else:
          → Conversation Agent drafts the reply (grounded in matched_kb_entry + urgency)
                │
                ▼
          Safety Agent reviews draft
                │
                ├── fail → Conversation Agent regenerates with the violation flagged,
                │           or falls back to a safe canned message
                │
                └── pass → send to TTS (Sarvam) + display text
                                │
                                ▼
                          Session marked complete →
                          Note Agent generates the follow-up note
```

Key detail: **the clarifying-question loop is capped.** Don't let the Intake/Conversation agents ask indefinitely — 2–3 clarifying questions max, then fall back to the most cautious applicable urgency level ("when in doubt, recommend seeing a vet soon" rather than staying stuck in a loop).

---

## 4. Session state schema

Keep this simple and framework-agnostic — whatever agent framework you use (LangGraph, CrewAI, a custom loop), pass this object between nodes:

```json
{
  "session_id": "uuid",
  "language_code": "hi-IN",
  "species": "cat",
  "breed": null,
  "age": null,
  "turns": [
    {"role": "user", "text": "...", "timestamp": "..."},
    {"role": "assistant", "text": "...", "timestamp": "..."}
  ],
  "extracted_symptoms": [
    {"symptom": "vomiting", "duration": "since this morning", "severity_cues": []}
  ],
  "urgency": "soon",
  "matched_kb_entries": ["Vomiting"],
  "missing_info": [],
  "safety_flags": [],
  "status": "in_progress"
}
```

This whole object is what the Note Agent reads at the end — the follow-up note is just this state, summarized in prose, and it's also what gets written to the results folder as a plain-text transcript (§8).

---

## 4.1 The knowledge base — no database, no file reads at runtime

Decision made: **the KB is not read from a spreadsheet or database at request time.** Instead, bake the (vet-reviewed) KB content directly into the Intake/Triage prompt as a static block — either as literal text in the system prompt, or as a Python constant/dict in code. Same grounding as a file-based lookup, zero I/O, nothing to wire up.

```python
# triage_kb.py — vet-reviewed, static, versioned with your code, cats only
TRIAGE_KB = {
    "vomiting": {
        "label": "Vomiting",
        "typical_triage_level": "varies",  # documentation only, see §10 - engine still decides dynamically
        "questions_to_ask": ["Does the vomit contain hair, food, or fluid?", "..."],
        "red_flags": ["blood in vomit", "distended abdomen", "3+ times in a few hours", "lethargy"],
        "yellow_flags": ["persists past 24 hours"],
        "owner_guidance": "Withhold food a few hours (not water), monitor for repeat episodes.",
    },
    # ... rest of the ~17 entries, see §10
}
```

The Triage Engine (§2, §6) is still a deterministic function — it just reads `TRIAGE_KB` from this in-code constant instead of a JSON/Excel file. This keeps the safety property (fixed, vet-approved, auditable) while dropping the file/database dependency entirely.

---

## 5. The RAG question — direct answer

**For the triage decision itself: no, don't use RAG, and no database either (see §4.1).** Nothing changes here from the earlier recommendation. The Triage Engine should stay a deterministic lookup against the in-code KB (species + symptom → red/yellow flags + guidance), called as a tool. RAG introduces similarity-search fuzziness into exactly the one decision that needs to be predictable and auditable. If a vet reviews and approves "vomiting → these red flags," you want that exact entry retrieved every time someone says "throwing up," not a semantically-similar-but-not-identical entry pulled by embedding search.

**Where RAG *does* earn its place: the optional Knowledge Agent.** If you want the chatbot to also answer general, non-urgent questions — "is it normal for kittens to lose baby teeth," "what's hyperthyroidism in cats," "how much should a 6-month-old kitten weigh" — that's a different job than triage, and a small RAG setup is a reasonable fit there:

- **Corpus**: general cat-care reference material — breed guides, common-condition explainers, care guides. Public/licensed veterinary reference content, not your triage KB (keep those separate). `backend/knowledge_docs/` (§10) is the seed corpus for this prototype - one document per demo scenario plus a cat-toxins reference, ingestible via `backend/scripts/seed_kb.py`.
- **Chunking**: a few hundred words per chunk, by topic/section.
- **Embedding + store**: a lightweight setup is enough at this scale — `sentence-transformers` embeddings into Chroma or pgvector. No need for anything heavier.
- **Retrieval**: top-3–5 chunks, fed to the Knowledge Agent as context, answer generated with citations back to the source doc.
- **Hard boundary**: the Knowledge Agent should never issue an urgency classification. If a "general" question turns out to describe an actual symptom ("is it normal for a cat to vomit up a hairball occasionally" — okay, informational — vs. "my cat has been vomiting for 2 days" — that's triage), the Orchestrator should route it to the Intake Agent/Triage Engine instead, not let the Knowledge Agent free-wheel a medical read on an active symptom.

So: **two knowledge stores, two different retrieval strategies, doing two different jobs** — a deterministic keyed lookup for anything urgency-related, and RAG only for general background Q&A that's explicitly outside the safety-critical path. Build the deterministic one first (you already have it); add the Knowledge Agent + RAG later, once the core triage loop is solid, since it's genuinely optional for an MVP.

---

## 6. Saving the conversation to disk

At session end (right where the Note Agent runs), also write the raw turn-by-turn transcript to a plain `.txt` file in a `results/` folder — separate from the structured follow-up note, useful for your own debugging/logs.

```python
import os
from datetime import datetime

RESULTS_DIR = "results"

def save_conversation(session_state: dict) -> str:
    os.makedirs(RESULTS_DIR, exist_ok=True)
    session_id = session_state.get("session_id", "session")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(RESULTS_DIR, f"{session_id}_{timestamp}.txt")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"Session ID: {session_id}\n")
        f.write(f"Language: {session_state.get('language_code', 'unknown')}\n")
        f.write(f"Species: {session_state.get('species', 'unknown')}\n")
        f.write(f"Urgency: {session_state.get('urgency', 'unclassified')}\n")
        f.write("-" * 50 + "\n\n")
        for turn in session_state.get("turns", []):
            role = "You" if turn["role"] == "user" else "Assistant"
            f.write(f"[{turn.get('timestamp', '')}] {role}: {turn['text']}\n\n")
    return filepath
```

Call this once per completed session, not per turn. `utf-8` encoding matters here specifically — these transcripts will contain Hindi/regional-language text, and some systems don't default to UTF-8, which silently corrupts non-English characters.

---

## 7. Tools each agent needs (function-calling surface)

```
get_kb_entry(species, symptom) -> KBEntry | None       # reads from in-code TRIAGE_KB, §4.1
classify_urgency(extracted_fields) -> {urgency, matched_entry, missing_info}
run_safety_check(draft_reply) -> {passed: bool, violations: [...]}
generate_followup_note(session_state) -> structured note (dict)
save_conversation(session_state) -> filepath            # §6
send_note(note, channel, contact) -> delivery confirmation
[optional] retrieve_general_info(query) -> top-k chunks with sources   # Knowledge Agent only, §5
```

---

## 8. RAG knowledge base — upload, chunk, store, and the LLM/RAG switch

This is now **implemented** in `backend/rag_store.py` and `backend/main.py`, and in the frontend's new Settings panel. It's entirely separate from the triage KB in §4.1 — this store holds whatever PDFs/MD/DOCX you upload for the Knowledge Agent's general-question answering, and it never influences an urgency decision.

**Ingestion pipeline (`rag_store.py`, fully working, no API key needed):**

```
upload file (pdf/docx/md/txt)
   │
   ▼
extract_text()   — pypdf for PDF, python-docx for DOCX, plain read for md/txt
   │
   ▼
chunk_text()     — ~220 words per chunk, 40-word overlap, paragraph-aware
   │
   ▼
embed_texts()    — sentence-transformers (all-MiniLM-L6-v2), runs locally
   │
   ▼
saved to backend/kb_store/  — index.json (chunk text + metadata) + vectors.npy
```

No database server required — it's two flat files on disk. Retrieval (`retrieve()`) embeds the query the same way and does a cosine similarity search (a dot product, since vectors are pre-normalized) over the stored vectors — top-k chunks come back with filename + score.

**Endpoints (`main.py`):**

| Endpoint | Method | Purpose |
|---|---|---|
| `/kb/upload` | POST (multipart file) | Ingest one document — extract, chunk, embed, save. Returns `doc_id` + chunk count. |
| `/kb/documents` | GET | List uploaded documents and their chunk counts |
| `/kb/documents/{doc_id}` | DELETE | Remove a document and its chunks from the store |
| `/kb/ask` | POST `{query, mode, language_code}` | **The LLM/RAG switch.** `mode: "llm"` → answered from the model directly, no retrieval. `mode: "rag"` → retrieves top-4 chunks first, answer is grounded in only those chunks. |

`generate_llm_only_answer()` and `generate_rag_answer()` in `main.py` are the two TODO-wire stubs for this — same pattern as `generate_reply()`, same LLM host, just a different system prompt per mode (see the docstrings in the file for the exact prompt shape). The RAG-mode prompt explicitly tells the model to say "I don't have that information" rather than guessing when retrieval comes back empty or irrelevant — don't skip that instruction, it's what keeps RAG mode from quietly hallucinating when the docs don't cover something.

**Frontend (Settings panel in `index.html`):** a gear-icon toggle reveals a panel with an LLM/RAG switch (radio-style buttons), a file upload + document list, and a text-based "ask" box that calls `/kb/ask` with whichever mode is selected. This is wired to real `fetch()` calls against the backend (not mocked, unlike the voice triage demo above) — run `backend/main.py` for it to work.

**Where this sits relative to the rest of the system:** `/kb/ask` is the Knowledge Agent's endpoint from §2 — a separate path from `/consult` (the triage flow). Nothing here should ever be asked to classify urgency; if a question posed to `/kb/ask` actually describes an active symptom, the right long-term fix is having the Orchestrator route it to `/consult` instead, not answering it here.

---

## 9. What to build first

1. Triage Engine as a standalone, testable function reading the in-code KB (§4.1) — wrap it in `classify_urgency()`.
2. Intake Agent + Conversation Agent + Safety Agent as the minimal loop, single language, text-only, no voice yet — all on Groq per §2.1.
3. `save_conversation()` — trivial, do it early so every test run leaves a trail.
4. Wire in Sarvam STT/TTS once the text loop is solid.
5. Note Agent.
6. Knowledge Agent + RAG (§8) — implemented and ready to use once you add your LLM API key; upload/chunk/embed/retrieve already work standalone.

---

## 10. Cat-specific health scenarios (demo set)

This is the independent research-and-design pass behind the cats-only pivot: not
just relabeling a species-agnostic KB, but identifying where feline presentation of
a symptom actually changes what "urgent" means. Full entries with red/yellow flags
and phrasing live in `backend/triage_kb.py`; the six required demo scenarios are
summarized here alongside the supporting entries added to make the KB coherent.

| Scenario | Typical triage level | Why it's different in cats |
|---|---|---|
| **Urinary obstruction** (`urinary_obstruction`) | Emergency | Far more common in male cats (narrow urethra); a blocked cat can go into fatal kidney failure within 24-48h. This is the single highest-stakes entry in the KB. |
| **Loss of appetite** (`not_eating`) | Soon → emergency past 24-48h | Cats (especially overweight ones) can develop hepatic lipidosis (fatty liver) from as little as 1-2 days without food - a risk that doesn't apply the same way to most other pets. |
| **Vomiting** (`vomiting`) | Varies | The key judgment call is distinguishing a normal occasional hairball from a chronic pattern that, in cats, often signals IBD, hyperthyroidism, or kidney disease rather than being dismissed as "just a hairball cat." |
| **Diarrhoea** (`diarrhea`) | Soon | Same general picture as other species, but kittens dehydrate faster than adult cats, so age materially changes the urgency. |
| **Breathing difficulty** (`difficulty_breathing`) | Emergency (almost always) | Cats don't pant as a normal behavior the way dogs do - open-mouth breathing at rest is essentially always abnormal, and cats mask respiratory distress until it's severe. |
| **Skin issues** (`skin_irritation`) | Home → soon | Usually flea allergy or stress-related overgrooming; escalates only with signs of acute allergic reaction (facial swelling, hives + breathing changes). |

Two supporting entries were added specifically because of a common cat-owner
confusion point and a cat-specific toxin risk, not carried over from a generic KB:

- **Constipation** (`constipation`) - owners frequently can't visually distinguish
  straining-to-urinate from straining-to-defecate. The KB treats these as distinct
  entries with an explicit note in `constipation`'s guidance to default to the
  urinary emergency path whenever there's doubt.
- **Poisoning / toxin ingestion** (`poisoning_ingestion`) - expanded with feline-
  specific toxins: lilies (severely nephrotoxic even from pollen or vase water,
  and not well known as a hazard by most owners), permethrin (safe for dogs, toxic
  to cats - a real and recurring accidental-poisoning source), and onion/garlic.

The remaining entries (`lethargy`, `limping`, `seizure`, `bloated_abdomen`,
`eye_injury`, `ear_infection`, `coughing`, `pain_vocalizing`, `trauma_injury`) were
carried forward and localized for feline presentation - e.g. `bloated_abdomen`'s
guidance no longer references GDV/bloat, which is a large-breed-dog condition rare
in cats; a distended feline abdomen more often points to fluid buildup (FIP, heart,
or liver disease), organomegaly, or parasite load.

Each entry's `questions_to_ask` (vet-reviewed, per symptom) is read by the
Conversation Agent as phrasing hints for its one allowed clarifying question per
turn (`agents/conversation.py`'s `_suggested_questions`), and `owner_guidance` feeds
both the live reply (§3) and the Plan section of the SOAP note (§11).

The same triage content, written in longer explanatory form for retrieval quality,
is seeded into the RAG knowledge store as `backend/knowledge_docs/*.md` - one file
per demo scenario, plus a dedicated cat-toxins reference. Alongside those, the
corpus also includes original general-care documents (kitten care basics,
vaccination schedule, weight/nutrition, dental health, senior cat health, litter
box behavior) covering the non-urgent informational questions the Knowledge Agent
is actually meant to field, per §5. All 13 documents are original writing grounded
in general veterinary knowledge, not reproduced from any single publisher's
copyrighted text - see `backend/scripts/seed_kb.py` to ingest them. This is a
separate corpus from `triage_kb.py` per §5's hard boundary: the RAG copy is for the
Knowledge Agent's general Q&A, never for the urgency decision itself.

---

## 11. Consultation note format — SOAP

The Note Agent (`agents/note.py`) writes the end-of-session consultation note in
**SOAP** format - Subjective / Objective / Assessment / Plan - the standard
veterinary (and broader clinical) note structure, so it reads naturally to both the
cat owner and any vet it's shared with:

- **Subjective** — what the owner reported in their own words: symptom(s),
  duration, severity cues, relevant history (age, indoor/outdoor, prior episodes).
- **Objective** — observable details from the conversation only (frequency counts,
  described appearance of vomit/stool/urine, breathing pattern). No physical exam
  was performed, so this section says so explicitly rather than inventing exam
  findings or vitals.
- **Assessment** — the triage impression: matched concern(s) + urgency level,
  phrased as a possibility or reason to seek care, never a definitive diagnosis.
- **Plan** — the recommended action matching the urgency level, home-care guidance
  for the interim (drawn from the matched KB entries' `owner_guidance`, §10), and
  the specific red-flag signs that mean "stop waiting, seek care now."

Like every other LLM agent output in this system, the Note Agent is a summarizer,
not a decision-maker - it organizes what the deterministic Triage Engine and the
rest of the session state already established, and a fixed, non-LLM fallback note
(same SOAP shape) covers the case where the Groq call itself fails.