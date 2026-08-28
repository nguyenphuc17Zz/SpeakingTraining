"use client";

import { apiClient } from "@/services/api-client";

export type PressureLevel = "relaxed" | "normal" | "fast" | "reflex" | "extreme";

export interface ReflexExercise {
  id: string;
  exercise_type: string;
  title: string;
  objective: string;
  scenario: string | null;
  instructions: string;
  constraints: string[];
  target_patterns: string[];
  difficulty: string;
  scaffold_level: string;
  scaffold_hint: string | null;
  estimated_minutes: number;
  created_at: string;
  // reflex extra
  subMode?: string;
  timerLimitMs: number;
  pressureLevel?: string;
  canonical?: string;
  acceptableVariants?: string[];
  acceptable_variants?: string[];
  prompt?: string;
  verb?: string;
  conjugationTarget?: string;
  extra_metadata?: any;
}

export interface ReflexResult {
  exerciseId: string;
  success: boolean;
  score: number;
  feedback: string;
  transcript: string;
  normalized: string;
  assessment: any;
  reactionLatencyMs: number | null;
  semanticLatencyMs: number | null;
  timerLimitMs: number;
  timedOut: boolean;
  lateResponse: boolean;
  masteryDeltas: Record<string, number>;
  isPerfect: boolean;
  userAudioUrl?: string | null;
  canonicalAnswer?: string;
  acceptableVariants?: string[];
  promptText?: string;
  promptTranslation?: string;
  targetForm?: string;
  verb?: string;
}

export interface GenerateOpts {
  subMode: string;
  pressureLevel?: PressureLevel;
  timerLimitMs?: number;
  verb?: string;
  conjugationTarget?: string;
  difficulty?: string;
}

export async function generateExercise(opts: GenerateOpts): Promise<ReflexExercise> {
  // Map mixed to random weighted before request (defensive: backend also supports mixed via factory fallback)
  let effMode = opts.subMode;
  if (effMode === "mixed") {
    const r = Math.random();
    if (r < 0.30) effMode = "reflex_conjugation";
    else if (r < 0.60) effMode = "reflex_qna";
    else if (r < 0.80) effMode = "reflex_transformation";
    else effMode = "reflex_context";
  }
  const params = new URLSearchParams();
  params.set("sub_mode", effMode);
  if (opts.pressureLevel) params.set("pressure_level", opts.pressureLevel);
  if (opts.timerLimitMs) params.set("timer_limit_ms", String(opts.timerLimitMs));
  if (opts.verb) params.set("verb", opts.verb);
  if (opts.conjugationTarget) params.set("conjugation_target", opts.conjugationTarget);
  if (opts.difficulty) params.set("difficulty", opts.difficulty);
  params.set("nonce", `${Date.now()}_${Math.random().toString(36).slice(2, 7)}`);
  const data = await apiClient.post(`/reflex/exercises/generate?${params.toString()}`);
  const ex = data as any;
  const rc = ex.extra_metadata?.reflex_config || {};
  return {
    ...ex,
    subMode: rc.sub_mode || ex.exercise_type,
    timerLimitMs: rc.timer_limit_ms || 3000,
    pressureLevel: rc.pressure_level || opts.pressureLevel || "normal",
    canonical: rc.canonical,
    acceptableVariants: rc.acceptable_variants || ex.acceptable_variants,
    prompt: rc.prompt || ex.scenario,
    verb: rc.verb,
    conjugationTarget: rc.conjugation_target,
  };
}

export async function submitAttempt(exerciseId: string, payload: Record<string, any>): Promise<any> {
  // Try reflex endpoint first, fallback to learning
  try {
    const data = await apiClient.post(`/reflex/exercises/${exerciseId}/submit`, payload);
    return data;
  } catch (e: any) {
    // Fallback to learning endpoint
    const fallbackPayload: any = {
      user_transcript: payload.user_transcript || payload.transcript || "",
      response_speed_ms: payload.reaction_latency_ms || payload.response_speed_ms,
      used_hint: payload.used_hint || false,
      reaction_latency_ms: payload.reaction_latency_ms,
      semantic_latency_ms: payload.semantic_latency_ms,
      timer_limit_ms: payload.timer_limit_ms,
      timed_out: payload.timed_out,
      late_response: payload.late_response,
      speech_confidence: payload.speech_confidence,
      reflex_metrics: payload.reflex_metrics || {
        reaction_latency_ms: payload.reaction_latency_ms,
        timer_limit_ms: payload.timer_limit_ms,
        timed_out: payload.timed_out,
        late_response: payload.late_response,
        speech_confidence: payload.speech_confidence,
      },
    };
    const data2 = await apiClient.post(`/learning/exercises/${exerciseId}/submit`, fallbackPayload);
    return data2;
  }
}

export async function getPressureProfiles(): Promise<any> {
  const data = await apiClient.get("/reflex/pressure-profiles");
  return data;
}

export async function getProgress(period: string = "30d"): Promise<any> {
  const data = await apiClient.get(`/reflex/progress?period=${period}`);
  return data;
}

export async function getExercise(exerciseId: string): Promise<ReflexExercise> {
  const data = await apiClient.get(`/reflex/exercises/${exerciseId}`);
  return data as ReflexExercise;
}
