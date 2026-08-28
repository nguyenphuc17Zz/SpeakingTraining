"use client";

import { useCallback, useEffect, useState } from "react";
import { AudioSessionType } from "@/types/audio";

interface ActiveSessionState {
  sessionId: string;
  sessionType: AudioSessionType;
  activeOwner: string | null;
}

let globalActiveSession: ActiveSessionState | null = null;
const listeners = new Set<(state: ActiveSessionState | null) => void>();

function notifyListeners() {
  listeners.forEach((l) => l(globalActiveSession));
}

export function useAudioSession(sessionType: AudioSessionType, sessionId = "default") {
  const [currentSession, setCurrentSession] = useState<ActiveSessionState | null>(
    globalActiveSession
  );

  useEffect(() => {
    const handler = (st: ActiveSessionState | null) => setCurrentSession(st);
    listeners.add(handler);
    return () => {
      listeners.delete(handler);
    };
  }, []);

  const claimOwnership = useCallback(
    (ownerId: string) => {
      globalActiveSession = {
        sessionId,
        sessionType,
        activeOwner: ownerId,
      };
      notifyListeners();
    },
    [sessionId, sessionType]
  );

  const releaseOwnership = useCallback(
    (ownerId: string) => {
      if (globalActiveSession?.activeOwner === ownerId) {
        globalActiveSession = null;
        notifyListeners();
      }
    },
    []
  );

  const isOwner = useCallback(
    (ownerId: string) => {
      return (
        globalActiveSession?.sessionType === sessionType &&
        globalActiveSession?.activeOwner === ownerId
      );
    },
    [sessionType]
  );

  // Release on unmount if we own it
  useEffect(() => {
    return () => {
      if (globalActiveSession?.sessionType === sessionType) {
        globalActiveSession = null;
        notifyListeners();
      }
    };
  }, [sessionType]);

  return {
    activeSession: currentSession,
    claimOwnership,
    releaseOwnership,
    isOwner,
  };
}
