"use client";

import React, { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Clock, Play, Pause, Volume2, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

interface MoraMetronomeProps {
  defaultBpm?: number;
  activeMoraCount?: number;
  className?: string;
}

export function MoraMetronomeControl({
  defaultBpm = 130,
  activeMoraCount = 4,
  className,
}: MoraMetronomeProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [bpm, setBpm] = useState(defaultBpm);
  const [beatIndex, setBeatIndex] = useState(0);

  const audioCtxRef = useRef<AudioContext | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const playClick = (isFirstBeat: boolean) => {
    try {
      if (!audioCtxRef.current) {
        const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
        audioCtxRef.current = new AudioCtx();
      }
      const ctx = audioCtxRef.current;
      if (ctx.state === "suspended") {
        ctx.resume();
      }

      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = "sine";
      osc.frequency.setValueAtTime(isFirstBeat ? 900 : 600, ctx.currentTime);

      gain.gain.setValueAtTime(0.12, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.05);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + 0.05);
    } catch (e) {
      // AudioContext might be blocked until user interacts
    }
  };

  useEffect(() => {
    if (!isPlaying) {
      if (timerRef.current) clearInterval(timerRef.current);
      setBeatIndex(0);
      return;
    }

    const intervalMs = (60 / bpm) * 1000;
    timerRef.current = setInterval(() => {
      setBeatIndex((prev) => {
        const next = (prev + 1) % activeMoraCount;
        playClick(next === 0);
        return next;
      });
    }, intervalMs);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isPlaying, bpm, activeMoraCount]);

  const togglePlay = () => {
    setIsPlaying((prev) => !prev);
  };

  return (
    <div
      className={cn(
        "flex flex-wrap items-center justify-between gap-2.5 p-2.5 rounded-2xl bg-muted/40 border border-border/70 text-xs",
        className
      )}
    >
      <div className="flex items-center gap-2">
        <Button
          size="sm"
          variant={isPlaying ? "sakura" : "outline"}
          onClick={togglePlay}
          className="h-7 px-2.5 text-xs font-bold gap-1 shadow-2xs"
          title="Bật máy đếm nhịp phách"
        >
          {isPlaying ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5 ml-0.5" />}
          <span>{isPlaying ? "Dừng Nhịp" : "Máy Gõ Phách (Metronome)"}</span>
        </Button>

        <span className="text-[11px] font-mono text-muted-foreground font-semibold">
          {bpm} BPM
        </span>
      </div>

      {/* Visual Pulsing Mora Beat Dots */}
      <div className="flex items-center gap-1.5 ml-auto">
        {Array.from({ length: activeMoraCount }).map((_, idx) => {
          const isCurrent = isPlaying && beatIndex === idx;
          return (
            <div
              key={idx}
              className={cn(
                "h-3 w-3 rounded-full border transition-all duration-100 flex items-center justify-center text-[8px] font-mono font-bold",
                isCurrent
                  ? "bg-primary border-primary text-primary-foreground scale-125 shadow-xs shadow-primary/30"
                  : "bg-card border-border/80 text-muted-foreground"
              )}
            >
              {idx + 1}
            </div>
          );
        })}
      </div>
    </div>
  );
}
