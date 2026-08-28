"use client";

import React from "react";
import { PracticeDistributionDTO } from "../types/analytics";
import { PieChart, Clock } from "lucide-react";

interface PracticeDistributionChartProps {
  distribution: PracticeDistributionDTO;
}

export const PracticeDistributionChart: React.FC<PracticeDistributionChartProps> = ({
  distribution,
}) => {
  return (
    <div className="p-5 rounded-2xl bg-card/80 border border-border space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-indigo-400" />
          <h4 className="text-xs font-bold text-foreground uppercase tracking-wider">
            Practice Modality Balance (練習バランス)
          </h4>
        </div>
        <span className="text-xs font-mono text-muted-foreground">
          Total: <strong className="text-foreground">{distribution.total_minutes}</strong> min
        </span>
      </div>

      {/* Distribution Multi-segment Bar */}
      <div className="h-3 w-full bg-muted rounded-full overflow-hidden flex shadow-inner">
        <div
          className="bg-rose-500 h-full transition-all"
          style={{ width: `${distribution.conversation_pct}%` }}
          title={`Conversation: ${distribution.conversation_pct}%`}
        />
        <div
          className="bg-amber-500 h-full transition-all"
          style={{ width: `${distribution.pronunciation_pct}%` }}
          title={`Pronunciation: ${distribution.pronunciation_pct}%`}
        />
        <div
          className="bg-cyan-500 h-full transition-all"
          style={{ width: `${distribution.shadowing_pct}%` }}
          title={`Shadowing: ${distribution.shadowing_pct}%`}
        />
        <div
          className="bg-indigo-500 h-full transition-all"
          style={{ width: `${distribution.review_pct + distribution.drill_pct}%` }}
          title={`Review & Drill: ${distribution.review_pct + distribution.drill_pct}%`}
        />
      </div>

      {/* Legend */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px]">
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-rose-500 shrink-0" />
          <span className="text-muted-foreground">Conversation ({distribution.conversation_pct}%)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-amber-500 shrink-0" />
          <span className="text-muted-foreground">Pronunciation ({distribution.pronunciation_pct}%)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-cyan-500 shrink-0" />
          <span className="text-muted-foreground">Shadowing ({distribution.shadowing_pct}%)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-indigo-500 shrink-0" />
          <span className="text-muted-foreground">Drill & Review ({distribution.drill_pct + distribution.review_pct}%)</span>
        </div>
      </div>
    </div>
  );
};
