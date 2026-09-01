"use client";
import { useState, useCallback, useRef, useEffect } from "react";
import {
  rampApi,
  RampSession,
  NextExerciseResponse,
  SubmitAttemptResult,
  RampProgressSnapshot,
  RampSessionSummary,
  RampTaskSpec,
} from "@/services/ramp-api";

export type RampPhase =
  | "idle"
  | "setup"
  | "prompting"
  | "preparing"
  | "recording"
  | "submitting"
  | "feedback"
  | "complete";

export function useRamp() {
  const [phase, setPhase] = useState<RampPhase>("idle");
  const [session, setSession] = useState<RampSession | null>(null);
  const [currentExercise, setCurrentExercise] = useState<NextExerciseResponse | null>(null);
  const [submitResult, setSubmitResult] = useState<SubmitAttemptResult | null>(null);
  const [progress, setProgress] = useState<RampProgressSnapshot | null>(null);
  const [summary, setSummary] = useState<RampSessionSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [stage, setStage] = useState(0);
  const [supportLevel, setSupportLevel] = useState(3);
  const [usedHint, setUsedHint] = useState(false);
  const latencyStartRef = useRef<number | null>(null);

  // Synchronous refs to prevent React state closure lag during async sequences
  const sessionRef = useRef<RampSession | null>(null);
  const currentExerciseRef = useRef<NextExerciseResponse | null>(null);

  useEffect(() => {
    sessionRef.current = session;
  }, [session]);

  useEffect(() => {
    currentExerciseRef.current = currentExercise;
  }, [currentExercise]);

  const clearError = useCallback(() => setError(null), []);

  const startSession = useCallback(
    async (params: {
      desired_minutes?: number;
      session_goal?: string;
      current_stage?: number;
      support_level?: number;
    }) => {
      setIsLoading(true);
      setError(null);
      try {
        const s = await rampApi.createSession(params);
        sessionRef.current = s;
        setSession(s);
        setStage(s.stage);
        setSupportLevel(s.support_level);
        return s;
      } catch (e: any) {
        setError(e?.message || "Failed to start session");
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const loadNextExercise = useCallback(
    async (isRetry = false, forceFollowup = false, explicitSessionId?: string) => {
      const activeSessionId = explicitSessionId || sessionRef.current?.id || session?.id;
      if (!activeSessionId) {
        console.warn("loadNextExercise: No active session ID found.");
        return null;
      }
      setIsLoading(true);
      setError(null);
      setSubmitResult(null);
      setUsedHint(false);
      try {
        const ex = await rampApi.generateNextExercise(activeSessionId, {
          is_retry: isRetry,
          force_followup: forceFollowup,
        });
        currentExerciseRef.current = ex;
        setCurrentExercise(ex);
        setPhase("prompting");
        latencyStartRef.current = performance.now();
        return ex;
      } catch (e: any) {
        setError(e?.message || "Failed to generate exercise");
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [session]
  );

  const submitAttempt = useCallback(
    async (payload: {
      user_transcript: string;
      audio_base64?: string;
      support_level_used?: number;
      used_hint?: boolean;
    }) => {
      const activeSession = sessionRef.current || session;
      const activeExercise = currentExerciseRef.current || currentExercise;
      if (!activeSession || !activeExercise) return null;

      setIsLoading(true);
      setError(null);
      setPhase("submitting");

      const latency = latencyStartRef.current
        ? performance.now() - latencyStartRef.current
        : undefined;

      try {
        const result = await rampApi.submitAttempt(
          activeSession.id,
          activeExercise.exercise_id,
          {
            ...payload,
            response_latency_ms: latency,
          }
        );
        setSubmitResult(result);
        setStage(result.new_stage);
        setSupportLevel(result.new_support_level);
        setPhase("feedback");
        // Refresh session counters
        const updatedSession = await rampApi.getSession(activeSession.id);
        sessionRef.current = updatedSession;
        setSession(updatedSession);
        return result;
      } catch (e: any) {
        setError(e?.message || "Evaluation failed — please try again");
        setPhase("recording");
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [session, currentExercise]
  );

  const revealHint = useCallback(() => {
    setUsedHint(true);
  }, []);

  const fetchProgress = useCallback(async () => {
    const activeSessionId = sessionRef.current?.id || session?.id;
    if (!activeSessionId) return null;
    try {
      const p = await rampApi.getSessionProgress(activeSessionId);
      setProgress(p);
      return p;
    } catch (e) {
      return null;
    }
  }, [session]);

  const completeSession = useCallback(async () => {
    const activeSessionId = sessionRef.current?.id || session?.id;
    if (!activeSessionId) return null;
    setIsLoading(true);
    try {
      const s = await rampApi.completeSession(activeSessionId);
      sessionRef.current = null;
      currentExerciseRef.current = null;
      setSummary(s);
      setPhase("complete");
      return s;
    } catch (e: any) {
      setError(e?.message || "Failed to complete session");
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [session]);

  return {
    // State
    phase,
    setPhase,
    session,
    currentExercise,
    submitResult,
    progress,
    summary,
    error,
    isLoading,
    stage,
    supportLevel,
    usedHint,
    // Actions
    startSession,
    loadNextExercise,
    submitAttempt,
    revealHint,
    fetchProgress,
    completeSession,
    clearError,
  };
}
