"use client";

import { useEffect, useState, useCallback } from "react";
import { analyticsApi } from "../services/analyticsApi";
import { WeeklyReviewDTO } from "../types/analytics";

export function useWeeklyReview(weekStart?: string) {
  const [review, setReview] = useState<WeeklyReviewDTO | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchReview = useCallback(async () => {
    try {
      setLoading(true);
      const data = await analyticsApi.getWeeklyReview(weekStart);
      setReview(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to load weekly review.");
    } finally {
      setLoading(false);
    }
  }, [weekStart]);

  useEffect(() => {
    fetchReview();
  }, [fetchReview]);

  return {
    review,
    loading,
    error,
    refetch: fetchReview,
  };
}
