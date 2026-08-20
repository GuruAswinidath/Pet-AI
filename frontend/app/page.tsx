"use client";

import { useCallback, useState } from "react";
import Composer from "@/components/Composer";
import Header from "@/components/Header";
import MessageList from "@/components/MessageList";
import SettingsPanel from "@/components/SettingsPanel";
import UrgencyBanner from "@/components/UrgencyBanner";
import { useTriageChat } from "@/hooks/useTriageChat";
import { useVoiceRecorder } from "@/hooks/useVoiceRecorder";

export default function Home() {
  const { messages, isSending, isTyping, urgency, status, sendText, sendAudio, newSession, audioRef } =
    useTriageChat();
  const [languageCode, setLanguageCode] = useState("en-IN");
  const [voiceMode, setVoiceMode] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [recorderStatus, setRecorderStatus] = useState("");

  const handleRecordingComplete = useCallback(
    (blob: Blob) => {
      setRecorderStatus("");
      sendAudio(blob, languageCode, voiceMode);
    },
    [sendAudio, languageCode, voiceMode]
  );

  const handleRecorderError = useCallback((message: string) => {
    setRecorderStatus(message);
  }, []);

  const { isRecording, toggle: toggleRecording } = useVoiceRecorder(handleRecordingComplete, handleRecorderError);

  const composerStatus = recorderStatus || (isRecording ? "Recording... click the mic again to stop." : status);

  return (
    <div className="flex flex-col h-screen">
      <Header
        languageCode={languageCode}
        onLanguageChange={setLanguageCode}
        onNewChat={newSession}
        onOpenSettings={() => setSettingsOpen(true)}
      />

      <main className="flex flex-1 min-h-0">
        <section className="flex-1 flex flex-col min-w-0">
          <UrgencyBanner urgency={urgency} />
          <MessageList messages={messages} isTyping={isTyping} />
          <Composer
            onSend={(text) => sendText(text, languageCode, voiceMode)}
            onToggleRecording={toggleRecording}
            isRecording={isRecording}
            isSending={isSending}
            status={composerStatus}
            voiceMode={voiceMode}
            onVoiceModeChange={setVoiceMode}
          />
        </section>

        <SettingsPanel open={settingsOpen} onClose={() => setSettingsOpen(false)} languageCode={languageCode} />
      </main>

      <audio ref={audioRef} hidden />
    </div>
  );
}
