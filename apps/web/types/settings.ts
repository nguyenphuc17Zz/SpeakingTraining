export interface UserSettings {
  id: string;
  user_id: string;
  theme: string;
  language: string;
  timezone: string;
  default_ai_provider: string;
  default_ai_model: string;
  default_tts_provider: string;
  default_stt_provider: string;
  created_at: string;
  updated_at: string;
}

export interface UserSettingsUpdate {
  theme?: string;
  language?: string;
  timezone?: string;
  default_ai_provider?: string;
  default_ai_model?: string;
  default_tts_provider?: string;
  default_stt_provider?: string;
}
