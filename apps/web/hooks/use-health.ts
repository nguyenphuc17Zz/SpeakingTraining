"use client";

import { useEffect, useState } from "react";
import { ComponentHealth, HealthStatus, healthApi } from "@/services/health-api";

export function useHealth() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [dbHealth, setDbHealth] = useState<ComponentHealth | null>(null);
  const [redisHealth, setRedisHealth] = useState<ComponentHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const checkHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const [h, db, red] = await Promise.allSettled([
        healthApi.getHealth(),
        healthApi.getDbHealth(),
        healthApi.getRedisHealth(),
      ]);

      if (h.status === "fulfilled") setHealth(h.value);
      if (db.status === "fulfilled") setDbHealth(db.value);
      if (red.status === "fulfilled") setRedisHealth(red.value);
    } catch (err: any) {
      setError(err.message || "Failed to connect to backend API");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);

  return { health, dbHealth, redisHealth, loading, error, refetch: checkHealth };
}
