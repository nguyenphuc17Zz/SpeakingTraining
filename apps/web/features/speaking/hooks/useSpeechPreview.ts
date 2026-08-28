import { useCallback, useEffect, useRef, useState } from "react";
import {
  registerSpeechRecognition,
  unregisterSpeechRecognition,
} from "@/hooks/use-global-audio-cleanup";

export interface UseSpeechPreviewOptions {
  language?: string; // Default 'ja-JP'
  enabled?: boolean;
  onTranscriptChange?: (text: string) => void;
}

export function useSpeechPreview(options: UseSpeechPreviewOptions = {}) {
  const { language = "ja-JP", enabled = true, onTranscriptChange } = options;
  const [interimTranscript, setInterimTranscript] = useState<string>("");
  const [isRecognizing, setIsRecognizing] = useState(false);

  const recognitionRef = useRef<any>(null);
  const isListeningRef = useRef(false);
  const accumulatedFinalRef = useRef<string>("");
  const onTranscriptChangeRef = useRef(onTranscriptChange);
  onTranscriptChangeRef.current = onTranscriptChange;

  const startPreview = useCallback(() => {
    if (!enabled || typeof window === "undefined") return;

    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) return;

    isListeningRef.current = true;

    try {
      if (recognitionRef.current) {
        unregisterSpeechRecognition(recognitionRef.current);
        try {
          recognitionRef.current.abort();
        } catch {}
      }

      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = language;
      recognition.maxAlternatives = 1;

      recognition.onstart = () => {
        setIsRecognizing(true);
      };

      recognition.onresult = (event: any) => {
        let interim = "";
        let newFinal = "";

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const res = event.results[i];
          const transcript = res[0]?.transcript || "";
          if (res.isFinal) {
            newFinal += transcript;
          } else {
            interim += transcript;
          }
        }

        if (newFinal) {
          accumulatedFinalRef.current += newFinal;
        }

        const fullText = (accumulatedFinalRef.current + " " + interim).trim();
        setInterimTranscript(fullText);
        if (fullText) {
          onTranscriptChangeRef.current?.(fullText);
        }
      };

      recognition.onerror = (e: any) => {
        if (e.error !== "no-speech" && e.error !== "aborted") {
          console.debug("[SpeechPreview] Interim notice:", e.error);
        }
      };

      recognition.onend = () => {
        // If still in listening state (e.g. user paused between sentences), auto-restart
        if (isListeningRef.current) {
          try {
            recognition.start();
            return;
          } catch {
            // If restart fails, set state
          }
        }
        setIsRecognizing(false);
      };

      recognition.start();
      recognitionRef.current = recognition;
      registerSpeechRecognition(recognition);
    } catch (e) {
      console.debug("[SpeechPreview] Could not start browser recognizer:", e);
    }
  }, [enabled, language]);

  const stopPreview = useCallback(() => {
    isListeningRef.current = false;
    if (recognitionRef.current) {
      unregisterSpeechRecognition(recognitionRef.current);
      try {
        recognitionRef.current.onstart = null;
        recognitionRef.current.onresult = null;
        recognitionRef.current.onerror = null;
        recognitionRef.current.onend = null;
        recognitionRef.current.abort();
      } catch {}
      recognitionRef.current = null;
    }
    setIsRecognizing(false);
  }, []);

  const clearPreview = useCallback(() => {
    accumulatedFinalRef.current = "";
    setInterimTranscript("");
  }, []);

  useEffect(() => {
    return () => {
      isListeningRef.current = false;
      if (recognitionRef.current) {
        try {
          recognitionRef.current.onstart = null;
          recognitionRef.current.onresult = null;
          recognitionRef.current.onerror = null;
          recognitionRef.current.onend = null;
          recognitionRef.current.abort();
        } catch {}
        recognitionRef.current = null;
      }
    };
  }, []);

  return {
    interimTranscript,
    isRecognizing,
    startPreview,
    stopPreview,
    clearPreview,
    setInterimTranscript,
  };
}
