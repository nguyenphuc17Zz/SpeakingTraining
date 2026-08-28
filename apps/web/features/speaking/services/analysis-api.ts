import { apiClient } from "@/services/api-client";
import {
  AnalysisFeedbackPayload,
  ConversationAnalysisSummary,
  TurnAnalysis,
} from "../types";

export const analysisApi = {
  async getSessionAnalysisSummary(
    sessionId: string
  ): Promise<ConversationAnalysisSummary> {
    return apiClient.get<ConversationAnalysisSummary>(
      `/conversations/${sessionId}/analysis`
    );
  },

  async getTurnAnalysis(
    sessionId: string,
    turnId: string
  ): Promise<TurnAnalysis> {
    return apiClient.get<TurnAnalysis>(
      `/conversations/${sessionId}/turns/${turnId}/analysis`
    );
  },

  async triggerSessionAnalysis(sessionId: string): Promise<any> {
    return apiClient.post(`/conversations/${sessionId}/analysis`);
  },

  async triggerTurnAnalysis(
    sessionId: string,
    turnId: string
  ): Promise<any> {
    return apiClient.post(`/conversations/${sessionId}/turns/${turnId}/analysis`);
  },

  async submitFeedback(payload: AnalysisFeedbackPayload): Promise<any> {
    return apiClient.post("/analyses/feedback", payload);
  },

  async getJobStatus(jobId: string): Promise<any> {
    return apiClient.get(`/analyses/jobs/${jobId}`);
  },
};
