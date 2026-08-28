"use client";

import React from "react";
import Link from "next/link";
import { BottleneckDTO } from "../types/analytics";
import { AlertCircle, ArrowRight, Zap, Target, CheckCircle2 } from "lucide-react";

interface BottleneckCardProps {
  bottleneck: BottleneckDTO;
}

export const BottleneckCard: React.FC<BottleneckCardProps> = ({ bottleneck }) => {
  return (
    <div className="relative overflow-hidden p-6 rounded-3xl bg-gradient-to-br from-amber-950/40 via-slate-900/90 to-slate-950 border border-amber-500/30 shadow-xl shadow-amber-500/5">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="px-3 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 uppercase tracking-wider">
              Diagnostic Bottleneck Analysis (最優先の改善ポイント)
            </span>
          </div>

          <h3 className="text-xl font-black text-foreground font-jp tracking-tight flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-amber-400 shrink-0" />
            <span>{bottleneck.candidate}</span>
          </h3>

          <p className="text-xs text-foreground max-w-2xl leading-relaxed">
            {bottleneck.description}
          </p>

          {/* Evidence tags */}
          {bottleneck.evidence_keys.length > 0 && (
            <div className="flex flex-wrap items-center gap-2 pt-1">
              <span className="text-[10px] text-muted-foreground font-semibold uppercase">Evidence:</span>
              {bottleneck.evidence_keys.map((ev, idx) => (
                <span
                  key={idx}
                  className="px-2 py-0.5 rounded-md bg-muted/80 border border-border text-[10px] font-mono text-foreground"
                >
                  {ev}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Suggested Focus Action */}
        <div className="shrink-0 p-4 rounded-2xl bg-background/60 border border-border flex flex-col justify-between space-y-3 min-w-[220px]">
          <div>
            <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
              Suggested Next Step
            </span>
            <p className="text-xs font-bold text-foreground mt-1 font-jp">
              {bottleneck.suggested_focus || "10 phút hội thoại tự do"}
            </p>
          </div>

          <Link href="/speaking">
            <button className="w-full py-2 px-3 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white text-xs font-bold flex items-center justify-center gap-1.5 shadow-md shadow-amber-500/20 transition-all">
              <Zap className="w-3.5 h-3.5" />
              <span>Practice This Now (今すぐ特訓)</span>
            </button>
          </Link>
        </div>
      </div>
    </div>
  );
};
