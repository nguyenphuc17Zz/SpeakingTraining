"use client";

import React from "react";

interface Props {
  remainingMs: number;
  timerLimitMs: number;
  progress: number; // 0-1
  state: "normal" | "warning" | "critical";
  isActive: boolean;
}

export function ReflexTimer({ remainingMs, timerLimitMs, progress, state, isActive }: Props) {
  const pct = Math.max(0, Math.min(1, progress));
  const circumference = 2 * Math.PI * 44;
  const offset = circumference * (1 - pct);
  const color =
    state === "critical" ? "stroke-red-500" : state === "warning" ? "stroke-amber-500" : "stroke-primary";
  const bgColor =
    state === "critical" ? "bg-red-500/10 border-red-500/20" : state === "warning" ? "bg-amber-500/10 border-amber-500/20" : "bg-primary/5 border-primary/10";

  const secs = (remainingMs / 1000).toFixed(1);

  // Respect prefers-reduced-motion: linear bar fallback + disable animation
  return (
    <div
      className={`relative flex flex-col items-center gap-2 rounded-2xl border p-4 ${bgColor} transition-colors`}
      role="progressbar"
      aria-valuenow={Math.round(pct * 100)}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={`Timer ${secs} seconds remaining`}
    >
      <div className="relative h-[112px] w-[112px]">
        <svg className="h-full w-full -rotate-90" viewBox="0 0 100 100" aria-hidden="true">
          <circle cx="50" cy="50" r="44" fill="none" strokeWidth="8" className="stroke-muted/30" />
          <circle
            cx="50"
            cy="50"
            r="44"
            fill="none"
            strokeWidth="8"
            strokeLinecap="round"
            className={`${color} motion-safe:transition-all motion-safe:duration-100 motion-reduce:transition-none`}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{ transition: "stroke-dashoffset 0.1s linear" }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span
            className={`text-2xl font-black tabular-nums ${state === "critical" ? "text-red-600" : state === "warning" ? "text-amber-600" : "text-foreground"}`}
            aria-live="polite"
          >
            {secs}s
          </span>
          <span className="text-[10px] font-bold tracking-widest text-muted-foreground">REMAINING</span>
        </div>
      </div>
      {/* Linear fallback for reduced-motion / narrow */}
      <div className="hidden motion-reduce:block w-full h-1.5 rounded-full bg-muted overflow-hidden" aria-hidden="true">
        <div className={`h-full ${state === "critical" ? "bg-red-500" : state === "warning" ? "bg-amber-500" : "bg-primary"}`} style={{ width: `${pct * 100}%` }} />
      </div>
      <div className="text-xs font-medium text-muted-foreground">
        {timerLimitMs / 1000}s limit • {isActive ? "● Listening" : "○ Idle"}
      </div>
    </div>
  );
}
