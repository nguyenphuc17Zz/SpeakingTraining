export interface MemoryEvidence {
  id: string;
  memory_id: string;
  session_id: string;
  turn_id?: string | null;
  turn_analysis_id?: string | null;
  correction_id?: string | null;
  evidence_type: string;
  weight: number;
  original_snippet?: string | null;
  corrected_snippet?: string | null;
  context_tag?: string | null;
  created_at: string;
}

export interface LearnerMemory {
  id: string;
  user_id: string;
  memory_type: string;
  key: string;
  statement: string;
  category?: string | null;
  evidence_count: number;
  confidence: number;
  severity: string;
  severity_score: number;
  priority_score: number;
  mastery: number;
  attempt_count: number;
  correct_count: number;
  error_count: number;
  first_seen: string;
  last_seen: string;
  trend: "new" | "improving" | "stable" | "worsening" | "resolved" | "unknown";
  status: "new" | "active" | "improving" | "stable" | "resolved" | "archived" | "dismissed";
  is_regression: boolean;
  contexts_used?: string[] | null;
  created_at: string;
  updated_at: string;
}

export interface LearnerMemoryDetail extends LearnerMemory {
  evidences: MemoryEvidence[];
}

export interface ProfileWeakness {
  id: string;
  key: string;
  statement: string;
  category: string;
  priority_score: number;
  mastery: number;
  trend: string;
  evidence_count: number;
  is_regression: boolean;
  severity: string;
  last_seen?: string | null;
}

export interface ProfileStrength {
  id: string;
  key: string;
  statement: string;
  priority_score: number;
  mastery: number;
  evidence_count: number;
  last_seen?: string | null;
}

export interface LearnerProfile {
  id: string;
  user_id: string;
  overall_level: string;
  speaking_level: string;
  fluency_level: string;
  grammar_level: string;
  vocabulary_level: string;
  naturalness_level: string;
  confidence_score: number;
  level_confidence: "insufficient_evidence" | "low" | "medium" | "high";
  total_sessions_analyzed: number;
  total_turns_analyzed: number;
  avg_response_speed_ms?: number | null;
  current_focus?: string | null;
  strengths?: ProfileStrength[] | null;
  weaknesses?: ProfileWeakness[] | null;
  learning_goals?: string[] | null;
  summary?: string | null;
  summary_version: number;
  summary_generated_at?: string | null;
  last_recalculated_at: string;
}

export interface LearningPriority {
  key: string;
  type: string;
  priority_score: number;
  reason: string;
  mastery: number;
  trend: string;
  recommended_focus: string;
  evidence_count: number;
  last_seen?: string | null;
}

export interface MemoryFeedbackCreate {
  action: "dismiss" | "mark_inaccurate" | "restore";
  feedback_text?: string;
}

export interface MemoryFeedback {
  id: string;
  memory_id: string;
  user_id: string;
  action: string;
  feedback_text?: string | null;
  created_at: string;
}
