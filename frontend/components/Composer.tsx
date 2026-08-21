"use client";

import { useRef, useState } from "react";
import { ChatIcon, InfoIcon, MicIcon, SendIcon } from "./icons";

interface ComposerProps {
  onSend: (text: string) => void;
  onToggleRecording: () => void;
  isRecording: boolean;
  isSending: boolean;
  status: string;
  voiceMode: boolean;
  onVoiceModeChange: (voiceMode: boolean) => void;
}

export default function Composer({
  onSend,
  onToggleRecording,
  isRecording,
  isSending,
  status,
  voiceMode,
  onVoiceModeChange,
}: ComposerProps) {
  const [text, setText] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  const handleSend = () => {
    if (!text.trim() || isSending) return;
    onSend(text);
    setText("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const autoResize = (el: HTMLTextAreaElement) => {
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 120) + "px";
  };

  return (
    <div className="composer px-6 pt-3.5 pb-4 shrink-0">
      <div className="max-w-3xl mx-auto">
      <div className="mode-toggle inline-flex rounded-full p-[3px] mb-2.5 gap-[3px]">
        <button
          type="button"
          onClick={() => onVoiceModeChange(false)}
          className={`mode-pill ${!voiceMode ? "active" : ""} inline-flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-[0.82rem] font-semibold cursor-pointer`}
        >
          <ChatIcon className="w-4 h-4" />
          Text
        </button>
        <button
          type="button"
          onClick={() => onVoiceModeChange(true)}
          className={`mode-pill ${voiceMode ? "active" : ""} inline-flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-[0.82rem] font-semibold cursor-pointer`}
        >
          <MicIcon className="w-4 h-4" />
          Voice
        </button>
      </div>

      <div className="flex items-center gap-2.5">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => {
            setText(e.target.value);
            autoResize(e.target);
          }}
          onKeyDown={handleKeyDown}
          placeholder={voiceMode ? "Type, or click the mic to speak..." : "Type your message..."}
          rows={1}
          className="message-input flex-1 resize-none rounded-[22px] px-[18px] py-3 text-[0.94rem] max-h-[120px]"
        />
        <button
          onClick={handleSend}
          disabled={isSending || !text.trim()}
          className="send-btn shrink-0 w-[42px] h-[42px] rounded-full flex items-center justify-center cursor-pointer"
          title="Send"
          aria-label="Send"
        >
          <SendIcon className="w-[18px] h-[18px]" />
        </button>
        <button
          onClick={onToggleRecording}
          className={`mic-standalone ${isRecording ? "recording" : ""} shrink-0 inline-flex items-center gap-2 rounded-full px-4 py-2.5 text-[0.82rem] font-semibold cursor-pointer`}
          title="Click to speak"
          aria-label="Record a voice message"
        >
          <MicIcon className="w-4 h-4" />
          <span className="hidden sm:inline">{isRecording ? "Recording..." : "Click to speak"}</span>
        </button>
      </div>

      <div className="text-[0.78rem] text-[var(--text-muted)] min-h-[1em] mt-2">{status}</div>

      <div className="disclaimer flex items-center justify-center gap-1.5 mt-2 text-[0.74rem] text-center">
        <InfoIcon className="w-3.5 h-3.5 shrink-0" />
        Pet AI provides general information only. Consult a veterinarian for medical advice.
      </div>
      </div>
    </div>
  );
}
