"use client";

import { apiClient } from "@/services/api-client";

export type PitchPressureLevel = "infinite" | "relaxed" | "normal" | "fast" | "reflex" | "extreme";

export interface MoraToken {
  index: number;
  mora: string;
  tone: "H" | "L" | string;
  is_downstep?: boolean;
}

export interface PitchQuizOption {
  option_id: string;
  key: string;
  word: string;
  meaning: string;
  accent_type: string;
  is_correct: boolean;
}

export interface PitchExercise {
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
  reading?: string;
  translation?: string;
  pitchPattern?: string[];
  moraBreakdown?: MoraToken[];
  downstepIndex?: number;
  downstepNotation?: string;
  pitfallVi?: string;
  quizOptions?: PitchQuizOption[];
  extra_metadata?: any;
}

export interface PitchMetrics {
  pitch_accuracy?: number;
  mora_score?: number;
  devoicing_score?: number;
  naturalness_score?: number;
  f0_contour?: number[];
  target_contour?: string[];
}

export interface PitchResult {
  exerciseId: string;
  score: number;
  success: boolean;
  isPerfect: boolean;
  timedOut: boolean;
  reactionLatencyMs: number;
  userTranscript: string;
  feedback?: string;
  strengths: string[];
  improvements: string[];
  drillScores?: Record<string, number>;
  pitchMetrics?: PitchMetrics;
  moraBreakdown?: MoraToken[];
  downstepNotation?: string;
  pitfallVi?: string;
}

export interface GeneratePitchParams {
  subMode?: string;
  pressureLevel?: PitchPressureLevel;
  timerLimitMs?: number;
  difficulty?: string;
}

export async function generateExercise(params: GeneratePitchParams = {}): Promise<PitchExercise> {
  const { subMode = "pitch_minimal_pair", pressureLevel = "normal", timerLimitMs, difficulty } = params;
  const q = new URLSearchParams({
    sub_mode: subMode,
    pressure_level: pressureLevel,
  });
  if (timerLimitMs !== undefined) q.set("timer_limit_ms", String(timerLimitMs));
  if (difficulty) q.set("difficulty", difficulty);

  const res = await apiClient.post<any>(`/pitch/exercises/generate?${q.toString()}`);
  const pc = res.extra_metadata?.pitch_config || {};

  return {
    ...res,
    subMode: pc.sub_mode || subMode,
    timerLimitMs: pc.timer_limit_ms !== undefined ? pc.timer_limit_ms : (timerLimitMs !== undefined ? timerLimitMs : 5000),
    pressureLevel: pc.pressure_level || pressureLevel,
    canonical: pc.canonical || res.canonicalAnswer || pc.prompt || res.prompt,
    acceptableVariants: pc.accepted || res.acceptableVariants || [],
    prompt: pc.prompt || res.prompt || pc.canonical,
    reading: pc.reading || "",
    translation: pc.translation || res.scenario || "",
    pitchPattern: pc.pitch_pattern || [],
    moraBreakdown: pc.mora_breakdown || [],
    downstepIndex: pc.downstep_index ?? 0,
    downstepNotation: pc.downstep_notation || "",
    pitfallVi: pc.pitfall_vi || "",
    quizOptions: pc.quiz_options || [],
  };
}

export async function submitAttempt(payload: {
  exercise_id: string;
  transcript?: string;
  pitch_metrics?: any;
  reflex_metrics?: {
    reaction_latency_ms: number;
    timed_out: boolean;
  };
}): Promise<PitchResult> {
  const res = await apiClient.post<any>(`/pitch/exercises/${payload.exercise_id}/submit`, {
    user_transcript: payload.transcript || "",
    reaction_latency_ms: payload.reflex_metrics?.reaction_latency_ms || 0,
    timed_out: payload.reflex_metrics?.timed_out || false,
    pitch_metrics: payload.pitch_metrics,
  });
  return {
    exerciseId: payload.exercise_id,
    score: res.score ?? (res.success ? 90 : 50),
    success: res.success ?? true,
    isPerfect: res.isPerfect ?? (res.score >= 90),
    timedOut: res.timedOut ?? false,
    reactionLatencyMs: res.reactionLatencyMs ?? payload.reflex_metrics?.reaction_latency_ms ?? 0,
    userTranscript: res.userTranscript || payload.transcript || "",
    feedback: res.feedback || "Phát âm chuẩn cao độ Tokyo",
    strengths: res.strengths || [],
    improvements: res.improvements || [],
    drillScores: res.drillScores || {},
    pitchMetrics: res.pitchMetrics || (res as any).pitch_metrics || {},
    moraBreakdown: res.moraBreakdown || (res as any).mora_breakdown,
    downstepNotation: res.downstepNotation || (res as any).downstep_notation,
    pitfallVi: res.pitfallVi || (res as any).pitfall_vi,
  };
}
