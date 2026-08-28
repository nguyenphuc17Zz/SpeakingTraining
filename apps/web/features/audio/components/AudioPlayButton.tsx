"use client";

import React from "react";
import { Play, Pause, Loader2, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PlaybackState } from "@/types/audio";

interface AudioPlayButtonProps {
  state: PlaybackState;
  onPlay: () => void;
  onPause?: () => void;
  onReplay?: () => void;
  size?: "sm" | "md" | "lg";
  variant?: "primary" | "secondary" | "outline" | "ghost";
  label?: string;
  className?: string;
  disabled?: boolean;
}

export function AudioPlayButton({
  state,
  onPlay,
  onPause,
  onReplay,
  size = "md",
  variant = "outline",
  label,
  className = "",
  disabled = false,
}: AudioPlayButtonProps) {
  const isPlaying = state === "playing";
  const isLoading = state === "loading";
  const isCompleted = state === "completed";

  const handleClick = () => {
    if (isPlaying && onPause) {
      onPause();
    } else if (isCompleted && onReplay) {
      onReplay();
    } else {
      onPlay();
    }
  };

  const iconSizes = {
    sm: "h-3.5 w-3.5",
    md: "h-4 w-4",
    lg: "h-5 w-5",
  };

  return (
    <Button
      variant={isPlaying ? "primary" : variant}
      size={size}
      onClick={handleClick}
      disabled={disabled || isLoading}
      className={`transition-all duration-150 ${isPlaying ? "shadow-md shadow-primary/20" : ""} ${className}`}
    >
      {isLoading ? (
        <Loader2 className={`${iconSizes[size]} animate-spin ${label ? "mr-1.5" : ""}`} />
      ) : isPlaying ? (
        <Pause className={`${iconSizes[size]} ${label ? "mr-1.5" : ""}`} />
      ) : isCompleted ? (
        <RotateCcw className={`${iconSizes[size]} ${label ? "mr-1.5" : ""}`} />
      ) : (
        <Play className={`${iconSizes[size]} fill-current ${label ? "mr-1.5" : ""}`} />
      )}
      {label && <span>{label}</span>}
    </Button>
  );
}
