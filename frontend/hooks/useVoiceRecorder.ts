"use client";

import { useCallback, useRef, useState } from "react";

export function useVoiceRecorder(onComplete: (blob: Blob) => void, onError: (message: string) => void) {
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const toggle = useCallback(async () => {
    const current = mediaRecorderRef.current;
    if (current && current.state === "recording") {
      current.stop();
      return;
    }

    if (!navigator.mediaDevices?.getUserMedia) {
      onError("Voice input isn't supported in this browser.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      chunksRef.current = [];
      const recorder = new MediaRecorder(stream);
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = () => {
        setIsRecording(false);
        stream.getTracks().forEach((track) => track.stop());
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        if (blob.size > 0) onComplete(blob);
      };
      recorder.start();
      mediaRecorderRef.current = recorder;
      setIsRecording(true);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      onError(`Microphone access denied or unavailable (${message}).`);
    }
  }, [onComplete, onError]);

  return { isRecording, toggle };
}
