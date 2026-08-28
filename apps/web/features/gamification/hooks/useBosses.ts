"use client";

import { useEffect, useState, useCallback } from "react";
import { gameApi } from "../services/gameApi";
import { BossDTO, BossStartResponseDTO, BossAttemptResultDTO } from "../types/game";

export function useBosses() {
  const [bosses, setBosses] = useState<BossDTO[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeBattle, setActiveBattle] = useState<BossStartResponseDTO | null>(null);

  const fetchBosses = useCallback(async () => {
    try {
      setLoading(true);
      const data = await gameApi.getBosses();
      setBosses(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to load boss challenges.");
    } finally {
      setLoading(false);
    }
  }, []);

  const startBoss = async (bossId: string) => {
    try {
      const battle = await gameApi.startBoss(bossId);
      setActiveBattle(battle);
      return battle;
    } catch (err: any) {
      throw new Error(err.message || "Failed to start boss battle.");
    }
  };

  const submitBossResult = async (bossId: string, exerciseAttemptId: string): Promise<BossAttemptResultDTO> => {
    try {
      const result = await gameApi.submitBoss(bossId, exerciseAttemptId);
      await fetchBosses();
      return result;
    } catch (err: any) {
      throw new Error(err.message || "Failed to submit boss result.");
    }
  };

  useEffect(() => {
    fetchBosses();
  }, [fetchBosses]);

  return {
    bosses,
    activeBattle,
    loading,
    error,
    startBoss,
    submitBossResult,
    refetch: fetchBosses,
  };
}
