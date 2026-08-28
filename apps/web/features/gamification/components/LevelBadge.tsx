"use client";

import React from "react";
import { Swords, Shield, Award, Sparkles, Flame } from "lucide-react";

interface LevelBadgeProps {
  level: number;
  rank: string;
  totalXp?: number;
  size?: "sm" | "md" | "lg";
}

export const LevelBadge: React.FC<LevelBadgeProps> = ({
  level,
  rank,
  totalXp,
  size = "md",
}) => {
  const getRankTheme = (lvl: number) => {
    if (lvl >= 70) return { bg: "from-amber-400 via-rose-500 to-purple-600", text: "text-amber-300", border: "border-amber-400/50", glow: "shadow-amber-500/20" };
    if (lvl >= 50) return { bg: "from-cyan-400 to-blue-600", text: "text-cyan-300", border: "border-cyan-400/50", glow: "shadow-cyan-500/20" };
    if (lvl >= 35) return { bg: "from-amber-500 to-yellow-600", text: "text-amber-300", border: "border-yellow-400/50", glow: "shadow-yellow-500/20" };
    if (lvl >= 20) return { bg: "from-slate-300 to-slate-500", text: "text-foreground", border: "border-slate-300/50", glow: "shadow-slate-400/20" };
    if (lvl >= 10) return { bg: "from-amber-700 to-amber-900", text: "text-amber-400", border: "border-amber-600/50", glow: "shadow-amber-600/20" };
    return { bg: "from-indigo-600 to-slate-800", text: "text-indigo-300", border: "border-indigo-500/40", glow: "shadow-indigo-500/10" };
  };

  const theme = getRankTheme(level);

  if (size === "sm") {
    return (
      <div className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-card/80 border ${theme.border} text-[11px] font-bold ${theme.text}`}>
        <Swords className="w-3 h-3" />
        <span>Lv.{level}</span>
      </div>
    );
  }

  return (
    <div className={`relative flex items-center gap-3 p-3 rounded-2xl bg-card/90 border ${theme.border} shadow-lg ${theme.glow} backdrop-blur-md`}>
      <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${theme.bg} flex flex-col items-center justify-center text-white shadow-inner font-black`}>
        <span className="text-[9px] uppercase tracking-wider text-white/80 leading-none">LV</span>
        <span className="text-lg leading-tight font-jp">{level}</span>
      </div>
      <div>
        <div className="flex items-center gap-1.5">
          <h4 className="text-sm font-bold text-foreground font-jp tracking-tight">{rank}</h4>
          <Sparkles className={`w-3.5 h-3.5 ${theme.text}`} />
        </div>
        {totalXp !== undefined && (
          <p className="text-xs text-muted-foreground font-mono">
            {totalXp.toLocaleString()} <span className="text-[10px] text-muted-foreground font-sans">Total XP</span>
          </p>
        )}
      </div>
    </div>
  );
};
