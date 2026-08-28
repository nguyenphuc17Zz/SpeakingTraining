"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Persona } from "@/types/persona";
import {
  ConversationTurn,
  RecordingState,
  SessionMode,
  SessionSummary,
  VoiceSession,
  VoiceSettingsConfig,
} from "../types";
import { conversationApi } from "../services/conversation-api";
import { speechApi } from "../services/speech-api";
import { useMicrophone } from "./useMicrophone";
import { useVoiceActivityDetection } from "./useVoiceActivityDetection";
import { useAudioPlayback } from "./useAudioPlayback";
import { useSessionTimer } from "./useSessionTimer";
import { useSpeechPreview } from "./useSpeechPreview";
import { speakJapaneseText, stopWebSpeech } from "../services/web-speech";
import {
  getSavedLobbyPreferences,
  saveLobbyPreferences,
} from "../services/lobby-preferences";

export function useVoiceSession() {
  const [session, setSession] = useState<VoiceSession | null>(null);
  const [turns, setTurns] = useState<ConversationTurn[]>([]);
  const [state, setState] = useState<RecordingState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<SessionSummary | null>(null);
  const [settings, setSettings] = useState<VoiceSettingsConfig>(() => {
    const p = getSavedLobbyPreferences();
    return {
      ai_provider: p.ai_provider,
      ai_model: p.ai_model,
      stt_provider: p.stt_provider,
      stt_model: p.stt_model,
      tts_provider: p.tts_provider,
      tts_voice: p.tts_voice,
      tts_enabled: p.tts_enabled,
      tts_engine: p.tts_engine,
      vad_sensitivity: p.vad_sensitivity,
      auto_end_of_speech: p.auto_end_of_speech,
    };
  });
  const [isManualRecording, setIsManualRecording] = useState(false);
  const [manualSeconds, setManualSeconds] = useState(0);
  const [isVoiceMuted, setIsVoiceMuted] = useState(false);
  const [latestUserTranscript, setLatestUserTranscript] = useState<string | null>(null);
  const [latestSttMetrics, setLatestSttMetrics] = useState<{
    model?: string;
    latency_ms?: number;
  } | null>(null);

  const isProcessingRef = useRef(false);
  const activeTurnIdRef = useRef(0);
  const manualTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Audio Playback Hook
  const { isPlaying, playAudioBase64, stopPlayback } = useAudioPlayback({
    onPlaybackEnded: () => {
      setTimeout(() => {
        setState((current) => (current === "ai_speaking" ? "listening" : current));
      }, 300);
    },
    onError: (err) => {
      console.warn("[VoiceSession] Audio playback error:", err);
      setState((current) => (current === "ai_speaking" ? "listening" : current));
    },
  });

  // Microphone Hook
  const {
    hasPermission,
    isInitializing,
    isRecording,
    volumeLevel,
    requestPermission,
    releaseMicrophone,
    startRecording,
    stopRecording,
  } = useMicrophone();

  // Real-time Live Speech Preview Hook (0ms browser Japanese subtitles)
  const {
    interimTranscript,
    startPreview,
    stopPreview,
    clearPreview,
  } = useSpeechPreview({ language: "ja-JP", enabled: true });

  // Core Turn Handlers
  const handleAudioUtterance = useCallback(
    async (blob: Blob) => {
      if (!session || isProcessingRef.current) return;
      isProcessingRef.current = true;
      stopPreview();
      setState("processing_stt");

      const clientTurnId = `turn-${Date.now()}-${++activeTurnIdRef.current}`;

      try {
        setTimeout(() => {
          setState((curr) => (curr === "processing_stt" ? "ai_thinking" : curr));
        }, 500);

        const capturedPreview = interimTranscript.trim();
        const response = await conversationApi.sendAudioTurn(
          session.id,
          blob,
          clientTurnId,
          capturedPreview || undefined
        );

        clearPreview();
        setLatestUserTranscript(response.user_turn.transcript);
        setLatestSttMetrics({
          model: response.user_turn.stt_model || settings.stt_model,
          latency_ms:
            response.metrics?.stt_latency_ms ||
            response.user_turn.processing_time_ms ||
            undefined,
        });

        setTurns((prev) => {
          const existingIds = new Set(prev.map((t) => t.id));
          const next = [...prev];
          if (!existingIds.has(response.user_turn.id)) {
            next.push(response.user_turn);
          }
          if (!existingIds.has(response.assistant_turn.id)) {
            next.push(response.assistant_turn);
          }
          return next.sort((a, b) => a.sequence - b.sequence);
        });

        const isTtsDisabled =
          isVoiceMuted ||
          settings.tts_enabled === false ||
          settings.tts_engine === "none" ||
          settings.tts_provider === "none";

        if (isTtsDisabled) {
          setState("listening");
        } else if (settings.tts_engine === "web_speech" || response.assistant_turn.transcript) {
          if (settings.tts_engine === "web_speech") {
            setState("ai_speaking");
            speakJapaneseText(response.assistant_turn.transcript, {
              onEnd: () => {
                setTimeout(() => {
                  setState((curr) => (curr === "ai_speaking" ? "listening" : curr));
                }, 300);
              },
              onError: () => {
                setState((curr) => (curr === "ai_speaking" ? "listening" : curr));
              },
            });
          } else if (response.audio_base64) {
            setState("ai_speaking");
            await playAudioBase64(response.audio_base64, response.audio_format);
          } else {
            setState("listening");
          }
        } else {
          setState("listening");
        }
      } catch (err: any) {
        console.error("[VoiceSession] Audio turn processing failed:", err);
        setError(err.message || "Failed to process spoken turn.");
        setState("listening");
      } finally {
        isProcessingRef.current = false;
      }
    },
    [isVoiceMuted, playAudioBase64, session, settings]
  );

  // Auto Voice Activity Detection Hook
  const isAutoVAD = settings.auto_end_of_speech !== false;
  const { isUserSpeaking } = useVoiceActivityDetection({
    volumeLevel,
    sensitivity: settings.vad_sensitivity,
    enabled: state === "listening" && isAutoVAD && !isManualRecording,
    isCaptureSuppressed: state !== "listening" || isPlaying || isProcessingRef.current,
    onSpeechStart: async () => {
      if (
        state === "listening" &&
        isAutoVAD &&
        !isManualRecording &&
        !isProcessingRef.current &&
        !isPlaying
      ) {
        startPreview();
        await startRecording();
      }
    },
    onSpeechEnd: async () => {
      if (state === "listening" && isAutoVAD && !isManualRecording && !isProcessingRef.current) {
        const blob = await stopRecording();
        if (blob.size > 800) {
          await handleAudioUtterance(blob);
        }
      }
    },
  });

  // Session Timer
  const { elapsedSeconds, formattedElapsed, formattedSpeaking, resetTimer } =
    useSessionTimer(state !== "idle" && state !== "ended", isUserSpeaking || isManualRecording);

  const sendTextTurn = useCallback(
    async (text: string) => {
      if (!session || !text.trim() || isProcessingRef.current) return;
      isProcessingRef.current = true;
      setState("ai_thinking");

      const clientTurnId = `turn-text-${Date.now()}-${++activeTurnIdRef.current}`;

      try {
        const response = await conversationApi.sendTextTurn(
          session.id,
          text,
          clientTurnId
        );

        setLatestUserTranscript(text);

        setTurns((prev) => {
          const existingIds = new Set(prev.map((t) => t.id));
          const next = [...prev];
          if (!existingIds.has(response.user_turn.id)) {
            next.push(response.user_turn);
          }
          if (!existingIds.has(response.assistant_turn.id)) {
            next.push(response.assistant_turn);
          }
          return next.sort((a, b) => a.sequence - b.sequence);
        });

        const isTtsDisabled =
          isVoiceMuted ||
          settings.tts_enabled === false ||
          settings.tts_engine === "none" ||
          settings.tts_provider === "none";

        if (isTtsDisabled) {
          setState("listening");
        } else if (settings.tts_engine === "web_speech") {
          setState("ai_speaking");
          speakJapaneseText(response.assistant_turn.transcript, {
            onEnd: () => {
              setTimeout(() => {
                setState((curr) => (curr === "ai_speaking" ? "listening" : curr));
              }, 300);
            },
            onError: () => {
              setState((curr) => (curr === "ai_speaking" ? "listening" : curr));
            },
          });
        } else if (response.audio_base64) {
          setState("ai_speaking");
          await playAudioBase64(response.audio_base64, response.audio_format);
        } else {
          setState("listening");
        }
      } catch (err: any) {
        console.error("[VoiceSession] Text turn failed:", err);
        setError(err.message || "Failed to send turn.");
        setState("listening");
      } finally {
        isProcessingRef.current = false;
      }
    },
    [isVoiceMuted, playAudioBase64, session, settings]
  );

  const toggleVoiceMute = useCallback(() => {
    setIsVoiceMuted((prev) => {
      if (!prev) {
        stopPlayback();
        stopWebSpeech();
      }
      return !prev;
    });
  }, [stopPlayback]);

  const toggleAutoEndOfSpeech = useCallback(() => {
    setSettings((prev) => {
      const nextVal = !prev.auto_end_of_speech;
      saveLobbyPreferences({ auto_end_of_speech: nextVal });
      return { ...prev, auto_end_of_speech: nextVal };
    });
  }, []);

  const startSession = useCallback(
    async (
      persona: Persona,
      mode: SessionMode = "conversation",
      overrideSettings: Partial<VoiceSettingsConfig> = {}
    ) => {
      const mergedSettings = { ...settings, ...overrideSettings };
      setSettings(mergedSettings);
      setError(null);
      setSummary(null);
      setLatestUserTranscript(null);
      setLatestSttMetrics(null);
      resetTimer();

      // Step 1: Ensure Mic Permission
      const ok = await requestPermission();
      if (!ok) {
        setState("permission_denied");
        return;
      }

      setState("ready");

      // Step 2: Initialize Session in Backend
      try {
        const isTtsDisabled =
          isVoiceMuted ||
          mergedSettings.tts_enabled === false ||
          mergedSettings.tts_engine === "none" ||
          mergedSettings.tts_provider === "none";

        const ttsProviderPref = isTtsDisabled
          ? "none"
          : mergedSettings.tts_engine === "web_speech"
          ? "web_speech"
          : mergedSettings.tts_provider;

        const newSession = await conversationApi.startSession({
          persona_id: persona.id,
          mode,
          provider_preference:
            mergedSettings.ai_provider === "auto" ? null : mergedSettings.ai_provider,
          model_preference:
            mergedSettings.ai_model === "auto" ? null : mergedSettings.ai_model,
          stt_provider_preference:
            mergedSettings.stt_provider ||
            (mergedSettings.stt_model === "web_speech" ? "web_speech" : "faster_whisper"),
          stt_model_preference:
            mergedSettings.stt_model === "web_speech"
              ? "web_speech"
              : mergedSettings.stt_model === "auto"
              ? null
              : mergedSettings.stt_model,
          tts_provider_preference: ttsProviderPref,
          tts_voice_preference: mergedSettings.tts_voice,
        });

        setSession(newSession);

        // Load Opening Greeting Turn from AI Persona
        const initialTurns = newSession.turns || [];
        setTurns(initialTurns);

        // Play Opening Speech Greeting
        if (initialTurns.length > 0) {
          const openingTurn = initialTurns[0];
          if (!isTtsDisabled) {
            if (mergedSettings.tts_engine === "web_speech") {
              setState("ai_speaking");
              speakJapaneseText(openingTurn.transcript, {
                onEnd: () => {
                  setTimeout(() => {
                    setState((curr) => (curr === "ai_speaking" ? "listening" : curr));
                  }, 300);
                },
                onError: () => {
                  setState((curr) => (curr === "ai_speaking" ? "listening" : curr));
                },
              });
            } else if (newSession.opening_audio_base64) {
              setState("ai_speaking");
              await playAudioBase64(
                newSession.opening_audio_base64,
                newSession.opening_audio_format || "wav"
              );
            } else {
              setState("listening");
            }
          } else {
            setState("listening");
          }
        } else {
          setState("listening");
        }
      } catch (err: any) {
        console.error("[VoiceSession] Failed to start session:", err);
        setError(err.message || "Could not initialize conversation session.");
        setState("error");
      }
    },
    [isVoiceMuted, playAudioBase64, requestPermission, resetTimer, settings]
  );

  const startManualRecording = useCallback(async () => {
    if (state !== "listening" || isPlaying || isProcessingRef.current) return;
    const started = await startRecording();
    if (started) {
      startPreview();
      setIsManualRecording(true);
      setManualSeconds(0);
      if (manualTimerRef.current) clearInterval(manualTimerRef.current);
      manualTimerRef.current = setInterval(() => {
        setManualSeconds((s) => s + 1);
      }, 1000);
    }
  }, [isPlaying, startPreview, startRecording, state]);

  const stopAndSendManualRecording = useCallback(async () => {
    if (manualTimerRef.current) {
      clearInterval(manualTimerRef.current);
      manualTimerRef.current = null;
    }
    setIsManualRecording(false);
    const blob = await stopRecording();
    if (blob.size > 400) {
      await handleAudioUtterance(blob);
    }
  }, [handleAudioUtterance, stopRecording]);

  const pauseSession = useCallback(() => {
    stopPlayback();
    stopWebSpeech();
    if (manualTimerRef.current) {
      clearInterval(manualTimerRef.current);
      manualTimerRef.current = null;
    }
    if (isRecording) {
      stopRecording();
    }
    setIsManualRecording(false);
    setState("paused");
  }, [isRecording, stopPlayback, stopRecording]);

  const resumeSession = useCallback(() => {
    setState("listening");
  }, []);

  const endSession = useCallback(async () => {
    stopPlayback();
    stopWebSpeech();
    if (manualTimerRef.current) {
      clearInterval(manualTimerRef.current);
      manualTimerRef.current = null;
    }
    if (isRecording) {
      await stopRecording();
    }
    setIsManualRecording(false);

    if (!session) {
      setState("ended");
      return;
    }

    try {
      await conversationApi.endSession(session.id);
      const sessionSummary = await conversationApi.getSessionSummary(session.id);
      setSummary(sessionSummary);
    } catch (err) {
      console.warn("[VoiceSession] Failed to fetch session summary:", err);
    } finally {
      releaseMicrophone();
      setState("ended");
    }
  }, [isRecording, releaseMicrophone, session, stopPlayback, stopRecording]);

  const replayVoice = useCallback(
    async (text: string) => {
      if (isVoiceMuted || settings.tts_enabled === false || settings.tts_engine === "none") return;
      try {
        if (settings.tts_engine === "web_speech") {
          setState("ai_speaking");
          speakJapaneseText(text, {
            onEnd: () => setState((curr) => (curr === "ai_speaking" ? "listening" : curr)),
            onError: () => setState((curr) => (curr === "ai_speaking" ? "listening" : curr)),
          });
          return;
        }

        setState("ai_speaking");
        const res = await speechApi.synthesize(
          text,
          settings.tts_voice || "1"
        );
        if (res.audio_base64) {
          await playAudioBase64(res.audio_base64, res.format);
        } else {
          setState("listening");
        }
      } catch (e) {
        console.error("[VoiceSession] Replay synthesis failed:", e);
        setState("listening");
      }
    },
    [isVoiceMuted, playAudioBase64, settings.tts_enabled, settings.tts_engine, settings.tts_voice]
  );

  const resetSession = useCallback(() => {
    stopPlayback();
    stopWebSpeech();
    if (manualTimerRef.current) {
      clearInterval(manualTimerRef.current);
      manualTimerRef.current = null;
    }
    releaseMicrophone();
    stopPreview();
    clearPreview();
    setSession(null);
    setTurns([]);
    setState("idle");
    setError(null);
    setSummary(null);
    setIsManualRecording(false);
    setManualSeconds(0);
    setLatestUserTranscript(null);
    setLatestSttMetrics(null);
    resetTimer();
  }, [releaseMicrophone, resetTimer, stopPlayback]);

  useEffect(() => {
    return () => {
      if (manualTimerRef.current) {
        clearInterval(manualTimerRef.current);
      }
      releaseMicrophone();
      stopPlayback();
      stopWebSpeech();
    };
  }, [releaseMicrophone, stopPlayback]);

  // Complete audio and microphone cleanup on idle/ended or on unmount
  useEffect(() => {
    if (state === "idle" || state === "ended") {
      releaseMicrophone();
      stopPreview();
      stopPlayback();
      stopWebSpeech();
    }
  }, [state, releaseMicrophone, stopPreview, stopPlayback]);

  useEffect(() => {
    return () => {
      releaseMicrophone();
      stopPreview();
      stopPlayback();
      stopWebSpeech();
    };
  }, [releaseMicrophone, stopPreview, stopPlayback]);

  return {
    session,
    turns,
    state,
    error,
    summary,
    settings,
    volumeLevel,
    isUserSpeaking,
    hasPermission,
    isInitializing,
    isRecording,
    elapsedSeconds,
    formattedElapsed,
    formattedSpeaking,
    isVoiceMuted,
    toggleVoiceMute,
    autoEndOfSpeech: settings.auto_end_of_speech !== false,
    toggleAutoEndOfSpeech,
    interimTranscript,
    latestUserTranscript,
    latestSttMetrics,
    startSession,
    sendTextTurn,
    handleAudioUtterance,
    isManualRecording,
    manualSeconds,
    startManualRecording,
    stopAndSendManualRecording,
    pauseSession,
    resumeSession,
    endSession,
    resetSession,
    replayVoice,
    setSettings,
    requestPermission,
  };
}
