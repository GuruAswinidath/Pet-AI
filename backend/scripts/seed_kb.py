"""Seeds the RAG knowledge store (README section 8) with the cat health
knowledge documents under backend/knowledge_docs/.

This is entirely separate from the triage KB (triage_kb.py) - these
documents feed the Knowledge Agent's general-question answering via
/kb/ask, not the deterministic urgency decision. Safe to re-run: it just
adds another copy of each document each time, so delete existing
documents first (via the Settings panel or DELETE /kb/documents/{doc_id})
if you want a clean re-seed instead of duplicates.

Usage (from the backend/ directory, with the venv active):
    python scripts/seed_kb.py

No API key is required - embedding runs locally via sentence-transformers,
same as a manual upload through the UI.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag_store import ingest_document

_DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "knowledge_docs")


def main() -> None:
    if not os.path.isdir(_DOCS_DIR):
        print(f"No knowledge_docs directory found at {_DOCS_DIR}")
        return

    filenames = sorted(f for f in os.listdir(_DOCS_DIR) if f.endswith(".md"))
    if not filenames:
        print(f"No .md files found in {_DOCS_DIR}")
        return

    for filename in filenames:
        path = os.path.join(_DOCS_DIR, filename)
        with open(path, "rb") as f:
            file_bytes = f.read()
        result = ingest_document(filename, file_bytes)
        print(f"Ingested {filename}: {result['chunk_count']} chunks (doc_id={result['doc_id']})")


if __name__ == "__main__":
    main()
