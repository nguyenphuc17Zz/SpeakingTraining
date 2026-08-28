"use client";
import { useCallback, useState } from "react";
import { monologueApi, SpeechSubmitPayload } from "@/services/monologue-api";
import { Exercise } from "@/types/learning";

export type MonologuePhase = "idle" | "preparing" | "ready" | "recording" | "processing" | "result" | "retry";

export function useMonologue() {
  const [exercise, setExercise] = useState<Exercise | null>(null);
  const [phase, setPhase] = useState<MonologuePhase>("idle");
  const [result, setResult] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // timers
  const [prepRemaining, setPrepRemaining] = useState(0);
  const [recRemaining, setRecRemaining] = useState(0);

  const generate = useCallback(async (params: any = {}) => {
    try {
      setLoading(true); setError(null);
      const ex = await monologueApi.generate(params);
      setExercise(ex);
      setPhase("preparing");
      // set prep countdown from metadata
      const prepSec = (ex.extra_metadata as any)?.speech_config?.prep_duration_sec ?? 30;
      setPrepRemaining(prepSec);
      return ex;
    } catch (e: any) {
      setError(e.message || "Generate failed");
      throw e;
    } finally {
      setLoading(false);
    }
  }, []);

  const submit = useCallback(async (payload: SpeechSubmitPayload) => {
    if (!exercise) return;
    try {
      setPhase("processing"); setError(null);
      const res = await monologueApi.submit(exercise.id, payload);
      setResult(res);
      if (res.status === "RETRY_AUDIO") {
        setPhase("retry");
      } else {
        setPhase("result");
      }
      return res;
    } catch (e: any) {
      setError(e.message || "Submit failed");
      setPhase("retry");
      throw e;
    }
  }, [exercise]);

  const submitMultipart = useCallback(async (blob: Blob, payload: Omit<SpeechSubmitPayload, "audio_base64">) => {
    if (!exercise) return;
    try {
      setPhase("processing"); setError(null);
      const res = await monologueApi.submitMultipart(exercise.id, blob, payload);
      setResult(res);
      if (res.status === "RETRY_AUDIO") {
        setPhase("retry");
      } else {
        setPhase("result");
      }
      return res;
    } catch (e: any) {
      setError(e.message || "Submit failed");
      setPhase("retry");
      throw e;
    }
  }, [exercise]);

  const reset = useCallback(() => {
    setExercise(null); setResult(null); setPhase("idle"); setError(null);
  }, []);

  return { exercise, setExercise, phase, setPhase, result, loading, error, prepRemaining, setPrepRemaining, recRemaining, setRecRemaining, generate, submit, submitMultipart, reset };
}
