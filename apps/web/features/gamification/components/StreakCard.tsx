"use client";

import React from "react";
import { Flame, ShieldCheck, Calendar, Zap } from "lucide-react";
import { StreakOverviewDTO } from "../types/game";

interface StreakCardProps {
  streak: StreakOverviewDTO;
}

export const StreakCard: React.FC<StreakCardProps> = ({ streak }) => {
  return (
    <div className="relative overflow-hidden p-5 rounded-2xl bg-gradient-to-br from-slate-900/95 to-slate-950 border border-amber-500/30 shadow-lg shadow-amber-500/5 backdrop-blur-md">
      {/* Background Accent Glow */}
      <div className="absolute -right-6 -top-6 w-24 h-24 bg-amber-500/10 rounded-full blur-2xl pointer-events-none" />

      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center text-white shadow-md shadow-amber-500/20">
            <Flame className="w-7 h-7 animate-bounce" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-2xl font-black text-foreground font-jp tracking-tight">
                {streak.current_streak}
              </span>
              <span className="text-xs font-bold text-amber-400 uppercase tracking-wider">
                Day Streak (連続日数)
              </span>
            </div>
            <p className="text-xs text-muted-foreground">
              {streak.is_qualified_today
                ? "Streak protected for today! 🔥"
                : "Complete 1 practice to keep your streak!"}
            </p>
          </div>
        </div>

        {/* Freezes badge */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-muted/80 border border-border/60 text-xs text-foreground font-medium">
          <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
          <span>{streak.streak_freezes_available} Freeze</span>
        </div>
      </div>

      {/* 7-Day Flame Track */}
      <div className="mt-5 pt-4 border-t border-border/60">
        <div className="flex items-center justify-between gap-2">
          {streak.activity_history_last_7_days.map((day, idx) => (
            <div key={idx} className="flex flex-col items-center gap-1.5 flex-1">
              <div
                className={`w-8 h-8 rounded-xl flex items-center justify-center transition-all ${
                  day.is_active
                    ? "bg-amber-500/20 border border-amber-500/50 text-amber-400 shadow-sm shadow-amber-500/30"
                    : "bg-muted/40 border border-border text-slate-600"
                }`}
              >
                <Flame className={`w-4 h-4 ${day.is_active ? "fill-amber-400" : ""}`} />
              </div>
              <span className="text-[10px] text-muted-foreground font-medium">{day.day_name}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
