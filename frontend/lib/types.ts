export type Urgency = "emergency" | "soon" | "home";
export type Route = "triage" | "knowledge";
export type KBMode = "kb" | "llm" | "rag";

export interface ConsultTurnRequest {
  session_id: string | null;
  message: string;
  language_code: string;
  want_audio: boolean;
}

/** Consultation note in SOAP format (Subjective / Objective / Assessment / Plan). */
export interface FollowupNote {
  subjective?: string;
  objective?: string;
  assessment?: string;
  plan?: string;
  urgency?: Urgency;
  key_symptoms?: string[];
}

export interface KBAskSource {
  doc_id: string;
  filename: string;
  score: number;
  text: string;
}

export interface ConsultTurnResponse {
  session_id: string;
  route: Route;
  reply: string;
  status: string;
  urgency: Urgency | null;
  matched_kb_entries: string[];
  missing_info: string[];
  safety_flags: string[];
  is_final: boolean;
  audio_base64: string | null;
  audio_mime_type: string | null;
  followup_note: FollowupNote | null;
  transcript_path: string | null;
  sources: KBAskSource[];
  tts_error?: string | null;
}

export interface KBDocument {
  doc_id: string;
  filename: string;
  chunk_count: number;
  uploaded_at: string;
}

export interface KBUploadResponse {
  doc_id: string;
  filename: string;
  chunk_count: number;
}

export interface KBAskResponse {
  answer: string;
  mode: KBMode;
  sources: KBAskSource[];
}

export type MessageKind = "normal" | "note";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  timestamp: number;
  kind: MessageKind;
}

export const LANGUAGES: { code: string; label: string }[] = [
  { code: "en-IN", label: "English" },
  { code: "hi-IN", label: "हिन्दी" },
  { code: "ta-IN", label: "தமிழ்" },
  { code: "te-IN", label: "తెలుగు" },
  { code: "kn-IN", label: "ಕನ್ನಡ" },
  { code: "ml-IN", label: "മലയാളം" },
  { code: "mr-IN", label: "मराठी" },
  { code: "bn-IN", label: "বাংলা" },
  { code: "gu-IN", label: "ગુજરાતી" },
  { code: "pa-IN", label: "ਪੰਜਾਬੀ" },
  { code: "od-IN", label: "ଓଡ଼ିଆ" },
];
