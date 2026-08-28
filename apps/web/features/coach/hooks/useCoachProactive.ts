"use client";
import { useEffect, useState, useCallback } from "react";
import { coachCoreApi } from "../services/coachCoreApi";

export function useCoachProactive(pollMs = 60000) {
  const [insights, setInsights] = useState<any[]>([]);
  const [dismissed, setDismissed] = useState<Set<string>>(new Set());

  const fetch = useCallback(async () => {
    try {
      const data = await coachCoreApi.getProactive();
      setInsights(data);
    } catch { /* ignore */ }
  }, []);

  useEffect(() => {
    fetch();
    const id = setInterval(fetch, pollMs);
    return () => clearInterval(id);
  }, [fetch, pollMs]);

  const dismiss = (id: string) => setDismissed((s) => { const n = new Set<string>(Array.from(s)); n.add(id); return n; });

  const visible = insights.filter((i) => !dismissed.has(i.insight_type + (i.evidence?.candidate || "")));

  return { insights: visible, dismiss, refresh: fetch };
}
