"use client";

import { useEffect, useState, useCallback } from "react";
import { UserSettings, UserSettingsUpdate } from "@/types/settings";
import { settingsApi } from "@/services/settings-api";

export function useSettings() {
  const [settings, setSettings] = useState<UserSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSettings = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await settingsApi.getSettings();
      setSettings(data);
    } catch (err: any) {
      setError(err.message || "Failed to load user settings");
    } finally {
      setLoading(false);
    }
  }, []);

  const updateSettings = async (payload: UserSettingsUpdate): Promise<UserSettings | null> => {
    setSaving(true);
    setError(null);
    try {
      const updated = await settingsApi.updateSettings(payload);
      setSettings(updated);
      return updated;
    } catch (err: any) {
      setError(err.message || "Failed to save settings");
      return null;
    } finally {
      setSaving(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  return { settings, loading, saving, error, updateSettings, refetch: fetchSettings };
}
