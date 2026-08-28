"use client";

import { useEffect, useState, useCallback } from "react";
import { analyticsApi } from "../services/analyticsApi";
import {
  CoachAnswerDTO,
  CoachQuickCardDTO,
  DailyBriefingDTO,
} from "../types/analytics";

export interface ChatMessage {
  id: string;
  sender: "user" | "coach";
  text: string;
  answerDTO?: CoachAnswerDTO;
  timestamp: Date;
}

export function useCoach() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [quickCards, setQuickCards] = useState<CoachQuickCardDTO[]>([]);
  const [briefing, setBriefing] = useState<DailyBriefingDTO | null>(null);

  const fetchInitialData = useCallback(async () => {
    try {
      const [cards, brief] = await Promise.all([
        analyticsApi.getCoachQuickCards().catch(() => []),
        analyticsApi.getDailyBriefing().catch(() => null),
      ]);
      setQuickCards(cards);
      setBriefing(brief);
    } catch {
      //
    }
  }, []);

  useEffect(() => {
    fetchInitialData();
  }, [fetchInitialData]);

  const askCoach = async (question: string) => {
    if (!question.trim()) return;

    const userMsgId = String(Date.now());
    const userMsg: ChatMessage = {
      id: userMsgId,
      sender: "user",
      text: question,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);
    setError(null);

    try {
      const resp = await analyticsApi.askCoach({ question });
      const coachMsg: ChatMessage = {
        id: String(Date.now() + 1),
        sender: "coach",
        text: resp.answer,
        answerDTO: resp,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, coachMsg]);
    } catch (err: any) {
      setError(err.message || "Failed to get answer from Personal Coach.");
    } finally {
      setLoading(false);
    }
  };

  const submitFeedback = async (conversationId: string, rating: "helpful" | "not_helpful" | "incorrect") => {
    try {
      await analyticsApi.submitCoachFeedback({ conversation_id: conversationId, rating });
    } catch {
      //
    }
  };

  return {
    messages,
    loading,
    error,
    quickCards,
    briefing,
    askCoach,
    submitFeedback,
    refetchBriefing: fetchInitialData,
  };
}
