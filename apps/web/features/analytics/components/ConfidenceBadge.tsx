"use client";

import React from "react";
import { ShieldCheck, ShieldAlert, Shield } from "lucide-react";

interface ConfidenceBadgeProps {
  confidence: string;
  sampleSize?: number;
}

export const ConfidenceBadge: React.FC<ConfidenceBadgeProps> = ({ confidence, sampleSize }) => {
  const getStyle = (c: string) => {
    switch (c) {
      case "high":
        return {
          bg: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
          icon: ShieldCheck,
          text: "High Confidence",
        };
      case "medium":
        return {
          bg: "bg-cyan-500/10 text-cyan-400 border-cyan-500/30",
          icon: Shield,
          text: "Medium Confidence",
        };
      case "low":
        return {
          bg: "bg-amber-500/10 text-amber-400 border-amber-500/30",
          icon: ShieldAlert,
          text: "Low Confidence",
        };
      default:
        return {
          bg: "bg-muted text-muted-foreground border-border",
          icon: Shield,
          text: "Need More Data",
        };
    }
  };

  const style = getStyle(confidence);
  const Icon = style.icon;

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-medium border ${style.bg}`}>
      <Icon className="w-2.5 h-2.5" />
      <span>{style.text}</span>
      {sampleSize !== undefined && sampleSize > 0 && (
        <span className="font-mono text-[8px] opacity-75">({sampleSize} samples)</span>
      )}
    </span>
  );
};
