"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { Clock, Infinity as InfinityIcon } from "lucide-react";

interface Props {
  remainingMs: number;
  timerLimitMs: number;
  progress: number; // 0-1
  state: "normal" | "warning" | "critical";
  isActive: boolean;
  isPaused?: boolean;
  variant?: "ring" | "badge" | "bar";
  className?: string;
}

export function ReflexTimer({
  remainingMs,
  timerLimitMs,
  progress,
  state,
  isActive,
  isPaused = false,
  variant = "ring",
  className,
}: Props) {
  const isInfinite = timerLimitMs <= 0;
  const pct = isInfinite ? 1 : Math.max(0, Math.min(1, progress));
  const circumference = 2 * Math.PI * 42;
  const offset = circumference * (1 - pct);

  const strokeColor = isPaused
    ? "stroke-amber-500 text-amber-500"
    : isInfinite
    ? "stroke-emerald-500 text-emerald-500"
    : state === "critical"
    ? "stroke-rose-500 text-rose-500"
    : state === "warning"
    ? "stroke-amber-500 text-amber-500"
    : "stroke-primary text-primary";

  const glowShadow = isPaused
    ? "shadow-[0_0_20px_rgba(245,158,11,0.25)] border-amber-500/40 ring-2 ring-amber-500/20"
    : isActive && !isInfinite && state === "critical"
    ? "shadow-[0_0_24px_rgba(244,63,94,0.35)]"
    : isActive && !isInfinite && state === "warning"
    ? "shadow-[0_0_20px_rgba(245,158,11,0.3)]"
    : isActive
    ? "shadow-[0_0_20px_rgba(var(--primary),0.25)]"
    : "";

  const secs = isInfinite ? (remainingMs / 1000).toFixed(1) : (remainingMs / 1000).toFixed(1);

  if (variant === "badge") {
    return (
      <div
        className={cn(
          "inline-flex items-center gap-1.5 px-3 py-1 rounded-full border text-xs font-bold font-mono transition-all",
          isPaused
            ? "bg-amber-500/15 border-amber-500/30 text-amber-600 dark:text-amber-400"
            : isInfinite
            ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-600 dark:text-emerald-400"
            : state === "critical"
            ? "bg-rose-500/10 border-rose-500/30 text-rose-600 dark:text-rose-400"
            : state === "warning"
            ? "bg-amber-500/10 border-amber-500/30 text-amber-600 dark:text-amber-400"
            : "bg-primary/10 border-primary/20 text-primary",
          className
        )}
      >
        {isInfinite ? (
          <InfinityIcon className="h-3.5 w-3.5 text-emerald-500" />
        ) : (
          <Clock className={cn("h-3.5 w-3.5", isActive && "animate-spin duration-3000")} />
        )}
        <span>
          {isPaused
            ? `⏸️ ${secs}s (Tạm dừng)`
            : isInfinite
            ? `∞ ${secs}s (Tự do)`
            : `${secs}s`}
        </span>
      </div>
    );
  }

  if (variant === "bar") {
    return (
      <div className={cn("w-full space-y-1.5", className)}>
        <div className="flex items-center justify-between text-xs font-mono font-bold">
          <span className="text-muted-foreground flex items-center gap-1">
            {isInfinite ? (
              <InfinityIcon className="h-3.5 w-3.5 text-emerald-500" />
            ) : (
              <Clock className="h-3.5 w-3.5" />
            )}
            <span>
              {isPaused
                ? "Đang tạm dừng:"
                : isInfinite
                ? "Thời gian: ∞ Vô hạn (Tự do phát âm)"
                : `Giới hạn: ${timerLimitMs / 1000}s`}
            </span>
          </span>
          <span className={cn(strokeColor, "text-sm")}>{secs}s</span>
        </div>
        <div className="w-full h-2 rounded-full bg-muted overflow-hidden border border-border">
          <div
            className={cn(
              "h-full transition-all duration-100",
              isPaused
                ? "bg-amber-500"
                : isInfinite
                ? "bg-emerald-500"
                : state === "critical"
                ? "bg-rose-500"
                : state === "warning"
                ? "bg-amber-500"
                : "bg-primary"
            )}
            style={{ width: `${pct * 100}%` }}
          />
        </div>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "relative flex flex-col items-center justify-center p-4 md:p-5 rounded-3xl border bg-card/90 washi-texture transition-all",
        glowShadow,
        isPaused
          ? "border-amber-500/40 ring-2 ring-amber-500/20"
          : isActive
          ? "border-primary/40 ring-2 ring-primary/20"
          : "border-border/80",
        className
      )}
      role="progressbar"
      aria-valuenow={Math.round(pct * 100)}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={`Timer ${secs}s`}
    >
      <div className="relative h-[110px] w-[110px]">
        <svg className="h-full w-full -rotate-90" viewBox="0 0 100 100" aria-hidden="true">
          {/* Background circle */}
          <circle
            cx="50"
            cy="50"
            r="42"
            fill="none"
            strokeWidth="7"
            className="stroke-muted/40 dark:stroke-muted/20"
          />
          {/* Active progress arc */}
          <circle
            cx="50"
            cy="50"
            r="42"
            fill="none"
            strokeWidth="7"
            strokeLinecap="round"
            className={cn(strokeColor, "transition-all duration-100 ease-linear")}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
          />
        </svg>

        {/* Center countdown number */}
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          {isInfinite ? (
            <div className="flex flex-col items-center">
              <span className="text-3xl font-black text-emerald-500 font-mono">∞</span>
              <span className="text-[10px] font-mono text-muted-foreground">{secs}s</span>
            </div>
          ) : (
            <span
              className={cn(
                "text-2xl md:text-3xl font-black font-mono tracking-tight tabular-nums transition-colors",
                isPaused
                  ? "text-amber-600 dark:text-amber-400"
                  : state === "critical"
                  ? "text-rose-600 dark:text-rose-400 animate-pulse"
                  : state === "warning"
                  ? "text-amber-600 dark:text-amber-400"
                  : "text-foreground"
              )}
            >
              {secs}
              <span className="text-xs font-bold text-muted-foreground ml-0.5">s</span>
            </span>
          )}
          <span className="text-[9px] font-extrabold uppercase tracking-widest text-muted-foreground mt-0.5">
            {isPaused ? "PAUSED" : isActive ? (isInfinite ? "THOẢI MÁI NÓI" : "NÓI NGAY") : "SẴN SÀNG"}
          </span>
        </div>
      </div>

      <div className="mt-2 flex items-center gap-1.5 text-[11px] font-medium text-muted-foreground">
        <span
          className={cn(
            "h-2 w-2 rounded-full",
            isPaused
              ? "bg-amber-500 animate-pulse"
              : isActive
              ? "bg-primary animate-ping"
              : "bg-emerald-500/60"
          )}
        />
        <span>{isInfinite ? "∞ Không giới hạn" : `${timerLimitMs / 1000}s limit`}</span>
        <span>•</span>
        <span>
          {isPaused
            ? "Đang tạm dừng suy nghĩ"
            : isInfinite
            ? "Tự do suy nghĩ và phát âm"
            : isActive
            ? "Đang đếm ngược"
            : "Chờ bắt đầu nói"}
        </span>
      </div>
    </div>
  );
}
