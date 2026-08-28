"use client";
import React from "react";
import { Lightbulb, X, Zap } from "lucide-react";

export function CoachInsightCard({ insight, onDismiss, onAction }: { insight: any; onDismiss?: () => void; onAction?: (insight: any) => void }) {
  return (
    <div className="p-3 rounded-xl bg-amber-500/8 dark:bg-amber-500/10 border border-amber-500/25 dark:border-amber-500/30 flex gap-3 items-start animate-in slide-in-from-top-1 shadow-sm">
      <span className="h-7 w-7 rounded-lg bg-amber-500/15 border border-amber-500/25 flex items-center justify-center text-amber-600 dark:text-amber-400 shrink-0 shadow-sm">
        <Lightbulb className="w-4 h-4" />
      </span>
      <div className="flex-1 min-w-0 space-y-1">
        <div className="flex items-center justify-between gap-2">
          <span className="text-xs font-bold text-amber-700 dark:text-amber-300">💡 Coach Insight • {insight.insight_type}</span>
          {onDismiss && (
            <button
              onClick={onDismiss}
              className="p-1 rounded-lg hover:bg-amber-500/15 text-muted-foreground hover:text-foreground transition-colors"
              aria-label="Dismiss insight"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
        <p className="text-xs text-foreground/90 dark:text-foreground/90 leading-relaxed font-medium">{insight.description}</p>
        {insight.recommended_action && (
          <button
            onClick={() => onAction?.(insight)}
            className="mt-1.5 inline-flex items-center gap-1.5 text-xs font-bold px-3 py-1 rounded-lg bg-amber-600 hover:bg-amber-500 text-white dark:bg-amber-500 dark:hover:bg-amber-400 dark:text-sumi-950 shadow-sm transition-all active:scale-95"
          >
            <Zap className="w-3.5 h-3.5" /> {insight.recommended_action}
          </button>
        )}
      </div>
    </div>
  );
}

