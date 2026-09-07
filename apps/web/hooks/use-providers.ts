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
      return { success: true };
    } catch (err: any) {
      const msg = err.message || "Không thể lưu API key";
      setError(msg);
      return { success: false, error: msg };
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
      return { success: true };
    } catch (err: any) {
      const msg = err.message || "Không thể cập nhật API key";
      setError(msg);
      return { success: false, error: msg };
    } finally {
      setActionLoading(false);
    }
  };

  const saveOrUpdateCredential = async (
    providerId: string,
    apiKey: string,
    existingCredentialId?: string | null
  ) => {
    const trimmedKey = apiKey.trim();
    if (!trimmedKey) {
      return { success: false, error: "API Key không được để trống" };
    }

    // 1. If existing credential ID is provided, PATCH directly
    if (existingCredentialId) {
      return updateCredential(existingCredentialId, { api_key: trimmedKey });
    }

    // 2. Check if we already have a credential in our local state for this provider
    const found = providers.find((p) => p.id === providerId);
    if (found?.credential?.id) {
      return updateCredential(found.credential.id, { api_key: trimmedKey });
    }

    // 3. Otherwise, try POST
    const createResult = await saveCredential({
      provider: providerId,
      api_key: trimmedKey,
      is_enabled: true,
    });

    // 4. If POST failed with 409 Conflict (already exists), re-fetch and try PATCH
    if (!createResult.success && (createResult.error?.includes("already exists") || createResult.error?.includes("409"))) {
      try {
        const latest = await providersApi.listProviders();
        setProviders(latest);
        const latestCred = latest.find((p) => p.id === providerId)?.credential;
        if (latestCred?.id) {
          return updateCredential(latestCred.id, { api_key: trimmedKey });
        }
      } catch {
        // Fall through to returning createResult
      }
    }

    return createResult;
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
    saveOrUpdateCredential,
    deleteCredential,
    refetch: fetchProviders,
  };
}
