"use client";

import React from "react";
import { AlertCircle } from "lucide-react";
import { useAudioLevelMeter } from "../hooks/useAudioLevelMeter";

interface AudioLevelMeterProps {
  volume: number;
  showClippingWarning?: boolean;
  className?: string;
}

export function AudioLevelMeter({
  volume,
  showClippingWarning = true,
  className = "",
}: AudioLevelMeterProps) {
  const { isClipping, levelCategory } = useAudioLevelMeter(volume);

  const getMeterColor = () => {
    if (isClipping) return "bg-rose-500";
    if (levelCategory === "good") return "bg-emerald-500";
    if (levelCategory === "loud") return "bg-amber-500";
    if (levelCategory === "quiet") return "bg-indigo-400";
    return "bg-slate-700";
  };

  const percentage = Math.min(100, Math.max(0, volume * 100));

  return (
    <div className={`space-y-1.5 ${className}`}>
      <div className="flex items-center justify-between text-[10px] text-muted-foreground">
        <span>Âm lượng micro</span>
        <span className="font-mono uppercase font-semibold">
          {levelCategory}
        </span>
      </div>

      <div className="w-full h-1.5 rounded-full bg-background border border-border overflow-hidden">
        <div
          className={`h-full transition-all duration-75 ${getMeterColor()}`}
          style={{ width: `${percentage}%` }}
        />
      </div>

      {isClipping && showClippingWarning && (
        <div className="flex items-center gap-1 text-[10px] text-rose-400 font-medium animate-pulse">
          <AlertCircle className="h-3 w-3 shrink-0" />
          <span>Vỡ tiếng (Clipping) — hãy nói xa micro hơn</span>
        </div>
      )}
    </div>
  );
}
