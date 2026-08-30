"use client";

import React from "react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export interface MoraToken {
  index: number;
  mora: string;
  tone: "H" | "L" | string;
  is_downstep?: boolean;
}

interface PitchAccentVisualizerProps {
  reading: string;
  moraBreakdown?: MoraToken[];
  pitchPattern?: string[];
  downstepIndex?: number;
  downstepNotation?: string;
  accentType?: string;
  className?: string;
}

export function PitchAccentVisualizer({
  reading,
  moraBreakdown,
  pitchPattern = [],
  downstepIndex = 0,
  downstepNotation,
  accentType,
  className,
}: PitchAccentVisualizerProps) {
  // If no moraBreakdown is passed, generate fallback tokens from reading
  const tokens: MoraToken[] = React.useMemo(() => {
    if (moraBreakdown && moraBreakdown.length > 0) return moraBreakdown;
    if (!reading) return [];

    const moras: string[] = [];
    let i = 0;
    const chars = Array.from(reading);
    while (i < chars.length) {
      const c = chars[i];
      if (i + 1 < chars.length && "ゃゅょャュョぁぃぅぇぉァィゥェォ".includes(chars[i + 1])) {
        moras.push(c + chars[i + 1]);
        i += 2;
      } else {
        moras.push(c);
        i += 1;
      }
    }

    return moras.map((m, idx) => {
      let tone = "L";
      if (idx < pitchPattern.length) {
        tone = pitchPattern[idx].toUpperCase();
      } else if (downstepIndex === 0) {
        tone = idx === 0 && moras.length > 1 ? "L" : "H";
      } else if (downstepIndex === 1) {
        tone = idx === 0 ? "H" : "L";
      } else if (idx + 1 <= downstepIndex) {
        tone = idx === 0 ? "L" : "H";
      } else {
        tone = "L";
      }

      return {
        index: idx + 1,
        mora: m,
        tone: tone as "H" | "L",
        is_downstep: downstepIndex > 0 && idx + 1 === downstepIndex,
      };
    });
  }, [moraBreakdown, reading, pitchPattern, downstepIndex]);

  if (!tokens.length) return null;

  return (
    <div
      className={cn(
        "rounded-2xl border border-sky-500/20 bg-sky-500/5 dark:bg-sky-950/20 p-3.5 space-y-3 washi-texture",
        className
      )}
    >
      {/* Header Info */}
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-1.5 font-bold text-foreground">
          <span className="text-sky-600 dark:text-sky-400">📈 Sơ Đồ Cao Độ Tokyo (NHK Notation)</span>
          {accentType && (
            <Badge variant="fuji" size="sm" className="text-[10px] font-mono">
              {accentType}
            </Badge>
          )}
        </div>

        {downstepNotation && (
          <span className="font-jp font-black text-sm text-primary tracking-wider" title="Ký hiệu hạ giọng NHK">
            {downstepNotation}
          </span>
        )}
      </div>

      {/* NHK Pitch Beam & Continuous Step Visualizer */}
      <div className="flex items-end justify-center gap-1 sm:gap-2 pt-4 pb-2 select-none overflow-x-auto">
        {tokens.map((t, idx) => {
          const isHigh = t.tone === "H";
          const isDownstep = t.is_downstep;

          return (
            <div key={idx} className="flex flex-col items-center flex-1 max-w-[64px] min-w-[40px] relative group">
              {/* Downstep Nucleus Marker */}
              {isDownstep && (
                <div className="absolute -top-3.5 text-rose-500 font-bold text-xs animate-bounce" title="Điểm rơi cao độ (Accent Nucleus)">
                  ꜜ
                </div>
              )}

              {/* Tone Label */}
              <span
                className={cn(
                  "text-[10px] font-bold font-mono transition-colors",
                  isHigh ? "text-rose-500" : "text-sky-500"
                )}
              >
                {isHigh ? "H (Cao)" : "L (Thấp)"}
              </span>

              {/* Pitch Level Step Bar */}
              <div
                className={cn(
                  "w-full rounded-xl border transition-all duration-300 flex flex-col items-center justify-between p-1.5 shadow-2xs font-jp",
                  isHigh
                    ? "h-14 bg-rose-500/15 border-rose-500/40 text-rose-700 dark:text-rose-300 -translate-y-2.5 shadow-rose-500/10"
                    : "h-9 bg-sky-500/15 border-sky-500/40 text-sky-700 dark:text-sky-300 shadow-sky-500/10"
                )}
              >
                <span className="text-xs font-black">{t.mora}</span>
                <span className="text-[9px] font-mono opacity-60">#{t.index}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
