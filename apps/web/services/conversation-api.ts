import { apiClient } from "./api-client";

export interface RecentSessionItem {
  id: string;
  persona_id: string;
  persona_name: string;
  persona_avatar_url?: string | null;
  mode: string;
  status: string;
  started_at: string;
  ended_at?: string | null;
  duration_seconds: number;
  turns_count: number;
  score?: number | null;
  topic?: string | null;
}

export const conversationApi = {
  getRecentSessions: (limit = 5): Promise<RecentSessionItem[]> =>
    apiClient.get<RecentSessionItem[]>(`/conversations/recent?limit=${limit}`),
};
