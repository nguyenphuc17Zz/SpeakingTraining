export type AnalysisConfidenceLevel = "high" | "medium" | "low" | "uncertain";
export type TargetType = "word" | "phrase" | "sentence" | "conversation_line" | "custom";
export type ReferenceType = "human" | "synthetic" | "youtube" | "unknown";
export type PitchAccentPattern = "heiban" | "atamadaka" | "nakadaka" | "odaka" | "unknown";

export interface AudioQualityReport {
  is_usable: boolean;
  signal_level_rms: number;
  is_clipped: boolean;
  snr_estimate_db?: number | null;
  silence_ratio: number;
  duration_ms: number;
  issues: string[];
  guidance?: string | null;
}

export interface MoraUnit {
  mora_index: number;
  kana: string;
  phonemes: string[];
  is_special: boolean;
  special_type?: string | null;
  expected_duration_ms?: number | null;
  actual_duration_ms?: number | null;
  duration_ratio?: number | null;
  score?: number | null;
  issue?: string | null;
  confidence: number;
}

export interface PitchPoint {
  timestamp_ms: number;
  frequency_hz: number;
  normalized_semitones: number;
  is_voiced: boolean;
  confidence: number;
}

export interface PitchCurve {
  points: PitchPoint[];
  speaker_f0_mean?: number | null;
  speaker_f0_std?: number | null;
  voiced_ratio: number;
  confidence: number;
  normalization_method: string;
}

export interface PhonemeAssessment {
  mora_index: number;
  kana: string;
  target_phonemes: string[];
  detected_sound_category?: string | null;
  score: number;
  confidence: number;
  issue_type?: string | null;
  tip?: string | null;
}

export interface MoraTimingAssessment {
  overall_score: number;
  confidence: number;
  mora_units: MoraUnit[];
  speech_rate_mora_per_sec: number;
  rhythm_regularity_score: number;
  top_timing_issues: string[];
}

export interface PitchAssessment {
  overall_score: number;
  confidence: number;
  accent_pattern_target: PitchAccentPattern;
  accent_pattern_observed: PitchAccentPattern;
  pattern_matched: boolean;
  pitch_curve?: PitchCurve | null;
  reference_pitch_curve?: PitchCurve | null;
  explanation?: string | null;
}

export interface RhythmAssessment {
  overall_score: number;
  confidence: number;
  speech_rate_mora_per_sec: number;
  reference_rate_mora_per_sec?: number | null;
  pause_count: number;
  hesitation_count: number;
  naturalness_score: number;
  details: Record<string, any>;
}

export interface IntonationAssessment {
  overall_score: number;
  confidence: number;
  sentence_final_type: string;
  is_sentence_final_natural: boolean;
  phrase_boundaries_count: number;
  contour_smoothness: number;
  explanation?: string | null;
}

export interface PronunciationScoreComponent {
  score: number;
  confidence: number;
  weight: number;
  available: boolean;
  interpretation: string;
}

export interface PronunciationFeedbackItem {
  issue_key: string;
  category: string;
  severity: "MUST_FIX" | "SHOULD_FIX" | "NATIVE_ALTERNATIVE" | "STRENGTH";
  title: string;
  explanation: string;
  practice_tip: string;
  target_snippet?: string | null;
  detected_snippet?: string | null;
  can_listen_reference?: boolean;
  can_listen_user?: boolean;
  audio_timestamp_ms?: number | null;
}

export interface PronunciationResult {
  overall_score: number;
  overall_confidence: AnalysisConfidenceLevel;
  score_interpretation: string;
  phoneme_score?: PronunciationScoreComponent | null;
  mora_timing_score?: PronunciationScoreComponent | null;
  pitch_score?: PronunciationScoreComponent | null;
  rhythm_score?: PronunciationScoreComponent | null;
  intonation_score?: PronunciationScoreComponent | null;
  phoneme_assessment?: PhonemeAssessment[] | null;
  mora_assessment?: MoraTimingAssessment | null;
  pitch_assessment?: PitchAssessment | null;
  rhythm_assessment?: RhythmAssessment | null;
  intonation_assessment?: IntonationAssessment | null;
  audio_quality?: AudioQualityReport | null;
  top_issues: PronunciationFeedbackItem[];
  strengths: string[];
  practice_recommendation?: string | null;
  engine_version: string;
  scoring_version: string;
  reference_type: ReferenceType;
  partial_reasons: string[];
}

export interface PronunciationAttemptResponse {
  id: string;
  user_id: string;
  session_id?: string | null;
  turn_id?: string | null;
  reference_text: string;
  expected_reading?: string | null;
  user_text?: string | null;
  target_type: TargetType;
  reference_type: ReferenceType;
  analysis_status: "pending" | "processing" | "completed" | "failed";
  overall_score?: number | null;
  overall_confidence?: string | null;
  score_interpretation?: string | null;
  engine_version: string;
  result?: PronunciationResult | null;
  top_issues: PronunciationFeedbackItem[];
  strengths: string[];
  practice_recommendation?: string | null;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PronunciationPracticeTargetDTO {
  id: string;
  target_text: string;
  target_reading: string;
  target_type: string;
  difficulty: string;
  weak_area_key: string;
  category: string;
  hint?: string | null;
}

export interface PronunciationHistoryItemDTO {
  id: string;
  reference_text: string;
  target_type: string;
  overall_score?: number | null;
  score_interpretation?: string | null;
  analysis_status: string;
  created_at: string;
}

export interface PronunciationSummaryStatsDTO {
  total_attempts: number;
  avg_overall_score: number;
  avg_mora_score: number;
  avg_pitch_score: number;
  avg_phoneme_score: number;
  top_weaknesses: string[];
  recent_trend: "improving" | "stable" | "worsening" | "new";
}
