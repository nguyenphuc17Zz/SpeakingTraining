"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useMicrophone } from "@/features/speaking/hooks/useMicrophone";
import { useVoiceActivityDetection } from "@/features/speaking/hooks/useVoiceActivityDetection";
import { useSpeechPreview } from "@/features/speaking/hooks/useSpeechPreview";
import { useReflexTimer as useKeigoTimer } from "@/features/reflex/hooks/useReflexTimer";
import * as keigoApi from "../services/keigo-api";
import type { KeigoExercise, KeigoResult, PressureLevel } from "../services/keigo-api";

export type KeigoPhase =
  | "idle"
  | "loading"
  | "prompt_playing"
  | "ready"
  | "waiting_for_speech"
  | "recording"
  | "evaluating"
  | "result"
  | "summary";

export interface UseKeigoSessionOptions {
  subMode: string;
  pressureLevel: PressureLevel;
  timerLimitMs?: number;
  autoNext?: boolean;
  autoNextDelayMs?: number;
  startTrigger?: "manual" | "auto";
}

export function useKeigoSession(opts: UseKeigoSessionOptions) {
  const {
    subMode,
    pressureLevel,
    timerLimitMs: overrideTimer,
    autoNext = false,
    autoNextDelayMs = 4500,
    startTrigger = "manual",
  } = opts;

  const [phase, setPhase] = useState<KeigoPhase>("idle");
  const [exercise, setExercise] = useState<KeigoExercise | null>(null);
  const [result, setResult] = useState<KeigoResult | null>(null);
  const [results, setResults] = useState<KeigoResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [prefetched, setPrefetched] = useState<KeigoExercise[]>([]);
  const [isPaused, setIsPaused] = useState(false);
  const [hintLevel, setHintLevel] = useState<0 | 1 | 2>(0);
  const [stats, setStats] = useState({
    total: 0,
    correct: 0,
    avgLatency: 0,
    bestLatency: Number.POSITIVE_INFINITY,
  });

  const phaseRef = useRef<KeigoPhase>(phase);
  phaseRef.current = phase;

  const exerciseRef = useRef<KeigoExercise | null>(exercise);
  exerciseRef.current = exercise;

  const overrideTimerRef = useRef<number | undefined>(overrideTimer);
  overrideTimerRef.current = overrideTimer;

  const autoNextRef = useRef(autoNext);
  autoNextRef.current = autoNext;

  const autoNextDelayMsRef = useRef(autoNextDelayMs);
  autoNextDelayMsRef.current = autoNextDelayMs;

  const startTriggerRef = useRef(startTrigger);
  startTriggerRef.current = startTrigger;

  const hintLevelRef = useRef<0 | 1 | 2>(hintLevel);
  hintLevelRef.current = hintLevel;

  const promptCompletedAtRef = useRef<number | null>(null);
  const reactionLatencyRef = useRef<number | null>(null);
  const latestTranscriptRef = useRef<string>("");
  const speechSubmitTimerRef = useRef<NodeJS.Timeout | null>(null);
  const autoNextTimerRef = useRef<NodeJS.Timeout | null>(null);
  const promptSafetyTimerRef = useRef<NodeJS.Timeout | null>(null);
  const createdAudioUrlsRef = useRef<string[]>([]);

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

  // Release microphone whenever session is NOT actively capturing speech or evaluating
  useEffect(() => {
    if (phase !== "waiting_for_speech" && phase !== "recording" && phase !== "evaluating") {
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
      createdAudioUrlsRef.current.forEach((url) => {
        try {
          URL.revokeObjectURL(url);
        } catch {}
      });
      createdAudioUrlsRef.current = [];
    };
  }, [mic, speechPreview]);

  const timerLimit = overrideTimer ?? exercise?.timerLimitMs ?? 5000;
  const timer = useKeigoTimer({
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
    if (r < 0.15) return "keigo_vocab_blitz";
    if (r < 0.35) return "keigo_sonkeigo";
    if (r < 0.55) return "keigo_kenjougo";
    if (r < 0.70) return "keigo_teineigo";
    if (r < 0.85) return "keigo_transformation";
    return "keigo_context";
  }, [subMode]);

  const fetchExercise = useCallback(async (): Promise<KeigoExercise> => {
    const eff = resolveMixed();
    if (prefetched.length > 0) {
      const [next, ...rest] = prefetched;
      setPrefetched(rest);
      const nm = resolveMixed();
      keigoApi
        .generateExercise({ subMode: nm, pressureLevel, timerLimitMs: overrideTimer })
        .then((ex) => setPrefetched((p) => [...p, ex]))
        .catch(() => {});
      return next;
    }
    return await keigoApi.generateExercise({ subMode: eff, pressureLevel, timerLimitMs: overrideTimer });
  }, [subMode, pressureLevel, overrideTimer, prefetched, resolveMixed]);

  const onPromptAudioFinished = useCallback(() => {
    if (phaseRef.current !== "prompt_playing") return;
    if (promptSafetyTimerRef.current) {
      clearTimeout(promptSafetyTimerRef.current);
      promptSafetyTimerRef.current = null;
    }

    if (startTriggerRef.current === "manual") {
      setPhase("ready");
    } else {
      promptCompletedAtRef.current = performance.now();
      setPhase("waiting_for_speech");
      timer.reset(exerciseRef.current?.timerLimitMs ?? 5000);
      timer.start();
      micRef.current.startRecording().catch(() => {});
      speechPreviewRef.current.startPreview();
    }
  }, [timer]);

  const startVoiceRecording = useCallback(() => {
    if (phaseRef.current !== "ready" && phaseRef.current !== "waiting_for_speech") return;
    promptCompletedAtRef.current = performance.now();
    setPhase("waiting_for_speech");
    timer.reset(exerciseRef.current?.timerLimitMs ?? 5000);
    timer.start();
    micRef.current.startRecording().catch(() => {});
    speechPreviewRef.current.startPreview();
  }, [timer]);

  const cycleHint = useCallback(() => {
    setHintLevel((prev) => ((prev + 1) % 3 as 0 | 1 | 2));
  }, []);

  const resetHint = useCallback(() => {
    setHintLevel(0);
  }, []);

  const startNext = useCallback(async () => {
    if (autoNextTimerRef.current) {
      clearTimeout(autoNextTimerRef.current);
      autoNextTimerRef.current = null;
    }
    if (speechSubmitTimerRef.current) {
      clearTimeout(speechSubmitTimerRef.current);
      speechSubmitTimerRef.current = null;
    }

    try {
      setPhase("loading");
      setError(null);
      setResult(null);
      setHintLevel(0);
      reactionLatencyRef.current = null;
      promptCompletedAtRef.current = null;
      latestTranscriptRef.current = "";

      const ex = await fetchExercise();
      setExercise(ex);
      setPhase("prompt_playing");

      // Fallback safety timer if audio doesn't fire onEnd event
      promptSafetyTimerRef.current = setTimeout(() => {
        if (phaseRef.current === "prompt_playing") {
          onPromptAudioFinished();
        }
      }, 7000);
    } catch (e: any) {
      setError(e.message || "Không thể tải bài tập kính ngữ.");
      setPhase("idle");
    }
  }, [fetchExercise, onPromptAudioFinished]);

  const handleTimeout = useCallback(async () => {
    const currentEx = exerciseRef.current;
    if (!currentEx) return;

    timer.stop();
    speechPreviewRef.current.stopPreview();

    let audioBlobUrl: string | undefined;
    try {
      const blob = await micRef.current.stopRecording();
      if (blob && blob.size > 0) {
        audioBlobUrl = URL.createObjectURL(blob);
        createdAudioUrlsRef.current.push(audioBlobUrl);
      }
    } catch {}

    setPhase("evaluating");

    const capturedText = latestTranscriptRef.current.trim();
    const curHintLevel = hintLevelRef.current;
    try {
      const payload: any = {
        reaction_latency_ms: reactionLatencyRef.current,
        timer_limit_ms: currentEx.timerLimitMs,
        timed_out: true,
        late_response: false,
        user_transcript: capturedText || "",
        used_hint: curHintLevel > 0,
        hint_level: curHintLevel,
      };
      const res = await keigoApi.submitAttempt(currentEx.id, payload);
      const mapped = mapApiResult(res, currentEx, true, curHintLevel, audioBlobUrl, capturedText);
      setResult(mapped);
      setResults((r) => [...r, mapped]);
      updateStats(mapped);
      setPhase("result");

      if (autoNextRef.current) {
        autoNextTimerRef.current = setTimeout(() => {
          if (phaseRef.current === "result") {
            startNext();
          }
        }, autoNextDelayMsRef.current);
      }
    } catch (e: any) {
      setError(e.message || "Lỗi khi nộp kết quả quá giờ.");
      setPhase("result");
    }
  }, [timer, startNext]);

  const submitWithTranscript = useCallback(
    async (transcript: string, opts?: { late?: boolean }) => {
      const currentEx = exerciseRef.current;
      if (!currentEx) return;

      if (speechSubmitTimerRef.current) {
        clearTimeout(speechSubmitTimerRef.current);
        speechSubmitTimerRef.current = null;
      }

      timer.stop();
      speechPreviewRef.current.stopPreview();

      let audioBlobUrl: string | undefined;
      try {
        const blob = await micRef.current.stopRecording();
        if (blob && blob.size > 0) {
          audioBlobUrl = URL.createObjectURL(blob);
          createdAudioUrlsRef.current.push(audioBlobUrl);
        }
      } catch {}

      setPhase("evaluating");

      const latency = reactionLatencyRef.current;
      const isLate = opts?.late || (latency !== null && latency > currentEx.timerLimitMs);
      const curHintLevel = hintLevelRef.current;

      const payload: any = {
        user_transcript: transcript,
        reaction_latency_ms: latency,
        timer_limit_ms: currentEx.timerLimitMs,
        timed_out: false,
        late_response: !!isLate,
        speech_confidence: 0.92,
        response_speed_ms: latency,
        used_hint: curHintLevel > 0,
        hint_level: curHintLevel,
      };

      try {
        const res = await keigoApi.submitAttempt(currentEx.id, payload);
        const mapped = mapApiResult(res, currentEx, false, curHintLevel, audioBlobUrl, transcript);
        setResult(mapped);
        setResults((r) => [...r, mapped]);
        updateStats(mapped);
        setPhase("result");

        if (autoNextRef.current) {
          autoNextTimerRef.current = setTimeout(() => {
            if (phaseRef.current === "result") {
              startNext();
            }
          }, autoNextDelayMsRef.current);
        }
        return mapped;
      } catch (e: any) {
        setError(e.message || "Lỗi khi chấm điểm kính ngữ.");
        setPhase("result");
        return null;
      }
    },
    [timer, startNext]
  );

  const updateStats = (r: KeigoResult) => {
    setStats((s) => {
      const total = s.total + 1;
      const correct = s.correct + (r.success ? 1 : 0);
      const lat = r.reactionLatencyMs;
      const avg = lat != null ? (s.avgLatency * s.total + lat) / total : s.avgLatency;
      const best = lat != null ? Math.min(s.bestLatency, lat) : s.bestLatency;
      return { total, correct, avgLatency: avg, bestLatency: best };
    });
  };

  const startSession = useCallback(() => {
    setResults([]);
    setStats({ total: 0, correct: 0, avgLatency: 0, bestLatency: Number.POSITIVE_INFINITY });
    setIsPaused(false);
    setHintLevel(0);
    const m1 = resolveMixed();
    const m2 = resolveMixed();
    Promise.all([
      keigoApi.generateExercise({ subMode: m1, pressureLevel, timerLimitMs: overrideTimer }),
      keigoApi.generateExercise({ subMode: m2, pressureLevel, timerLimitMs: overrideTimer }),
    ])
      .then(([a, b]) => setPrefetched([a, b]))
      .catch(() => {});
    startNext();
  }, [subMode, pressureLevel, overrideTimer, startNext, resolveMixed]);

  const cancelAutoNext = useCallback(() => {
    if (autoNextTimerRef.current) {
      clearTimeout(autoNextTimerRef.current);
      autoNextTimerRef.current = null;
    }
  }, []);

  const skip = useCallback(() => {
    cancelAutoNext();
    timer.stop();
    startNext();
  }, [cancelAutoNext, timer, startNext]);

  const retry = useCallback(() => {
    cancelAutoNext();
    if (exerciseRef.current) {
      promptCompletedAtRef.current = performance.now();
      reactionLatencyRef.current = null;
      latestTranscriptRef.current = "";
      setResult(null);
      setHintLevel(0);
      setPhase("waiting_for_speech");
      timer.reset(exerciseRef.current.timerLimitMs);
      timer.start();
      micRef.current.startRecording().catch(() => {});
      speechPreviewRef.current.startPreview();
    } else {
      startNext();
    }
  }, [cancelAutoNext, timer, startNext]);

  return {
    phase,
    exercise,
    result,
    results,
    stats,
    timer,
    hintLevel,
    cycleHint,
    resetHint,
    recorder: {
      volumeLevel: mic.volumeLevel,
      isRecording: mic.isRecording,
      releaseMicrophone: mic.releaseMicrophone,
    },
    speech: {
      transcript: speechPreview.interimTranscript,
      isListening: speechPreview.isRecognizing,
      stopListening: speechPreview.stopPreview,
    },
    isUserSpeaking,
    isPaused,
    setIsPaused,
    error,
    startSession,
    startNext,
    submitWithTranscript,
    retry,
    skip,
    setPhase,
    onPromptAudioFinished,
    startVoiceRecording,
    cancelAutoNext,
  };
}

function mapApiResult(
  api: any,
  ex: KeigoExercise,
  timedOut: boolean,
  hintLevel: number = 0,
  userAudioUrl?: string,
  fallbackTranscript?: string
): KeigoResult {
  const keigoMetrics = api.metrics?.keigo || api.metrics?.reflex || {};
  const canonical =
    ex.canonical ||
    (ex.target_patterns && ex.target_patterns.length > 0 ? ex.target_patterns[0] : "") ||
    api.feedback?.split("->")[1]?.trim() ||
    "";

  const resolvedTranscript =
    api.metrics?.keigo?.transcript ||
    api.metrics?.reflex?.transcript ||
    api.transcript ||
    api.user_transcript ||
    fallbackTranscript ||
    "";

  return {
    exerciseId: ex.id,
    success: !!api.success,
    score: api.score ?? (api.success ? 90 : 30),
    feedback: api.feedback || (api.success ? "Chính xác! Sử dụng đúng chuẩn mực kính ngữ." : "Chưa hoàn toàn chuẩn xác."),
    transcript: resolvedTranscript,
    normalized: "",
    assessment: api.metrics?.keigo?.assessment || keigoMetrics.assessment || null,
    reactionLatencyMs: keigoMetrics.reaction_latency_ms ?? api.response_speed_ms ?? null,
    timerLimitMs: keigoMetrics.timer_limit_ms ?? ex.timerLimitMs,
    timedOut: !!keigoMetrics.timed_out || timedOut,
    lateResponse: !!keigoMetrics.late_response,
    masteryDeltas: api.target_mastery_delta || {},
    isPerfect: (api.score >= 80 && api.success && hintLevel === 0) || false,
    doubleKeigo: keigoMetrics.double_keigo || api.metrics?.double_keigo,
    userAudioUrl,
    canonicalAnswer: canonical,
    acceptableVariants: ex.acceptableVariants || ex.target_patterns || [],
    targetRegister: ex.extra_metadata?.keigo_config?.target_register,
    hints: ex.hints,
    anatomy: ex.anatomy,
    persona: ex.persona,
    usedHint: hintLevel > 0,
    hintLevel,
  };
}
