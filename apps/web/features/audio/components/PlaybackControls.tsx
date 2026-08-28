"use client";

import React from "react";
import { Repeat } from "lucide-react";
import { AudioPlayButton } from "./AudioPlayButton";
import { SpeedSelector } from "./SpeedSelector";
import { PlaybackState } from "@/types/audio";

interface PlaybackControlsProps {
  state: PlaybackState;
  currentTime: number;
  duration: number;
  speed: number;
  isLooping: boolean;
  onPlay: () => void;
  onPause: () => void;
  onSeek: (seconds: number) => void;
  onSpeedChange: (speed: number) => void;
  onToggleLoop: () => void;
  className?: string;
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
}

export function PlaybackControls({
  state,
  currentTime,
  duration,
  speed,
  isLooping,
  onPlay,
  onPause,
  onSeek,
  onSpeedChange,
  onToggleLoop,
  className = "",
}: PlaybackControlsProps) {
  const progressPercent = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <div className={`flex flex-col gap-2 p-3 rounded-xl bg-card/90 border border-border shadow-md ${className}`}>
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <AudioPlayButton
            state={state}
            onPlay={onPlay}
            onPause={onPause}
            size="sm"
            variant="primary"
          />

          <button
            type="button"
            onClick={onToggleLoop}
            className={`p-1.5 rounded-lg border transition-all ${
              isLooping
                ? "bg-primary/20 text-primary border-primary/40"
                : "bg-background text-muted-foreground border-border hover:text-foreground"
            }`}
            title="Lặp lại câu"
          >
            <Repeat className="h-3.5 w-3.5" />
          </button>
        </div>

        {/* Timeline Slider */}
        <div className="flex-1 flex items-center gap-2">
          <span className="text-[11px] font-mono text-muted-foreground w-10 text-right">
            {formatTime(currentTime)}
          </span>
          <div className="relative flex-1 group">
            <input
              type="range"
              min={0}
              max={duration || 100}
              step={0.1}
              value={currentTime}
              onChange={(e) => onSeek(parseFloat(e.target.value))}
              className="w-full h-1.5 bg-background rounded-lg appearance-none cursor-pointer accent-primary"
            />
          </div>
          <span className="text-[11px] font-mono text-muted-foreground w-10">
            {formatTime(duration)}
          </span>
        </div>

        {/* Speed Selector */}
        <SpeedSelector value={speed} onChange={onSpeedChange} size="sm" />
      </div>
    </div>
  );
}
