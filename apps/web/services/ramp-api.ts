import { apiClient } from "@/services/api-client";

export interface RampSession {
  id: string;
  state: string;
  stage: number;
  support_level: number;
  desired_minutes: number;
  exercises_total: number;
  exercises_completed?: number;
  milestones_achieved?: string[];
  started_at?: string;
}

export interface RampScaffold {
  support_level: number;
  topic?: string;
  keywords: string[];
  guided_questions: string[];
  sentence_starter?: string;
  structure_outline: string[];
  example_response?: string;
  translation_reference?: string;
}

export interface RampTaskSpec {
  exercise_type: string;
  stage: number;
  topic: string;
  topic_domain: string;
  prompt_jp: string;
  prompt_vi?: string;
  target_duration_sec: number;
  support_level: number;
  scaffold: RampScaffold;
  echo_sentence?: string;
  template_sentence?: string;
  substitution_variable?: string;
  seed_sentence?: string;
  expansion_dimension?: string;
  keywords_for_production: string[];
  previous_response?: string;
  is_retry: boolean;
}

export interface NextExerciseResponse {
  exercise_id: string;
  exercise_type: string;
  title: string;
  instructions: string;
  ramp_config: Record<string, any>;
  task_spec: RampTaskSpec;
}

export interface RampScore {
  overall: number;
  production_accuracy: number;
  independence: number;
  completeness: number;
  fluency: number;
  elaboration: number;
  reaction: number;
  support_level_used: number;
  sentence_count: number;
  idea_count: number;
  speech_duration_ms?: number;
  filler_rate?: number;
  long_pause_count?: number;
  response_latency_ms?: number;
  independence_level: string;
}

export interface ElaborationPrompt {
  signal: string;
  cue_jp: string;
  cue_vi?: string;
  step: number;
}

export interface FollowUpSpec {
  question_jp: string;
  question_vi?: string;
  follow_up_type: string;
  depth_level: number;
  relates_to?: string;
}

export interface RampAttemptFeedback {
  meaning_clear: boolean;
  grammar_ok: boolean;
  too_short: boolean;
  missing_reason: boolean;
  missing_example: boolean;
  incomplete_sentence: boolean;
  elaboration_prompt?: ElaborationPrompt;
  correction?: string;
  badges: string[];
  next_action: string;
  ramp_score?: RampScore;
  followup?: FollowUpSpec;
}

export interface SubmitAttemptResult {
  score: RampScore;
  feedback: RampAttemptFeedback;
  delta: {
    stage_changed: boolean;
    new_stage: number;
    support_changed: boolean;
    new_support: number;
    new_milestones: string[];
    success: boolean;
  };
  new_stage: number;
  new_support_level: number;
  followup?: FollowUpSpec;
  session_state: string;
}

export interface RampProgressSnapshot {
  user_id: string;
  current_stage: number;
  current_support_level: number;
  max_independent_duration_ms: number;
  avg_independent_duration_ms: number;
  sentence_completeness_rate: number;
  elaboration_success_rate: number;
  reason_success_rate: number;
  example_success_rate: number;
  followup_success_rate: number;
  independent_success_rate: number;
  total_attempts: number;
}

export interface RampSessionSummary {
  session_id: string;
  duration_minutes: number;
  exercises_completed: number;
  stage_start: number;
  stage_end: number;
  support_level_start: number;
  support_level_end: number;
  independent_speaking_pct: number;
  avg_response_duration_ms: number;
  full_sentence_rate: number;
  elaboration_success_rate: number;
  reason_example_rate: number;
  strengths: string[];
  weaknesses: string[];
  next_recommendation: string;
  milestones_achieved: string[];
}

export interface StageMetadata {
  stage: number;
  name: string;
  target_duration_sec: number;
  exercise_type: string;
}

export const rampApi = {
  async createSession(params: {
    desired_minutes?: number;
    session_goal?: string;
    current_stage?: number;
    support_level?: number;
  } = {}): Promise<RampSession> {
    return apiClient.post<RampSession>("/ramp/sessions", params);
  },

  async getSession(sessionId: string): Promise<RampSession> {
    return apiClient.get<RampSession>(`/ramp/sessions/${sessionId}`);
  },

  async generateNextExercise(
    sessionId: string,
    params: { is_retry?: boolean; force_followup?: boolean } = {}
  ): Promise<NextExerciseResponse> {
    return apiClient.post<NextExerciseResponse>(
      `/ramp/sessions/${sessionId}/next-exercise`,
      params
    );
  },

  async submitAttempt(
    sessionId: string,
    exerciseId: string,
    payload: {
      user_transcript: string;
      audio_base64?: string;
      support_level_used?: number;
      used_hint?: boolean;
      response_latency_ms?: number;
    }
  ): Promise<SubmitAttemptResult> {
    return apiClient.post<SubmitAttemptResult>(
      `/ramp/sessions/${sessionId}/exercises/${exerciseId}/submit`,
      payload
    );
  },

  async getSessionProgress(sessionId: string): Promise<RampProgressSnapshot> {
    return apiClient.get<RampProgressSnapshot>(
      `/ramp/sessions/${sessionId}/progress`
    );
  },

  async completeSession(sessionId: string): Promise<RampSessionSummary> {
    return apiClient.post<RampSessionSummary>(
      `/ramp/sessions/${sessionId}/complete`,
      {}
    );
  },

  async getRampProgress(period: string = "30d"): Promise<any> {
    return apiClient.get<any>(`/ramp/progress?period=${period}`);
  },

  async getStages(): Promise<{ stages: StageMetadata[]; support_levels: any[] }> {
    return apiClient.get<any>("/ramp/stages");
  },
};
