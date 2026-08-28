"use client";

import { useEffect, useRef, useState } from "react";

export type VADSensitivity = "low" | "medium" | "high";

export interface UseVADOptions {
  volumeLevel: number;
  sensitivity?: VADSensitivity;
  isCaptureSuppressed?: boolean;
  enabled?: boolean;
  onSpeechStart?: () => void;
  onSpeechEnd?: () => void;
}

export function useVAD({
  volumeLevel,
  sensitivity = "medium",
  isCaptureSuppressed = false,
  enabled = true,
  onSpeechStart,
  onSpeechEnd,
}: UseVADOptions) {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const speakingRef = useRef(false);
  const silenceTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Thresholds based on sensitivity mode
  let speechThreshold = 0.035;
  let silenceDurationMs = 1500;

  if (sensitivity === "low") {
    speechThreshold = 0.055;
    silenceDurationMs = 2200;
  } else if (sensitivity === "high") {
    speechThreshold = 0.02;
    silenceDurationMs = 1000;
  }

  useEffect(() => {
    if (!enabled || isCaptureSuppressed) {
      if (speakingRef.current) {
        speakingRef.current = false;
        setIsSpeaking(false);
      }
      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
        silenceTimerRef.current = null;
      }
      return;
    }

    if (volumeLevel > speechThreshold) {
      // Speech active
      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
        silenceTimerRef.current = null;
      }

      if (!speakingRef.current) {
        speakingRef.current = true;
        setIsSpeaking(true);
        onSpeechStart?.();
      }
    } else if (speakingRef.current) {
      // Below threshold -> start silence countdown
      if (!silenceTimerRef.current) {
        silenceTimerRef.current = setTimeout(() => {
          speakingRef.current = false;
          setIsSpeaking(false);
          silenceTimerRef.current = null;
          onSpeechEnd?.();
        }, silenceDurationMs);
      }
    }
  }, [
    volumeLevel,
    enabled,
    isCaptureSuppressed,
    speechThreshold,
    silenceDurationMs,
    onSpeechStart,
    onSpeechEnd,
  ]);

  useEffect(() => {
    return () => {
      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
      }
    };
  }, []);

  return {
    isUserSpeaking: isSpeaking,
  };
}
