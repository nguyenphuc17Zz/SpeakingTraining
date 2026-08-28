"use client";

import { useEffect, useState, useCallback } from "react";
import { gameApi } from "../services/gameApi";
import { AchievementDTO } from "../types/game";

export function useAchievements() {
  const [achievements, setAchievements] = useState<AchievementDTO[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAchievements = useCallback(async () => {
    try {
      setLoading(true);
      const data = await gameApi.getAchievements();
      setAchievements(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to load achievements.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAchievements();
  }, [fetchAchievements]);

  const unlockedCount = achievements.filter((a) => a.is_unlocked).length;
  const totalXP = achievements
    .filter((a) => a.is_unlocked)
    .reduce((sum, a) => sum + a.xp_reward, 0);

  return {
    achievements,
    unlockedCount,
    totalCount: achievements.length,
    totalAchievementXP: totalXP,
    loading,
    error,
    refetch: fetchAchievements,
  };
}
