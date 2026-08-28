"use client";

import { useEffect, useState, useCallback } from "react";
import { analyticsApi } from "../services/analyticsApi";
import { AnalyticsDashboardDTO } from "../types/analytics";

export function useAnalyticsDashboard(period = "30d") {
  const [dashboard, setDashboard] = useState<AnalyticsDashboardDTO | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboard = useCallback(async (force = false) => {
    try {
      setLoading(true);
      const data = await analyticsApi.getDashboard(period, force);
      setDashboard(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to load analytics dashboard.");
    } finally {
      setLoading(false);
    }
  }, [period]);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  return {
    dashboard,
    loading,
    error,
    refetch: () => fetchDashboard(true),
  };
}
