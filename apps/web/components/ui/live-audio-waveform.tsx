"use client";

import React, { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

interface LiveAudioWaveformProps {
  isRecording: boolean;
  volume?: number;
  barCount?: number;
  className?: string;
  showRecBadge?: boolean;
}

export function LiveAudioWaveform({
  isRecording,
  volume = 0,
  barCount = 20,
  className,
  showRecBadge = true,
}: LiveAudioWaveformProps) {
  const [frame, setFrame] = useState(0);

  useEffect(() => {
    if (!isRecording) return;
    let animId: number;
    let lastTime = performance.now();

    const loop = (now: number) => {
      if (now - lastTime > 60) {
        setFrame((f) => (f + 1) % 360);
        lastTime = now;
      }
      animId = requestAnimationFrame(loop);
    };
    animId = requestAnimationFrame(loop);

    return () => cancelAnimationFrame(animId);
  }, [isRecording]);

  const effectiveVolume = Math.max(0.15, Math.min(1, volume || 0.4));

  const bars = Array.from({ length: barCount }, (_, i) => {
    if (!isRecording) return 15;

    // Harmonized double-sine wave envelope with phase drift
    const normalizedIndex = i / (barCount - 1);
    const centerDist = 1 - Math.abs(normalizedIndex - 0.5) * 2;
    const wave = Math.sin((i * 18 + frame * 12) * (Math.PI / 180));
    const wave2 = Math.cos((i * 30 - frame * 8) * (Math.PI / 180));
    const combined = Math.abs(wave * 0.6 + wave2 * 0.4);

    const heightPct = Math.round(
      Math.max(12, Math.min(100, centerDist * combined * effectiveVolume * 120 + 12))
    );
    return heightPct;
  });

  return (
    <div
      className={cn(
        "flex items-center justify-between gap-3 px-3 py-1.5 rounded-xl border transition-all duration-300",
        isRecording
          ? "bg-rose-500/10 border-rose-500/30 shadow-xs"
          : "bg-muted/40 border-border/60",
        className
      )}
    >
      {showRecBadge && (
        <div className="flex items-center gap-1.5 shrink-0">
          <span
            className={cn(
              "h-2 w-2 rounded-full",
              isRecording
                ? "bg-rose-500 animate-ping"
                : "bg-muted-foreground/40"
            )}
          />
          <span
            className={cn(
              "text-[10px] font-mono font-extrabold uppercase tracking-wider",
              isRecording ? "text-rose-500 font-bold" : "text-muted-foreground"
            )}
          >
            {isRecording ? "REC" : "MIC"}
          </span>
        </div>
      )}

      {/* Reactive Bars */}
      <div className="flex items-center justify-center gap-1 h-5 flex-1 max-w-[280px] mx-auto">
        {bars.map((height, idx) => (
          <div
            key={idx}
            className={cn(
              "w-1 rounded-full transition-all duration-75",
              isRecording
                ? "bg-gradient-to-t from-rose-500 via-amber-400 to-emerald-400 shadow-[0_0_6px_rgba(244,63,94,0.4)]"
                : "bg-muted-foreground/25"
            )}
            style={{
              height: `${height}%`,
              transform: isRecording ? "scaleY(1)" : "scaleY(0.6)",
            }}
          />
        ))}
      </div>
    </div>
  );
}
