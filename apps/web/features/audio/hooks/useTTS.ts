"use client";

import { useCallback, useState } from "react";
import { audioApi } from "@/features/audio/services/audio-api";
import { TTSState } from "@/types/audio";
import { useAudioPlayer } from "./useAudioPlayer";

export interface UseTTSOptions {
  onPlaybackStarted?: () => void;
  onPlaybackEnded?: () => void;
  onError?: (err: Error) => void;
}

export function useTTS(options: UseTTSOptions = {}) {
  const [state, setState] = useState<TTSState>("idle");
  const [error, setError] = useState<string | null>(null);

  const player = useAudioPlayer({
    onPlaybackStarted: () => {
      setState("playing");
      options.onPlaybackStarted?.();
    },
    onPlaybackEnded: () => {
      setState("completed");
      options.onPlaybackEnded?.();
    },
    onError: (err) => {
      setState("error");
      setError(err.message);
      options.onError?.(err);
    },
  });

  const previewVoice = useCallback(
    async (
      text: string,
      voiceId: string,
      provider = "voicevox",
      speed = 1.0,
      pitch = 0.0,
      style?: string
    ) => {
      setState("generating");
      setError(null);
      try {
        const res = await audioApi.previewVoice(text, voiceId, provider, speed, pitch, style);
        if (res.audio_base64) {
          setState("ready");
          await player.playBase64(res.audio_base64, res.format, speed);
        } else {
          setState("completed");
        }
      } catch (err: any) {
        console.error("[useTTS] Preview error:", err);
        setState("error");
        setError(err.message || "Không thể tổng hợp giọng nói.");
        options.onError?.(err);
      }
    },
    [options, player]
  );

  const stop = useCallback(() => {
    player.stop();
    setState("idle");
  }, [player]);

  return {
    state,
    isGenerating: state === "generating",
    isPlaying: state === "playing",
    error,
    previewVoice,
    stop,
    playbackState: player.state,
  };
}
