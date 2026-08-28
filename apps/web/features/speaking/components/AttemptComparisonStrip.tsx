"use client";

import React from "react";
import { ArrowUpRight, TrendingUp, History } from "lucide-react";

export interface AttemptSummary {
  attemptNumber: number;
  overallScore: number;
  moraScore?: number;
  pitchScore?: number;
  timestamp: string;
}

interface Props {
  attempts: AttemptSummary[];
}

export const AttemptComparisonStrip: React.FC<Props> = ({ attempts }) => {
  if (!attempts || attempts.length <= 1) return null;

  const firstScore = attempts[0].overallScore;
  const lastScore = attempts[attempts.length - 1].overallScore;
  const delta = lastScore - firstScore;

  return (
    <div className="p-4 rounded-2xl bg-gradient-to-r from-slate-900/90 via-indigo-950/40 to-slate-900/90 border border-indigo-500/20 shadow-lg backdrop-blur-md">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-indigo-400" />
          <h4 className="font-semibold text-foreground text-xs tracking-wide">
            Tiến độ qua các lần thử (Attempt Progression)
          </h4>
        </div>
        {delta > 0 && (
          <div className="flex items-center gap-1 text-xs font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
            <ArrowUpRight className="w-3.5 h-3.5" />
            <span>+{delta.toFixed(0)} điểm tiến bộ!</span>
          </div>
        )}
      </div>

      <div className="flex items-center gap-2 overflow-x-auto pb-1">
        {attempts.map((att, idx) => (
          <div
            key={idx}
            className={`flex items-center gap-2.5 px-3.5 py-2 rounded-xl border text-xs font-mono transition-all ${
              idx === attempts.length - 1
                ? "bg-indigo-600/20 border-indigo-400/50 text-indigo-200 font-semibold shadow-md"
                : "bg-muted/40 border-border/60 text-muted-foreground"
            }`}
          >
            <span>Lần {att.attemptNumber}</span>
            <span
              className={`text-sm font-bold ${
                att.overallScore >= 80
                  ? "text-emerald-400"
                  : att.overallScore >= 65
                  ? "text-indigo-300"
                  : "text-amber-400"
              }`}
            >
              {att.overallScore.toFixed(0)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};
