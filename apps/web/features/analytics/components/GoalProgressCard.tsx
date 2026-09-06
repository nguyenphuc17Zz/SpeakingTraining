"use client";

import React from "react";
import { GoalProgressDTO } from "../types/analytics";
import { ConfidenceBadge } from "./ConfidenceBadge";
import { Target, AlertCircle, Brain } from "lucide-react";

interface GoalProgressCardProps {
  goal: GoalProgressDTO;
}

export const GoalProgressCard: React.FC<GoalProgressCardProps> = ({ goal }) => {
  const percent = Math.round(goal.progress_ratio * 100);

  // Parse FSRS Retrievability from blocker string: e.g. "Cần củng cố: ... (Khả năng nhớ: 78%)"
  const retentionMatch = goal.blocked_by?.match(/Khả năng nhớ:\s*(\d+)%/i);
  const retentionPct = retentionMatch ? parseInt(retentionMatch[1], 10) : null;

  const getRetentionBadge = (pct: number) => {
    if (pct >= 80) {
      return {
        label: `Trí nhớ vững (${pct}%)`,
        style: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
      };
    }
    if (pct >= 65) {
      return {
        label: `Cần củng cố (${pct}%)`,
        style: "text-amber-400 bg-amber-500/10 border-amber-500/20",
      };
    }
    return {
      label: `Nguy cơ quên (${pct}%)`,
      style: "text-rose-400 bg-rose-500/10 border-rose-500/20 animate-pulse",
    };
  };

  const retention = retentionPct !== null ? getRetentionBadge(retentionPct) : null;

  return (
    <div className="p-4 rounded-2xl bg-card/80 border border-border space-y-3 shadow-xs">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-rose-500/10 text-rose-400 flex items-center justify-center shrink-0">
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
          <span className="flex items-center gap-1.5">
            <span>Độ thành thục (FSRS Grounded)</span>
          </span>
          <span className="font-mono text-rose-400 font-bold">{percent}%</span>
        </div>
        <div className="h-2 w-full bg-muted rounded-full overflow-hidden">
          <div
            className="h-full rounded-full bg-gradient-to-r from-rose-500 to-indigo-500 transition-all duration-300"
            style={{ width: `${percent}%` }}
          />
        </div>
      </div>

      {/* FSRS Retention Indicator & Blocker */}
      {goal.blocked_by && (
        <div className="space-y-1.5 pt-1 border-t border-border/50">
          <div className="flex items-center justify-between gap-2 text-[11px]">
            <div className="flex items-center gap-1.5 text-muted-foreground min-w-0">
              <AlertCircle className="w-3.5 h-3.5 shrink-0 text-amber-400" />
              <span className="truncate">{goal.blocked_by.replace(/\s*\(Khả năng nhớ:.*?\)/, "")}</span>
            </div>

            {retention && (
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-lg border shrink-0 flex items-center gap-1 ${retention.style}`}>
                <Brain className="w-3 h-3" />
                {retention.label}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

