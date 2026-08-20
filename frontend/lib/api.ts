import type {
  ConsultTurnRequest,
  ConsultTurnResponse,
  KBAskResponse,
  KBDocument,
  KBMode,
  KBUploadResponse,
} from "./types";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

async function handleJson<T>(response: Response): Promise<T> {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = (data as { detail?: string }).detail || `Request failed (${response.status}).`;
    throw new Error(detail);
  }
  return data as T;
}

export async function consult(payload: ConsultTurnRequest): Promise<ConsultTurnResponse> {
  const res = await fetch(`${API_BASE_URL}/consult`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handleJson(res);
}

export async function consultAudio(params: {
  audio: Blob;
  sessionId: string | null;
  languageCode: string;
  wantAudio: boolean;
}): Promise<ConsultTurnResponse> {
  const form = new FormData();
  form.append("audio", params.audio, "recording.webm");
  if (params.sessionId) form.append("session_id", params.sessionId);
  form.append("language_code", params.languageCode);
  form.append("want_audio", params.wantAudio ? "true" : "false");
  const res = await fetch(`${API_BASE_URL}/consult/audio`, { method: "POST", body: form });
  return handleJson(res);
}

export async function fetchKbDocuments(): Promise<KBDocument[]> {
  const res = await fetch(`${API_BASE_URL}/kb/documents`);
  return handleJson(res);
}

export async function uploadKbDocument(file: File): Promise<KBUploadResponse> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE_URL}/kb/upload`, { method: "POST", body: form });
  return handleJson(res);
}

export async function deleteKbDocument(docId: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/kb/documents/${docId}`, { method: "DELETE" });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error((data as { detail?: string }).detail || "Delete failed.");
  }
}

export async function askKb(payload: {
  query: string;
  mode: KBMode;
  language_code: string;
}): Promise<KBAskResponse> {
  const res = await fetch(`${API_BASE_URL}/kb/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handleJson(res);
}
