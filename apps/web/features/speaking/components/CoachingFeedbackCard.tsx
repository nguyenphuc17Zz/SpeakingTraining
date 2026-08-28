"use client";

import React from "react";
import { CorrectionItem } from "../types";
import { Sparkles, Volume2, ArrowRight, CheckCircle2, AlertTriangle, Info } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface CoachingFeedbackCardProps {
  correction: CorrectionItem;
  onViewDetails?: (correction: CorrectionItem) => void;
  onPlayCorrection?: (text: string) => void;
}

export function CoachingFeedbackCard({
  correction,
  onViewDetails,
  onPlayCorrection,
}: CoachingFeedbackCardProps) {
  const isMustFix = correction.severity === "MUST_FIX";
  const isShouldFix = correction.severity === "SHOULD_FIX";
  const isNative = correction.severity === "NATIVE_ALTERNATIVE";

  const getSeverityBadge = () => {
    if (isMustFix) {
      return (
        <Badge variant="outline" size="sm" className="bg-destructive/10 text-destructive border-destructive/30">
          🔴 Must Fix (Cần sửa)
        </Badge>
      );
    }
    if (isShouldFix) {
      return (
        <Badge variant="outline" size="sm" className="bg-amber-500/10 text-amber-400 border-amber-500/30">
          🟠 Should Fix (Nên cải thiện)
        </Badge>
      );
    }
    return (
      <Badge variant="outline" size="sm" className="bg-aizome-500/10 text-aizome-300 border-aizome-500/30">
        ⭐ Native Alternative (Cách nói bản xứ)
      </Badge>
    );
  };

  return (
    <div className="p-3.5 rounded-2xl bg-gradient-to-r from-slate-900/95 via-slate-950/95 to-slate-900/95 border border-primary/25 shadow-lg shadow-primary/5 animate-in slide-in-from-bottom-2 duration-300">
      <div className="flex items-center justify-between gap-2 pb-2 border-b border-border/80">
        <div className="flex items-center gap-1.5 text-xs font-bold text-primary">
          <Sparkles className="h-3.5 w-3.5 text-primary" />
          <span>Coaching Tip (Gợi ý nâng cao)</span>
        </div>
        {getSeverityBadge()}
      </div>

      <div className="pt-2.5 space-y-2">
        {/* Before / After Diff */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="line-through text-muted-foreground bg-muted/80 px-2 py-0.5 rounded font-mono">
            {correction.original}
          </span>
          <ArrowRight className="h-3.5 w-3.5 text-primary shrink-0" />
          <span className="font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded font-mono">
            {correction.corrected}
          </span>
        </div>

        {/* Explanation */}
        <p className="text-[11px] text-foreground leading-relaxed line-clamp-2">
          {correction.explanation}
        </p>

        {/* Actions Bar */}
        <div className="flex items-center justify-between pt-1 border-t border-border/60 text-[11px]">
          {onPlayCorrection && (
            <button
              onClick={() => onPlayCorrection(correction.corrected)}
              className="flex items-center gap-1 text-emerald-400 hover:text-emerald-300 transition-colors py-0.5 px-1.5 rounded hover:bg-emerald-500/10"
              title="Nghe phát âm chuẩn"
            >
              <Volume2 className="h-3 w-3" />
              <span>Listen to correction (Nghe mẫu)</span>
            </button>
          )}

          {onViewDetails && (
            <button
              onClick={() => onViewDetails(correction)}
              className="text-primary hover:text-primary/80 font-medium ml-auto hover:underline"
            >
              Details & Feedback ➔
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
