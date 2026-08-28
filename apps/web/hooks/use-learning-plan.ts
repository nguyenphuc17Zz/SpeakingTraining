"use client";

import { useCallback, useEffect, useState } from "react";
import { learningApi } from "@/services/learning-api";
import { DailyPlan } from "@/types/learning";

export function useLearningPlan(initialBudget: number = 30) {
  const [plan, setPlan] = useState<DailyPlan | null>(null);
  const [timeBudget, setTimeBudget] = useState<number>(initialBudget);
  const [loading, setLoading] = useState<boolean>(true);
  const [regenerating, setRegenerating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPlan = useCallback(
    async (budget: number = timeBudget) => {
      try {
        setLoading(true);
        setError(null);
        const data = await learningApi.getTodayPlan(budget);
        setPlan(data);
      } catch (err: any) {
        setError(err.message || "Failed to load today's learning plan");
      } finally {
        setLoading(false);
      }
    },
    [timeBudget]
  );

  const regeneratePlan = useCallback(async (newBudget: number = timeBudget) => {
    try {
      setRegenerating(true);
      setError(null);
      const data = await learningApi.regenerateTodayPlan(newBudget);
      setPlan(data);
      setTimeBudget(newBudget);
    } catch (err: any) {
      setError(err.message || "Failed to regenerate learning plan");
    } finally {
      setRegenerating(false);
    }
  }, [timeBudget]);

  useEffect(() => {
    fetchPlan();
  }, [fetchPlan]);

  return {
    plan,
    timeBudget,
    setTimeBudget,
    loading,
    regenerating,
    error,
    refreshPlan: fetchPlan,
    regeneratePlan,
  };
}
