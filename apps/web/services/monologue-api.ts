import { apiClient } from "@/services/api-client";
import { Exercise, ExerciseResult } from "@/types/learning";

export interface SpeechExercise extends Exercise {
  extra_metadata?: any;
}

export interface SpeechSubmitPayload {
  user_transcript?: string;
  audio_base64?: string;
  speech_metrics?: {
    started_at?: string;
    ended_at?: string;
    target_duration_ms?: number;
    speech_duration_ms?: number;
    audio_confidence?: number;
  };
  used_hint?: boolean;
  plan_item_id?: string;
}

export const monologueApi = {
  async generate(params: {
    duration_sec?: number;
    prep_sec?: number;
    difficulty?: number;
    genre?: string;
    support_level?: number;
    topic_domain?: string;
    seed?: string;
  } = {}): Promise<Exercise> {
    return apiClient.post<Exercise>("/monologue/exercises/generate", params);
  },

  async generateGet(params: Record<string, any> = {}): Promise<Exercise> {
    const q = new URLSearchParams();
    for (const [k,v] of Object.entries(params)) if (v!=null) q.append(k, String(v));
    const qs = q.toString();
    return apiClient.get<Exercise>(`/monologue/exercises/generate${qs?"?"+qs:""}`);
  },

  async getExercise(id: string): Promise<Exercise> {
    return apiClient.get<Exercise>(`/monologue/exercises/${id}`);
  },

  async submit(id: string, payload: SpeechSubmitPayload): Promise<any> {
    return apiClient.post<any>(`/monologue/exercises/${id}/submit`, payload);
  },

  async submitMultipart(id: string, blob: Blob, payload: Omit<SpeechSubmitPayload, "audio_base64">): Promise<any> {
    const form = new FormData();
    form.append("audio", blob, "speech.webm");
    if (payload.user_transcript) form.append("user_transcript", payload.user_transcript);
    form.append("used_hint", String(!!payload.used_hint));
    if (payload.plan_item_id) form.append("plan_item_id", payload.plan_item_id);
    if (payload.speech_metrics) form.append("speech_metrics", JSON.stringify(payload.speech_metrics));
    return apiClient.postMultipart<any>(`/monologue/exercises/${id}/submit_multipart`, form);
  },

  async getProgress(period: string = "30d"): Promise<any> {
    return apiClient.get<any>(`/monologue/progress?period=${period}`);
  },

  async listGenres(): Promise<any> {
    return apiClient.get<any>("/monologue/genres");
  },

  async listDomains(): Promise<any> {
    return apiClient.get<any>("/monologue/domains");
  },

  // also via learning endpoint (fallback)
  async submitViaLearning(id: string, payload: any): Promise<ExerciseResult> {
    return apiClient.post<ExerciseResult>(`/learning/exercises/${id}/submit`, payload);
  },
};
