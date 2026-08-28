"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { PlaybackState } from "@/types/audio";

export interface UseAudioPlayerOptions {
  onPlaybackStarted?: () => void;
  onPlaybackEnded?: () => void;
  onError?: (err: Error) => void;
  onTimeUpdate?: (currentTime: number, duration: number) => void;
}

export function useAudioPlayer(options: UseAudioPlayerOptions = {}) {
  const [state, setState] = useState<PlaybackState>("idle");
  const [currentAudioUrl, setCurrentAudioUrl] = useState<string | null>(null);
  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [playbackSpeed, setPlaybackSpeedState] = useState(1.0);
  const [isLooping, setIsLooping] = useState(false);

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const activeBlobUrlRef = useRef<string | null>(null);

  const cleanupActiveBlob = useCallback(() => {
    if (activeBlobUrlRef.current) {
      URL.revokeObjectURL(activeBlobUrlRef.current);
      activeBlobUrlRef.current = null;
    }
  }, []);

  const stop = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current.src = "";
    }
    cleanupActiveBlob();
    setCurrentAudioUrl(null);
    setCurrentTime(0);
    setState("stopped");
  }, [cleanupActiveBlob]);

  const pause = useCallback(() => {
    if (audioRef.current && state === "playing") {
      audioRef.current.pause();
      setState("paused");
    }
  }, [state]);

  const resume = useCallback(async () => {
    if (audioRef.current && state === "paused") {
      try {
        await audioRef.current.play();
        setState("playing");
      } catch (err: any) {
        setState("error");
        options.onError?.(err);
      }
    }
  }, [options, state]);

  const seek = useCallback((seconds: number) => {
    if (audioRef.current) {
      audioRef.current.currentTime = seconds;
      setCurrentTime(seconds);
    }
  }, []);

  const setPlaybackSpeed = useCallback((speed: number) => {
    setPlaybackSpeedState(speed);
    if (audioRef.current) {
      audioRef.current.playbackRate = speed;
    }
  }, []);

  const playBase64 = useCallback(
    async (base64Data: string, format = "wav", speed = playbackSpeed): Promise<void> => {
      stop();
      if (!base64Data) return;

      setState("loading");
      try {
        const byteCharacters = atob(base64Data);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: `audio/${format}` });
        const objectUrl = URL.createObjectURL(blob);

        activeBlobUrlRef.current = objectUrl;
        setCurrentAudioUrl(objectUrl);

        if (!audioRef.current) {
          audioRef.current = new Audio();
        }

        const audio = audioRef.current;
        audio.src = objectUrl;
        audio.playbackRate = speed;
        audio.loop = isLooping;

        audio.onloadedmetadata = () => {
          setDuration(audio.duration || 0);
          setState("ready");
        };

        audio.ontimeupdate = () => {
          setCurrentTime(audio.currentTime);
          options.onTimeUpdate?.(audio.currentTime, audio.duration || 0);
        };

        audio.onplay = () => {
          setState("playing");
          options.onPlaybackStarted?.();
        };

        audio.onended = () => {
          setState("completed");
          cleanupActiveBlob();
          setCurrentAudioUrl(null);
          options.onPlaybackEnded?.();
        };

        audio.onerror = () => {
          setState("error");
          const err = new Error("Audio playback failed");
          options.onError?.(err);
        };

        await audio.play();
      } catch (err: any) {
        console.error("[useAudioPlayer] Failed to play base64 audio:", err);
        setState("error");
        options.onError?.(err);
      }
    },
    [cleanupActiveBlob, isLooping, options, playbackSpeed, stop]
  );

  const playUrl = useCallback(
    async (url: string, speed = playbackSpeed): Promise<void> => {
      stop();
      if (!url) return;

      setState("loading");
      try {
        if (!audioRef.current) {
          audioRef.current = new Audio();
        }

        const audio = audioRef.current;
        audio.src = url;
        audio.playbackRate = speed;
        audio.loop = isLooping;

        audio.onloadedmetadata = () => {
          setDuration(audio.duration || 0);
          setState("ready");
        };

        audio.ontimeupdate = () => {
          setCurrentTime(audio.currentTime);
          options.onTimeUpdate?.(audio.currentTime, audio.duration || 0);
        };

        audio.onplay = () => {
          setState("playing");
          options.onPlaybackStarted?.();
        };

        audio.onended = () => {
          setState("completed");
          options.onPlaybackEnded?.();
        };

        audio.onerror = () => {
          setState("error");
          options.onError?.(new Error("Audio playback failed"));
        };

        await audio.play();
      } catch (err: any) {
        console.error("[useAudioPlayer] Failed to play url:", err);
        setState("error");
        options.onError?.(err);
      }
    },
    [isLooping, options, playbackSpeed, stop]
  );

  // Auto cleanup on unmount
  useEffect(() => {
    return () => {
      stop();
    };
  }, [stop]);

  return {
    state,
    isPlaying: state === "playing",
    isPaused: state === "paused",
    currentTime,
    duration,
    playbackSpeed,
    isLooping,
    currentAudioUrl,
    playBase64,
    playUrl,
    pause,
    resume,
    stop,
    seek,
    setPlaybackSpeed,
    setIsLooping,
  };
}
