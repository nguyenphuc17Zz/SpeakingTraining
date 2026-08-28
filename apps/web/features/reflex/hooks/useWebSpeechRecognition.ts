"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  registerSpeechRecognition,
  unregisterSpeechRecognition,
} from "@/hooks/use-global-audio-cleanup";

export interface UseWebSpeechRecognitionOptions {
  lang?: string; // Default: "ja-JP"
  continuous?: boolean;
  interimResults?: boolean;
  onSpeechStart?: () => void;
  onTranscriptChange?: (fullText: string) => void;
  onFinalResult?: (transcript: string) => void;
  onError?: (error: string) => void;
}

export function useWebSpeechRecognition(opts: UseWebSpeechRecognitionOptions = {}) {
  const {
    lang = "ja-JP",
    continuous = true,
    interimResults = true,
    onSpeechStart,
    onTranscriptChange,
    onFinalResult,
    onError,
  } = opts;

  const [isSupported, setIsSupported] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isAudioStreaming, setIsAudioStreaming] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [interimTranscript, setInterimTranscript] = useState("");
  const [finalTranscript, setFinalTranscript] = useState("");

  const recognitionRef = useRef<any>(null);
  const isListeningRef = useRef(false);
  const hasSpokenRef = useRef(false);
  const accumulatedFinalRef = useRef("");
  const transcriptRef = useRef("");
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null);

  const onSpeechStartRef = useRef(onSpeechStart);
  onSpeechStartRef.current = onSpeechStart;

  const onTranscriptChangeRef = useRef(onTranscriptChange);
  onTranscriptChangeRef.current = onTranscriptChange;

  const onFinalResultRef = useRef(onFinalResult);
  onFinalResultRef.current = onFinalResult;

  const onErrorRef = useRef(onError);
  onErrorRef.current = onError;

  // Check browser support
  useEffect(() => {
    if (typeof window !== "undefined") {
      const SpeechRecognition =
        (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      setIsSupported(!!SpeechRecognition);
    }
  }, []);

  const clearTimers = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
  }, []);

  const cleanupOldInstance = useCallback(() => {
    if (recognitionRef.current) {
      const rec = recognitionRef.current;
      unregisterSpeechRecognition(rec);
      try {
        rec.onstart = null;
        rec.onaudiostart = null;
        rec.onsoundstart = null;
        rec.onspeechstart = null;
        rec.onresult = null;
        rec.onerror = null;
        rec.onend = null;
        rec.abort();
      } catch {}
      recognitionRef.current = null;
    }
  }, []);

  const resetTranscript = useCallback(() => {
    accumulatedFinalRef.current = "";
    transcriptRef.current = "";
    hasSpokenRef.current = false;
    setTranscript("");
    setInterimTranscript("");
    setFinalTranscript("");
  }, []);

  const startListening = useCallback(() => {
    if (typeof window === "undefined") return;
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      onErrorRef.current?.("Trình duyệt không hỗ trợ Web Speech API. Hãy sử dụng Google Chrome hoặc Microsoft Edge.");
      return;
    }

    isListeningRef.current = true;
    clearTimers();
    cleanupOldInstance();
    resetTranscript();

    const spawnInstance = () => {
      if (!isListeningRef.current) return;

      try {
        const recognition = new SpeechRecognition();
        recognition.lang = lang;
        recognition.continuous = continuous;
        recognition.interimResults = interimResults;
        recognition.maxAlternatives = 1;

        recognition.onstart = () => {
          setIsListening(true);
        };

        // Native audio hardware streaming started
        recognition.onaudiostart = () => {
          setIsAudioStreaming(true);
        };

        // Sound/Speech detected at microphone hardware level (15ms latency)
        recognition.onsoundstart = () => {
          if (!hasSpokenRef.current) {
            hasSpokenRef.current = true;
            onSpeechStartRef.current?.();
          }
        };

        recognition.onspeechstart = () => {
          if (!hasSpokenRef.current) {
            hasSpokenRef.current = true;
            onSpeechStartRef.current?.();
          }
        };

        recognition.onresult = (event: any) => {
          let interim = "";
          let newFinal = "";

          for (let i = event.resultIndex; i < event.results.length; ++i) {
            const res = event.results[i];
            const text = res[0]?.transcript || "";
            if (res.isFinal) {
              newFinal += text;
            } else {
              interim += text;
            }
          }

          if (newFinal) {
            accumulatedFinalRef.current = (accumulatedFinalRef.current + " " + newFinal).trim();
            setFinalTranscript(accumulatedFinalRef.current);
            onFinalResultRef.current?.(accumulatedFinalRef.current);
          }

          const fullText = (accumulatedFinalRef.current + " " + interim).trim();
          transcriptRef.current = fullText;
          setTranscript(fullText);
          setInterimTranscript(interim);

          if (fullText && !hasSpokenRef.current) {
            hasSpokenRef.current = true;
            onSpeechStartRef.current?.();
          }

          if (fullText) {
            onTranscriptChangeRef.current?.(fullText);
          }
        };

        recognition.onerror = (event: any) => {
          if (event.error === "no-speech" || event.error === "aborted") return;
          console.debug("[useWebSpeechRecognition] Error notice:", event.error);
          if (event.error === "not-allowed" || event.error === "service-not-allowed") {
            isListeningRef.current = false;
            setIsListening(false);
            setIsAudioStreaming(false);
            onErrorRef.current?.("Quyền truy cập Microphone bị từ chối.");
          }
        };

        recognition.onend = () => {
          setIsAudioStreaming(false);
          // If still in listening state (e.g. Chrome 5-second silence timeout), instantly restart
          if (isListeningRef.current) {
            clearTimers();
            reconnectTimerRef.current = setTimeout(() => {
              if (isListeningRef.current) {
                spawnInstance();
              }
            }, 30);
          } else {
            setIsListening(false);
          }
        };

        recognitionRef.current = recognition;
        registerSpeechRecognition(recognition);
        recognition.start();
      } catch (err: any) {
        console.debug("[useWebSpeechRecognition] Start spawn error:", err);
        if (isListeningRef.current) {
          reconnectTimerRef.current = setTimeout(() => {
            if (isListeningRef.current) {
              spawnInstance();
            }
          }, 80);
        }
      }
    };

    spawnInstance();
  }, [lang, continuous, interimResults, resetTranscript, clearTimers, cleanupOldInstance]);

  const stopListening = useCallback((abortImmediate = true): Promise<string> => {
    return new Promise((resolve) => {
      isListeningRef.current = false;
      clearTimers();
      cleanupOldInstance();
      setIsListening(false);
      setIsAudioStreaming(false);
      const captured = transcriptRef.current || accumulatedFinalRef.current || "";
      resolve(captured);
    });
  }, [clearTimers, cleanupOldInstance]);

  useEffect(() => {
    return () => {
      isListeningRef.current = false;
      clearTimers();
      cleanupOldInstance();
    };
  }, [clearTimers, cleanupOldInstance]);

  return {
    isSupported,
    isListening,
    isAudioStreaming,
    transcript,
    interimTranscript,
    finalTranscript,
    startListening,
    stopListening,
    resetTranscript,
  };
}
