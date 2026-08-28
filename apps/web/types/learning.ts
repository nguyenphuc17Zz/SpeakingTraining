export type LearningGoalType =
  | "speaking"
  | "pronunciation"
  | "conversation"
  | "workplace"
  | "travel"
  | "interview"
  | "jlpt"
  | "naturalness"
  | "fluency";

export type LearningGoalStatus = "active" | "paused" | "completed" | "archived";

export interface LearningGoal {
  id: string;
  title: string;
  description: string | null;
  goal_type: LearningGoalType;
  priority: number;
  status: LearningGoalStatus;
  target_date: string | null;
  created_at: string;
  updated_at: string;
}

export type LearningItemLifecycle =
  | "discovered"
  | "active"
  | "practicing"
  | "improving"
  | "mastered"
  | "maintenance"
  | "regressed";

export interface LearningItem {
  id: string;
  key: string;
  item_type: string;
  title: string;
  description: string | null;
  difficulty: string;
  lifecycle: LearningItemLifecycle;
  status: string;
  overall_mastery: number;
  recognition_mastery: number;
  production_mastery: number;
  spontaneous_mastery: number;
  context_variety_score: number;
  confidence: number;
  priority_score: number;
  attempt_count: number;
  success_count: number;
  review_streak: number;
  review_interval_days: number;
  last_practiced_at: string | null;
  next_review_at: string | null;
}

export interface SpeechSupport {
  keywords: string[];
  grammar_structures: string[];
  sentence_starters: string[];
  sample_dialogue_turns: { speaker: string; text: string; translation?: string }[];
}

export interface Exercise {
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
  canonical?: string;
  acceptable_variants?: string[];
  prompt?: string;
  extra_metadata?: any;
}

export interface ExerciseResult {
  exercise_id: string;
  user_id: string;
  score: number;
  success: boolean;
  confidence: number;
  target_mastery_delta: Record<string, number>;
  feedback: string;
  evidence: string[];
  metrics: Record<string, any>;
  independence: string;
  response_speed_ms: number | null;
  target_usage: string;
  pronunciation_score: number | null;
  grammar_score: number | null;
  naturalness_score: number | null;
  attempt_id: string | null;
}

export interface ExerciseStartResponse {
  exercise: Exercise;
  session_id?: string;
  pronunciation_attempt_id?: string;
  initial_context?: Record<string, any>;
}

export interface LearningPlanItem {
  id: string;
  plan_id: string;
  exercise_id: string;
  planned_order: number;
  status: "pending" | "in_progress" | "completed" | "skipped";
  duration_minutes: number;
  priority_score: number;
  exercise?: Exercise;
  target_type?: string;
  title?: string;
  estimated_minutes?: number;
}

export interface DailyPlan {
  id: string;
  user_id: string;
  plan_date: string;
  total_duration_minutes: number;
  estimated_minutes: number;
  status: "active" | "completed" | "archived";
  items: LearningPlanItem[];
  created_at: string;
  focus_title?: string;
  focus_reason?: string;
}

export interface LearningRecommendation {
  item?: LearningItem;
  priority_score: number;
  reason: string;
  recommended_action: string;
  why: string;
  how: string;
  // Flat properties for backward compatibility
  item_type?: string;
  difficulty?: string;
  estimated_minutes?: number;
  title?: string;
  mastery_percent?: number;
  success_count?: number;
  attempt_count?: number;
  key?: string;
}

export interface CurriculumUnit {
  id: string;
  title: string;
  objective: string;
  target_learning_items: string[];
  recommended_exercise_types: string[];
  completion_criteria: string;
  estimated_sessions: number;
  is_completed: boolean;
  progress_ratio: number;
}

// 4-Stage Interactive Dynamic AI Roadmap Models
export interface CurriculumNode {
  id: string;
  title: string;
  description: string;
  target_mode: string; // '/pitch' | '/keigo' | '/situations' | '/shadowing' | '/speaking' | '/bosses'
  mode_label: string;
  difficulty: string;
  key_patterns: string[];
  estimated_minutes: number;
  is_completed: boolean;
  score?: number;
}

export interface CurriculumStage {
  stage_number: number;
  title: string;
  badge: string;
  color: "sky" | "emerald" | "purple" | "amber" | string;
  objective: string;
  nodes: CurriculumNode[];
}

export interface CurriculumRoadmap {
  curriculum_id: string;
  title: string;
  description: string;
  level: string;
  level_label: string;
  target_goal: string;
  target_goal_label: string;
  daily_minutes: number;
  estimated_weeks: number;
  total_lessons: number;
  stages: CurriculumStage[];
}
