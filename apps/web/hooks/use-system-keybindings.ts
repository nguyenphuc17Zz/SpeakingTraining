"use client";

import { useState, useEffect, useCallback } from "react";

export type KeybindingCategory =
  | "situations"
  | "pitch"
  | "keigo"
  | "reflex"
  | "speaking"
  | "shadowing"
  | "system";

export interface SystemKeybindings {
  // 1. Shadowing Studio (/shadowing)
  toggleMic: string;
  replay: string;
  nextSegment: string;
  prevSegment: string;
  toggleLoop: string;
  markerA: string;
  markerB: string;

  // 2. Speaking / Conversation (/speaking)
  speakingMic: string;
  speakingReplay: string;
  speakingHint: string;
  speakingSubtitle: string;
  speakingMute: string;
  speakingModeToggle: string;

  // 3. Keigo Studio (/keigo)
  keigoSubmitOrNext: string;
  keigoListenPrompt: string;
  keigoReplayModel: string;
  keigoToggleHint: string;
  keigoRetry: string;
  keigoSkip: string;
  keigoOpenCheatsheet: string;
  keigoStartVoice: string;
  keigoToggleInputMode: string;

  // 4. Pitch Lab (/pitch)
  pitchSubmitOrNext: string;
  pitchListenPrompt: string;
  pitchReplayModel: string;
  pitchRetry: string;
  pitchSkip: string;
  pitchOpenCheatsheet: string;
  pitchStartVoice: string;
  pitchToggleInputMode: string;
  pitchMetronome: string;
  pitchQuizOption1: string;
  pitchQuizOption2: string;

  // 5. Situations Studio (/situations)
  situationsSubmitOrNext: string;
  situationsListenPrompt: string;
  situationsReplayModel: string;
  situationsToggleHint: string;
  situationsRetry: string;
  situationsSkip: string;
  situationsOpenCheatsheet: string;
  situationsStartVoice: string;
  situationsToggleInputMode: string;

  // 6. Reflex Practice (/reflex)
  reflexSubmitOrNext: string;
  reflexListenPrompt: string;
  reflexReplayModel: string;
  reflexRetry: string;
  reflexSkip: string;
  reflexToggleHelp: string;
  reflexPauseOrResume: string;
  reflexStartVoice: string;
  reflexToggleInputMode: string;

  // Generic Drills Aliases (for backward compatibility)
  drillSubmitOrNext: string;
  drillReplayAudio: string;
  drillRetry: string;
  drillSkip: string;
  drillToggleHelp: string;
  drillPauseOrResume: string;
  drillStartQuestion: string;

  // 7. System & Navigation
  globalSearch: string;
  openCoach: string;
  openKeybindingsModal: string;
  openDojo: string;
  toggleTheme: string;
  toggleFurigana: string;
}

export type ShadowingKeybindings = SystemKeybindings;

export const DEFAULT_KEYBINDINGS: SystemKeybindings = {
  // Shadowing
  toggleMic: "q",
  replay: "c",
  nextSegment: "arrowright",
  prevSegment: "arrowleft",
  toggleLoop: "l",
  markerA: "[",
  markerB: "]",

  // Speaking
  speakingMic: "space",
  speakingReplay: "r",
  speakingHint: "h",
  speakingSubtitle: "s",
  speakingMute: "m",
  speakingModeToggle: "t",

  // Keigo
  keigoSubmitOrNext: "enter",
  keigoListenPrompt: "l",
  keigoReplayModel: "a",
  keigoToggleHint: "h",
  keigoRetry: "r",
  keigoSkip: "n",
  keigoOpenCheatsheet: "c",
  keigoStartVoice: "space",
  keigoToggleInputMode: "t",

  // Pitch
  pitchSubmitOrNext: "enter",
  pitchListenPrompt: "l",
  pitchReplayModel: "a",
  pitchRetry: "r",
  pitchSkip: "n",
  pitchOpenCheatsheet: "c",
  pitchStartVoice: "space",
  pitchToggleInputMode: "t",
  pitchMetronome: "m",
  pitchQuizOption1: "1",
  pitchQuizOption2: "2",

  // Situations
  situationsSubmitOrNext: "enter",
  situationsListenPrompt: "l",
  situationsReplayModel: "a",
  situationsToggleHint: "h",
  situationsRetry: "r",
  situationsSkip: "n",
  situationsOpenCheatsheet: "c",
  situationsStartVoice: "space",
  situationsToggleInputMode: "t",

  // Reflex
  reflexSubmitOrNext: "enter",
  reflexListenPrompt: "l",
  reflexReplayModel: "a",
  reflexRetry: "r",
  reflexSkip: "n",
  reflexToggleHelp: "?",
  reflexPauseOrResume: "p",
  reflexStartVoice: "space",
  reflexToggleInputMode: "t",

  // Generic Drills Aliases
  drillSubmitOrNext: "enter",
  drillReplayAudio: "space",
  drillRetry: "r",
  drillSkip: "n",
  drillToggleHelp: "?",
  drillPauseOrResume: "p",
  drillStartQuestion: "s",

  // System
  globalSearch: "k",
  openCoach: "j",
  openKeybindingsModal: "?",
  openDojo: "d",
  toggleTheme: "t",
  toggleFurigana: "f",
};

export const ACTION_CATEGORIES: Record<keyof SystemKeybindings, KeybindingCategory> = {
  // Shadowing
  toggleMic: "shadowing",
  replay: "shadowing",
  nextSegment: "shadowing",
  prevSegment: "shadowing",
  toggleLoop: "shadowing",
  markerA: "shadowing",
  markerB: "shadowing",

  // Speaking
  speakingMic: "speaking",
  speakingReplay: "speaking",
  speakingHint: "speaking",
  speakingSubtitle: "speaking",
  speakingMute: "speaking",
  speakingModeToggle: "speaking",

  // Keigo
  keigoSubmitOrNext: "keigo",
  keigoListenPrompt: "keigo",
  keigoReplayModel: "keigo",
  keigoToggleHint: "keigo",
  keigoRetry: "keigo",
  keigoSkip: "keigo",
  keigoOpenCheatsheet: "keigo",
  keigoStartVoice: "keigo",
  keigoToggleInputMode: "keigo",

  // Pitch
  pitchSubmitOrNext: "pitch",
  pitchListenPrompt: "pitch",
  pitchReplayModel: "pitch",
  pitchRetry: "pitch",
  pitchSkip: "pitch",
  pitchOpenCheatsheet: "pitch",
  pitchStartVoice: "pitch",
  pitchToggleInputMode: "pitch",
  pitchMetronome: "pitch",
  pitchQuizOption1: "pitch",
  pitchQuizOption2: "pitch",

  // Situations
  situationsSubmitOrNext: "situations",
  situationsListenPrompt: "situations",
  situationsReplayModel: "situations",
  situationsToggleHint: "situations",
  situationsRetry: "situations",
  situationsSkip: "situations",
  situationsOpenCheatsheet: "situations",
  situationsStartVoice: "situations",
  situationsToggleInputMode: "situations",

  // Reflex
  reflexSubmitOrNext: "reflex",
  reflexListenPrompt: "reflex",
  reflexReplayModel: "reflex",
  reflexRetry: "reflex",
  reflexSkip: "reflex",
  reflexToggleHelp: "reflex",
  reflexPauseOrResume: "reflex",
  reflexStartVoice: "reflex",
  reflexToggleInputMode: "reflex",

  // Generic Drills Aliases
  drillSubmitOrNext: "reflex",
  drillReplayAudio: "reflex",
  drillRetry: "reflex",
  drillSkip: "reflex",
  drillToggleHelp: "reflex",
  drillPauseOrResume: "reflex",
  drillStartQuestion: "reflex",

  // System
  globalSearch: "system",
  openCoach: "system",
  openKeybindingsModal: "system",
  openDojo: "system",
  toggleTheme: "system",
  toggleFurigana: "system",
};

const STORAGE_KEY = "hanasu_system_keybindings_v6";

export function formatKeyDisplay(keyVal: string): string {
  if (!keyVal) return "";
  const lower = keyVal.toLowerCase();
  if (lower === "arrowright") return "→";
  if (lower === "arrowleft") return "←";
  if (lower === "arrowup") return "↑";
  if (lower === "arrowdown") return "↓";
  if (lower === "space" || lower === " ") return "Space";
  if (lower === "enter") return "Enter ↵";
  if (lower === "escape" || lower === "esc") return "Esc";
  return keyVal.toUpperCase();
}

export function isKeyMatch(e: KeyboardEvent, targetKey: string): boolean {
  if (!targetKey) return false;
  const pressed = (e.key || "").toLowerCase();
  const code = (e.code || "").toLowerCase();
  const target = targetKey.toLowerCase();

  if (target === "space") {
    return pressed === " " || code === "space";
  }
  if (target === "enter") {
    return pressed === "enter" || code === "enter" || code === "numpadenter";
  }
  if (target === "arrowright") {
    return pressed === "arrowright" || code === "arrowright";
  }
  if (target === "arrowleft") {
    return pressed === "arrowleft" || code === "arrowleft";
  }
  if (target === "arrowup") {
    return pressed === "arrowup" || code === "arrowup";
  }
  if (target === "arrowdown") {
    return pressed === "arrowdown" || code === "arrowdown";
  }
  if (target === "escape" || target === "esc") {
    return pressed === "escape" || code === "escape";
  }
  if (target === "1") {
    return pressed === "1" || code === "digit1" || code === "numpad1";
  }
  if (target === "2") {
    return pressed === "2" || code === "digit2" || code === "numpad2";
  }
  if (target === "3") {
    return pressed === "3" || code === "digit3" || code === "numpad3";
  }
  if (target === "?") {
    return pressed === "?" || (pressed === "/" && e.shiftKey);
  }

  // Handle single character letter keys (e.g. 'h', 'a', 'l', 'r', 'n', 'c', 't', 'm', 'f', 'p')
  if (target.length === 1 && target >= "a" && target <= "z") {
    return pressed === target || code === `key${target}`;
  }

  return pressed === target || code === target;
}

export function useSystemKeybindings() {
  const [keybindings, setKeybindings] = useState<SystemKeybindings>(DEFAULT_KEYBINDINGS);
  const [isLoaded, setIsLoaded] = useState(false);

  // Load from localStorage
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        setKeybindings({ ...DEFAULT_KEYBINDINGS, ...parsed });
      }
    } catch (e) {
      console.warn("Failed to load keybindings from localStorage:", e);
    } finally {
      setIsLoaded(true);
    }
  }, []);

  // Save single keybinding
  const updateKeybinding = useCallback((action: keyof SystemKeybindings, key: string) => {
    let normalized = key.toLowerCase();
    if (normalized === " ") normalized = "space";

    setKeybindings((prev) => {
      const updated = { ...prev, [action]: normalized };
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      } catch (e) {}
      return updated;
    });
  }, []);

  // Check if a key conflicts with other actions in the same category
  const getConflicts = useCallback(
    (action: keyof SystemKeybindings, candidateKey: string): (keyof SystemKeybindings)[] => {
      const category = ACTION_CATEGORIES[action];
      const normalizedCandidate = candidateKey.toLowerCase() === " " ? "space" : candidateKey.toLowerCase();
      const conflicts: (keyof SystemKeybindings)[] = [];

      (Object.keys(keybindings) as (keyof SystemKeybindings)[]).forEach((act) => {
        if (act !== action && ACTION_CATEGORIES[act] === category) {
          const currentKey = keybindings[act]?.toLowerCase();
          if (currentKey === normalizedCandidate) {
            conflicts.push(act);
          }
        }
      });

      return conflicts;
    },
    [keybindings]
  );

  // Reset by category or reset all
  const resetToDefaults = useCallback((category?: KeybindingCategory) => {
    setKeybindings((prev) => {
      if (!category) {
        try {
          localStorage.removeItem(STORAGE_KEY);
        } catch (e) {}
        return DEFAULT_KEYBINDINGS;
      }

      const updated = { ...prev };
      (Object.keys(DEFAULT_KEYBINDINGS) as (keyof SystemKeybindings)[]).forEach((act) => {
        if (ACTION_CATEGORIES[act] === category) {
          updated[act] = DEFAULT_KEYBINDINGS[act];
        }
      });

      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      } catch (e) {}
      return updated;
    });
  }, []);

  // Helper to match an action against a key event
  const matchesAction = useCallback(
    (e: KeyboardEvent, action: keyof SystemKeybindings): boolean => {
      const target = keybindings[action];
      return isKeyMatch(e, target);
    },
    [keybindings]
  );

  return {
    keybindings,
    updateKeybinding,
    resetToDefaults,
    getConflicts,
    matchesAction,
    isLoaded,
  };
}

// Backwards compatibility
export const useShadowingKeybindings = useSystemKeybindings;
