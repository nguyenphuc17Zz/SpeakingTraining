"use client";

import { useCallback, useState } from "react";
import { learningApi } from "@/services/learning-api";
import { Exercise, ExerciseResult, ExerciseStartResponse } from "@/types/learning";

export function useExercise() {
  const [activeExercise, setActiveExercise] = useState<Exercise | null>(null);
  const [attempt, setAttempt] = useState<ExerciseStartResponse | null>(null);
  const [result, setResult] = useState<ExerciseResult | null>(null);
  const [showHint, setShowHint] = useState<boolean>(false);
  const [usedHint, setUsedHint] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const startExercise = useCallback(async (exerciseId: string) => {
    try {
      setLoading(true);
      setError(null);
      setResult(null);
      setShowHint(false);
      setUsedHint(false);

      const [ex, att] = await Promise.all([
        learningApi.getExercise(exerciseId),
        learningApi.startExercise(exerciseId),
      ]);
      setActiveExercise(ex);
      setAttempt(att);
    } catch (err: any) {
      setError(err.message || "Failed to start exercise");
    } finally {
      setLoading(false);
    }
  }, []);

  const revealHint = useCallback(() => {
    setShowHint(true);
    setUsedHint(true);
  }, []);

  const submitTranscript = useCallback(
    async (
      transcript: string,
      options?: {
        turn_analysis_score?: number;
        pronunciation_score?: number;
        response_speed_ms?: number;
        plan_item_id?: string;
      }
    ) => {
      if (!activeExercise) return;
      try {
        setSubmitting(true);
        setError(null);

        const res = await learningApi.submitExercise(activeExercise.id, {
          user_transcript: transcript,
          turn_analysis_score: options?.turn_analysis_score,
          pronunciation_score: options?.pronunciation_score,
          response_speed_ms: options?.response_speed_ms,
          used_hint: usedHint,
          plan_item_id: options?.plan_item_id,
        });
        setResult(res);
        return res;
      } catch (err: any) {
        setError(err.message || "Failed to evaluate exercise");
      } finally {
        setSubmitting(false);
      }
    },
    [activeExercise, usedHint]
  );

  const resetExercise = useCallback(() => {
    setActiveExercise(null);
    setAttempt(null);
    setResult(null);
    setShowHint(false);
    setUsedHint(false);
    setError(null);
  }, []);

  return {
    activeExercise,
    attempt,
    result,
    showHint,
    usedHint,
    loading,
    submitting,
    error,
    startExercise,
    revealHint,
    submitTranscript,
    resetExercise,
    setActiveExercise,
  };
}
