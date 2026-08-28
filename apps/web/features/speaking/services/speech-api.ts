import { apiClient } from "@/services/api-client";
import { STTModelOption, TTSVoiceOption } from "../types";

export const speechApi = {
  async getVoices(provider = "voicevox"): Promise<TTSVoiceOption[]> {
    return apiClient.get<TTSVoiceOption[]>(`/speech/voices?provider=${provider}`);
  },

  async getSTTModels(): Promise<STTModelOption[]> {
    return apiClient.get<STTModelOption[]>("/speech/stt-models");
  },

  async transcribe(
    audioBlob: Blob,
    model = "base",
    language = "ja"
  ): Promise<{ text: string; confidence?: number; duration_ms?: number }> {
    const formData = new FormData();
    formData.append("audio_file", audioBlob, "audio.wav");
    formData.append("model", model);
    formData.append("language", language);
    return apiClient.postMultipart<{ text: string; confidence?: number; duration_ms?: number }>(
      "/speech/transcribe",
      formData,
      { timeoutMs: 120000 }
    );
  },

  async synthesize(
    text: string,
    voiceId = "1",
    speed = 1.0,
    pitch = 0.0
  ): Promise<{ audio_base64: string; format: string; duration_ms?: number }> {
    return apiClient.post<{ audio_base64: string; format: string; duration_ms?: number }>(
      "/speech/synthesize",
      { text, voice_id: voiceId, speed, pitch, return_base64: true },
      { timeoutMs: 60000 }
    );
  },
};
