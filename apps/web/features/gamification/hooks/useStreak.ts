"use client";

import { useEffect, useState, useCallback } from "react";
import { gameApi } from "../services/gameApi";
import { StreakOverviewDTO } from "../types/game";

export function useStreak() {
  const [streak, setStreak] = useState<StreakOverviewDTO | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStreak = useCallback(async () => {
    try {
      setLoading(true);
      const data = await gameApi.getStreak();
      setStreak(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to load streak.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStreak();
  }, [fetchStreak]);

  return {
    streak,
    loading,
    error,
    refetch: fetchStreak,
  };
}
