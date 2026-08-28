"use client";

import { useEffect, useState, useCallback } from "react";
import {
  CredentialCreateInput,
  CredentialUpdateInput,
  ProviderDetail,
} from "@/types/provider";
import { providersApi } from "@/services/providers-api";

export function useProviders() {
  const [providers, setProviders] = useState<ProviderDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchProviders = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await providersApi.listProviders();
      setProviders(data);
    } catch (err: any) {
      setError(err.message || "Failed to load AI providers");
    } finally {
      setLoading(false);
    }
  }, []);

  const saveCredential = async (payload: CredentialCreateInput) => {
    setActionLoading(true);
    setError(null);
    try {
      await providersApi.createCredential(payload);
      await fetchProviders();
      return true;
    } catch (err: any) {
      setError(err.message || "Failed to save API key");
      return false;
    } finally {
      setActionLoading(false);
    }
  };

  const updateCredential = async (id: string, payload: CredentialUpdateInput) => {
    setActionLoading(true);
    setError(null);
    try {
      await providersApi.updateCredential(id, payload);
      await fetchProviders();
      return true;
    } catch (err: any) {
      setError(err.message || "Failed to update API key");
      return false;
    } finally {
      setActionLoading(false);
    }
  };

  const deleteCredential = async (id: string) => {
    setActionLoading(true);
    setError(null);
    try {
      await providersApi.deleteCredential(id);
      await fetchProviders();
      return true;
    } catch (err: any) {
      setError(err.message || "Failed to delete API key");
      return false;
    } finally {
      setActionLoading(false);
    }
  };

  useEffect(() => {
    fetchProviders();
  }, [fetchProviders]);

  return {
    providers,
    loading,
    actionLoading,
    error,
    saveCredential,
    updateCredential,
    deleteCredential,
    refetch: fetchProviders,
  };
}
