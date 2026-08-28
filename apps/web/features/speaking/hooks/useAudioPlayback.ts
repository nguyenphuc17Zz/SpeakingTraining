"use client";

import { useCallback } from "react";
import { useAudioPlayer, UseAudioPlayerOptions } from "@/features/audio/hooks/useAudioPlayer";

export interface UseAudioPlaybackOptions extends UseAudioPlayerOptions {}

export function useAudioPlayback(options: UseAudioPlaybackOptions = {}) {
  const player = useAudioPlayer(options);

  return {
    isPlaying: player.isPlaying,
    currentAudioUrl: player.currentAudioUrl,
    playAudioBase64: player.playBase64,
    playAudioUrl: player.playUrl,
    stopPlayback: player.stop,
  };
}
