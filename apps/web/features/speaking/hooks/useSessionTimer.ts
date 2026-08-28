"use client";

import { useEffect, useRef, useState } from "react";

export function useSessionTimer(isActive: boolean, isUserSpeaking: boolean) {
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [speakingSeconds, setSpeakingSeconds] = useState(0);

  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!isActive) {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
      return;
    }

    timerRef.current = setInterval(() => {
      setElapsedSeconds((prev) => prev + 1);
      if (isUserSpeaking) {
        setSpeakingSeconds((prev) => prev + 1);
      }
    }, 1000);

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [isActive, isUserSpeaking]);

  const resetTimer = () => {
    setElapsedSeconds(0);
    setSpeakingSeconds(0);
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  return {
    elapsedSeconds,
    speakingSeconds,
    formattedElapsed: formatTime(elapsedSeconds),
    formattedSpeaking: formatTime(speakingSeconds),
    resetTimer,
  };
}
