import { apiClient } from "@/services/api-client";
import {
  LearnerMemory,
  LearnerMemoryDetail,
  LearnerProfile,
  LearningPriority,
  MemoryEvidence,
  MemoryFeedback,
  MemoryFeedbackCreate,
} from "@/types/profile";

export const profileApi = {
  async getProfile(): Promise<LearnerProfile> {
    return apiClient.get<LearnerProfile>("/learner/profile");
  },

  async recalculateProfile(): Promise<LearnerProfile> {
    return apiClient.post<LearnerProfile>("/learner/profile/recalculate");
  },

  async listMemories(params?: {
    type?: string;
    status?: string;
    trend?: string;
    min_priority?: number;
    limit?: number;
  }): Promise<LearnerMemory[]> {
    const query = new URLSearchParams();
    if (params?.type) query.append("type", params.type);
    if (params?.status) query.append("status", params.status);
    if (params?.trend) query.append("trend", params.trend);
    if (params?.min_priority !== undefined) query.append("min_priority", params.min_priority.toString());
    if (params?.limit) query.append("limit", params.limit.toString());

    const queryString = query.toString();
    const path = `/learner/memories${queryString ? `?${queryString}` : ""}`;
    return apiClient.get<LearnerMemory[]>(path);
  },

  async getMemoryDetail(memoryId: string): Promise<LearnerMemoryDetail> {
    return apiClient.get<LearnerMemoryDetail>(`/learner/memories/${memoryId}`);
  },

  async getMemoryEvidence(memoryId: string): Promise<MemoryEvidence[]> {
    return apiClient.get<MemoryEvidence[]>(`/learner/memories/${memoryId}/evidence`);
  },

  async getTopWeaknesses(limit = 5): Promise<LearnerMemory[]> {
    return apiClient.get<LearnerMemory[]>(`/learner/weaknesses?limit=${limit}`);
  },

  async getTopStrengths(limit = 5): Promise<LearnerMemory[]> {
    return apiClient.get<LearnerMemory[]>(`/learner/strengths?limit=${limit}`);
  },

  async getLearningPriorities(limit = 5): Promise<LearningPriority[]> {
    return apiClient.get<LearningPriority[]>(`/learner/priorities?limit=${limit}`);
  },

  async submitFeedback(memoryId: string, payload: MemoryFeedbackCreate): Promise<MemoryFeedback> {
    return apiClient.post<MemoryFeedback>(`/learner/memories/${memoryId}/feedback`, payload);
  },
};
