"use client";

/**
 * Lightweight Client-Side Web Speech API Synthesis for Japanese.
 * 100% offline-first, zero-latency, reliable voice synthesis using local system voices.
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

let cachedVoices: SpeechSynthesisVoice[] = [];

function loadVoices(): SpeechSynthesisVoice[] {
  if (!isWebSpeechSupported()) return [];
  try {
    const voices = window.speechSynthesis.getVoices() || [];
    if (voices.length > 0) {
      cachedVoices = voices;
    }
  } catch {}
  return cachedVoices;
}

// Pre-load voices on browser initialization
if (typeof window !== "undefined" && "speechSynthesis" in window) {
  loadVoices();
  window.speechSynthesis.onvoiceschanged = () => {
    loadVoices();
  };
}

export function getJapaneseWebVoices(): SpeechSynthesisVoice[] {
  const allVoices = cachedVoices.length > 0 ? cachedVoices : loadVoices();
  return allVoices.filter((v) => {
    const lang = (v.lang || "").toLowerCase().replace("_", "-");
    const name = (v.name || "").toLowerCase();
    return lang.includes("ja") || name.includes("japanese") || name.includes("japan") || name.includes("日本語");
  });
}

/**
 * Select the best reliable local offline Japanese voice.
 * Prioritizes built-in offline OS voices (Haruka, Ichiro, Ayumi, Google 日本語, Kyoko) over flaky online/cloud voices.
 */
export function getPreferredJapaneseVoice(preferredURI?: string): SpeechSynthesisVoice | null {
  const voices = getJapaneseWebVoices();
  if (voices.length === 0) return null;

  if (preferredURI) {
    const matched = voices.find((v) => v.voiceURI === preferredURI);
    if (matched) return matched;
  }

  // 1. High quality built-in Windows Japanese voices (Haruka, Ichiro, Ayumi)
  const windowsVoice = voices.find((v) => {
    const name = v.name.toLowerCase();
    return name.includes("haruka") || name.includes("ichiro") || name.includes("ayumi");
  });
  if (windowsVoice) return windowsVoice;

  // 2. Google Japanese Voice (Chrome built-in)
  const googleVoice = voices.find((v) => {
    const name = v.name.toLowerCase();
    return name.includes("google") && (name.includes("日本語") || name.includes("japanese") || name.includes("ja-jp"));
  });
  if (googleVoice) return googleVoice;

  // 3. Apple/Mac Japanese voices (Kyoko, Otoya)
  const appleVoice = voices.find((v) => {
    const name = v.name.toLowerCase();
    return name.includes("kyoko") || name.includes("otoya");
  });
  if (appleVoice) return appleVoice;

  // 4. Any local service voice for ja-JP
  const localJa = voices.find((v) => (v.lang || "").toLowerCase().replace("_", "-") === "ja-jp" && (v as any).localService);
  if (localJa) return localJa;

  // 5. Any standard ja-JP voice
  const exactJa = voices.find((v) => (v.lang || "").toLowerCase().replace("_", "-") === "ja-jp");
  if (exactJa) return exactJa;

  return voices[0];
}

// Global active utterances set to prevent V8 Garbage Collection mid-speech
const activeUtterancesSet = new Set<SpeechSynthesisUtterance>();
let activeSpeakTimeout: NodeJS.Timeout | null = null;

export function stopWebSpeech(): void {
  if (!isWebSpeechSupported()) return;
  if (activeSpeakTimeout) {
    clearTimeout(activeSpeakTimeout);
    activeSpeakTimeout = null;
  }
  try {
    window.speechSynthesis.cancel();
  } catch (e) {
    console.warn("[WebSpeech] Cancel error:", e);
  }
  activeUtterancesSet.clear();
}

/**
 * Speaks Japanese text cleanly, directly, and reliably using offline voices.
 */
export function speakJapaneseText(text: string, options: WebSpeechOptions = {}): boolean {
  if (!isWebSpeechSupported() || !text?.trim()) {
    options.onEnd?.();
    return false;
  }

  // Clean text of hints or special delimiters
  const cleanText = text.split("---HINT---")[0].trim();
  if (!cleanText) {
    options.onEnd?.();
    return false;
  }

  if (activeSpeakTimeout) {
    clearTimeout(activeSpeakTimeout);
    activeSpeakTimeout = null;
  }

  const wasSpeaking = window.speechSynthesis.speaking || window.speechSynthesis.pending;
  if (wasSpeaking) {
    try {
      window.speechSynthesis.cancel();
    } catch {}
  }

  // If previous speech was cancelled, wait 50ms for Windows Audio buffer to purge before new speak
  const delayMs = wasSpeaking ? 50 : 0;

  activeSpeakTimeout = setTimeout(() => {
    activeSpeakTimeout = null;
    try {
      if (window.speechSynthesis.paused) {
        window.speechSynthesis.resume();
      }

      const utterance = new SpeechSynthesisUtterance(cleanText);
      utterance.lang = "ja-JP";
      utterance.rate = options.rate ?? 1.0;
      utterance.pitch = options.pitch ?? 1.0;

      const voice = getPreferredJapaneseVoice(options.voiceURI);
      if (voice) {
        utterance.voice = voice;
      }

      utterance.onstart = () => {
        options.onStart?.();
      };

      utterance.onend = () => {
        activeUtterancesSet.delete(utterance);
        options.onEnd?.();
      };

      utterance.onerror = (e: any) => {
        activeUtterancesSet.delete(utterance);
        const isCanceled = e?.error === "canceled" || e?.error === "interrupted";
        if (isCanceled) {
          options.onError?.(e);
          return;
        }
        console.warn("[WebSpeech] Speech error:", e);
        options.onError?.(e);
        options.onEnd?.();
      };

      activeUtterancesSet.add(utterance);
      window.speechSynthesis.speak(utterance);
    } catch (err) {
      console.error("[WebSpeech] Failed to speak:", err);
      options.onError?.(err);
      options.onEnd?.();
    }
  }, delayMs);

  return true;
}
