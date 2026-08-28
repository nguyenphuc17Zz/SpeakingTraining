export type VideoStatus =
  | "queued"
  | "fetching_metadata"
  | "resolving_transcript"
  | "transcribing"
  | "segmenting"
  | "analyzing"
  | "ready"
  | "partial"
  | "failed";

export type SpeakingDifficulty = "easy" | "normal" | "hard" | "very_hard";

export type CandidateCategory =
  | "BEST_FOR_BEGINNER"
  | "BEST_FOR_PRONUNCIATION"
  | "BEST_FOR_NATURALNESS"
  | "BEST_FOR_SPEED"
  | "BEST_FOR_WORKPLACE"
  | "BEST_FOR_CHALLENGE";

export type ShadowingMode =
  | "listen"
  | "shadow"
  | "listen_shadow"
  | "repeat"
  | "ab_loop";

export interface ExtractedVocabulary {
  word: string;
  reading: string;
  meaning: string;
  part_of_speech?: string;
  difficulty?: string;
  frequency?: string;
  context_sentence: string;
  source_segment_id?: string;
  source_text_span?: string;
  learning_value: number;
}

export interface ExtractedGrammar {
  pattern: string;
  level: string;
  meaning: string;
  context: string;
  example?: string;
  source_segment_id?: string;
  source_text_span?: string;
  learning_value: number;
}

export interface NaturalExpression {
  expression: string;
  reading?: string;
  meaning: string;
  category: string;
  context_sentence: string;
  source_segment_id?: string;
  source_text_span?: string;
  learning_value: number;
}

export interface DifficultyReport {
  lexical_score: number;
  grammar_score: number;
  speed_mora_per_sec: number;
  pronunciation_complexity: number;
  sentence_density: number;
  context_naturalness: number;
  overall_difficulty: SpeakingDifficulty;
  reasons: string[];
}

export interface RubyChunk {
  text: string;
  reading?: string | null;
}

export interface TranscriptSegment {
  id: string;
  video_id: string;
  start_time: number;
  end_time: number;
  duration: number;
  text: string;
  normalized_text: string;
  reading?: string;
  ruby?: RubyChunk[];
  language: string;
  confidence: number;
  speaker_id: string;
  sequence: number;
  difficulty?: DifficultyReport;
  vocabulary: ExtractedVocabulary[];
  grammar: ExtractedGrammar[];
  expressions: NaturalExpression[];
  candidate_categories: CandidateCategory[];
  recommendation_score?: number;
  recommendation_reason?: string;
}

export interface ShadowingCandidate {
  segment_id: string;
  video_id: string;
  start_time: number;
  end_time: number;
  text: string;
  reading?: string;
  ruby?: RubyChunk[];
  speaker_id: string;
  score: number;
  categories: CandidateCategory[];
  reason: string;
  target_skill: string;
  difficulty: SpeakingDifficulty;
  matched_weakness?: string;
  matched_goal?: string;
}

export interface ShadowingVideo {
  id: string;
  video_id: string;
  url: string;
  canonical_url: string;
  title: string;
  channel_name: string;
  channel_id?: string;
  thumbnail_url?: string;
  duration_seconds: number;
  language: string;
  import_status: VideoStatus;
  overall_difficulty: SpeakingDifficulty;
  summary_json?: {
    topic?: string;
    speaking_style?: string;
    difficulty_summary?: Record<string, any>;
    recommended_count?: number;
    total_segments?: number;
    transcript_source?: string;
    quality?: string;
  };
  created_at: string;
  updated_at: string;
}

export interface ShadowingVideoDetail extends ShadowingVideo {
  segments_count: number;
  recommended_count: number;
  segments: TranscriptSegment[];
  recommended_segments: ShadowingCandidate[];
  progress?: ShadowingVideoProgress;
}

export interface ShadowingVideoProgress {
  watch_progress: number;
  shadow_progress: number;
  mastery_progress: number;
  segments_completed: number;
  total_practice_time_seconds: number;
  best_score?: number;
  last_position_seconds: number;
  last_opened_at?: string;
}

export interface ShadowingSegmentProgress {
  id: string;
  segment_id: string;
  exercise_id?: string;
  listen_count: number;
  shadow_attempts: number;
  best_score?: number;
  mastery: string;
  last_practiced_at?: string;
}

export interface ShadowingLesson {
  id: string;
  video_id: string;
  title: string;
  goal: string;
  mode: string;
  estimated_minutes: number;
  difficulty: SpeakingDifficulty;
  segments: TranscriptSegment[];
}

export interface VideoImportResult {
  video_id: string;
  canonical_video_id: string;
  job_id: string;
  status: VideoStatus;
  message: string;
  is_existing: boolean;
}

export interface ShadowingJobStatus {
  job_id: string;
  video_id: string;
  stage: string;
  status: string;
  attempts: number;
  stage_statuses?: Record<string, string>;
  error_type?: string;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
}

export interface PracticeAttemptFeedback {
  exercise_id: string;
  attempt_id: string;
  segment_id: string;
  target_text?: string;
  user_transcript?: string;
  user_audio_url?: string;
  score: number;
  timing_score: number;
  pronunciation_score: number;
  rhythm_score: number;
  accuracy_score: number;
  feedback: string;
  strengths: string[];
  top_issues: Array<{
    issue_key: string;
    category: string;
    severity: string;
    title: string;
    explanation: string;
    practice_tip: string;
    target_snippet?: string;
    detected_snippet?: string;
  }>;
  mastery: string;
  mastery_delta: number;
  review_scheduled_at?: string;
}

export interface Bookmark {
  id: string;
  user_id: string;
  video_id: string;
  segment_id: string;
  note?: string;
  created_at: string;
}

export interface SegmentTranslation {
  segment_id: string;
  source_text: string;
  target_language: string;
  translated_text: string;
  explanation?: string;
}
