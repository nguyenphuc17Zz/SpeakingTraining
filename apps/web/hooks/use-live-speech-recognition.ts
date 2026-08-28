"use client";

import { useState, useEffect, useRef, useCallback } from "react";

export function useLiveSpeechRecognition(language = "ja-JP") {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [interimTranscript, setInterimTranscript] = useState("");
  const [isSupported, setIsSupported] = useState(false);

  const recognitionRef = useRef<any>(null);
  const shouldListenRef = useRef(false);
  const restartTimerRef = useRef<NodeJS.Timeout | null>(null);
  const retryTimerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const SpeechRecognition =
        (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        setIsSupported(true);
      }
    }
  }, []);

  const clearTimers = () => {
    if (restartTimerRef.current) {
      clearTimeout(restartTimerRef.current);
      restartTimerRef.current = null;
    }
    if (retryTimerRef.current) {
      clearTimeout(retryTimerRef.current);
      retryTimerRef.current = null;
    }
  };

  const cleanupOldInstance = () => {
    if (recognitionRef.current) {
      try {
        // Detach old handlers so they don't fire during abort
        recognitionRef.current.onstart = null;
        recognitionRef.current.onresult = null;
        recognitionRef.current.onerror = null;
        recognitionRef.current.onend = null;
        recognitionRef.current.abort();
      } catch (e) {}
      recognitionRef.current = null;
    }
  };

  const startListening = useCallback(() => {
    if (typeof window === "undefined") return;

    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.warn("[SpeechRecognition] Web Speech API is not supported in this browser.");
      return;
    }

    shouldListenRef.current = true;
    clearTimers();
    cleanupOldInstance();

    const spawnRecognition = () => {
      if (!shouldListenRef.current) return;

      try {
        const recognition = new SpeechRecognition();
        recognition.lang = language;
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.maxAlternatives = 1;

        recognition.onstart = () => {
          setIsListening(true);
          setInterimTranscript("");
        };

        recognition.onresult = (event: any) => {
          let currentInterim = "";
          let currentFinal = "";

          for (let i = event.resultIndex; i < event.results.length; ++i) {
            const result = event.results[i];
            const transcriptChunk = result[0]?.transcript || "";
            if (result.isFinal) {
              currentFinal += transcriptChunk;
            } else {
              currentInterim += transcriptChunk;
            }
          }

          if (currentFinal) {
            setTranscript((prev) => (prev ? `${prev} ${currentFinal}` : currentFinal));
          }
          setInterimTranscript(currentInterim);
        };

        recognition.onerror = (event: any) => {
          // 'no-speech' is normal when user is pausing
          if (event.error === "not-allowed" || event.error === "service-not-allowed") {
            console.warn("[SpeechRecognition] Permission or service denied:", event.error);
            shouldListenRef.current = false;
            setIsListening(false);
          }
        };

        recognition.onend = () => {
          setInterimTranscript("");
          // Auto-restart with a FRESH instance if user is still in recording mode (multi-burst speech)
          if (shouldListenRef.current) {
            clearTimers();
            restartTimerRef.current = setTimeout(() => {
              if (shouldListenRef.current) {
                spawnRecognition();
              }
            }, 80);
          } else {
            setIsListening(false);
          }
        };

        recognitionRef.current = recognition;
        recognition.start();
      } catch (err: any) {
        console.warn("[SpeechRecognition] Start error, retrying in 120ms:", err);
        // Retry if browser speech engine is still clearing previous session
        if (shouldListenRef.current) {
          retryTimerRef.current = setTimeout(() => {
            if (shouldListenRef.current) {
              spawnRecognition();
            }
          }, 120);
        }
      }
    };

    spawnRecognition();
  }, [language]);

  const stopListening = useCallback(() => {
    shouldListenRef.current = false;
    clearTimers();
    cleanupOldInstance();
    setIsListening(false);
    setInterimTranscript("");
  }, []);

  const resetTranscript = useCallback(() => {
    setTranscript("");
    setInterimTranscript("");
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      shouldListenRef.current = false;
      clearTimers();
      cleanupOldInstance();
    };
  }, []);

  const fullTranscript = (transcript + " " + interimTranscript).trim();

  return {
    isListening,
    transcript,
    interimTranscript,
    fullTranscript,
    startListening,
    stopListening,
    resetTranscript,
    isSupported,
  };
}

