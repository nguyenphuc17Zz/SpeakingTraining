"use client";

import React from "react";
import { RecordingState } from "../types";

interface AudioVisualizerProps {
  state: RecordingState;
  volumeLevel: number;
  isUserSpeaking: boolean;
}

export function AudioVisualizer({ state, volumeLevel, isUserSpeaking }: AudioVisualizerProps) {
  // Generate 24 animated wave bars
  const barsCount = 20;

  return (
    <div className="flex flex-col items-center justify-center p-6 space-y-4">
      {/* Central Animated Orb */}
      <div className="relative flex items-center justify-center">
        {/* Outer Glow Ring */}
        <div
          className={`absolute rounded-full transition-all duration-300 pointer-events-none ${
            state === "listening" && isUserSpeaking
              ? "h-40 w-40 bg-emerald-500/20 blur-xl scale-125"
              : state === "ai_speaking"
              ? "h-40 w-40 bg-primary/30 blur-2xl animate-pulse"
              : state === "ai_thinking" || state === "processing_stt"
              ? "h-36 w-36 bg-aizome-500/20 blur-xl animate-spin"
              : "h-32 w-32 bg-muted/40 blur-md"
          }`}
        />

        {/* Middle Pulse Ring */}
        <div
          className={`relative h-28 w-28 rounded-full border flex items-center justify-center transition-all duration-300 ${
            state === "listening" && isUserSpeaking
              ? "border-emerald-400/80 bg-emerald-950/40 shadow-lg shadow-emerald-500/20 scale-110"
              : state === "ai_speaking"
              ? "border-primary/80 bg-primary/20 shadow-lg shadow-primary/20 scale-105 animate-bounce"
              : state === "ai_thinking" || state === "processing_stt"
              ? "border-aizome-400/60 bg-aizome-950/30"
              : "border-border bg-card/60"
          }`}
        >
          {/* Inner Core Icon / Glyph */}
          <span className="text-2xl font-bold select-none">
            {state === "listening" && isUserSpeaking ? (
              <span className="text-emerald-400 animate-pulse">🎙️</span>
            ) : state === "listening" ? (
              <span className="text-emerald-400/80">👂</span>
            ) : state === "processing_stt" ? (
              <span className="text-amber-400 animate-spin">⚡</span>
            ) : state === "ai_thinking" ? (
              <span className="text-aizome-400 animate-pulse">✨</span>
            ) : state === "ai_speaking" ? (
              <span className="text-primary animate-pulse">🌸</span>
            ) : state === "paused" ? (
              <span className="text-muted-foreground">⏸️</span>
            ) : (
              <span className="text-muted-foreground">🎙️</span>
            )}
          </span>
        </div>
      </div>

      {/* Real-time Dynamic Waveform Bars */}
      <div className="flex items-center justify-center gap-1.5 h-10 w-full max-w-xs px-4">
        {Array.from({ length: barsCount }).map((_, i) => {
          let heightPercent = 15;
          if (state === "listening") {
            const factor = Math.sin((i / barsCount) * Math.PI);
            heightPercent = Math.max(15, Math.min(100, volumeLevel * factor * 220 + (isUserSpeaking ? 25 : 5)));
          } else if (state === "ai_speaking") {
            const timeOffset = (Date.now() / 200 + i * 0.5) % Math.PI;
            heightPercent = 30 + Math.abs(Math.sin(timeOffset)) * 60;
          } else if (state === "ai_thinking" || state === "processing_stt") {
            const wave = (i % 4) * 20 + 20;
            heightPercent = wave;
          }

          let barColor = "bg-slate-700";
          if (state === "listening" && isUserSpeaking) {
            barColor = "bg-gradient-to-t from-emerald-600 to-emerald-400";
          } else if (state === "listening") {
            barColor = "bg-emerald-500/40";
          } else if (state === "ai_speaking") {
            barColor = "bg-gradient-to-t from-primary to-aizome-400";
          } else if (state === "processing_stt") {
            barColor = "bg-amber-400/60";
          } else if (state === "ai_thinking") {
            barColor = "bg-aizome-400/60";
          }

          return (
            <div
              key={i}
              className={`w-1 rounded-full transition-all duration-75 ${barColor}`}
              style={{ height: `${heightPercent}%` }}
            />
          );
        })}
      </div>
    </div>
  );
}
