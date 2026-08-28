"use client";

import React from "react";
import { Trophy, Flame, Mic, PlayCircle, Award, Swords, MessageCircle, Lock, CheckCircle2, Zap } from "lucide-react";
import { AchievementDTO } from "../types/game";

interface AchievementCardProps {
  achievement: AchievementDTO;
}

export const AchievementCard: React.FC<AchievementCardProps> = ({ achievement }) => {
  const getRarityConfig = (rarity: string) => {
    switch (rarity.toLowerCase()) {
      case "legendary":
        return {
          border: "border-amber-400/60",
          bg: "from-amber-950/40 via-slate-900/90 to-purple-950/30",
          glow: "shadow-amber-500/20",
          tag: "bg-amber-500/20 text-amber-300 border-amber-500/40",
          iconBg: "from-amber-500 to-yellow-600",
        };
      case "epic":
        return {
          border: "border-purple-500/50",
          bg: "from-purple-950/30 via-slate-900/90 to-slate-950",
          glow: "shadow-purple-500/10",
          tag: "bg-purple-500/20 text-purple-300 border-purple-500/40",
          iconBg: "from-purple-500 to-indigo-600",
        };
      case "rare":
        return {
          border: "border-cyan-500/40",
          bg: "from-cyan-950/20 via-slate-900/90 to-slate-950",
          glow: "shadow-cyan-500/10",
          tag: "bg-cyan-500/20 text-cyan-300 border-cyan-500/40",
          iconBg: "from-cyan-500 to-blue-600",
        };
      default:
        return {
          border: "border-border",
          bg: "from-slate-900/80 to-slate-950",
          glow: "shadow-none",
          tag: "bg-muted text-muted-foreground border-border",
          iconBg: "from-slate-700 to-slate-800",
        };
    }
  };

  const getIcon = (iconName: string) => {
    switch (iconName) {
      case "flame":
        return Flame;
      case "mic":
        return Mic;
      case "play-circle":
        return PlayCircle;
      case "award":
        return Award;
      case "swords":
        return Swords;
      case "zap":
        return Zap;
      default:
        return Trophy;
    }
  };

  const config = getRarityConfig(achievement.rarity);
  const IconComponent = getIcon(achievement.icon);
  const percent = Math.min(100, Math.max(0, Math.round(achievement.progress_ratio * 100)));

  return (
    <div
      className={`relative overflow-hidden p-5 rounded-2xl border bg-gradient-to-br ${config.bg} ${config.border} shadow-lg ${config.glow} transition-all duration-300 ${
        achievement.is_unlocked ? "opacity-100" : "opacity-75 hover:opacity-90"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3.5">
          <div
            className={`w-12 h-12 rounded-2xl bg-gradient-to-br ${
              achievement.is_unlocked ? config.iconBg : "from-slate-800 to-slate-900"
            } flex items-center justify-center text-white shadow-md shrink-0`}
          >
            {achievement.is_unlocked ? (
              <IconComponent className="w-6 h-6" />
            ) : (
              <Lock className="w-5 h-5 text-muted-foreground" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="text-sm font-bold text-foreground font-jp tracking-tight">
                {achievement.title}
              </h4>
              <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold border uppercase tracking-wider ${config.tag}`}>
                {achievement.rarity}
              </span>
            </div>
            <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
              {achievement.description}
            </p>
          </div>
        </div>

        {/* Reward Tag */}
        <div className="shrink-0 flex items-center gap-1 px-2.5 py-1 rounded-xl bg-muted/80 border border-border text-xs font-mono font-bold text-amber-300">
          <Trophy className="w-3.5 h-3.5 text-amber-400" />
          <span>+{achievement.xp_reward} XP</span>
        </div>
      </div>

      {/* Progress or Unlocked Timestamp */}
      <div className="mt-4 pt-3 border-t border-border/60">
        {achievement.is_unlocked ? (
          <div className="flex items-center gap-1.5 text-xs font-medium text-emerald-400 font-jp">
            <CheckCircle2 className="w-4 h-4" />
            <span>Unlocked (達成完了)</span>
          </div>
        ) : (
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-[11px] font-medium text-muted-foreground">
              <span>Progress</span>
              <span className="font-mono">
                {achievement.current_value} / {achievement.target_value} ({percent}%)
              </span>
            </div>
            <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
              <div
                className="h-full rounded-full bg-gradient-to-r from-amber-500 to-indigo-500 transition-all duration-300"
                style={{ width: `${percent}%` }}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
