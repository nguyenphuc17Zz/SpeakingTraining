import { apiClient } from "@/services/api-client";
import {
  AudioQualityReport,
  AudioSettings,
  PlaybackPreset,
  ProviderHealth,
  VoiceProfile,
} from "@/types/audio";

export const audioApi = {
  /**
   * Lists available TTS voices from the specified provider with capability tags.
   */
  async getVoices(provider = "voicevox"): Promise<VoiceProfile[]> {
    return apiClient.get<VoiceProfile[]>(`/audio/voices?provider=${provider}`);
  },

  /**
   * Retrieves real-time health and latency of registered speech synthesis engines.
   */
  async getProvidersHealth(): Promise<ProviderHealth[]> {
    return apiClient.get<ProviderHealth[]>("/audio/providers/health");
  },

  /**
   * Generates a short preview audio sample for a selected voice.
   */
  async previewVoice(
    text: string,
    voiceId: string,
    provider = "voicevox",
    speed = 1.0,
    pitch = 0.0,
    style?: string
  ): Promise<{ audio_base64: string; format: string; duration_ms?: number; is_cached: boolean }> {
    return apiClient.post("/audio/tts/preview", {
      text,
      voice_id: voiceId,
      provider,
      speed,
      pitch,
      style: style || null,
    });
  },

  /**
   * Lists user-saved custom voice profiles.
   */
  async listVoiceProfiles(): Promise<VoiceProfile[]> {
    return apiClient.get<VoiceProfile[]>("/audio/voice-profiles");
  },

  /**
   * Saves a new custom voice profile for the learner.
   */
  async createVoiceProfile(data: {
    name: string;
    provider: string;
    voice_id: string;
    description?: string;
    settings_json?: Record<string, any>;
    is_default?: boolean;
    is_favorite?: boolean;
  }): Promise<VoiceProfile> {
    return apiClient.post<VoiceProfile>("/audio/voice-profiles", data);
  },

  /**
   * Updates an existing voice profile.
   */
  async updateVoiceProfile(
    id: string,
    data: Partial<{
      name: string;
      description?: string;
      settings_json?: Record<string, any>;
      is_default?: boolean;
      is_favorite?: boolean;
    }>
  ): Promise<VoiceProfile> {
    return apiClient.patch<VoiceProfile>(`/audio/voice-profiles/${id}`, data);
  },

  /**
   * Deletes a voice profile.
   */
  async deleteVoiceProfile(id: string): Promise<{ success: boolean }> {
    return apiClient.delete<{ success: boolean }>(`/audio/voice-profiles/${id}`);
  },

  /**
   * Lists system and custom playback presets.
   */
  async listPresets(): Promise<PlaybackPreset[]> {
    return apiClient.get<PlaybackPreset[]>("/audio/presets");
  },

  /**
   * Creates a custom playback preset.
   */
  async createPreset(data: {
    name: string;
    description?: string;
    speed: number;
    volume: number;
    loop_count: number;
    pause_after_ms: number;
    auto_play?: boolean;
    record_after?: boolean;
  }): Promise<PlaybackPreset> {
    return apiClient.post<PlaybackPreset>("/audio/presets", data);
  },

  /**
   * Analyzes an audio recording for volume levels, noise floors, and clipping.
   */
  async checkAudioQuality(audioBase64: string): Promise<AudioQualityReport> {
    return apiClient.post<AudioQualityReport>("/audio/quality-check", {
      audio_base64: audioBase64,
    });
  },

  /**
   * Fetches user audio preferences.
   */
  async getSettings(): Promise<AudioSettings> {
    return apiClient.get<AudioSettings>("/audio/settings");
  },

  /**
   * Updates user audio preferences.
   */
  async updateSettings(data: Partial<AudioSettings>): Promise<AudioSettings> {
    return apiClient.patch<AudioSettings>("/audio/settings", data);
  },

  /**
   * Fetches comprehensive system audio diagnostics report.
   */
  async getDiagnostics(): Promise<Record<string, any>> {
    return apiClient.get<Record<string, any>>("/audio/diagnostics");
  },

  async getEngine(): Promise<import("@/types/audio").VoicevoxEngine> {
    return apiClient.get<import("@/types/audio").VoicevoxEngine>("/audio/engine");
  },
  async updateEngine(data: { path?: string; url?: string }): Promise<import("@/types/audio").VoicevoxEngine> {
    return apiClient.put<import("@/types/audio").VoicevoxEngine>("/audio/engine", data);
  },
  async startEngine(): Promise<import("@/types/audio").VoicevoxEngine> {
    return apiClient.post<import("@/types/audio").VoicevoxEngine>("/audio/engine/start", {});
  },
  async listSTTModels(activeModel = "base"): Promise<import("@/types/audio").STTModelInfo[]> {
    return apiClient.get<import("@/types/audio").STTModelInfo[]>(`/speech/stt-models?active_model=${activeModel}`);
  },
  async downloadSTTModel(modelId: string): Promise<{ success: boolean; message: string; models: import("@/types/audio").STTModelInfo[] }> {
    return apiClient.post("/speech/stt-models/download", { model_id: modelId }, { timeoutMs: 300000 });
  },
  async selectSTTModel(modelId: string): Promise<{ success: boolean; active_model: string; message: string; models: import("@/types/audio").STTModelInfo[] }> {
    return apiClient.post("/speech/stt-models/select", { model_id: modelId });
  },
};
