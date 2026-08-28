import { apiClient } from "@/services/api-client";
import {
  CurriculumRoadmap,
  CurriculumUnit,
  DailyPlan,
  Exercise,
  ExerciseResult,
  ExerciseStartResponse,
  LearningGoal,
  LearningItem,
  LearningRecommendation,
} from "@/types/learning";

export const learningApi = {
  async getTodayPlan(timeBudget: number = 30): Promise<DailyPlan> {
    return apiClient.get<DailyPlan>(`/learning/today?time_budget=${timeBudget}`);
  },

  async regenerateTodayPlan(timeBudget: number = 30): Promise<DailyPlan> {
    return apiClient.post<DailyPlan>("/learning/today/regenerate", {
      time_budget_minutes: timeBudget,
    });
  },

  async getPriorities(limit: number = 5): Promise<LearningRecommendation[]> {
    return apiClient.get<LearningRecommendation[]>(`/learning/priorities?limit=${limit}`);
  },

  async listItems(params?: {
    item_type?: string;
    lifecycle?: string;
    limit?: number;
  }): Promise<LearningItem[]> {
    const query = new URLSearchParams();
    if (params?.item_type) query.append("item_type", params.item_type);
    if (params?.lifecycle) query.append("lifecycle", params.lifecycle);
    if (params?.limit) query.append("limit", params.limit.toString());

    const queryString = query.toString();
    return apiClient.get<LearningItem[]>(`/learning/items${queryString ? `?${queryString}` : ""}`);
  },

  async getItem(id: string): Promise<LearningItem> {
    return apiClient.get<LearningItem>(`/learning/items/${id}`);
  },

  async startItemPractice(id: string): Promise<Exercise> {
    return apiClient.post<Exercise>(`/learning/items/${id}/practice`);
  },

  async getDueReviews(): Promise<LearningItem[]> {
    return apiClient.get<LearningItem[]>("/learning/reviews");
  },

  async listGoals(): Promise<LearningGoal[]> {
    return apiClient.get<LearningGoal[]>("/learning/goals");
  },

  async createGoal(payload: {
    title: string;
    goal_type?: string;
    description?: string;
    priority?: number;
  }): Promise<LearningGoal> {
    return apiClient.post<LearningGoal>("/learning/goals", payload);
  },

  async updateGoal(
    id: string,
    payload: {
      title?: string;
      description?: string;
      status?: string;
      priority?: number;
    }
  ): Promise<LearningGoal> {
    return apiClient.patch<LearningGoal>(`/learning/goals/${id}`, payload);
  },

  async getExercise(id: string): Promise<Exercise> {
    return apiClient.get<Exercise>(`/learning/exercises/${id}`);
  },

  async startExercise(
    id: string,
    payload: { session_id?: string; pronunciation_attempt_id?: string } = {}
  ): Promise<ExerciseStartResponse> {
    return apiClient.post<ExerciseStartResponse>(`/learning/exercises/${id}/start`, payload);
  },

  async submitExercise(
    id: string,
    payload: {
      user_transcript: string;
      turn_analysis_score?: number;
      pronunciation_score?: number;
      response_speed_ms?: number;
      used_hint?: boolean;
      plan_item_id?: string;
    }
  ): Promise<ExerciseResult> {
    return apiClient.post<ExerciseResult>(`/learning/exercises/${id}/submit`, payload);
  },

  async getCurriculum(): Promise<CurriculumUnit[]> {
    return apiClient.get<CurriculumUnit[]>("/learning/curriculum");
  },

  // Dynamic AI Milestone Roadmap
  async getRoadmap(): Promise<CurriculumRoadmap> {
    return apiClient.get<CurriculumRoadmap>("/learning/roadmap");
  },

  async generateRoadmap(payload: {
    level: string;
    target_goal: string;
    daily_minutes: number;
    custom_wish?: string;
  }): Promise<CurriculumRoadmap> {
    return apiClient.post<CurriculumRoadmap>("/learning/roadmap/generate", payload);
  },

  async toggleRoadmapNode(
    nodeId: string,
    payload: { is_completed?: boolean; score?: number } = {}
  ): Promise<CurriculumRoadmap> {
    return apiClient.post<CurriculumRoadmap>(`/learning/roadmap/nodes/${nodeId}/toggle`, payload);
  },

  async triggerRecalculate(): Promise<{ status: string; message: string }> {
    return apiClient.post<{ status: string; message: string }>("/learning/recalculate");
  },
};
