"""RAG knowledge store - README section 8.

Entirely separate from the triage KB (triage_kb.py) - this store holds
whatever documents get uploaded for the Knowledge Agent's general-question
answering, and it never influences an urgency decision.

No database server: two flat files on disk under KB_STORE_DIR -
index.json (chunk text + metadata) and vectors.npy (aligned embeddings).
Embeddings run locally via sentence-transformers, no API key needed.
"""

import io
import json
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

import numpy as np

import config

_INDEX_FILENAME = "index.json"
_VECTORS_FILENAME = "vectors.npy"

_embedding_model = None  # lazy singleton, sentence-transformers is slow to import/load


def _index_path() -> str:
    return os.path.join(config.KB_STORE_DIR, _INDEX_FILENAME)


def _vectors_path() -> str:
    return os.path.join(config.KB_STORE_DIR, _VECTORS_FILENAME)


def _load_index() -> list[dict[str, Any]]:
    path = _index_path()
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_index(index: list[dict[str, Any]]) -> None:
    os.makedirs(config.KB_STORE_DIR, exist_ok=True)
    with open(_index_path(), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def _load_vectors(dim: Optional[int] = None) -> np.ndarray:
    path = _vectors_path()
    if not os.path.exists(path):
        return np.zeros((0, dim), dtype=np.float32) if dim else np.zeros((0, 0), dtype=np.float32)
    return np.load(path)


def _save_vectors(vectors: np.ndarray) -> None:
    os.makedirs(config.KB_STORE_DIR, exist_ok=True)
    np.save(_vectors_path(), vectors)


def _get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer

        _embedding_model = SentenceTransformer(config.EMBEDDING_MODEL_NAME)
    return _embedding_model


def embed_texts(texts: list[str]) -> np.ndarray:
    """Embeds a list of strings, L2-normalized so cosine similarity is a
    plain dot product at retrieval time."""
    if not texts:
        return np.zeros((0, 384), dtype=np.float32)
    model = _get_embedding_model()
    vectors = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
    return vectors.astype(np.float32)


def extract_text(file_bytes: bytes, filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(file_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if ext == ".docx":
        from docx import Document

        doc = Document(io.BytesIO(file_bytes))
        return "\n".join(p.text for p in doc.paragraphs)
    if ext in (".md", ".txt"):
        return file_bytes.decode("utf-8", errors="replace")
    raise ValueError(f"Unsupported file type: {ext}. Use pdf, docx, md, or txt.")


def chunk_text(
    text: str,
    chunk_words: int = config.RAG_CHUNK_WORDS,
    overlap_words: int = config.RAG_CHUNK_OVERLAP_WORDS,
) -> list[str]:
    """~chunk_words per chunk, overlap_words overlap, paragraph-aware:
    paragraphs are packed into a chunk until the word budget is hit, then
    the tail of the chunk carries forward as overlap into the next one."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paragraphs:
        return []

    words: list[str] = []
    for p in paragraphs:
        words.extend(p.split())
        words.append("\n\n")  # paragraph boundary marker

    chunks: list[str] = []
    start = 0
    n = len(words)
    while start < n:
        end = min(start + chunk_words, n)
        chunk_words_slice = words[start:end]
        chunk = " ".join(chunk_words_slice).replace(" \n\n ", "\n\n").strip()
        if chunk:
            chunks.append(chunk)
        if end >= n:
            break
        start = end - overlap_words if end - overlap_words > start else end
    return chunks


def ingest_document(filename: str, file_bytes: bytes) -> dict[str, Any]:
    text = extract_text(file_bytes, filename)
    chunks = chunk_text(text)
    if not chunks:
        raise ValueError("No extractable text found in the uploaded document.")

    doc_id = str(uuid.uuid4())
    uploaded_at = datetime.now(timezone.utc).isoformat()

    new_vectors = embed_texts(chunks)

    index = _load_index()
    existing_vectors = _load_vectors(dim=new_vectors.shape[1] if new_vectors.size else None)

    for i, chunk in enumerate(chunks):
        index.append(
            {
                "id": str(uuid.uuid4()),
                "doc_id": doc_id,
                "filename": filename,
                "chunk_index": i,
                "text": chunk,
                "uploaded_at": uploaded_at,
            }
        )

    if existing_vectors.size:
        all_vectors = np.vstack([existing_vectors, new_vectors])
    else:
        all_vectors = new_vectors

    _save_index(index)
    _save_vectors(all_vectors)

    return {"doc_id": doc_id, "filename": filename, "chunk_count": len(chunks)}


def list_documents() -> list[dict[str, Any]]:
    index = _load_index()
    docs: dict[str, dict[str, Any]] = {}
    for entry in index:
        doc_id = entry["doc_id"]
        if doc_id not in docs:
            docs[doc_id] = {
                "doc_id": doc_id,
                "filename": entry["filename"],
                "chunk_count": 0,
                "uploaded_at": entry.get("uploaded_at", ""),
            }
        docs[doc_id]["chunk_count"] += 1
    return list(docs.values())


def delete_document(doc_id: str) -> bool:
    index = _load_index()
    keep_positions = [i for i, entry in enumerate(index) if entry["doc_id"] != doc_id]
    if len(keep_positions) == len(index):
        return False

    vectors = _load_vectors()
    new_index = [index[i] for i in keep_positions]
    new_vectors = vectors[keep_positions] if vectors.size else vectors

    _save_index(new_index)
    _save_vectors(new_vectors)
    return True


def retrieve(query: str, top_k: int = config.RAG_TOP_K) -> list[dict[str, Any]]:
    index = _load_index()
    if not index:
        return []

    vectors = _load_vectors()
    if vectors.size == 0 or len(vectors) != len(index):
        return []

    query_vector = embed_texts([query])[0]
    scores = vectors @ query_vector  # pre-normalized -> dot product == cosine similarity

    top_indices = np.argsort(-scores)[:top_k]
    results = []
    for i in top_indices:
        entry = index[int(i)]
        results.append(
            {
                "doc_id": entry["doc_id"],
                "filename": entry["filename"],
                "text": entry["text"],
                "score": float(scores[int(i)]),
            }
        )
    return results
