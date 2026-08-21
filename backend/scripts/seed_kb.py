"""Seeds the RAG knowledge store (README section 8) with the cat health
knowledge documents under backend/knowledge_docs/.

This is entirely separate from the triage KB (triage_kb.py) - these
documents feed the Knowledge Agent's general-question answering via
/kb/ask, not the deterministic urgency decision.

Idempotent by filename: a document already present in the store is
skipped rather than re-ingested as a duplicate. This matters on hosts like
Railway where the filesystem doesn't persist across redeploys (kb_store/
is also gitignored, so it never ships pre-built) - the intended usage
there is running this on every boot to guarantee the store is populated,
which would otherwise pile up duplicate copies on any restart where the
filesystem *did* survive. Delete a document first (Settings panel or
DELETE /kb/documents/{doc_id}) if you want to force a genuine re-ingest.

Usage (from the backend/ directory, with the venv active):
    python scripts/seed_kb.py

No API key is required - embedding runs locally via sentence-transformers,
same as a manual upload through the UI.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag_store import ingest_document, list_documents

_DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "knowledge_docs")


def main() -> None:
    if not os.path.isdir(_DOCS_DIR):
        print(f"No knowledge_docs directory found at {_DOCS_DIR}")
        return

    filenames = sorted(f for f in os.listdir(_DOCS_DIR) if f.endswith(".md"))
    if not filenames:
        print(f"No .md files found in {_DOCS_DIR}")
        return

    already_seeded = {doc["filename"] for doc in list_documents()}

    for filename in filenames:
        if filename in already_seeded:
            print(f"Skipping {filename}: already in the store")
            continue
        path = os.path.join(_DOCS_DIR, filename)
        with open(path, "rb") as f:
            file_bytes = f.read()
        result = ingest_document(filename, file_bytes)
        print(f"Ingested {filename}: {result['chunk_count']} chunks (doc_id={result['doc_id']})")


if __name__ == "__main__":
    main()
