"use client";

import React from "react";
import { MetricValueDTO } from "../types/analytics";
import { TrendBadge } from "./TrendBadge";
import { ConfidenceBadge } from "./ConfidenceBadge";
import { Sparkles, Info } from "lucide-react";

interface MetricCardProps {
  metric: MetricValueDTO;
  onClick?: (metric: MetricValueDTO) => void;
  isSelected?: boolean;
}

export const MetricCard: React.FC<MetricCardProps> = ({ metric, onClick, isSelected }) => {
  const isInsufficient = metric.confidence === "insufficient" || metric.sample_size === 0;

  return (
    <div
      onClick={() => onClick && onClick(metric)}
      className={`relative p-5 rounded-2xl border transition-all cursor-pointer ${
        isSelected
          ? "bg-card/90 border-rose-500/80 ring-2 ring-rose-500/20 shadow-lg shadow-rose-500/10"
          : "bg-card/70 border-border/80 hover:border-border shadow-md hover:bg-card/90"
      }`}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="flex items-center gap-1.5">
            <h4 className="text-xs font-bold text-foreground font-jp tracking-tight">
              {metric.name}
            </h4>
            {metric.ja_name && (
              <span className="text-[10px] text-muted-foreground font-jp">({metric.ja_name})</span>
            )}
          </div>
          <p className="text-[11px] text-muted-foreground mt-0.5 line-clamp-1">
            {metric.description}
          </p>
        </div>
        <TrendBadge trend={metric.trend} />
      </div>

      {/* Main Value */}
      <div className="mt-4 flex items-baseline justify-between">
        <div className="flex items-baseline gap-1.5">
          {isInsufficient ? (
            <span className="text-xl font-bold text-muted-foreground font-mono">--</span>
          ) : (
            <span className="text-2xl font-black text-foreground font-mono tracking-tight">
              {metric.value}
            </span>
          )}
          <span className="text-xs text-muted-foreground font-semibold">{metric.unit}</span>
        </div>

        {/* Change delta */}
        {metric.change !== null && metric.change !== undefined && !isInsufficient && (
          <div
            className={`text-xs font-mono font-bold ${
              metric.change >= 0 ? "text-emerald-400" : "text-rose-400"
            }`}
          >
            {metric.change >= 0 ? `+${metric.change}` : metric.change} {metric.unit}
          </div>
        )}
      </div>

      {/* Footer: Confidence & Sample Size */}
      <div className="mt-3 pt-3 border-t border-border/60 flex items-center justify-between">
        <ConfidenceBadge confidence={metric.confidence} sampleSize={metric.sample_size} />
        <span className="text-[10px] text-muted-foreground font-mono">Window: {metric.period}</span>
      </div>
    </div>
  );
};
