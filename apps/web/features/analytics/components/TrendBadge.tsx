"use client";

import React from "react";
import { TrendingUp, TrendingDown, Minus, Activity, HelpCircle, PauseCircle } from "lucide-react";

interface TrendBadgeProps {
  trend: string;
}

export const TrendBadge: React.FC<TrendBadgeProps> = ({ trend }) => {
  const getStyle = (t: string) => {
    switch (t) {
      case "strongly_improving":
      case "improving":
        return {
          bg: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
          icon: TrendingUp,
          label: "Improving ↑",
        };
      case "strongly_declining":
      case "declining":
        return {
          bg: "bg-rose-500/20 text-rose-300 border-rose-500/40",
          icon: TrendingDown,
          label: "Declining ↓",
        };
      case "plateau":
        return {
          bg: "bg-amber-500/20 text-amber-300 border-amber-500/40",
          icon: PauseCircle,
          label: "Plateau →",
        };
      case "stable":
        return {
          bg: "bg-indigo-500/20 text-indigo-300 border-indigo-500/40",
          icon: Minus,
          label: "Stable 〰",
        };
      default:
        return {
          bg: "bg-muted text-muted-foreground border-border",
          icon: HelpCircle,
          label: "Insufficient Data",
        };
    }
  };

  const style = getStyle(trend);
  const Icon = style.icon;

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold border ${style.bg}`}>
      <Icon className="w-3 h-3" />
      <span>{style.label}</span>
    </span>
  );
};
