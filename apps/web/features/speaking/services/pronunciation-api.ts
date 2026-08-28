import { apiClient } from "@/services/api-client";
import {
  PronunciationAttemptResponse,
  PronunciationHistoryItemDTO,
  PronunciationPracticeTargetDTO,
  PronunciationSummaryStatsDTO,
  ReferenceType,
  TargetType,
} from "../types/pronunciation";

export interface AnalyzePronunciationParams {
  audioBlob: Blob;
  targetText: string;
  expectedReading?: string | null;
  targetType?: TargetType;
  referenceType?: ReferenceType;
  voicevoxSpeakerId?: number;
  sessionId?: string | null;
  turnId?: string | null;
}

export const pronunciationApi = {
  /**
   * Converts blob to base64 and executes end-to-end pronunciation analysis
   */
  async analyze(params: AnalyzePronunciationParams): Promise<PronunciationAttemptResponse> {
    const base64Audio = await this._blobToBase64(params.audioBlob);
    const payload = {
      audio_base64: base64Audio,
      target_text: params.targetText,
      expected_reading: params.expectedReading || null,
      target_type: params.targetType || "sentence",
      reference_type: params.referenceType || "synthetic",
      voicevox_speaker_id: params.voicevoxSpeakerId || 1,
      session_id: params.sessionId || null,
      turn_id: params.turnId || null,
    };
    return apiClient.post<PronunciationAttemptResponse>("/pronunciation/analyze", payload, {
      timeoutMs: 120000,
    });
  },

  async getAttempt(attemptId: string): Promise<PronunciationAttemptResponse> {
    return apiClient.get<PronunciationAttemptResponse>(`/pronunciation/attempts/${attemptId}`);
  },

  async getHistory(limit: number = 20): Promise<PronunciationHistoryItemDTO[]> {
    return apiClient.get<PronunciationHistoryItemDTO[]>(`/pronunciation/history?limit=${limit}`);
  },

  async getStats(): Promise<PronunciationSummaryStatsDTO> {
    return apiClient.get<PronunciationSummaryStatsDTO>("/pronunciation/stats");
  },

  async getTargets(limit: number = 6): Promise<PronunciationPracticeTargetDTO[]> {
    return apiClient.get<PronunciationPracticeTargetDTO[]>(`/pronunciation/targets?limit=${limit}`);
  },

  /**
   * Helper to convert Blob into base64 string
   */
  _blobToBase64(blob: Blob): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        const dataUrl = reader.result as string;
        // Strip data URL prefix (e.g. data:audio/wav;base64,)
        const base64 = dataUrl.split(",")[1] || dataUrl;
        resolve(base64);
      };
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  },
};
