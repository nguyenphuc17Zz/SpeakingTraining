import {
  AchievementDTO,
  BossAttemptResultDTO,
  BossDTO,
  BossStartResponseDTO,
  GameProfileDTO,
  GameSettingsDTO,
  QuestDTO,
  RewardNotificationDTO,
  SkillTreeOverviewDTO,
  StreakOverviewDTO,
  UnlockableDTO,
  XPOverviewDTO,
  XPTransactionDTO,
} from "../types/game";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(errData.detail || errData.message || `API Error: ${res.status}`);
  }

  return res.json();
}

export const gameApi = {
  getProfile: (): Promise<GameProfileDTO> => fetchJson<GameProfileDTO>("/game/profile"),
  getXPOverview: (): Promise<XPOverviewDTO> => fetchJson<XPOverviewDTO>("/game/xp"),
  getXPHistory: (limit = 50, offset = 0, category?: string): Promise<XPTransactionDTO[]> => {
    const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
    if (category) params.append("category", category);
    return fetchJson<XPTransactionDTO[]>(`/game/xp/history?${params.toString()}`);
  },
  getQuests: (): Promise<QuestDTO[]> => fetchJson<QuestDTO[]>("/game/quests"),
  getAchievements: (): Promise<AchievementDTO[]> => fetchJson<AchievementDTO[]>("/game/achievements"),
  getSkillTree: (): Promise<SkillTreeOverviewDTO> => fetchJson<SkillTreeOverviewDTO>("/game/skills"),
  getUnlocks: (unlockType?: string): Promise<UnlockableDTO[]> => {
    const query = unlockType ? `?unlock_type=${unlockType}` : "";
    return fetchJson<UnlockableDTO[]>(`/game/unlocks${query}`);
  },
  equipTitle: (title: string): Promise<GameProfileDTO> =>
    fetchJson<GameProfileDTO>(`/game/unlocks/equip-title?title=${encodeURIComponent(title)}`, {
      method: "POST",
    }),
  getBosses: (): Promise<BossDTO[]> => fetchJson<BossDTO[]>("/game/bosses"),
  startBoss: (bossId: string): Promise<BossStartResponseDTO> =>
    fetchJson<BossStartResponseDTO>(`/game/bosses/${bossId}/start`, { method: "POST" }),
  submitBoss: (bossId: string, exerciseAttemptId: string): Promise<BossAttemptResultDTO> =>
    fetchJson<BossAttemptResultDTO>(
      `/game/bosses/${bossId}/submit?exercise_attempt_id=${encodeURIComponent(exerciseAttemptId)}`,
      { method: "POST" }
    ),
  getNotifications: (limit = 20): Promise<RewardNotificationDTO[]> =>
    fetchJson<RewardNotificationDTO[]>(`/game/notifications?limit=${limit}`),
  markNotificationRead: (notificationId: string): Promise<{ status: string; id: string }> =>
    fetchJson<{ status: string; id: string }>(`/game/notifications/${notificationId}/read`, {
      method: "POST",
    }),
  getStreak: (): Promise<StreakOverviewDTO> => fetchJson<StreakOverviewDTO>("/game/streak"),
  getSettings: (): Promise<GameSettingsDTO> => fetchJson<GameSettingsDTO>("/game/settings"),
  updateSettings: (settings: Partial<GameSettingsDTO>): Promise<GameSettingsDTO> =>
    fetchJson<GameSettingsDTO>("/game/settings", {
      method: "PUT",
      body: JSON.stringify(settings),
    }),
};
