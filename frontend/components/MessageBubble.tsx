import { renderContent } from "@/lib/markdown";
import type { ChatMessage } from "@/lib/types";
import { PawIcon, PersonIcon } from "./icons";

function formatTime(timestamp: number): string {
  return new Date(timestamp).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

export default function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  const isNote = message.kind === "note";

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

  const bubbleClass = isNote
    ? "bubble-note"
    : isUser
      ? "bubble-user rounded-bl-2xl rounded-tl-2xl rounded-tr-2xl rounded-br-md"
      : "bubble-assistant rounded-br-2xl rounded-tr-2xl rounded-tl-2xl rounded-bl-md";

  return (
    <div className={`flex items-end gap-2.5 max-w-full ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && avatar}
      <div className={`flex flex-col max-w-[min(62ch,78%)] ${isUser ? "items-end" : "items-start"}`}>
        <div className={`bubble ${bubbleClass} px-4 py-3 text-[0.94rem] leading-relaxed break-words`}>
          {isNote || isUser ? (
            <span className="whitespace-pre-wrap">{message.text}</span>
          ) : (
            renderContent(message.text)
          )}
        </div>
        <div className="bubble-meta flex items-center gap-1 text-[0.7rem] mt-1 px-1">
          <span>{formatTime(message.timestamp)}</span>
          {isUser && <span className="ticks font-bold">✓✓</span>}
        </div>
      </div>
      {isUser && avatar}
    </div>
  );
}
