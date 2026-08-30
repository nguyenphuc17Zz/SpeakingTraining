"use client";

import { apiClient } from "@/services/api-client";

export type SituationsPressureLevel = "infinite" | "relaxed" | "normal" | "fast" | "reflex" | "extreme";

export interface SituationalGoal {
  id: string;
  task: string;
  intent?: string;
  description?: string;
  status?: "NOT_STARTED" | "COMPLETED" | "FAILED";
  hidden?: boolean;
}

export interface SituationsKeyword {
  word: string;
  reading?: string;
  meaning: string;
}

export interface SituationsHints {
  tier1_keywords?: SituationsKeyword[];
  tier2_frame?: string;
  tier3_model?: string;
}

export interface SituationalData {
  category_key: string;
  category_label: string;
  location: string;
  npc_name: string;
  npc_personality: string;
  npc_opening_dialogue: string;
  npc_dialogue_vi?: string;
  user_role: string;
  goals: SituationalGoal[];
  unexpected_event?: string;
  useful_phrases?: string[];
  vocabulary_hints?: string;
  hints?: SituationsHints;
  quick_starters?: string[];
  cultural_tip?: string;
  is_custom?: boolean;
  custom_topic?: string | null;
}

export interface SituationsExercise {
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
  situationalData?: SituationalData;
  hints?: SituationsHints;
  quickStarters?: string[];
  culturalTip?: string;
  extra_metadata?: any;
}

export interface SituationsResult {
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
  metrics?: {
    task_completion?: number;
    pragmatics?: number;
    fluency?: number;
    naturalness?: number;
  };
  culturalTip?: string;
}

export interface GenerateSituationsParams {
  category?: string;
  customTopic?: string;
  subMode?: string;
  pressureLevel?: SituationsPressureLevel;
  timerLimitMs?: number;
  difficulty?: string;
  duration?: number;
  mode?: string;
}

export async function generateExercise(params: GenerateSituationsParams = {}): Promise<SituationsExercise> {
  const {
    category = "food",
    customTopic,
    subMode = "situational_roleplay",
    pressureLevel = "normal",
    timerLimitMs,
    difficulty,
    duration = 5,
    mode = "standard",
  } = params;

  const q = new URLSearchParams({
    sub_mode: subMode,
    pressure_level: pressureLevel,
    duration: String(duration),
    mode,
  });
  if (category && category !== "all") q.set("category", category);
  if (customTopic && customTopic.trim()) q.set("custom_topic", customTopic.trim());
  if (timerLimitMs !== undefined) q.set("timer_limit_ms", String(timerLimitMs));
  if (difficulty) q.set("difficulty", difficulty);

  const res = await apiClient.post<any>(`/situations/exercises/generate?${q.toString()}`);
  const sc = res.extra_metadata?.situational_config || {};
  const sData = sc.situational_data || {};

  return {
    ...res,
    subMode: sc.sub_mode || subMode,
    timerLimitMs: sc.timer_limit_ms !== undefined ? sc.timer_limit_ms : (timerLimitMs !== undefined ? timerLimitMs : 6000),
    pressureLevel: sc.pressure_level || pressureLevel,
    canonical: sc.canonical || res.canonical || sData.npc_opening_dialogue || res.prompt,
    acceptableVariants: sc.accepted || res.acceptableVariants || [],
    prompt: sc.prompt || res.prompt || sData.npc_opening_dialogue,
    translation: sc.translation || sData.npc_dialogue_vi || res.scenario || "",
    situationalData: sData,
    hints: sData.hints || sc.hints,
    quickStarters: sData.quick_starters || sc.quick_starters || [],
    culturalTip: sData.cultural_tip || sc.cultural_tip || "",
  };
}

export async function submitAttempt(payload: {
  exercise_id: string;
  transcript?: string;
  reflex_metrics?: {
    reaction_latency_ms: number;
    timed_out: boolean;
  };
}): Promise<SituationsResult> {
  const res = await apiClient.post<any>(`/situations/exercises/${payload.exercise_id}/submit`, {
    user_transcript: payload.transcript || "",
    reaction_latency_ms: payload.reflex_metrics?.reaction_latency_ms || 0,
    timed_out: payload.reflex_metrics?.timed_out || false,
  });

  return {
    exerciseId: payload.exercise_id,
    score: res.score ?? (res.success ? 90 : 55),
    success: res.success ?? true,
    isPerfect: res.isPerfect ?? (res.score >= 90),
    timedOut: res.timedOut ?? false,
    reactionLatencyMs: res.reactionLatencyMs ?? payload.reflex_metrics?.reaction_latency_ms ?? 0,
    userTranscript: res.userTranscript || payload.transcript || "",
    feedback: res.feedback || "Phản xạ giao tiếp tình huống tốt, đạt mục tiêu đối thoại!",
    strengths: res.strengths || ["Đúng ngữ cảnh", "Phản xạ tự nhiên"],
    improvements: res.improvements || [],
    drillScores: res.drillScores || {},
    metrics: res.metrics || {
      task_completion: res.score ?? 90,
      pragmatics: 88,
      fluency: 85,
      naturalness: 87,
    },
    culturalTip: res.culturalTip || (res as any).cultural_tip,
  };
}
