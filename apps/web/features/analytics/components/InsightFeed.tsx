"use client";

import React from "react";
import Link from "next/link";
import { InsightDTO } from "../types/analytics";
import { Sparkles, TrendingUp, AlertTriangle, ArrowRight, CheckCircle2, PauseCircle } from "lucide-react";

interface InsightFeedProps {
  insights: InsightDTO[];
  onDismiss?: (id: string) => void;
}

export const InsightFeed: React.FC<InsightFeedProps> = ({ insights, onDismiss }) => {
  const getIcon = (type: string) => {
    switch (type) {
      case "improvement":
        return { icon: TrendingUp, color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/30" };
      case "plateau":
        return { icon: PauseCircle, color: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/30" };
      case "opportunity":
        return { icon: Sparkles, color: "text-purple-400", bg: "bg-purple-500/10 border-purple-500/30" };
      default:
        return { icon: AlertTriangle, color: "text-rose-400", bg: "bg-rose-500/10 border-rose-500/30" };
    }
  };

  if (insights.length === 0) {
    return null;
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Sparkles className="w-4 h-4 text-rose-400" />
        <h3 className="text-sm font-bold text-foreground uppercase tracking-wider">
          AI Diagnostic Insights (コーチからの分析インサイト)
        </h3>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {insights.map((ins) => {
          const style = getIcon(ins.insight_type);
          const Icon = style.icon;
          const targetUrl = ins.action_target_type === "shadowing" ? "/shadowing" : "/speaking";

          return (
            <div
              key={ins.id}
              className={`p-4 rounded-2xl border ${style.bg} bg-card/80 shadow-md flex flex-col justify-between space-y-3`}
            >
              <div className="flex items-start gap-3">
                <div className={`p-2 rounded-xl bg-background/60 border border-inherit shrink-0`}>
                  <Icon className={`w-5 h-5 ${style.color}`} />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-foreground font-jp">{ins.title}</h4>
                  <p className="text-xs text-foreground mt-1 leading-relaxed">{ins.description}</p>
                </div>
              </div>

              {ins.action_hint && (
                <div className="pt-2 border-t border-border/60 flex items-center justify-between gap-3">
                  <span className="text-[11px] text-muted-foreground italic font-jp line-clamp-1">
                    💡 {ins.action_hint}
                  </span>
                  <Link href={targetUrl} className="shrink-0">
                    <button className="px-2.5 py-1 rounded-lg bg-muted hover:bg-slate-700 text-foreground text-[11px] font-bold flex items-center gap-1">
                      <span>Practice</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  </Link>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
