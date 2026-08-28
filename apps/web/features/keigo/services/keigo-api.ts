"use client";

import { apiClient } from "@/services/api-client";

export type PressureLevel = "relaxed" | "normal" | "fast" | "reflex" | "extreme";

export interface KeigoExercise {
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
  subMode?: string;
  timerLimitMs: number;
  pressureLevel?: string;
  canonical?: string;
  acceptableVariants?: string[];
  prompt?: string;
  socialContext?: any;
  extra_metadata?: any;
}

export interface KeigoResult {
  exerciseId: string;
  success: boolean;
  score: number;
  feedback: string;
  transcript: string;
  normalized: string;
  assessment: any;
  reactionLatencyMs: number | null;
  timerLimitMs: number;
  timedOut: boolean;
  lateResponse: boolean;
  masteryDeltas: Record<string, number>;
  isPerfect: boolean;
  doubleKeigo?: any;
  userAudioUrl?: string;
  canonicalAnswer?: string;
  acceptableVariants?: string[];
  targetRegister?: string;
}

export interface GenerateOpts {
  subMode: string;
  pressureLevel?: PressureLevel;
  timerLimitMs?: number;
  difficulty?: string;
}

export async function generateExercise(opts: GenerateOpts): Promise<KeigoExercise> {
  let effMode = opts.subMode;
  if (effMode === "mixed") {
    const r = Math.random();
    if (r < 0.20) effMode = "keigo_sonkeigo";
    else if (r < 0.40) effMode = "keigo_kenjougo";
    else if (r < 0.60) effMode = "keigo_teineigo";
    else if (r < 0.80) effMode = "keigo_transformation";
    else effMode = "keigo_context";
  }
  const params = new URLSearchParams();
  params.set("sub_mode", effMode);
  if (opts.pressureLevel) params.set("pressure_level", opts.pressureLevel);
  if (opts.timerLimitMs) params.set("timer_limit_ms", String(opts.timerLimitMs));
  if (opts.difficulty) params.set("difficulty", opts.difficulty);
  const data = await apiClient.post(`/keigo/exercises/generate?${params.toString()}`);
  const ex = data as any;
  const rc = ex.extra_metadata?.keigo_config || {};
  return {
    ...ex,
    subMode: rc.sub_mode || ex.exercise_type,
    timerLimitMs: rc.timer_limit_ms || ex.timer_limit_ms || ex.extra_metadata?.timer_limit_ms || 5000,
    pressureLevel: rc.pressure_level || opts.pressureLevel || "normal",
    canonical: rc.canonical || ex.canonical || ex.target_patterns?.[0] || "",
    acceptableVariants: rc.accepted || ex.acceptable_variants || ex.target_patterns || (rc.canonical ? [rc.canonical] : []),
    prompt: rc.prompt || ex.prompt || ex.scenario || ex.title,
    socialContext: rc.social_context || ex.social_context || ex.extra_metadata?.social_context,
  };
}

export async function submitAttempt(exerciseId: string, payload: Record<string, any>): Promise<any> {
  try {
    const data = await apiClient.post(`/keigo/exercises/${exerciseId}/submit`, payload);
    return data;
  } catch (e: any) {
    const fallbackPayload: any = {
      user_transcript: payload.user_transcript || payload.transcript || "",
      response_speed_ms: payload.reaction_latency_ms || payload.response_speed_ms,
      used_hint: payload.used_hint || false,
      reaction_latency_ms: payload.reaction_latency_ms,
      timer_limit_ms: payload.timer_limit_ms,
      timed_out: payload.timed_out,
      late_response: payload.late_response,
      speech_confidence: payload.speech_confidence,
      keigo_metrics: payload.keigo_metrics || {
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
  const data = await apiClient.get("/keigo/pressure-profiles");
  return data;
}

export async function getProgress(period: string = "30d"): Promise<any> {
  const data = await apiClient.get(`/keigo/progress?period=${period}`);
  return data;
}
