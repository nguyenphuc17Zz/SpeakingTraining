"use client";

import React from "react";
import { LevelProgressInfo } from "../types/game";
import { Sparkles } from "lucide-react";

interface XPBarProps {
  levelProgress: LevelProgressInfo;
  className?: string;
  showLabels?: boolean;
}

export const XPBar: React.FC<XPBarProps> = ({
  levelProgress,
  className = "",
  showLabels = true,
}) => {
  const percent = Math.min(100, Math.max(0, Math.round(levelProgress.progress_ratio * 100)));

  return (
    <div className={`space-y-1.5 ${className}`}>
      {showLabels && (
        <div className="flex items-center justify-between text-xs font-semibold">
          <div className="flex items-center gap-1.5 text-foreground">
            <span className="font-bold text-primary font-jp">Lv. {levelProgress.level}</span>
            <span className="text-muted-foreground">→</span>
            <span className="text-muted-foreground">Lv. {levelProgress.level + 1}</span>
          </div>
          <div className="text-muted-foreground font-mono text-[11px]">
            <span className="text-foreground font-bold">{levelProgress.current_level_xp.toLocaleString()}</span>
            {" / "}
            <span>{levelProgress.next_level_xp.toLocaleString()} XP</span>
            <span className="text-primary font-bold ml-1.5">({percent}%)</span>
          </div>
        </div>
      )}

      {/* Progress Track */}
      <div className="relative h-3.5 w-full bg-card/90 rounded-full border border-border/80 p-0.5 overflow-hidden shadow-inner">
        <div
          className="h-full rounded-full bg-gradient-to-r from-primary via-primary/80 to-kintsugi-500 transition-all duration-500 ease-out shadow-sm shadow-primary/30"
          style={{ width: `${percent}%` }}
        />
        {/* Animated sheen highlight */}
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/15 to-transparent animate-pulse pointer-events-none" />
      </div>
    </div>
  );
};
