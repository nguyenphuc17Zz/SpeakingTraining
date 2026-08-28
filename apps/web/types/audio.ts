export type PlaybackState =
  | "idle"
  | "loading"
  | "ready"
  | "playing"
  | "paused"
  | "completed"
  | "stopped"
  | "error";

export type RecordingState =
  | "idle"
  | "requesting_permission"
  | "permission_denied"
  | "ready"
  | "recording"
  | "stopping"
  | "processing"
  | "completed"
  | "error";

export type TTSState =
  | "idle"
  | "generating"
  | "ready"
  | "playing"
  | "completed"
  | "error";

export type VoiceCapability =
  | "speed_control"
  | "pitch_control"
  | "style_control"
  | "streaming"
  | "volume_control";

export type VoiceStyle =
  | "normal"
  | "casual"
  | "polite"
  | "teacher"
  | "energetic"
  | "calm"
  | "professional"
  | "dramatic";

export type AudioQualityStatus =
  | "good"
  | "acceptable"
  | "noisy"
  | "clipping"
  | "too_quiet"
  | "silent";

export interface VoiceProfile {
  id: string;
  user_id?: string;
  name: string;
  provider: string;
  voice_id: string;
  description?: string | null;
  language?: string;
  gender?: string | null;
  default_speed?: number;
  default_pitch?: number;
  style?: string | null;
  capabilities?: VoiceCapability[];
  settings_json?: {
    speed?: number;
    pitch?: number;
    style?: string;
    volume?: number;
  };
  is_default?: boolean;
  is_favorite?: boolean;
  is_system?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface PlaybackPreset {
  id: string;
  name: string;
  description?: string | null;
  speed: number;
  volume: number;
  loop: boolean;
  loop_count: number;
  pause_after_ms: number;
  auto_play: boolean;
  record_after: boolean;
  is_system: boolean;
  created_at?: string;
}

export interface AudioQualityReport {
  volume_rms: number;
  volume_db: number;
  noise_level_db: number;
  snr_db?: number | null;
  has_clipping: boolean;
  clipping_samples_count: number;
  duration_ms: number;
  quality: AudioQualityStatus;
  recommendation: string;
  warnings: string[];
}

export interface ProviderHealth {
  provider_id: string;
  name: string;
  is_available: boolean;
  status_message: string;
  checked_at: string;
  latency_ms?: number | null;
  available_voices_count: number;
}

export interface AudioSettings {
  default_tts_provider: string;
  default_stt_provider: string;
  default_voice_profile_id?: string | null;
  default_tts_speed: number;
  default_tts_pitch: number;
  tts_fallback_enabled: boolean;
  tts_fallback_provider: string;
  tts_fallback_voice_id: string;
  auto_play_ai_response: boolean;
  auto_play_references: boolean;
  voicevox_engine_url: string;
  voicevox_engine_path: string;
}

export interface VoicevoxEngine {
  url: string;
  path: string;
  path_exists: boolean;
  run_exe_path: string;
  run_exe_exists: boolean;
  is_available: boolean;
  status_message: string;
  latency_ms?: number | null;
  available_voices_count: number;
}

export type AudioSessionType = "conversation" | "pronunciation" | "shadowing" | "exercise";

export interface AudioQueueItem {
  id: string;
  type: "tts" | "reference" | "user_recording" | "youtube_segment";
  source: string; // Base64 audio or URL or segment ID
  text?: string;
  priority?: number;
  autoplay?: boolean;
  repeat_count?: number;
  metadata?: Record<string, any>;
}

export interface AudioDeviceInfo {
  deviceId: string;
  label: string;
  kind: MediaDeviceKind;
}

export interface STTModelInfo {
  id: string;
  name: string;
  params: string;
  size_mb: number;
  size_display: string;
  ram_required: string;
  stars: number;
  speed_rating: string;
  accuracy_rating: string;
  recommended_for: string;
  description_vi: string;
  is_recommended: boolean;
  is_downloaded: boolean;
  is_loaded: boolean;
  is_active: boolean;
  device?: string;
  compute_type?: string;
}

