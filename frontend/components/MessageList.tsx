"use client";

import { useEffect, useRef } from "react";
import type { ChatMessage } from "@/lib/types";
import MessageBubble from "./MessageBubble";
import { PawIcon } from "./icons";

function TypingIndicator() {
  return (
    <div className="flex items-end gap-2.5 justify-start">
      <div className="avatar-assistant w-[34px] h-[34px] rounded-full flex items-center justify-center shrink-0">
        <PawIcon className="w-[18px] h-[18px]" />
      </div>
      <div className="bubble bubble-assistant rounded-br-2xl rounded-tr-2xl rounded-tl-2xl rounded-bl-md px-4 py-3.5">
        <span className="typing-dots inline-flex gap-1 items-center">
          <span className="w-1.5 h-1.5 rounded-full inline-block" />
          <span className="w-1.5 h-1.5 rounded-full inline-block" />
          <span className="w-1.5 h-1.5 rounded-full inline-block" />
        </span>
      </div>
    </div>
  );
}

export default function MessageList({ messages, isTyping }: { messages: ChatMessage[]; isTyping: boolean }) {
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ block: "end" });
  }, [messages, isTyping]);

  return (
    <div className="flex-1 overflow-y-auto px-6 pt-5 pb-2 flex flex-col gap-4">
      <div className="flex justify-center mb-1">
        <span className="date-separator text-xs font-semibold px-3.5 py-1.5 rounded-full">Today</span>
      </div>
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}
      {isTyping && <TypingIndicator />}
      <div ref={bottomRef} />
    </div>
  );
}
