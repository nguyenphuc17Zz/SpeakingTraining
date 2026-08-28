"use client";

import React from "react";
import { Mic, Radio, Volume2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface LiveSpeechPreviewCardProps {
  isRecording: boolean;
  volumeLevel: number;
  liveTranscript: string;
  interimTranscript: string;
  targetText?: string;
}

export function LiveSpeechPreviewCard({
  isRecording,
  volumeLevel,
  liveTranscript,
  interimTranscript,
  targetText,
}: LiveSpeechPreviewCardProps) {
  if (!isRecording) return null;

  const displayLive = liveTranscript || interimTranscript;

  return (
    <div className="p-4 rounded-2xl bg-card/95 border border-primary/50 washi-texture backdrop-blur-2xl shadow-enso ring-1 ring-primary/30 space-y-3 animate-in fade-in zoom-in-95 duration-150">
      {/* Recording Header with Live VU Meter Bar */}
      <div className="flex items-center justify-between gap-2 border-b border-primary/20 pb-2">
        <div className="flex items-center gap-2">
          <div className="relative flex items-center justify-center">
            <span className="w-3 h-3 rounded-full bg-primary animate-ping absolute" />
            <span className="w-2.5 h-2.5 rounded-full bg-primary" />
          </div>
          <span className="text-xs font-bold text-primary font-sans tracking-wide">
            Đang Thu Âm (Live Voice Preview)...
          </span>
        </div>

        {/* Volume Wave Level */}
        <div className="flex items-center gap-1">
          {[0.2, 0.4, 0.6, 0.8, 1.0].map((threshold, idx) => {
            const isActive = volumeLevel >= threshold * 0.7;
            return (
              <div
                key={idx}
                className={cn(
                  "w-1 rounded-full transition-all duration-75",
                  isActive ? "bg-primary shadow-xs" : "bg-muted"
                )}
                style={{
                  height: isActive ? `${Math.max(6, (idx + 1) * 4)}px` : "4px",
                }}
              />
            );
          })}
        </div>
      </div>

      {/* Real-time Subtitle Floating Area */}
      <div className="p-3 rounded-xl bg-background/90 border border-border min-h-[56px] flex flex-col justify-center space-y-1">
        {displayLive ? (
          <p className="font-jp text-base text-foreground font-bold leading-relaxed tracking-wide">
            <span>{liveTranscript}</span>
            <span className="text-primary italic opacity-90 animate-pulse ml-1">
              {interimTranscript}
            </span>
          </p>
        ) : (
          <p className="text-xs text-muted-foreground font-sans italic flex items-center gap-1.5">
            <Radio className="h-3.5 w-3.5 text-primary animate-spin" />
            <span>Hãy phát âm câu tiếng Nhật vào Microphone...</span>
          </p>
        )}
      </div>
    </div>
  );
}
