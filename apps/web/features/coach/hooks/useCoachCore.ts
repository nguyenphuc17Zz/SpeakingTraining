"use client";

import { useState, useCallback } from "react";
import { coachCoreApi, CoachChatResponse, CoachPersona } from "../services/coachCoreApi";

export interface CoachCoreMessage {
  id: string;
  sender: "user" | "coach";
  text: string;
  persona?: CoachPersona;
  raw?: CoachChatResponse;
  timestamp: Date;
}

export function useCoachCore() {
  const [messages, setMessages] = useState<CoachCoreMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [persona, setPersona] = useState<CoachPersona>("tanaka");

  const ask = useCallback(
    async (
      message: string,
      opts?: {
        route?: string;
        exerciseId?: string;
        sessionId?: string;
        actionMode?: string;
        personaOverride?: CoachPersona;
      }
    ) => {
      if (!message.trim() || loading) return null;
      const activePersona = opts?.personaOverride || persona;
      const userMsg: CoachCoreMessage = {
        id: String(Date.now()),
        sender: "user",
        text: message,
        timestamp: new Date(),
      };
      setMessages((p) => [...p, userMsg]);
      setLoading(true);
      setError(null);

      // Streaming
      const useStream = !opts?.actionMode;
      if (useStream) {
        const coachId = String(Date.now() + 1);
        let streamedText = "";
        setMessages((p) => [
          ...p,
          {
            id: coachId,
            sender: "coach",
            text: "",
            persona: activePersona,
            timestamp: new Date(),
          },
        ]);
        try {
          for await (const evt of coachCoreApi.chatStream({
            message,
            persona: activePersona,
            current_route: opts?.route,
            current_exercise_id: opts?.exerciseId,
            current_session_id: opts?.sessionId,
            action_mode: opts?.actionMode,
          })) {
            if (evt.type === "delta" && evt.text) {
              streamedText += evt.text;
              setMessages((p) =>
                p.map((m) => (m.id === coachId ? { ...m, text: streamedText } : m))
              );
            } else if (evt.type === "final" && evt.data) {
              const final = evt.data.tool_calls ? evt.data : evt.data.data || evt.data;
              const raw: CoachChatResponse = final.data ? final.data : final;
              const finalText = raw.response || streamedText || final.response || "";
              setMessages((p) =>
                p.map((m) => (m.id === coachId ? { ...m, text: finalText, raw } : m))
              );
              setLoading(false);
              return raw;
            } else if (evt.type === "error") {
              throw new Error(evt.data?.error || "Stream error");
            }
          }
          setLoading(false);
          return null;
        } catch {
          // fallback to non-stream on stream failure
          setMessages((p) => p.filter((m) => m.id !== coachId));
        }
      }

      // Non-stream fallback
      try {
        const res = await coachCoreApi.chat({
          message,
          persona: activePersona,
          current_route: opts?.route,
          current_exercise_id: opts?.exerciseId,
          current_session_id: opts?.sessionId,
          action_mode: opts?.actionMode,
        });
        const coachMsg: CoachCoreMessage = {
          id: String(Date.now() + 1),
          sender: "coach",
          text: res.response,
          persona: activePersona,
          raw: res,
          timestamp: new Date(),
        };
        setMessages((p) => [...p, coachMsg]);
        return res;
      } catch (err: any) {
        setError(err.message || "Failed to get coach response");
        return null;
      } finally {
        setLoading(false);
      }
    },
    [loading, persona]
  );

  const clear = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return { messages, loading, error, persona, setPersona, ask, clear };
}
