"use client";

import { useEffect, useState, useCallback } from "react";
import { gameApi } from "../services/gameApi";
import { GameProfileDTO, XPOverviewDTO } from "../types/game";

export function useGameProfile() {
  const [profile, setProfile] = useState<GameProfileDTO | null>(null);
  const [xpOverview, setXpOverview] = useState<XPOverviewDTO | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchProfile = useCallback(async () => {
    try {
      setLoading(true);
      const [profData, xpData] = await Promise.all([
        gameApi.getProfile(),
        gameApi.getXPOverview().catch(() => null),
      ]);
      setProfile(profData);
      setXpOverview(xpData);
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to load game profile.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  return {
    profile,
    xpOverview,
    loading,
    error,
    refetch: fetchProfile,
  };
}
