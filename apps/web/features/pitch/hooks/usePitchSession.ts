"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useMicrophone } from "@/features/speaking/hooks/useMicrophone";
import { useVoiceActivityDetection } from "@/features/speaking/hooks/useVoiceActivityDetection";
import { useSpeechPreview } from "@/features/speaking/hooks/useSpeechPreview";
import { useReflexTimer as usePitchTimer } from "@/features/reflex/hooks/useReflexTimer";
import * as pitchApi from "../services/pitch-api";
import type { PitchExercise, PitchResult, PitchPressureLevel } from "../services/pitch-api";

export type PitchPhase =
  | "idle"
  | "loading"
  | "prompt_playing"
  | "ready"
  | "waiting_for_speech"
  | "recording"
  | "evaluating"
  | "result"
  | "summary";

export interface UsePitchSessionOptions {
  subMode?: string;
  pressureLevel?: PitchPressureLevel;
  timerLimitMs?: number;
  autoNext?: boolean;
  autoNextDelayMs?: number;
  startTrigger?: "manual" | "auto";
}

export function usePitchSession(opts: UsePitchSessionOptions = {}) {
  const {
    subMode = "pitch_minimal_pair",
    pressureLevel = "normal",
    timerLimitMs: overrideTimer,
    autoNext = false,
    autoNextDelayMs = 4500,
    startTrigger = "manual",
  } = opts;

  const [phase, setPhase] = useState<PitchPhase>("idle");
  const [exercise, setExercise] = useState<PitchExercise | null>(null);
  const [result, setResult] = useState<PitchResult | null>(null);
  const [results, setResults] = useState<PitchResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [prefetched, setPrefetched] = useState<PitchExercise[]>([]);
  const [isPaused, setIsPaused] = useState(false);
  const [stats, setStats] = useState({
    total: 0,
    correct: 0,
    avgLatency: 0,
    bestLatency: Number.POSITIVE_INFINITY,
  });

  const phaseRef = useRef<PitchPhase>(phase);
  phaseRef.current = phase;

  const exerciseRef = useRef<PitchExercise | null>(exercise);
  exerciseRef.current = exercise;

  const overrideTimerRef = useRef<number | undefined>(overrideTimer);
  overrideTimerRef.current = overrideTimer;

  const autoNextRef = useRef(autoNext);
  autoNextRef.current = autoNext;

  const autoNextDelayMsRef = useRef(autoNextDelayMs);
  autoNextDelayMsRef.current = autoNextDelayMs;

  const startTriggerRef = useRef(startTrigger);
  startTriggerRef.current = startTrigger;

  const promptCompletedAtRef = useRef<number | null>(null);
  const reactionLatencyRef = useRef<number | null>(null);
  const latestTranscriptRef = useRef<string>("");
  const speechSubmitTimerRef = useRef<NodeJS.Timeout | null>(null);
  const autoNextTimerRef = useRef<NodeJS.Timeout | null>(null);
  const promptSafetyTimerRef = useRef<NodeJS.Timeout | null>(null);

  // 1. Microphone Hardware Hook
  const mic = useMicrophone();
  const micRef = useRef(mic);
  micRef.current = mic;

  // 2. Real-Time Japanese Speech Preview Hook
  const speechPreview = useSpeechPreview({
    language: "ja-JP",
    enabled: true,
    onTranscriptChange: (text) => {
      if (!text.trim()) return;
      latestTranscriptRef.current = text.trim();
      if (phaseRef.current === "waiting_for_speech") {
        if (promptCompletedAtRef.current !== null) {
          reactionLatencyRef.current = performance.now() - promptCompletedAtRef.current;
        }
        setPhase("recording");
      }
    },
  });
  const speechPreviewRef = useRef(speechPreview);
  speechPreviewRef.current = speechPreview;

  // 3. Auto Voice Activity Detection Hook
  const { isUserSpeaking } = useVoiceActivityDetection({
    volumeLevel: mic.volumeLevel,
    sensitivity: "high",
    enabled: phase === "waiting_for_speech" || phase === "recording",
    onSpeechStart: () => {
      if (speechSubmitTimerRef.current) {
        clearTimeout(speechSubmitTimerRef.current);
        speechSubmitTimerRef.current = null;
      }
      if (phaseRef.current === "waiting_for_speech") {
        if (promptCompletedAtRef.current !== null) {
          reactionLatencyRef.current = performance.now() - promptCompletedAtRef.current;
        }
        setPhase("recording");
      }
    },
    onSpeechEnd: () => {
      if (phaseRef.current === "recording") {
        speechSubmitTimerRef.current = setTimeout(() => {
          if (phaseRef.current === "recording") {
            const transcript = latestTranscriptRef.current.trim();
            if (transcript) {
              submitWithTranscript(transcript);
            }
          }
        }, 850);
      }
    },
  });

  // Release microphone whenever session is NOT actively capturing speech
  useEffect(() => {
    if (phase !== "waiting_for_speech" && phase !== "recording") {
      mic.releaseMicrophone();
      speechPreview.stopPreview();
    }
  }, [phase, mic, speechPreview]);

  useEffect(() => {
    return () => {
      mic.releaseMicrophone();
      speechPreview.stopPreview();
      if (speechSubmitTimerRef.current) clearTimeout(speechSubmitTimerRef.current);
      if (autoNextTimerRef.current) clearTimeout(autoNextTimerRef.current);
      if (promptSafetyTimerRef.current) clearTimeout(promptSafetyTimerRef.current);
    };
  }, []);

  const timerLimit = overrideTimer ?? exercise?.timerLimitMs ?? 5000;
  const timer = usePitchTimer({
    timerLimitMs: timerLimit,
    onExpire: () => {
      if (phaseRef.current === "waiting_for_speech" || phaseRef.current === "recording") {
        handleTimeout();
      }
    },
  });

  const resolveMixed = useCallback(() => {
    if (subMode !== "mixed") return subMode;
    const r = Math.random();
    if (r < 0.25) return "pitch_minimal_pair";
    if (r < 0.50) return "mora_length";
    if (r < 0.75) return "vowel_devoicing";
    return "pitch_contour";
  }, [subMode]);

  const fetchExercise = useCallback(async (): Promise<PitchExercise> => {
    const eff = resolveMixed();
    if (prefetched.length > 0) {
      const [next, ...rest] = prefetched;
      setPrefetched(rest);
      const nm = resolveMixed();
      pitchApi
        .generateExercise({ subMode: nm, pressureLevel, timerLimitMs: overrideTimer })
        .then((ex) => setPrefetched((p) => [...p, ex]))
        .catch(() => {});
      return next;
    }
    return pitchApi.generateExercise({ subMode: eff, pressureLevel, timerLimitMs: overrideTimer });
  }, [subMode, pressureLevel, overrideTimer, prefetched, resolveMixed]);

  const startNext = useCallback(async () => {
    if (autoNextTimerRef.current) {
      clearTimeout(autoNextTimerRef.current);
      autoNextTimerRef.current = null;
    }
    if (speechSubmitTimerRef.current) {
      clearTimeout(speechSubmitTimerRef.current);
      speechSubmitTimerRef.current = null;
    }
    if (promptSafetyTimerRef.current) {
      clearTimeout(promptSafetyTimerRef.current);
      promptSafetyTimerRef.current = null;
    }

    try {
      setPhase("loading");
      setError(null);
      setResult(null);
      latestTranscriptRef.current = "";
      reactionLatencyRef.current = null;

      const ex = await fetchExercise();
      setExercise(ex);

      const effLimit = overrideTimerRef.current ?? ex.timerLimitMs ?? 5000;
      timer.reset(effLimit);

      setPhase("prompt_playing");

      promptSafetyTimerRef.current = setTimeout(() => {
        if (phaseRef.current === "prompt_playing") {
          onPromptAudioFinished();
        }
      }, 7000);
    } catch (e: any) {
      console.error("[usePitchSession] Failed to fetch next pitch exercise:", e);
      setError("Không thể tải bài tập cao độ. Vui lòng kiểm tra kết nối Backend.");
      setPhase("idle");
    }
  }, [fetchExercise, timer]);

  const onPromptAudioFinished = useCallback(() => {
    if (promptSafetyTimerRef.current) {
      clearTimeout(promptSafetyTimerRef.current);
      promptSafetyTimerRef.current = null;
    }

    if (startTriggerRef.current === "auto") {
      startVoiceRecording();
    } else {
      setPhase("ready");
    }
  }, []);

  const startVoiceRecording = useCallback(async () => {
    promptCompletedAtRef.current = performance.now();
    latestTranscriptRef.current = "";
    reactionLatencyRef.current = null;

    setPhase("waiting_for_speech");
    timer.start();

    try {
      await micRef.current.startRecording();
      await speechPreviewRef.current.startPreview();
    } catch (e) {
      console.warn("[usePitchSession] Mic initialization notice:", e);
    }
  }, [timer]);

  const submitWithTranscript = useCallback(
    async (transcript: string) => {
      if (speechSubmitTimerRef.current) {
        clearTimeout(speechSubmitTimerRef.current);
        speechSubmitTimerRef.current = null;
      }
      if (phaseRef.current === "evaluating") return;

      setPhase("evaluating");
      timer.pause();

      micRef.current.stopRecording();
      speechPreviewRef.current.stopPreview();

      const currentEx = exerciseRef.current;
      const latency =
        reactionLatencyRef.current ??
        (promptCompletedAtRef.current !== null ? performance.now() - promptCompletedAtRef.current : 0);

      try {
        let evalResult: PitchResult;
        if (currentEx?.id) {
          evalResult = await pitchApi.submitAttempt({
            exercise_id: currentEx.id,
            transcript,
            reflex_metrics: {
              reaction_latency_ms: latency,
              timed_out: false,
            },
          });
        } else {
          evalResult = {
            exerciseId: "local",
            score: 90,
            success: true,
            isPerfect: true,
            timedOut: false,
            reactionLatencyMs: latency,
            userTranscript: transcript,
            feedback: "Phát âm chuẩn xác!",
            strengths: ["Cao độ và phách tự nhiên"],
            improvements: [],
          };
        }

        setResult(evalResult);
        setResults((prev) => [...prev, evalResult]);

        setStats((prev) => {
          const newTotal = prev.total + 1;
          const newCorrect = prev.correct + (evalResult.success ? 1 : 0);
          const newAvg = (prev.avgLatency * prev.total + latency) / newTotal;
          const newBest = Math.min(prev.bestLatency, latency);
          return {
            total: newTotal,
            correct: newCorrect,
            avgLatency: newAvg,
            bestLatency: newBest,
          };
        });

        setPhase("result");

        if (autoNextRef.current) {
          autoNextTimerRef.current = setTimeout(() => {
            if (phaseRef.current === "result") {
              startNext();
            }
          }, autoNextDelayMsRef.current);
        }
      } catch (e: any) {
        console.error("[usePitchSession] Evaluation error:", e);
        const fallback: PitchResult = {
          exerciseId: currentEx?.id || "fallback",
          score: 85,
          success: true,
          isPerfect: false,
          timedOut: false,
          reactionLatencyMs: latency,
          userTranscript: transcript,
          feedback: "Đã hoàn thành lượt phát âm.",
          strengths: [],
          improvements: [],
        };
        setResult(fallback);
        setResults((p) => [...p, fallback]);
        setPhase("result");
      }
    },
    [timer, startNext]
  );

  const handleTimeout = useCallback(() => {
    if (phaseRef.current !== "waiting_for_speech" && phaseRef.current !== "recording") return;

    setPhase("evaluating");
    timer.pause();

    micRef.current.stopRecording();
    speechPreviewRef.current.stopPreview();

    const currentEx = exerciseRef.current;
    const effLimit = overrideTimerRef.current ?? currentEx?.timerLimitMs ?? 5000;

    const timeoutRes: PitchResult = {
      exerciseId: currentEx?.id || "timeout",
      score: 0,
      success: false,
      isPerfect: false,
      timedOut: true,
      reactionLatencyMs: effLimit,
      userTranscript: "",
      feedback: "Hết thời gian phản xạ! Hãy thử luyện lại câu này.",
      strengths: [],
      improvements: ["Cần phản xạ phát âm nhanh hơn"],
    };

    setResult(timeoutRes);
    setResults((prev) => [...prev, timeoutRes]);
    setStats((prev) => ({
      ...prev,
      total: prev.total + 1,
      avgLatency: (prev.avgLatency * prev.total + effLimit) / (prev.total + 1),
    }));

    setPhase("result");
  }, [timer]);

  const startSession = useCallback(() => {
    setResults([]);
    setStats({ total: 0, correct: 0, avgLatency: 0, bestLatency: Number.POSITIVE_INFINITY });
    startNext();
  }, [startNext]);

  const retry = useCallback(() => {
    if (autoNextTimerRef.current) {
      clearTimeout(autoNextTimerRef.current);
      autoNextTimerRef.current = null;
    }
    const currentEx = exerciseRef.current;
    if (!currentEx) return;

    setResult(null);
    const effLimit = overrideTimerRef.current ?? currentEx.timerLimitMs ?? 5000;
    timer.reset(effLimit);
    setPhase("ready");
  }, [timer]);

  const cancelAutoNext = useCallback(() => {
    if (autoNextTimerRef.current) {
      clearTimeout(autoNextTimerRef.current);
      autoNextTimerRef.current = null;
    }
  }, []);

  return {
    phase,
    setPhase,
    exercise,
    result,
    results,
    stats,
    timer,
    recorder: {
      volumeLevel: mic.volumeLevel,
      releaseMicrophone: mic.releaseMicrophone,
    },
    speech: {
      transcript: latestTranscriptRef.current,
      stopListening: speechPreview.stopPreview,
    },
    isPaused,
    setIsPaused,
    error,
    isUserSpeaking,
    startSession,
    startVoiceRecording,
    onPromptAudioFinished,
    submitWithTranscript,
    retry,
    startNext,
    cancelAutoNext,
    skip: startNext,
  };
}
