"use client";

import React from "react";
import { GoalProgressDTO } from "../types/analytics";
import { ConfidenceBadge } from "./ConfidenceBadge";
import { Target, CheckCircle2, AlertCircle } from "lucide-react";

interface GoalProgressCardProps {
  goal: GoalProgressDTO;
}

export const GoalProgressCard: React.FC<GoalProgressCardProps> = ({ goal }) => {
  const percent = Math.round(goal.progress_ratio * 100);

  return (
    <div className="p-4 rounded-2xl bg-card/80 border border-border space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-rose-500/10 text-rose-400 flex items-center justify-center">
            <Target className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-xs font-bold text-foreground font-jp">{goal.title}</h4>
            <span className="text-[10px] text-muted-foreground capitalize">{goal.goal_type} Goal</span>
          </div>
        </div>
        <ConfidenceBadge confidence={goal.confidence} sampleSize={goal.recent_activity_count} />
      </div>

      {/* Progress Bar */}
      <div className="space-y-1">
        <div className="flex items-center justify-between text-[11px] font-semibold text-foreground">
          <span>Mastery Progress</span>
          <span className="font-mono text-rose-400">{percent}%</span>
        </div>
        <div className="h-2 w-full bg-muted rounded-full overflow-hidden">
          <div
            className="h-full rounded-full bg-gradient-to-r from-rose-500 to-indigo-500 transition-all duration-300"
            style={{ width: `${percent}%` }}
          />
        </div>
      </div>

      {/* Blocker Note */}
      {goal.blocked_by && (
        <div className="flex items-center gap-1.5 text-[11px] text-amber-400 font-medium pt-1">
          <AlertCircle className="w-3.5 h-3.5 shrink-0" />
          <span className="line-clamp-1">{goal.blocked_by}</span>
        </div>
      )}
    </div>
  );
};
