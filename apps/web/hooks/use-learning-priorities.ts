"use client";

import { useCallback, useEffect, useState } from "react";
import { learningApi } from "@/services/learning-api";
import { CurriculumUnit, LearningGoal, LearningItem, LearningRecommendation } from "@/types/learning";

export function useLearningPriorities() {
  const [priorities, setPriorities] = useState<LearningRecommendation[]>([]);
  const [dueReviews, setDueReviews] = useState<LearningItem[]>([]);
  const [goals, setGoals] = useState<LearningGoal[]>([]);
  const [curriculum, setCurriculum] = useState<CurriculumUnit[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [priData, revData, goalsData, currData] = await Promise.all([
        learningApi.getPriorities(6),
        learningApi.getDueReviews(),
        learningApi.listGoals(),
        learningApi.getCurriculum(),
      ]);
      setPriorities(priData);
      setDueReviews(revData);
      setGoals(goalsData);
      setCurriculum(currData);
    } catch (err: any) {
      setError(err.message || "Failed to load learning priorities");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  return {
    priorities,
    dueReviews,
    goals,
    curriculum,
    loading,
    error,
    refresh: fetchAll,
  };
}
