"use client";

import React from "react";

interface RecordingWaveformProps {
  volume: number;
  isRecording: boolean;
  barCount?: number;
  className?: string;
}

export function RecordingWaveform({
  volume,
  isRecording,
  barCount = 16,
  className = "",
}: RecordingWaveformProps) {
  const bars = Array.from({ length: barCount }, (_, i) => {
    if (!isRecording) return 15;
    // Add jitter and wave variance to the active volume
    const seed = Math.sin((i / barCount) * Math.PI) * 0.8 + 0.2;
    const baseHeight = Math.max(10, volume * 100 * seed);
    return Math.min(100, Math.round(baseHeight));
  });

  return (
    <div className={`flex items-center justify-center gap-1 h-8 px-3 rounded-xl bg-background/80 border border-border ${className}`}>
      {bars.map((height, idx) => (
        <div
          key={idx}
          className={`w-1 rounded-full transition-all duration-75 ${
            isRecording
              ? "bg-gradient-to-t from-rose-500 to-indigo-400"
              : "bg-slate-700"
          }`}
          style={{ height: `${height}%` }}
        />
      ))}
    </div>
  );
}
