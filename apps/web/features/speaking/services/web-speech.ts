"use client";

/**
 * Lightweight Client-Side Web Speech API Synthesis for Japanese.
 * Runs 100% in-browser with 0MB additional backend RAM/VRAM load.
 */

export interface WebSpeechOptions {
  rate?: number; // 0.8 to 1.2, default 1.0
  pitch?: number; // 0.8 to 1.2, default 1.0
  voiceURI?: string;
  onStart?: () => void;
  onEnd?: () => void;
  onError?: (err: any) => void;
}

export function isWebSpeechSupported(): boolean {
  return typeof window !== "undefined" && "speechSynthesis" in window && typeof SpeechSynthesisUtterance !== "undefined";
}

export function getJapaneseWebVoices(): SpeechSynthesisVoice[] {
  if (!isWebSpeechSupported()) return [];
  const allVoices = window.speechSynthesis.getVoices();
  return allVoices.filter(
    (v) =>
      v.lang.toLowerCase().includes("ja") ||
      v.name.toLowerCase().includes("japanese") ||
      v.name.toLowerCase().includes("japan")
  );
}

let activeUtterance: SpeechSynthesisUtterance | null = null;
let currentUtteranceId = 0;

export function stopWebSpeech(): void {
  if (!isWebSpeechSupported()) return;
  currentUtteranceId++;
  try {
    window.speechSynthesis.cancel();
  } catch (e) {
    console.warn("[WebSpeech] Cancel error:", e);
  }
  activeUtterance = null;
}

export function speakJapaneseText(text: string, options: WebSpeechOptions = {}): boolean {
  if (!isWebSpeechSupported() || !text.trim()) {
    options.onEnd?.();
    return false;
  }

  try {
    stopWebSpeech();
    const utteranceId = ++currentUtteranceId;

    // Clean text of hints if any
    const cleanText = text.split("---HINT---")[0].trim();
    if (!cleanText) {
      options.onEnd?.();
      return false;
    }

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = "ja-JP";
    utterance.rate = options.rate ?? 1.0;
    utterance.pitch = options.pitch ?? 1.0;

    const jpVoices = getJapaneseWebVoices();
    if (options.voiceURI) {
      const selected = jpVoices.find((v) => v.voiceURI === options.voiceURI);
      if (selected) utterance.voice = selected;
    } else if (jpVoices.length > 0) {
      // Pick best default: Microsoft Haruka / Ayumi / Ichiro or first JP voice
      const preferred =
        jpVoices.find((v) => v.name.includes("Haruka") || v.name.includes("Ayumi") || v.name.includes("Ichiro") || v.name.includes("Google 日本語")) ||
        jpVoices[0];
      utterance.voice = preferred;
    }

    utterance.onstart = () => {
      if (utteranceId !== currentUtteranceId) return;
      options.onStart?.();
    };

    utterance.onend = () => {
      if (utteranceId !== currentUtteranceId) return;
      activeUtterance = null;
      options.onEnd?.();
    };

    utterance.onerror = (e: any) => {
      if (utteranceId !== currentUtteranceId) return;
      activeUtterance = null;
      // Do not trigger onEnd if utterance was canceled or interrupted intentionally
      const isCanceled = e?.error === "canceled" || e?.error === "interrupted";
      if (isCanceled) {
        options.onError?.(e);
        return;
      }
      console.warn("[WebSpeech] Speech synthesis error:", e);
      options.onError?.(e);
      options.onEnd?.();
    };

    activeUtterance = utterance;
    window.speechSynthesis.speak(utterance);
    return true;
  } catch (err) {
    console.error("[WebSpeech] Failed to speak:", err);
    options.onError?.(err);
    options.onEnd?.();
    return false;
  }
}
