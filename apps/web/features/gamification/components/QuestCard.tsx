"use client";

import React from "react";
import { CheckCircle2, Circle, Sparkles, MessageCircle, Mic, PlayCircle, Award, Target } from "lucide-react";
import { QuestDTO } from "../types/game";

interface QuestCardProps {
  quest: QuestDTO;
}

export const QuestCard: React.FC<QuestCardProps> = ({ quest }) => {
  const getCategoryIcon = (cat: string) => {
    switch (cat.toLowerCase()) {
      case "conversation":
        return MessageCircle;
      case "pronunciation":
        return Mic;
      case "shadowing":
        return PlayCircle;
      case "mastery":
        return Award;
      default:
        return Target;
    }
  };

  const IconComponent = getCategoryIcon(quest.category);
  const percent = Math.min(100, Math.max(0, Math.round(quest.progress_ratio * 100)));

  return (
    <div
      className={`relative overflow-hidden p-4 rounded-2xl border transition-all duration-200 ${
        quest.is_completed
          ? "bg-card/60 border-emerald-500/40 shadow-sm shadow-emerald-500/10"
          : "bg-card/80 border-border/80 hover:border-border shadow-md"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <div
            className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
              quest.is_completed
                ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                : "bg-primary/10 text-primary border border-primary/20"
            }`}
          >
            {quest.is_completed ? (
              <CheckCircle2 className="w-5 h-5" />
            ) : (
              <IconComponent className="w-5 h-5" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="text-sm font-bold text-foreground font-jp tracking-tight">
                {quest.title}
              </h4>
              {quest.frequency === "weekly" && (
                <span className="px-2 py-0.5 rounded-full text-[9px] font-bold bg-aizome-500/20 text-aizome-300 border border-aizome-500/30 uppercase tracking-wider">
                  Weekly
                </span>
              )}
            </div>
            <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2 leading-relaxed">
              {quest.description}
            </p>
          </div>
        </div>

        {/* XP Reward Chip */}
        <div className="shrink-0 flex items-center gap-1 px-2.5 py-1 rounded-xl bg-primary/10 border border-primary/25 text-primary font-mono font-bold text-xs">
          <Sparkles className="w-3.5 h-3.5 text-primary" />
          <span>+{quest.xp_reward} XP</span>
        </div>
      </div>

      {/* Progress Track */}
      <div className="mt-3.5 space-y-1">
        <div className="flex items-center justify-between text-[11px] font-medium text-muted-foreground">
          <span>Progress</span>
          <span className="font-mono">
            {quest.current_count} / {quest.target_count} ({percent}%)
          </span>
        </div>
        <div className="h-2 w-full bg-muted/80 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-300 ${
              quest.is_completed
                ? "bg-gradient-to-r from-emerald-500 to-teal-400"
                : "bg-gradient-to-r from-primary to-kintsugi-500"
            }`}
            style={{ width: `${percent}%` }}
          />
        </div>
      </div>
    </div>
  );
};
