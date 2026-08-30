"use client";

import { useCallback, useEffect, useRef, useState } from "react";

export interface UseReflexTimerOptions {
  timerLimitMs: number;
  autoStart?: boolean;
  onExpire?: () => void;
}

export function useReflexTimer({ timerLimitMs, autoStart = false, onExpire }: UseReflexTimerOptions) {
  const [remainingMs, setRemainingMs] = useState(timerLimitMs);
  const [totalLimitMs, setTotalLimitMs] = useState(timerLimitMs);
  const [isActive, setIsActive] = useState(autoStart);
  const [isPaused, setIsPaused] = useState(false);
  const [isExpired, setIsExpired] = useState(false);

  const rafRef = useRef<number | null>(null);
  const startTimeRef = useRef<number | null>(null);
  const pausedRemainingRef = useRef<number>(timerLimitMs);
  const totalLimitRef = useRef<number>(timerLimitMs);
  const onExpireRef = useRef(onExpire);

  useEffect(() => {
    onExpireRef.current = onExpire;
  }, [onExpire]);

  // Synchronize base limit if not currently active
  useEffect(() => {
    if (!isActive && !isPaused) {
      totalLimitRef.current = timerLimitMs;
      pausedRemainingRef.current = timerLimitMs;
      setTotalLimitMs(timerLimitMs);
      setRemainingMs(timerLimitMs);
    }
  }, [timerLimitMs, isActive, isPaused]);

  const tick = useCallback(() => {
    if (startTimeRef.current === null) return;
    const now = performance.now();
    const elapsed = now - startTimeRef.current;

    if (totalLimitRef.current <= 0) {
      // Infinite mode: track elapsed milliseconds without expiring
      setRemainingMs(Math.ceil(pausedRemainingRef.current + elapsed));
      rafRef.current = requestAnimationFrame(tick);
      return;
    }

    const remaining = Math.max(0, pausedRemainingRef.current - elapsed);
    setRemainingMs(Math.ceil(remaining));

    if (remaining <= 0) {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
        rafRef.current = null;
      }
      setIsActive(false);
      setIsPaused(false);
      setIsExpired(true);
      startTimeRef.current = null;
      onExpireRef.current?.();
      return;
    }

    rafRef.current = requestAnimationFrame(tick);
  }, []);

  const start = useCallback(
    (customLimitMs?: number) => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
        rafRef.current = null;
      }

      const limit = customLimitMs !== undefined ? customLimitMs : (totalLimitRef.current ?? timerLimitMs);
      totalLimitRef.current = limit;
      pausedRemainingRef.current = limit <= 0 ? 0 : limit;
      setTotalLimitMs(limit);
      setRemainingMs(limit <= 0 ? 0 : limit);
      setIsExpired(false);
      setIsPaused(false);
      setIsActive(true);
      startTimeRef.current = performance.now();

      rafRef.current = requestAnimationFrame(tick);
    },
    [timerLimitMs, tick]
  );

  const pause = useCallback(() => {
    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
    if (startTimeRef.current !== null) {
      const elapsed = performance.now() - startTimeRef.current;
      if (totalLimitRef.current <= 0) {
        pausedRemainingRef.current = pausedRemainingRef.current + elapsed;
        setRemainingMs(Math.ceil(pausedRemainingRef.current));
      } else {
        pausedRemainingRef.current = Math.max(0, pausedRemainingRef.current - elapsed);
        setRemainingMs(Math.ceil(pausedRemainingRef.current));
      }
    }
    setIsActive(false);
    setIsPaused(true);
    startTimeRef.current = null;
  }, []);

  const resume = useCallback(() => {
    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
    setIsPaused(false);
    setIsActive(true);
    startTimeRef.current = performance.now();
    rafRef.current = requestAnimationFrame(tick);
  }, [tick]);

  const stop = useCallback(() => {
    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
    setIsActive(false);
    setIsPaused(false);
    startTimeRef.current = null;
  }, []);

  const reset = useCallback(
    (newLimitMs?: number) => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
        rafRef.current = null;
      }
      const limit = newLimitMs !== undefined ? newLimitMs : timerLimitMs;
      totalLimitRef.current = limit;
      pausedRemainingRef.current = limit <= 0 ? 0 : limit;
      setTotalLimitMs(limit);
      setRemainingMs(limit <= 0 ? 0 : limit);
      setIsActive(false);
      setIsPaused(false);
      setIsExpired(false);
      startTimeRef.current = null;
    },
    [timerLimitMs]
  );

  useEffect(() => {
    if (autoStart) {
      start();
    }
    return () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
        rafRef.current = null;
      }
    };
  }, [autoStart, start]);

  const isInfinite = totalLimitMs <= 0;
  const effectiveLimit = isInfinite ? 0 : totalLimitMs;
  const progress = isInfinite ? 1 : Math.max(0, Math.min(1, remainingMs / effectiveLimit));
  const state: "normal" | "warning" | "critical" = isInfinite
    ? "normal"
    : remainingMs <= effectiveLimit * 0.25
    ? "critical"
    : remainingMs <= effectiveLimit * 0.5
    ? "warning"
    : "normal";

  return {
    remainingMs,
    totalLimitMs: effectiveLimit,
    isInfinite,
    progress,
    isActive,
    isPaused,
    isExpired,
    state,
    start,
    pause,
    resume,
    stop,
    reset,
  };
}
