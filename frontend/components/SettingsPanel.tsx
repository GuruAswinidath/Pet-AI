"use client";

import { useEffect, useRef, useState } from "react";
import { askKb, deleteKbDocument, fetchKbDocuments, uploadKbDocument } from "@/lib/api";
import type { KBDocument, KBMode } from "@/lib/types";

interface SettingsPanelProps {
  open: boolean;
  onClose: () => void;
  languageCode: string;
}

export default function SettingsPanel({ open, onClose, languageCode }: SettingsPanelProps) {
  const [mode, setMode] = useState<KBMode>("rag");
  const [docs, setDocs] = useState<KBDocument[]>([]);
  const [docsError, setDocsError] = useState("");
  const [uploadStatus, setUploadStatus] = useState("");
  const [askQuery, setAskQuery] = useState("");
  const [askAnswer, setAskAnswer] = useState("");
  const [asking, setAsking] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const refreshDocuments = async () => {
    try {
      const result = await fetchKbDocuments();
      setDocs(result);
      setDocsError("");
    } catch (err) {
      setDocsError(err instanceof Error ? err.message : String(err));
    }
  };

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    fetchKbDocuments()
      .then((result) => {
        if (!cancelled) {
          setDocs(result);
          setDocsError("");
        }
      })
      .catch((err) => {
        if (!cancelled) setDocsError(err instanceof Error ? err.message : String(err));
      });
    return () => {
      cancelled = true;
    };
  }, [open]);

  const handleUpload = async () => {
    const file = fileInputRef.current?.files?.[0];
    if (!file) {
      setUploadStatus("Choose a file first.");
      return;
    }
    setUploadStatus("Uploading...");
    try {
      const result = await uploadKbDocument(file);
      setUploadStatus(`Uploaded "${result.filename}" (${result.chunk_count} chunks).`);
      if (fileInputRef.current) fileInputRef.current.value = "";
      refreshDocuments();
    } catch (err) {
      setUploadStatus(`Error: ${err instanceof Error ? err.message : String(err)}`);
    }
  };

  const handleDelete = async (docId: string) => {
    try {
      await deleteKbDocument(docId);
      refreshDocuments();
    } catch (err) {
      setUploadStatus(`Delete failed: ${err instanceof Error ? err.message : String(err)}`);
    }
  };

  const handleAsk = async () => {
    if (!askQuery.trim()) return;
    setAsking(true);
    setAskAnswer("Thinking...");
    try {
      const result = await askKb({ query: askQuery, mode, language_code: languageCode });
      let text = result.answer;
      if (result.sources?.length) {
        text += "\n\nSources: " + result.sources.map((s) => `${s.filename} (${s.score.toFixed(2)})`).join(", ");
      }
      setAskAnswer(text);
    } catch (err) {
      setAskAnswer(`Error: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setAsking(false);
    }
  };

  if (!open) return null;

  return (
    <aside className="settings-panel w-[360px] shrink-0 flex flex-col overflow-y-auto fixed inset-0 z-20 md:static md:w-[360px]">
      <div className="settings-header flex items-center justify-between px-5 py-4">
        <h2 className="m-0 text-[1.05rem] font-semibold">Knowledge base</h2>
        <button onClick={onClose} className="icon-btn w-[34px] h-[34px] rounded-lg flex items-center justify-center cursor-pointer" aria-label="Close settings">
          ✕
        </button>
      </div>

      <div className="px-5 py-4 flex flex-col gap-5">
        <section>
          <h3 className="m-0 mb-1.5 text-[0.9rem] font-semibold">Answer mode</h3>
          <p className="text-[0.78rem] text-[var(--text-muted)] leading-relaxed mb-2.5">
            Controls how <code className="settings-hint px-1 rounded">/kb/ask</code> answers general questions.
            This is a comparison tool only - it never affects urgency triage in an actual consultation.
          </p>
          <div className="switch flex rounded-lg overflow-hidden">
            <label className="switch-option flex-1 flex items-center justify-center gap-1.5 px-1.5 py-2 text-[0.8rem] cursor-pointer">
              <input type="radio" name="kbMode" value="kb" checked={mode === "kb"} onChange={() => setMode("kb")} />
              <span>Current case</span>
            </label>
            <label className="switch-option flex-1 flex items-center justify-center gap-1.5 px-1.5 py-2 text-[0.8rem] cursor-pointer">
              <input type="radio" name="kbMode" value="llm" checked={mode === "llm"} onChange={() => setMode("llm")} />
              <span>LLM only</span>
            </label>
            <label className="switch-option flex-1 flex items-center justify-center gap-1.5 px-1.5 py-2 text-[0.8rem] cursor-pointer">
              <input type="radio" name="kbMode" value="rag" checked={mode === "rag"} onChange={() => setMode("rag")} />
              <span>RAG (grounded)</span>
            </label>
          </div>
          {mode === "kb" && (
            <p className="text-[0.72rem] text-[var(--text-muted)] leading-relaxed mt-1.5">
              Exact/alias lookup against the same rule-based knowledge base the live triage flow uses - no AI
              call. Try a known symptom name, e.g. &quot;vomiting&quot; or &quot;urinary obstruction&quot;.
            </p>
          )}
        </section>

        <section>
          <h3 className="m-0 mb-1.5 text-[0.9rem] font-semibold">Upload documents</h3>
          <p className="text-[0.78rem] text-[var(--text-muted)] leading-relaxed mb-2.5">
            PDF, DOCX, MD, or TXT. Chunked and embedded locally, no API key required.
          </p>
          <div className="flex gap-2">
            <input ref={fileInputRef} type="file" accept=".pdf,.docx,.md,.txt" className="flex-1 min-w-0 text-[0.8rem] text-[var(--text-muted)]" />
            <button onClick={handleUpload} className="pill-btn pill-btn-primary rounded-full px-3 py-1.5 text-[0.8rem] font-semibold cursor-pointer">
              Upload
            </button>
          </div>
          {uploadStatus && <div className="upload-status text-[0.78rem] mt-2">{uploadStatus}</div>}
        </section>

        <section>
          <h3 className="m-0 mb-1.5 text-[0.9rem] font-semibold">Documents</h3>
          {docsError && <div className="text-[0.8rem] text-[var(--danger)] mb-2">{docsError}</div>}
          <ul className="list-none m-0 p-0 flex flex-col gap-1.5">
            {docs.length === 0 ? (
              <li className="doc-empty text-[0.8rem]">No documents uploaded yet.</li>
            ) : (
              docs.map((doc) => (
                <li key={doc.doc_id} className="doc-item flex items-center justify-between gap-2 px-2.5 py-2 rounded-lg text-[0.8rem]">
                  <span className="overflow-hidden text-ellipsis whitespace-nowrap" title={doc.filename}>
                    {doc.filename}
                  </span>
                  <span className="doc-meta text-[0.72rem] shrink-0">{doc.chunk_count} chunks</span>
                  <button
                    onClick={() => handleDelete(doc.doc_id)}
                    className="doc-delete border-none bg-transparent cursor-pointer text-[0.9rem] shrink-0"
                    title="Delete document"
                  >
                    ✕
                  </button>
                </li>
              ))
            )}
          </ul>
        </section>

        <section>
          <h3 className="m-0 mb-1.5 text-[0.9rem] font-semibold">Ask a general question</h3>
          <div className="flex gap-2">
            <input
              type="text"
              value={askQuery}
              onChange={(e) => setAskQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleAsk()}
              placeholder="e.g. is it normal for cats to lose baby teeth?"
              className="kb-input flex-1 min-w-0 rounded-lg px-2.5 py-1.5 text-[0.85rem]"
            />
            <button
              onClick={handleAsk}
              disabled={asking}
              className="pill-btn pill-btn-primary rounded-full px-3 py-1.5 text-[0.8rem] font-semibold cursor-pointer disabled:opacity-60"
            >
              Ask
            </button>
          </div>
          {askAnswer && <div className="mt-2.5 text-[0.85rem] leading-relaxed whitespace-pre-wrap">{askAnswer}</div>}
        </section>
      </div>
    </aside>
  );
}
