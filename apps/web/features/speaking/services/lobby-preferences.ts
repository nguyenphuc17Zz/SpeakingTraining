"use client";

import { SessionMode, VADSensitivity, VoiceSettingsConfig } from "../types";

const LOBBY_STORAGE_KEY = "speaking_training_lobby_prefs_v1";

export interface SavedLobbyPreferences {
  mode: SessionMode;
  ai_provider: string;
  ai_model: string;
  stt_provider: string;
  stt_model: string;
  tts_provider: string;
  tts_engine: "voicevox" | "web_speech" | "none";
  tts_enabled: boolean;
  tts_voice: string;
  auto_end_of_speech: boolean;
  vad_sensitivity: VADSensitivity;
}

export const DEFAULT_SAVED_PREFERENCES: SavedLobbyPreferences = {
  mode: "conversation",
  ai_provider: "auto",
  ai_model: "auto",
  stt_provider: "faster_whisper",
  stt_model: "base",
  tts_provider: "voicevox",
  tts_engine: "voicevox",
  tts_enabled: true,
  tts_voice: "1",
  auto_end_of_speech: true,
  vad_sensitivity: "medium",
};

/**
 * Safely reads saved speaking lobby preferences from localStorage.
 */
export function getSavedLobbyPreferences(): SavedLobbyPreferences {
  if (typeof window === "undefined") {
    return DEFAULT_SAVED_PREFERENCES;
  }

  try {
    const raw = localStorage.getItem(LOBBY_STORAGE_KEY);
    if (!raw) return DEFAULT_SAVED_PREFERENCES;

    const parsed = JSON.parse(raw);
    return {
      ...DEFAULT_SAVED_PREFERENCES,
      ...parsed,
    };
  } catch (err) {
    console.warn("[LobbyPreferences] Failed to load preferences from localStorage:", err);
    return DEFAULT_SAVED_PREFERENCES;
  }
}

/**
 * Persists updated speaking lobby preferences to localStorage.
 */
export function saveLobbyPreferences(updates: Partial<SavedLobbyPreferences>): SavedLobbyPreferences {
  if (typeof window === "undefined") {
    return { ...DEFAULT_SAVED_PREFERENCES, ...updates };
  }

  try {
    const current = getSavedLobbyPreferences();
    const next: SavedLobbyPreferences = {
      ...current,
      ...updates,
    };
    localStorage.setItem(LOBBY_STORAGE_KEY, JSON.stringify(next));
    return next;
  } catch (err) {
    console.warn("[LobbyPreferences] Failed to save preferences to localStorage:", err);
    return { ...DEFAULT_SAVED_PREFERENCES, ...updates };
  }
}
