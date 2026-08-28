"use client";

import { useEffect, useState, useCallback } from "react";
import { gameApi } from "../services/gameApi";
import { RewardNotificationDTO } from "../types/game";

export function useRewardNotifications() {
  const [notifications, setNotifications] = useState<RewardNotificationDTO[]>([]);
  const [currentToast, setCurrentToast] = useState<RewardNotificationDTO | null>(null);

  const fetchNotifications = useCallback(async () => {
    try {
      const items = await gameApi.getNotifications(10);
      setNotifications(items);
      if (items.length > 0 && !currentToast) {
        // Show highest priority first
        setCurrentToast(items[0]);
      }
    } catch {
      // Non-critical background polling
    }
  }, [currentToast]);

  const dismissToast = async (id: string) => {
    try {
      await gameApi.markNotificationRead(id);
      setNotifications((prev) => prev.filter((n) => n.id !== id));
      const remaining = notifications.filter((n) => n.id !== id);
      setCurrentToast(remaining.length > 0 ? remaining[0] : null);
    } catch {
      setCurrentToast(null);
    }
  };

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 15000); // 15s poll
    return () => clearInterval(interval);
  }, [fetchNotifications]);

  return {
    notifications,
    currentToast,
    dismissToast,
    refetch: fetchNotifications,
  };
}
