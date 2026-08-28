export type RecordingState =
  | "idle"
  | "requesting_permission"
  | "permission_denied"
  | "ready"
  | "listening"
  | "processing_stt"
  | "ai_thinking"
  | "ai_speaking"
  | "paused"
  | "ended"
  | "error";

export type SessionMode = "conversation" | "coaching";
export type VADSensitivity = "low" | "medium" | "high";

export type CorrectionCategory =
  | "grammar"
  | "word_choice"
  | "particle"
  | "conjugation"
  | "naturalness"
  | "politeness"
  | "context"
  | "pronunciation_placeholder";

export type CorrectionSeverity =
  | "MUST_FIX"
  | "SHOULD_FIX"
  | "NATIVE_ALTERNATIVE"
  | "IGNORE";

export type AnalysisConfidence = "high" | "medium" | "low";
export type FeedbackRating = "helpful" | "not_helpful" | "wrong_correction";

export interface CorrectionItem {
  id: string;
  turn_analysis_id: string;
  category: CorrectionCategory;
  severity: CorrectionSeverity;
  severity_score: number;
  original: string;
  corrected: string;
  explanation: string;
  native_alternative?: string | null;
  acceptable_alternatives?: string[] | null;
  context_note?: string | null;
  confidence: AnalysisConfidence;
  created_at: string;
}

export interface GrammarNote {
  id: string;
  grammar_pattern: string;
  user_usage: string;
  correct_usage: string;
  short_explanation: string;
  example_sentence?: string | null;
}

export interface VocabularyNote {
  id: string;
  original_word: string;
  suggested_alternatives?: string[] | null;
  nuance_explanation: string;
  jlpt_level?: string | null;
}

export interface TurnAnalysis {
  id: string;
  turn_id: string;
  session_id: string;
  overall_quality_score: number;
  communicative_success: boolean;
  is_suspicious_transcript: boolean;
  strengths?: string[] | null;
  context_notes?: Array<{
    persona_role?: string | null;
    formality_level: string;
    observation: string;
  }> | null;
  corrections: CorrectionItem[];
  grammar_notes: GrammarNote[];
  vocabulary_notes: VocabularyNote[];
  prompt_version: string;
  analyzer_version: string;
  ai_provider?: string | null;
  ai_model?: string | null;
  created_at: string;
}

export interface SessionAnalysis {
  id: string;
  session_id: string;
  overall_score: number;
  strengths?: string[] | null;
  weaknesses?: string[] | null;
  repeated_issues?: Array<{
    pattern: string;
    occurrences_count: number;
    recommendation: string;
  }> | null;
  top_recommendations?: string[] | null;
  total_user_turns_analyzed: number;
  total_corrections_count: number;
  must_fix_count: number;
  should_fix_count: number;
  native_alt_count: number;
  grammar_summary?: string[] | null;
  vocabulary_summary?: string[] | null;
  prompt_version: string;
  analyzer_version: string;
  ai_provider?: string | null;
  ai_model?: string | null;
  created_at: string;
}

export interface ConversationAnalysisSummary {
  session_id: string;
  session_analysis?: SessionAnalysis | null;
  turn_analyses: TurnAnalysis[];
  pending_jobs_count: number;
}

export interface ConversationTurn {
  id: string;
  session_id: string;
  sequence: number;
  speaker: "user" | "assistant";
  transcript: string;
  client_turn_id?: string | null;
  stt_provider?: string | null;
  stt_model?: string | null;
  ai_provider?: string | null;
  ai_model?: string | null;
  tts_provider?: string | null;
  tts_voice?: string | null;
  processing_time_ms?: number | null;
  metrics?: {
    stt_ms?: number;
    ai_ms?: number;
    tts_ms?: number;
    total_ms?: number;
    speech_duration_ms?: number;
    confidence?: number;
  } | null;
  feedback_hint?: string | null;
  analysis?: TurnAnalysis | null;
  started_at: string;
  ended_at?: string | null;
  created_at: string;
}

export interface VoiceSession {
  id: string;
  user_id: string;
  persona_id: string;
  mode: SessionMode;
  status: "active" | "completed" | "cancelled" | "error";
  provider_preference?: string | null;
  model_preference?: string | null;
  stt_provider_preference?: string | null;
  stt_model_preference?: string | null;
  tts_provider_preference?: string | null;
  tts_voice_preference?: string | null;
  started_at: string;
  ended_at?: string | null;
  duration_seconds?: number | null;
  created_at: string;
  updated_at: string;
  turns?: ConversationTurn[];
  opening_audio_base64?: string | null;
  opening_audio_format?: string;
}

export interface AudioTurnResponse {
  session_id: string;
  user_turn: ConversationTurn;
  assistant_turn: ConversationTurn;
  audio_base64?: string | null;
  audio_format: string;
  metrics: Record<string, any>;
  tts_error?: string | null;
}

export interface SessionSummary {
  session_id: string;
  persona_id: string;
  persona_name: string;
  mode: string;
  status: string;
  started_at: string;
  ended_at?: string | null;
  duration_seconds: number;
  turn_count: number;
  user_turns_count: number;
  assistant_turns_count: number;
  total_speaking_time_seconds: number;
  avg_turn_latency_ms: number;
  primary_ai_provider?: string | null;
  primary_ai_model?: string | null;
}

export * from "./pronunciation";

export interface VoiceSettingsConfig {
  ai_provider: string; // 'auto' | 'gemini' | 'groq' | 'openrouter'
  ai_model: string;
  stt_provider: string; // 'faster_whisper'
  stt_model: string; // 'auto' | 'tiny' | 'base' | 'small' | 'medium' | 'turbo' | 'large-v3'
  tts_provider: string; // 'voicevox' | 'web_speech' | 'none'
  tts_voice: string; // '1' | '2' | ...
  tts_enabled?: boolean; // true = synthesize audio, false = text-only lightweight mode
  tts_engine?: "voicevox" | "web_speech" | "none"; // speech engine type
  vad_sensitivity: VADSensitivity;
  auto_end_of_speech?: boolean; // true = auto VAD detect, false = manual push-to-talk
}

export interface TTSVoiceOption {
  id: string;
  name: string;
  speaker_id: number | string;
  gender: string;
  style?: string | null;
}

export interface STTModelOption {
  id: string;
  name: string;
  recommended_for: string;
  is_recommended: boolean;
}

export interface AnalysisFeedbackPayload {
  rating: FeedbackRating;
  reason?: string;
  turn_analysis_id?: string;
  correction_id?: string;
}
