"use client";

import { useEffect, useState, useCallback } from "react";
import { gameApi } from "../services/gameApi";
import { SkillTreeOverviewDTO } from "../types/game";

export function useSkillTree() {
  const [skillTree, setSkillTree] = useState<SkillTreeOverviewDTO | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSkillTree = useCallback(async () => {
    try {
      setLoading(true);
      const data = await gameApi.getSkillTree();
      setSkillTree(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to load skill tree.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSkillTree();
  }, [fetchSkillTree]);

  return {
    skillTree,
    loading,
    error,
    refetch: fetchSkillTree,
  };
}
