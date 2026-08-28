"use client";

import { useState, useCallback, useEffect } from "react";
import { AIUsageSummaryRead } from "@/types/ai";
import { aiApi } from "@/services/ai-api";

export function useAIUsage(params?: { provider?: string; task?: string }) {
  const [usageSummary, setUsageSummary] = useState<AIUsageSummaryRead | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchUsage = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await aiApi.getUsage(params);
      setUsageSummary(data);
    } catch (err: any) {
      setError(err.message || "Failed to load AI usage metrics");
    } finally {
      setLoading(false);
    }
  }, [params?.provider, params?.task]);

  useEffect(() => {
    fetchUsage();
  }, [fetchUsage]);

  return {
    usageSummary,
    loading,
    error,
    refetch: fetchUsage,
  };
}
