export interface MetricValueDTO {
  metric_key: string;
  name: string;
  ja_name: string;
  unit: string;
  category: string;
  value: number;
  baseline?: number | null;
  change?: number | null;
  sample_size: number;
  confidence: "high" | "medium" | "low" | "insufficient";
  period: string;
  trend:
    | "strongly_improving"
    | "improving"
    | "stable"
    | "declining"
    | "strongly_declining"
    | "plateau"
    | "insufficient_data";
  metric_version: string;
  description: string;
  extra_metadata?: Record<string, any>;
}

export interface GoalProgressDTO {
  goal_id: string;
  title: string;
  goal_type: string;
  progress_ratio: number; // 0.0 - 1.0
  confidence: "high" | "medium" | "low" | "insufficient";
  recent_activity_count: number;
  linked_items_count: number;
  blocked_by?: string | null;
  next_actions: string[];
}

export interface PracticeDistributionDTO {
  total_minutes: number;
  conversation_pct: number;
  pronunciation_pct: number;
  shadowing_pct: number;
  review_pct: number;
  drill_pct: number;
  recommendation_note?: string | null;
}

export interface BottleneckDTO {
  candidate: string;
  confidence: "high" | "medium" | "low" | "insufficient";
  description: string;
  evidence_keys: string[];
  suggested_focus?: string | null;
}

export interface InsightDTO {
  id: string;
  insight_type: string;
  title: string;
  description: string;
  confidence: string;
  metric_key?: string | null;
  metric_value?: number | null;
  action_hint?: string | null;
  action_target_type?: string | null;
  action_target_key?: string | null;
  evidence_keys: string[];
  lifecycle: "new" | "seen" | "acted_on" | "expired";
  generated_at?: string | null;
}

export interface WeeklyReviewDTO {
  week_start: string;
  speaking_minutes: number;
  session_count: number;
  active_days_count: number;
  metrics_summary: Record<string, any>;
  top_wins: string[];
  top_weaknesses: string[];
  goal_progress: Array<Record<string, any>>;
  practice_distribution: Record<string, number>;
  narrative?: string | null;
  is_ai_generated: boolean;
  recommendations: Array<Record<string, any>>;
}

export interface AnalyticsDashboardDTO {
  user_id: string;
  period: string;
  metrics: Record<string, MetricValueDTO>;
  bottleneck?: BottleneckDTO | null;
  top_insights: InsightDTO[];
  goals: GoalProgressDTO[];
  practice_distribution?: PracticeDistributionDTO | null;
}

export interface CoachRecommendationDTO {
  id?: string;
  action_type: "conversation" | "drill" | "shadowing" | "pronunciation";
  target: string;
  reason: string;
  duration_minutes: number;
  expected_signal?: string | null;
  practice_url?: string | null;
}

export interface CoachAnswerDTO {
  answer: string;
  intent_type: string;
  key_points: string[];
  evidence_refs: Array<Record<string, any>>;
  recommendations: CoachRecommendationDTO[];
  confidence: "high" | "medium" | "low" | "insufficient";
  is_deterministic: boolean;
  context_hash?: string | null;
  generated_at?: string | null;
}

export interface CoachAskRequest {
  question: string;
  session_context_id?: string | null;
}

export interface CoachFeedbackRequest {
  conversation_id: string;
  rating: "helpful" | "not_helpful" | "incorrect";
  feedback_text?: string | null;
}

export interface CoachQuickCardDTO {
  card_type: string;
  title: string;
  summary: string;
  metrics_snippet: Array<Record<string, any>>;
  action_cta?: string | null;
  action_url?: string | null;
}

export interface DailyBriefingDTO {
  date: string;
  yesterday_summary: string;
  today_focus_title: string;
  today_focus_reason: string;
  recommendation?: CoachRecommendationDTO | null;
  streak_status?: string | null;
}
