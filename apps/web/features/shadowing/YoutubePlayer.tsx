"use client";

import React, { useEffect, useRef, useState } from "react";
import { Play, Pause, RotateCcw, Volume2, AlertCircle } from "lucide-react";

interface YoutubePlayerProps {
  videoId: string;
  onTimeUpdate?: (currentTime: number) => void;
  loopRange?: { start: number; end: number } | null;
  loopGap?: number;
  pauseAtTime?: number | null;
  onPauseAtTimeReached?: () => void;
  playbackSpeed?: number;
  autoPlay?: boolean;
}

export interface YoutubePlayerRef {
  play: () => void;
  pause: () => void;
  seekTo: (seconds: number) => void;
  setSpeed: (speed: number) => void;
  getCurrentTime: () => number;
}

export const YoutubePlayer = React.forwardRef<YoutubePlayerRef, YoutubePlayerProps>(
  ({ videoId, onTimeUpdate, loopRange, loopGap = 0, pauseAtTime = null, onPauseAtTimeReached, playbackSpeed = 1.0, autoPlay = false }, ref) => {
    const containerRef = useRef<HTMLDivElement>(null);
    const playerInstanceRef = useRef<any>(null);
    const timeIntervalRef = useRef<NodeJS.Timeout | null>(null);
    const isPausingForGapRef = useRef(false);
    const pauseTriggeredRef = useRef(false);

    const [isReady, setIsReady] = useState(false);
    const [isPlaying, setIsPlaying] = useState(false);
    const [hasError, setHasError] = useState(false);
    const [duration, setDuration] = useState(0);

    // Expose imperative player handles
    React.useImperativeHandle(ref, () => ({
      play: () => {
        pauseTriggeredRef.current = false;
        if (playerInstanceRef.current?.playVideo) {
          playerInstanceRef.current.playVideo();
        }
      },
      pause: () => {
        if (playerInstanceRef.current?.pauseVideo) {
          playerInstanceRef.current.pauseVideo();
        }
      },
      seekTo: (seconds: number) => {
        pauseTriggeredRef.current = false;
        if (playerInstanceRef.current?.seekTo) {
          playerInstanceRef.current.seekTo(seconds, true);
        }
      },
      setSpeed: (speed: number) => {
        if (playerInstanceRef.current?.setPlaybackRate) {
          playerInstanceRef.current.setPlaybackRate(speed);
        }
      },
      getCurrentTime: () => {
        return playerInstanceRef.current?.getCurrentTime ? playerInstanceRef.current.getCurrentTime() : 0;
      },
    }));

    useEffect(() => {
      // 1. Load YouTube IFrame API Script if not present
      if (!window.YT) {
        const tag = document.createElement("script");
        tag.src = "https://www.youtube.com/iframe_api";
        const firstScriptTag = document.getElementsByTagName("script")[0];
        firstScriptTag?.parentNode?.insertBefore(tag, firstScriptTag);
      }

      const initPlayer = () => {
        if (!containerRef.current || !window.YT || !window.YT.Player) return;

        try {
          playerInstanceRef.current = new window.YT.Player(containerRef.current, {
            videoId,
            playerVars: {
              autoplay: autoPlay ? 1 : 0,
              controls: 1,
              modestbranding: 1,
              rel: 0,
              playsinline: 1,
              enablejsapi: 1,
              origin: typeof window !== "undefined" ? window.location.origin : "",
            },
            events: {
              onReady: (event: any) => {
                setIsReady(true);
                setDuration(event.target.getDuration());
                event.target.setPlaybackRate(playbackSpeed);
                if (autoPlay) {
                  event.target.playVideo();
                }
              },
              onStateChange: (event: any) => {
                // 1 = playing, 2 = paused, 0 = ended
                const playing = event.data === 1;
                setIsPlaying(playing);
                if (playing) {
                  pauseTriggeredRef.current = false;
                }
              },
              onError: (error: any) => {
                console.warn("[YoutubePlayer] Player error:", error);
                setHasError(true);
              },
            },
          });
        } catch (e) {
          console.warn("[YoutubePlayer] Initialization error:", e);
          setHasError(true);
        }
      };

      if (window.YT && window.YT.Player) {
        initPlayer();
      } else {
        window.onYouTubeIframeAPIReady = initPlayer;
      }

      return () => {
        if (timeIntervalRef.current) {
          clearInterval(timeIntervalRef.current);
        }
        if (playerInstanceRef.current?.destroy) {
          try {
            playerInstanceRef.current.destroy();
          } catch (e) {}
        }
      };
    }, [videoId]);

    // Reset pauseTriggeredRef when pauseAtTime changes
    useEffect(() => {
      pauseTriggeredRef.current = false;
    }, [pauseAtTime]);

    // Track playback time & handle exact pause & A-B looping
    useEffect(() => {
      if (timeIntervalRef.current) {
        clearInterval(timeIntervalRef.current);
      }

      if (isPlaying && playerInstanceRef.current) {
        timeIntervalRef.current = setInterval(() => {
          try {
            const current = playerInstanceRef.current.getCurrentTime();
            if (typeof current === "number") {
              onTimeUpdate?.(current);

              // Exact Pause-At-Time enforcement (for Repeat / Echoing mode & Single Segment Play)
              if (
                pauseAtTime !== null &&
                pauseAtTime !== undefined &&
                !pauseTriggeredRef.current &&
                current >= pauseAtTime - 0.08
              ) {
                pauseTriggeredRef.current = true;
                playerInstanceRef.current.pauseVideo();
                onPauseAtTimeReached?.();
              }

              // A-B Loop enforcement
              if (loopRange && loopRange.end > loopRange.start && !isPausingForGapRef.current) {
                if (current >= loopRange.end) {
                  if (loopGap && loopGap > 0) {
                    isPausingForGapRef.current = true;
                    playerInstanceRef.current.pauseVideo();
                    playerInstanceRef.current.seekTo(loopRange.start, true);
                    setTimeout(() => {
                      if (playerInstanceRef.current) {
                        playerInstanceRef.current.playVideo();
                      }
                      isPausingForGapRef.current = false;
                    }, loopGap * 1000);
                  } else {
                    playerInstanceRef.current.seekTo(loopRange.start, true);
                  }
                }
              }
            }
          } catch (e) {}
        }, 50);
      }

      return () => {
        if (timeIntervalRef.current) {
          clearInterval(timeIntervalRef.current);
        }
      };
    }, [isPlaying, loopRange, loopGap, pauseAtTime, onPauseAtTimeReached, onTimeUpdate]);

    // Update speed if prop changes
    useEffect(() => {
      if (playerInstanceRef.current?.setPlaybackRate) {
        playerInstanceRef.current.setPlaybackRate(playbackSpeed);
      }
    }, [playbackSpeed]);

    return (
      <div className="relative w-full aspect-video rounded-2xl overflow-hidden bg-background border border-border shadow-2xl">
        <div ref={containerRef} className="w-full h-full" />

        {hasError && (
          <div className="absolute inset-0 flex flex-col items-center justify-center p-6 bg-background/90 text-center space-y-2">
            <AlertCircle className="h-8 w-8 text-rose-400" />
            <p className="text-sm font-semibold text-foreground">
              Không thể tải trực tiếp YouTube Player
            </p>
            <p className="text-xs text-muted-foreground max-w-sm">
              Video có thể bị hạn chế phát nhúng. Bạn vẫn có thể xem transcript và luyện phát âm bình thường.
            </p>
          </div>
        )}
      </div>
    );
  }
);

YoutubePlayer.displayName = "YoutubePlayer";

declare global {
  interface Window {
    YT: any;
    onYouTubeIframeAPIReady: () => void;
  }
}
