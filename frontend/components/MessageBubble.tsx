import { renderContent } from "@/lib/markdown";
import type { ChatMessage, MessageKind } from "@/lib/types";
import { AlertTriangleIcon, ClipboardIcon, InfoIcon, PawIcon, PersonIcon } from "./icons";

function formatTime(timestamp: number): string {
  // Explicit locale, not the runtime default ([]) - Node's ICU data and the
  // browser's often disagree on default hour format (24h vs 12h), which
  // otherwise reliably mismatches server-rendered vs. client-hydrated text
  // for the very first (welcome) message's timestamp.
  return new Date(timestamp).toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
}

const NOTE_META: Partial<
  Record<MessageKind, { icon: React.ComponentType<{ className?: string }>; label: string; extraClass: string }>
> = {
  note: { icon: ClipboardIcon, label: "Consultation note", extraClass: "" },
  sources: { icon: InfoIcon, label: "Sources", extraClass: "bubble-note-muted" },
  error: { icon: AlertTriangleIcon, label: "Something went wrong", extraClass: "bubble-note-error" },
};

export default function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  const meta = NOTE_META[message.kind];

  const avatar = (
    <div className="flex flex-col items-center gap-1 shrink-0">
      <div
        className={`avatar-${message.role} w-[34px] h-[34px] rounded-full flex items-center justify-center shrink-0`}
      >
        {isUser ? <PersonIcon className="w-[18px] h-[18px]" /> : <PawIcon className="w-[18px] h-[18px]" />}
      </div>
      {isUser && <div className="avatar-label text-[0.68rem]">You</div>}
    </div>
  );

  const bubbleClass = meta
    ? `bubble-note ${meta.extraClass}`
    : isUser
      ? "bubble-user rounded-bl-2xl rounded-tl-2xl rounded-tr-2xl rounded-br-md"
      : "bubble-assistant rounded-br-2xl rounded-tr-2xl rounded-tl-2xl rounded-bl-md";

  return (
    <div className={`flex items-end gap-2.5 max-w-full ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && avatar}
      <div className={`flex flex-col max-w-[min(62ch,78%)] ${isUser ? "items-end" : "items-start"}`}>
        <div className={`bubble ${bubbleClass} px-4 py-3 text-[0.94rem] leading-relaxed break-words`}>
          {meta && (
            <div className="bubble-note-header flex items-center gap-1.5 mb-2 text-[0.78rem] font-bold uppercase tracking-wide">
              <meta.icon className="bubble-note-icon w-3.5 h-3.5 shrink-0" />
              {meta.label}
            </div>
          )}
          {isUser ? <span className="whitespace-pre-wrap">{message.text}</span> : renderContent(message.text)}
        </div>
        <div className="bubble-meta flex items-center gap-1 text-[0.7rem] mt-1 px-1">
          {/* The very first (welcome) message's timestamp is set during
              render, so server vs. client can legitimately land in different
              minutes across the SSR/hydration gap - expected, not a bug. */}
          <span suppressHydrationWarning>{formatTime(message.timestamp)}</span>
          {isUser && <span className="ticks font-bold">✓✓</span>}
        </div>
      </div>
      {isUser && avatar}
    </div>
  );
}
