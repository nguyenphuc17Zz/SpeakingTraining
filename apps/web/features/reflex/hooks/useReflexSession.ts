"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useMicrophone } from "@/features/speaking/hooks/useMicrophone";
import { useVoiceActivityDetection } from "@/features/speaking/hooks/useVoiceActivityDetection";
import { useSpeechPreview } from "@/features/speaking/hooks/useSpeechPreview";
import { useReflexTimer } from "./useReflexTimer";
import * as reflexApi from "../services/reflex-api";
import type { ReflexExercise, ReflexResult, PressureLevel } from "../services/reflex-api";

export type ReflexPhase =
  | "idle"
  | "loading"
  | "prompt_playing"
  | "ready"
  | "waiting_for_speech"
  | "recording"
  | "evaluating"
  | "result"
  | "summary";

export interface UseReflexSessionOptions {
  subMode: string;
  pressureLevel: PressureLevel;
  timerLimitMs?: number;
  onResult?: (r: ReflexResult) => void;
  autoNext?: boolean;
  autoNextDelayMs?: number;
  startTrigger?: "manual" | "auto";
  conjugationTarget?: string;
  qnaTopic?: string;
  transformationCategory?: string;
  contextCategory?: string;
  vocabCategory?: string;
  keigoCategory?: string;
}

export function useReflexSession(opts: UseReflexSessionOptions) {
  const {
    subMode,
    pressureLevel,
    timerLimitMs: overrideTimer,
    autoNext = false,
    autoNextDelayMs = 4500,
    startTrigger = "manual",
    conjugationTarget,
    qnaTopic,
    transformationCategory,
    contextCategory,
    vocabCategory,
    keigoCategory,
  } = opts;

  const [phase, setPhase] = useState<ReflexPhase>("idle");
  const [exercise, setExercise] = useState<ReflexExercise | null>(null);
  const [result, setResult] = useState<ReflexResult | null>(null);
  const [results, setResults] = useState<ReflexResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [prefetched, setPrefetched] = useState<ReflexExercise[]>([]);
  const [stats, setStats] = useState({
    total: 0,
    correct: 0,
    avgLatency: 0,
    bestLatency: Number.POSITIVE_INFINITY,
  });

  const phaseRef = useRef<ReflexPhase>(phase);
  phaseRef.current = phase;

  const exerciseRef = useRef<ReflexExercise | null>(exercise);
  exerciseRef.current = exercise;

  const overrideTimerRef = useRef<number | undefined>(overrideTimer);
  overrideTimerRef.current = overrideTimer;

  const autoNextRef = useRef(autoNext);
  autoNextRef.current = autoNext;

  const autoNextDelayMsRef = useRef(autoNextDelayMs);
  autoNextDelayMsRef.current = autoNextDelayMs;

  const startTriggerRef = useRef(startTrigger);
  startTriggerRef.current = startTrigger;

  const conjugationTargetRef = useRef(conjugationTarget);
  conjugationTargetRef.current = conjugationTarget;

  const qnaTopicRef = useRef(qnaTopic);
  qnaTopicRef.current = qnaTopic;

  const transformationCategoryRef = useRef(transformationCategory);
  transformationCategoryRef.current = transformationCategory;

  const contextCategoryRef = useRef(contextCategory);
  contextCategoryRef.current = contextCategory;

  const vocabCategoryRef = useRef(vocabCategory);
  vocabCategoryRef.current = vocabCategory;
  const keigoCategoryRef = useRef(keigoCategory);
  keigoCategoryRef.current = keigoCategory;

  const promptCompletedAtRef = useRef<number | null>(null);
  const reactionLatencyRef = useRef<number | null>(null);
  const latestTranscriptRef = useRef<string>("");
  const speechSubmitTimerRef = useRef<NodeJS.Timeout | null>(null);
  const autoNextTimerRef = useRef<NodeJS.Timeout | null>(null);
  const promptSafetyTimerRef = useRef<NodeJS.Timeout | null>(null);
  const seenPromptsRef = useRef<Set<string>>(new Set());
  const createdAudioUrlsRef = useRef<string[]>([]);

  // 1. Microphone Hardware Hook (volume level & audio recording from Speaking architecture)
  const mic = useMicrophone();
  const micRef = useRef(mic);
  micRef.current = mic;

  // 2. Real-Time Japanese Speech Preview Hook (0ms text streaming from Speaking architecture)
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

  // 3. Auto Voice Activity Detection Hook (VU volume & auto-end-of-speech from Speaking architecture)
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
          const latency = performance.now() - promptCompletedAtRef.current;
          reactionLatencyRef.current = latency;
        }
        setPhase("recording");
      }
    },
    onSpeechEnd: async () => {
      if (phaseRef.current === "recording" || phaseRef.current === "waiting_for_speech") {
        const captured = latestTranscriptRef.current || speechPreviewRef.current.interimTranscript.trim();
        if (captured) {
          await submitWithTranscript(captured);
        }
      }
    },
  });

  // Postpone automatic submission while user is actively speaking
  useEffect(() => {
    if (isUserSpeaking && speechSubmitTimerRef.current) {
      clearTimeout(speechSubmitTimerRef.current);
      speechSubmitTimerRef.current = null;
    }
  }, [isUserSpeaking]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (speechSubmitTimerRef.current) clearTimeout(speechSubmitTimerRef.current);
      if (autoNextTimerRef.current) clearTimeout(autoNextTimerRef.current);
      if (promptSafetyTimerRef.current) clearTimeout(promptSafetyTimerRef.current);
      micRef.current.releaseMicrophone();
      speechPreviewRef.current.stopPreview();
      seenPromptsRef.current.clear();
      createdAudioUrlsRef.current.forEach((url) => {
        try {
          URL.revokeObjectURL(url);
        } catch {}
      });
      createdAudioUrlsRef.current = [];
    };
  }, []);

  // Release microphone and speech recognition resources whenever session is NOT actively capturing speech
  useEffect(() => {
    if (phase !== "waiting_for_speech" && phase !== "recording") {
      micRef.current.releaseMicrophone();
      speechPreviewRef.current.stopPreview();
    }
  }, [phase]);

  const cancelAutoNext = useCallback(() => {
    if (autoNextTimerRef.current) {
      clearTimeout(autoNextTimerRef.current);
      autoNextTimerRef.current = null;
    }
  }, []);

  const timerLimit = overrideTimer ?? exercise?.timerLimitMs ?? 4000;
  const timer = useReflexTimer({
    timerLimitMs: timerLimit,
    onExpire: () => {
      if (phaseRef.current === "waiting_for_speech" || phaseRef.current === "recording") {
        handleTimeout();
      }
    },
  });
  const timerRef = useRef(timer);
  timerRef.current = timer;

  // Start answering (activates countdown timer, mic recording, and speech recognition)
  const startAnswering = useCallback(async () => {
    if (promptSafetyTimerRef.current) {
      clearTimeout(promptSafetyTimerRef.current);
      promptSafetyTimerRef.current = null;
    }
    if (
      phaseRef.current !== "prompt_playing" &&
      phaseRef.current !== "ready" &&
      phaseRef.current !== "loading"
    ) {
      return;
    }
    promptCompletedAtRef.current = performance.now();
    reactionLatencyRef.current = null;
    latestTranscriptRef.current = "";
    speechPreviewRef.current.clearPreview();

    const currentEx = exerciseRef.current;
    const limit = overrideTimerRef.current ?? currentEx?.timerLimitMs ?? 4000;
    timerRef.current.reset(limit);
    timerRef.current.start(limit);
    setPhase("waiting_for_speech");

    speechPreviewRef.current.startPreview();
    await micRef.current.startRecording();
  }, []);

  // Called when prompt audio has finished reading
  const onPromptAudioFinished = useCallback(() => {
    if (promptSafetyTimerRef.current) {
      clearTimeout(promptSafetyTimerRef.current);
      promptSafetyTimerRef.current = null;
    }
    if (startTriggerRef.current === "manual") {
      setPhase((curr) => (curr === "prompt_playing" || curr === "loading" ? "ready" : curr));
    } else {
      startAnswering();
    }
  }, [startAnswering]);
  // Mixed adaptive rotation
  const resolveMixedSubMode = useCallback(() => {
    if (subMode !== "mixed") return subMode;
    const roll = Math.random();
    if (roll < 0.3) return "reflex_conjugation";
    if (roll < 0.6) return "reflex_qna";
    if (roll < 0.8) return "reflex_transformation";
    return "reflex_context";
  }, [subMode]);

  const fetchExercise = useCallback(async () => {
    const effMode = resolveMixedSubMode();
    if (prefetched.length > 0) {
      const [next, ...rest] = prefetched;
      setPrefetched(rest);
      const nextMode = resolveMixedSubMode();
      reflexApi
        .generateExercise({
          subMode: nextMode,
          pressureLevel,
          timerLimitMs: overrideTimerRef.current,
          conjugationTarget: conjugationTargetRef.current,
          topic: qnaTopicRef.current,
          transformationCategory: transformationCategoryRef.current,
          contextCategory: contextCategoryRef.current,
          vocabCategory: vocabCategoryRef.current,
          keigoCategory: keigoCategoryRef.current,
        })
        .then((ex) => setPrefetched((p) => [...p, ex] as any))
        .catch(() => {});
      return next as ReflexExercise;
    }
    return await reflexApi.generateExercise({
      subMode: effMode,
      pressureLevel,
      timerLimitMs: overrideTimerRef.current,
      conjugationTarget: conjugationTargetRef.current,
      topic: qnaTopicRef.current,
      transformationCategory: transformationCategoryRef.current,
      contextCategory: contextCategoryRef.current,
      vocabCategory: vocabCategoryRef.current,
      keigoCategory: keigoCategoryRef.current,
    });
  }, [pressureLevel, prefetched, resolveMixedSubMode]);

  const startNext = useCallback(async () => {
    try {
      if (speechSubmitTimerRef.current) clearTimeout(speechSubmitTimerRef.current);
      if (autoNextTimerRef.current) clearTimeout(autoNextTimerRef.current);
      if (promptSafetyTimerRef.current) clearTimeout(promptSafetyTimerRef.current);
      speechPreviewRef.current.clearPreview();
      speechPreviewRef.current.stopPreview();
      micRef.current.stopRecording().catch(() => {});
      setPhase("loading");
      setError(null);
      setResult(null);
      reactionLatencyRef.current = null;
      promptCompletedAtRef.current = null;
      latestTranscriptRef.current = "";

      const ex = await fetchExercise();
      if (ex.prompt) {
        seenPromptsRef.current.add(ex.prompt);
      }
      setExercise(ex);
      setPhase("prompt_playing");

      const limit = overrideTimerRef.current ?? ex.timerLimitMs ?? 4000;
      timerRef.current.stop();
      timerRef.current.reset(limit);

      // Fallback safety timeout (12s) in case browser blocks TTS autoplay or onEnd never fires
      promptSafetyTimerRef.current = setTimeout(() => {
        onPromptAudioFinished();
      }, 12000);
    } catch (e: any) {
      setError(e.message || "Không tải được bài tập");
      setPhase("idle");
    }
  }, [fetchExercise, onPromptAudioFinished]);

  const handleTimeout = useCallback(async () => {
    const currentEx = exerciseRef.current;
    if (!currentEx) return;
    if (speechSubmitTimerRef.current) clearTimeout(speechSubmitTimerRef.current);
    if (autoNextTimerRef.current) clearTimeout(autoNextTimerRef.current);
    timerRef.current.stop();
    speechPreviewRef.current.stopPreview();

    let userAudioUrl: string | null = null;
    try {
      const blob = await micRef.current.stopRecording();
      if (blob && blob.size > 0) {
        userAudioUrl = URL.createObjectURL(blob);
        createdAudioUrlsRef.current.push(userAudioUrl);
      }
    } catch (err) {
      console.debug("[useReflexSession] Error capturing audio blob on timeout:", err);
    }

    setPhase("evaluating");

    const capturedText = latestTranscriptRef.current || speechPreviewRef.current.interimTranscript.trim();
    const payload: any = {
      user_transcript: capturedText || "",
      reaction_latency_ms: currentEx.timerLimitMs,
      timer_limit_ms: currentEx.timerLimitMs,
      timed_out: true,
      late_response: false,
      speech_confidence: 0,
      response_speed_ms: currentEx.timerLimitMs,
    };

    try {
      const res = await reflexApi.submitAttempt(currentEx.id, payload);
      const mapped: ReflexResult = mapApiResult(res, currentEx, true, userAudioUrl, capturedText);
      setResult(mapped);
      setResults((r) => [...r, mapped]);
      updateStats(mapped);
      setPhase("result");
      if (autoNextRef.current) {
        autoNextTimerRef.current = setTimeout(() => startNext(), autoNextDelayMsRef.current);
      }
    } catch (e: any) {
      setError(e.message);
      setPhase("result");
    }
  }, [startNext]);

  const submitWithTranscript = useCallback(
    async (transcript: string, opts?: { semanticLatencyMs?: number; late?: boolean }) => {
      const currentEx = exerciseRef.current;
      if (!currentEx) return;
      if (speechSubmitTimerRef.current) clearTimeout(speechSubmitTimerRef.current);
      if (autoNextTimerRef.current) clearTimeout(autoNextTimerRef.current);
      timerRef.current.stop();
      speechPreviewRef.current.stopPreview();

      let userAudioUrl: string | null = null;
      try {
        const blob = await micRef.current.stopRecording();
        if (blob && blob.size > 0) {
          userAudioUrl = URL.createObjectURL(blob);
          createdAudioUrlsRef.current.push(userAudioUrl);
        }
      } catch (err) {
        console.debug("[useReflexSession] Error capturing audio blob on submit:", err);
      }

      setPhase("evaluating");

      const latency = reactionLatencyRef.current;
      const isLate = opts?.late || (latency !== null && latency > currentEx.timerLimitMs);
      const payload: any = {
        user_transcript: transcript,
        reaction_latency_ms: latency,
        semantic_latency_ms: opts?.semanticLatencyMs ?? null,
        timer_limit_ms: currentEx.timerLimitMs,
        timed_out: false,
        late_response: !!isLate,
        speech_confidence: 0.95,
        response_speed_ms: latency,
      };

      try {
        const res = await reflexApi.submitAttempt(currentEx.id, payload);
        const mapped = mapApiResult(res, currentEx, false, userAudioUrl, transcript);
        setResult(mapped);
        setResults((r) => [...r, mapped]);
        updateStats(mapped);
        setPhase("result");
        if (autoNextRef.current) {
          autoNextTimerRef.current = setTimeout(() => startNext(), autoNextDelayMsRef.current);
        }
        return mapped;
      } catch (e: any) {
        setError(e.message);
        setPhase("result");
        return null;
      }
    },
    [startNext]
  );

  const updateStats = (r: ReflexResult) => {
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
    seenPromptsRef.current.clear();
    setResults([]);
    setStats({ total: 0, correct: 0, avgLatency: 0, bestLatency: Number.POSITIVE_INFINITY });
    startNext();
  }, [startNext]);

  const skip = useCallback(() => {
    if (autoNextTimerRef.current) clearTimeout(autoNextTimerRef.current);
    timerRef.current.stop();
    speechPreviewRef.current.stopPreview();
    micRef.current.stopRecording().catch(() => {});
    startNext();
  }, [startNext]);

  const retry = useCallback(async () => {
    if (autoNextTimerRef.current) clearTimeout(autoNextTimerRef.current);
    const currentEx = exerciseRef.current;
    if (currentEx) {
      if (speechSubmitTimerRef.current) clearTimeout(speechSubmitTimerRef.current);
      speechPreviewRef.current.clearPreview();
      promptCompletedAtRef.current = performance.now();
      reactionLatencyRef.current = null;
      latestTranscriptRef.current = "";
      setResult(null);
      setPhase("waiting_for_speech");
      timerRef.current.reset(currentEx.timerLimitMs);
      timerRef.current.start(currentEx.timerLimitMs);
      speechPreviewRef.current.startPreview();
      await micRef.current.startRecording();
    } else {
      startNext();
    }
  }, [startNext]);

  const togglePause = useCallback(() => {
    const currentTimer = timerRef.current;
    if (currentTimer.isPaused) {
      currentTimer.resume();
      if (phaseRef.current === "waiting_for_speech" || phaseRef.current === "recording") {
        speechPreviewRef.current.startPreview();
        micRef.current.startRecording().catch(() => {});
      }
    } else {
      currentTimer.pause();
      speechPreviewRef.current.stopPreview();
      micRef.current.stopRecording().catch(() => {});
    }
  }, []);

  const startQuestionNow = useCallback(() => {
    if (phaseRef.current === "ready") {
      startAnswering();
    } else if (phaseRef.current === "prompt_playing" || phaseRef.current === "loading") {
      onPromptAudioFinished();
    }
  }, [startAnswering, onPromptAudioFinished]);

  return {
    phase,
    exercise,
    result,
    results,
    stats,
    timer,
    recorder: mic,
    speech: {
      transcript: speechPreview.interimTranscript,
      interimTranscript: speechPreview.interimTranscript,
      finalTranscript: speechPreview.interimTranscript,
      isListening: speechPreview.isRecognizing,
      isSupported: true,
      startListening: speechPreview.startPreview,
      stopListening: speechPreview.stopPreview,
      resetTranscript: speechPreview.clearPreview,
    },
    volumeLevel: mic.volumeLevel,
    isUserSpeaking,
    isPaused: timer.isPaused,
    error,
    setError,
    startSession,
    startNext,
    startAnswering,
    onPromptAudioFinished,
    startQuestionNow,
    togglePause,
    submitWithTranscript,
    cancelAutoNext,
    retry,
    skip,
    setPhase,
  };
}

function mapApiResult(
  api: any,
  ex: ReflexExercise,
  timedOut: boolean,
  userAudioUrl?: string | null,
  fallbackTranscript?: string
): ReflexResult {
  const reflexMetrics = api.metrics?.reflex || {};
  const rc = ex.extra_metadata?.reflex_config || {};
  
  // Resolve canonical correct answer
  const canonical =
    rc.canonical ||
    ex.canonical ||
    api.metrics?.reflex?.conjugation?.canonical ||
    api.metrics?.reflex?.canonical ||
    (ex.target_patterns && ex.target_patterns.length > 0 ? ex.target_patterns[0] : "") ||
    "";

  // Resolve acceptable variants
  const variants =
    rc.acceptable_variants ||
    ex.acceptableVariants ||
    ex.acceptable_variants ||
    (ex.target_patterns && ex.target_patterns.length > 1 ? ex.target_patterns.slice(1) : []);

  const promptText = rc.prompt || ex.prompt || ex.scenario || ex.title || "";
  const promptTranslation =
    rc.translation ||
    rc.vietnamese ||
    (ex.scenario && ex.scenario !== promptText ? ex.scenario : null) ||
    ex.extra_metadata?.translation ||
    "";

  const resolvedTranscript =
    api.metrics?.reflex?.transcript ||
    api.transcript ||
    api.user_transcript ||
    fallbackTranscript ||
    "";

  const promptReading = rc.word_reading || rc.prompt_reading || ex.extra_metadata?.word_reading || "";

  return {
    exerciseId: ex.id,
    success: !!api.success,
    score: api.score ?? (api.success ? 100 : 0),
    feedback: api.feedback || (api.success ? "Chính xác!" : "Cần cố gắng thêm."),
    transcript: resolvedTranscript,
    normalized: api.metrics?.reflex?.normalized || "",
    assessment: api.metrics?.reflex?.assessment || api.assessment || null,
    reactionLatencyMs: reflexMetrics.reaction_latency_ms ?? api.response_speed_ms ?? null,
    semanticLatencyMs: reflexMetrics.semantic_latency_ms ?? null,
    timerLimitMs: reflexMetrics.timer_limit_ms ?? ex.timerLimitMs,
    timedOut: !!reflexMetrics.timed_out || timedOut,
    lateResponse: !!reflexMetrics.late_response,
    masteryDeltas: api.target_mastery_delta || {},
    isPerfect: (api.score >= 80 && api.success) || false,
    userAudioUrl: userAudioUrl || null,
    canonicalAnswer: canonical,
    acceptableVariants: variants,
    promptText,
    promptReading,
    promptTranslation,
    targetForm: rc.conjugation_target || rc.form,
    verb: rc.verb,
    direction: rc.direction,
    targetType: rc.target_type,
    targetLabel: rc.target_label_vi,
    tripletSonkeigo: rc.triplet_sonkeigo,
    tripletKenjougo: rc.triplet_kenjougo,
    explanationVi: rc.explanation_vi,
  };
}
