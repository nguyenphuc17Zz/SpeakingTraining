import { apiClient } from "@/services/api-client";
import {
  AudioTurnResponse,
  ConversationTurn,
  SessionSummary,
  VoiceSession,
} from "../types";

export interface CreateSessionPayload {
  persona_id: string;
  mode?: string;
  provider_preference?: string | null;
  model_preference?: string | null;
  stt_provider_preference?: string | null;
  stt_model_preference?: string | null;
  tts_provider_preference?: string | null;
  tts_voice_preference?: string | null;
}

export const conversationApi = {
  async startSession(payload: CreateSessionPayload): Promise<VoiceSession> {
    return apiClient.post<VoiceSession>("/conversations", payload);
  },

  async getSession(sessionId: string): Promise<VoiceSession> {
    return apiClient.get<VoiceSession>(`/conversations/${sessionId}`);
  },

  async sendAudioTurn(
    sessionId: string,
    audioBlob: Blob,
    clientTurnId?: string,
    browserTranscript?: string
  ): Promise<AudioTurnResponse> {
    const formData = new FormData();
    formData.append("audio_file", audioBlob, "audio.wav");
    if (clientTurnId) {
      formData.append("client_turn_id", clientTurnId);
    }
    if (browserTranscript) {
      formData.append("browser_transcript", browserTranscript);
    }
    return apiClient.postMultipart<AudioTurnResponse>(
      `/conversations/${sessionId}/audio-turn`,
      formData
    );
  },

  async sendTextTurn(
    sessionId: string,
    transcript: string,
    clientTurnId?: string
  ): Promise<AudioTurnResponse> {
    return apiClient.post<AudioTurnResponse>(
      `/conversations/${sessionId}/turns`,
      { transcript, client_turn_id: clientTurnId }
    );
  },

  async endSession(sessionId: string): Promise<VoiceSession> {
    return apiClient.post<VoiceSession>(`/conversations/${sessionId}/end`);
  },

  async getSessionSummary(sessionId: string): Promise<SessionSummary> {
    return apiClient.get<SessionSummary>(`/conversations/${sessionId}/summary`);
  },
};
