"use client";

import { useCallback, useRef, useState } from "react";
import { consult, consultAudio } from "@/lib/api";
import type { ChatMessage, ConsultTurnResponse, Urgency } from "@/lib/types";

function newId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) return crypto.randomUUID();
  return Math.random().toString(36).slice(2);
}

const WELCOME_TEXT =
  'Hi, I\'m here to help you figure out how urgently your cat needs to see a vet. Tell me what\'s going on - for example, "my cat has been straining to pee since this morning".';

function welcomeMessage(): ChatMessage {
  return { id: newId(), role: "assistant", text: WELCOME_TEXT, timestamp: Date.now(), kind: "normal" };
}

export function useTriageChat() {
  const [messages, setMessages] = useState<ChatMessage[]>(() => [welcomeMessage()]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [urgency, setUrgency] = useState<Urgency | null>(null);
  const [status, setStatus] = useState("");
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const sessionIdRef = useRef<string | null>(null);

  const pushMessage = useCallback((msg: Omit<ChatMessage, "id" | "timestamp">) => {
    setMessages((prev) => [...prev, { ...msg, id: newId(), timestamp: Date.now() }]);
  }, []);

  const applyResponse = useCallback(
    (data: ConsultTurnResponse) => {
      sessionIdRef.current = data.session_id;
      setSessionId(data.session_id);
      pushMessage({ role: "assistant", text: data.reply, kind: "normal" });

      if (data.sources?.length) {
        const text =
          "Sources: " + data.sources.map((s) => `${s.filename} (score ${s.score.toFixed(2)})`).join(", ");
        pushMessage({ role: "assistant", text, kind: "note" });
      }

      setUrgency(data.urgency);

      if (data.is_final && data.followup_note) {
        const note = data.followup_note;
        const lines = [
          "Consultation note (SOAP)",
          note.key_symptoms?.length ? `Key symptoms: ${note.key_symptoms.join(", ")}` : null,
          note.subjective ? `S - Subjective: ${note.subjective}` : null,
          note.objective ? `O - Objective: ${note.objective}` : null,
          note.assessment ? `A - Assessment: ${note.assessment}` : null,
          note.plan ? `P - Plan: ${note.plan}` : null,
          data.transcript_path ? `Transcript saved to: ${data.transcript_path}` : null,
        ].filter((l): l is string => Boolean(l));
        pushMessage({ role: "assistant", text: lines.join("\n\n"), kind: "note" });
      }

      if (data.audio_base64 && audioRef.current) {
        audioRef.current.src = `data:${data.audio_mime_type || "audio/wav"};base64,${data.audio_base64}`;
        audioRef.current.play().catch(() => {});
      }

      setStatus(data.tts_error ? "Voice reply unavailable (text reply shown above)." : "");
    },
    [pushMessage]
  );

  const sendText = useCallback(
    async (text: string, languageCode: string, wantAudio: boolean) => {
      if (!text.trim() || isSending) return;
      setIsSending(true);
      pushMessage({ role: "user", text, kind: "normal" });
      setIsTyping(true);
      setStatus("Thinking...");
      try {
        const data = await consult({
          session_id: sessionIdRef.current,
          message: text,
          language_code: languageCode,
          want_audio: wantAudio,
        });
        applyResponse(data);
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        pushMessage({ role: "assistant", text: `Error: ${message}`, kind: "note" });
        setStatus("");
      } finally {
        setIsTyping(false);
        setIsSending(false);
      }
    },
    [isSending, pushMessage, applyResponse]
  );

  const sendAudio = useCallback(
    async (blob: Blob, languageCode: string, wantAudio: boolean) => {
      if (isSending) return;
      setIsSending(true);
      pushMessage({ role: "user", text: "(voice message)", kind: "normal" });
      setIsTyping(true);
      setStatus("Transcribing...");
      try {
        const data = await consultAudio({
          audio: blob,
          sessionId: sessionIdRef.current,
          languageCode,
          wantAudio,
        });
        applyResponse(data);
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        pushMessage({ role: "assistant", text: `Error: ${message}`, kind: "note" });
        setStatus("");
      } finally {
        setIsTyping(false);
        setIsSending(false);
      }
    },
    [isSending, pushMessage, applyResponse]
  );

  const newSession = useCallback(() => {
    sessionIdRef.current = null;
    setSessionId(null);
    setMessages([welcomeMessage()]);
    setUrgency(null);
    setStatus("");
  }, []);

  return {
    messages,
    sessionId,
    isSending,
    isTyping,
    urgency,
    status,
    sendText,
    sendAudio,
    newSession,
    audioRef,
  };
}
