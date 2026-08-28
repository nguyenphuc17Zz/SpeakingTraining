"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Persona,
  PersonaCreateInput,
  PersonaGenerateInput,
  PersonaGenerateResponse,
  PersonaUpdateInput,
} from "@/types/persona";
import { personasApi } from "@/services/personas-api";

export function usePersonas() {
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPersonas = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await personasApi.listPersonas();
      setPersonas(data);
    } catch (err: any) {
      setError(err.message || "Failed to load personas");
    } finally {
      setLoading(false);
    }
  }, []);

  const createPersona = async (payload: PersonaCreateInput) => {
    setActionLoading(true);
    setError(null);
    try {
      await personasApi.createPersona(payload);
      await fetchPersonas();
      return true;
    } catch (err: any) {
      setError(err.message || "Failed to create persona");
      return false;
    } finally {
      setActionLoading(false);
    }
  };

  const updatePersona = async (id: string, payload: PersonaUpdateInput) => {
    setActionLoading(true);
    setError(null);
    try {
      await personasApi.updatePersona(id, payload);
      await fetchPersonas();
      return true;
    } catch (err: any) {
      setError(err.message || "Failed to update persona");
      return false;
    } finally {
      setActionLoading(false);
    }
  };

  const deletePersona = async (id: string) => {
    setActionLoading(true);
    setError(null);
    try {
      await personasApi.deletePersona(id);
      await fetchPersonas();
      return true;
    } catch (err: any) {
      setError(err.message || "Failed to delete persona");
      return false;
    } finally {
      setActionLoading(false);
    }
  };

  const [generating, setGenerating] = useState(false);
  const generateRandomPersona = async (
    payload: PersonaGenerateInput = {}
  ): Promise<{ data: PersonaGenerateResponse | null; error: string | null }> => {
    setGenerating(true);
    setError(null);
    try {
      const data = await personasApi.generateRandomPersona(payload);
      return { data, error: null };
    } catch (err: any) {
      const msg = err.message || "Không thể tạo persona ngẫu nhiên";
      setError(msg);
      return { data: null, error: msg };
    } finally {
      setGenerating(false);
    }
  };

  const restoreDefaults = async () => {
    setActionLoading(true);
    setError(null);
    try {
      const data = await personasApi.restoreDefaults();
      setPersonas(data);
      return true;
    } catch (err: any) {
      setError(err.message || "Không thể khôi phục đối tác mẫu");
      return false;
    } finally {
      setActionLoading(false);
    }
  };

  useEffect(() => {
    fetchPersonas();
  }, [fetchPersonas]);

  return {
    personas,
    loading,
    actionLoading,
    generating,
    error,
    createPersona,
    updatePersona,
    deletePersona,
    generateRandomPersona,
    restoreDefaults,
    refetch: fetchPersonas,
  };
}
