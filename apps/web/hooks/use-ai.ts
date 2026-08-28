"use client";

import { useState, useCallback, useEffect } from "react";
import {
  AIRoutingPolicyRead,
  AIRoutingPolicyUpdate,
  AIResponseRead,
  AIStreamEvent,
  GenerateRequestInput,
  ProviderHealth,
} from "@/types/ai";
import { ModelMetadata } from "@/types/provider";
import { aiApi } from "@/services/ai-api";

export function useAI() {
  const [healthList, setHealthList] = useState<ProviderHealth[]>([]);
  const [routingPolicy, setRoutingPolicy] = useState<AIRoutingPolicyRead | null>(null);
  const [models, setModels] = useState<ModelMetadata[]>([]);
  const [loading, setLoading] = useState(false);
  const [testingProvider, setTestingProvider] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = useCallback(async () => {
    try {
      const data = await aiApi.getHealth();
      setHealthList(data);
    } catch (err: any) {
      console.error("Failed to fetch provider health:", err);
    }
  }, []);

  const fetchRoutingPolicy = useCallback(async () => {
    try {
      const data = await aiApi.getRoutingPolicy();
      setRoutingPolicy(data);
    } catch (err: any) {
      console.error("Failed to fetch routing policy:", err);
    }
  }, []);

  const [refreshingModels, setRefreshingModels] = useState(false);

  const fetchModels = useCallback(async (provider?: string, refresh: boolean = false) => {
    try {
      const data = await aiApi.listModels(provider, refresh);
      setModels(data);
    } catch (err: any) {
      console.error("Failed to fetch models:", err);
    }
  }, []);

  const refreshModels = async (provider?: string): Promise<ModelMetadata[]> => {
    setRefreshingModels(true);
    setError(null);
    try {
      const data = await aiApi.refreshModels(provider);
      setModels(data);
      return data;
    } catch (err: any) {
      setError(err.message || "Failed to refresh models");
      return [];
    } finally {
      setRefreshingModels(false);
    }
  };

  const testConnection = async (provider: string): Promise<ProviderHealth | null> => {
    setTestingProvider(provider);
    setError(null);
    try {
      const result = await aiApi.testConnection(provider);
      await fetchHealth();
      return result;
    } catch (err: any) {
      setError(err.message || `Failed to test connection for ${provider}`);
      return null;
    } finally {
      setTestingProvider(null);
    }
  };

  const updateRouting = async (payload: AIRoutingPolicyUpdate) => {
    setLoading(true);
    setError(null);
    try {
      const updated = await aiApi.updateRoutingPolicy(payload);
      setRoutingPolicy(updated);
      return true;
    } catch (err: any) {
      setError(err.message || "Failed to update routing policy");
      return false;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    fetchRoutingPolicy();
    fetchModels();
  }, [fetchHealth, fetchRoutingPolicy, fetchModels]);

  return {
    healthList,
    routingPolicy,
    models,
    loading,
    refreshingModels,
    testingProvider,
    error,
    fetchHealth,
    fetchRoutingPolicy,
    fetchModels,
    refreshModels,
    testConnection,
    updateRouting,
  };
}
