"use client";

import { useEffect, useState, useCallback } from "react";
import { gameApi } from "../services/gameApi";
import { QuestDTO } from "../types/game";

export function useQuests() {
  const [quests, setQuests] = useState<QuestDTO[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchQuests = useCallback(async () => {
    try {
      setLoading(true);
      const data = await gameApi.getQuests();
      setQuests(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to load quests.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchQuests();
  }, [fetchQuests]);

  const dailyQuests = quests.filter((q) => q.frequency === "daily");
  const weeklyQuests = quests.filter((q) => q.frequency === "weekly");
  const completedTodayCount = dailyQuests.filter((q) => q.is_completed).length;

  return {
    quests,
    dailyQuests,
    weeklyQuests,
    completedTodayCount,
    loading,
    error,
    refetch: fetchQuests,
  };
}
