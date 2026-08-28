"use client";

import React from "react";
import { Zap, Activity, CheckCircle2 } from "lucide-react";

interface MasteryBarProps {
  overall: number; // 0.0 - 1.0
  spontaneous?: number;
  production?: number;
  recognition?: number;
  contextsCount?: number;
  showDimensions?: boolean;
  size?: "sm" | "md" | "lg";
}

export const MasteryBar: React.FC<MasteryBarProps> = ({
  overall,
  spontaneous,
  production,
  recognition,
  contextsCount,
  showDimensions = false,
  size = "md",
}) => {
  const pct = Math.min(100, Math.max(0, Math.round(overall * 100)));

  const getColor = (val: number) => {
    if (val >= 80) return "from-emerald-500 to-teal-400";
    if (val >= 55) return "from-indigo-500 to-sky-400";
    if (val >= 35) return "from-amber-500 to-yellow-400";
    return "from-rose-500 to-pink-500";
  };

  const getTierLabel = (val: number) => {
    if (val >= 85) return "Thuần thục (Mastered)";
    if (val >= 60) return "Tiến bộ tốt (Improving)";
    if (val >= 35) return "Đang rèn luyện (Practicing)";
    return "Mới phát hiện (Discovered)";
  };

  const heightClass = size === "sm" ? "h-2" : size === "lg" ? "h-3.5" : "h-2.5";

  return (
    <div className="w-full space-y-1.5">
      <div className="flex items-center justify-between text-xs">
        <span className="font-medium text-foreground flex items-center gap-1">
          <Activity className="w-3.5 h-3.5 text-indigo-400" />
          Độ thuần thục: <span className="font-semibold text-white">{pct}%</span>
        </span>
        <span className="text-muted-foreground text-[11px]">{getTierLabel(pct)}</span>
      </div>

      {/* Main Progress Track */}
      <div className={`w-full ${heightClass} rounded-full bg-muted/80 border border-border/50 overflow-hidden p-0.5 shadow-inner`}>
        <div
          className={`h-full rounded-full bg-gradient-to-r ${getColor(pct)} transition-all duration-500 ease-out shadow-sm`}
          style={{ width: `${Math.max(5, pct)}%` }}
        />
      </div>

      {/* Multi-dimensional Breakdown */}
      {showDimensions && (
        <div className="grid grid-cols-3 gap-2 pt-2 text-[11px] border-t border-border/60 mt-2">
          <div className="bg-card/60 rounded px-2 py-1 border border-border">
            <span className="text-muted-foreground block text-[10px]">Tự phát (Spontaneous)</span>
            <span className="font-medium text-emerald-400">
              {spontaneous !== undefined ? `${Math.round(spontaneous * 100)}%` : "--"}
            </span>
          </div>
          <div className="bg-card/60 rounded px-2 py-1 border border-border">
            <span className="text-muted-foreground block text-[10px]">Tạo câu (Production)</span>
            <span className="font-medium text-sky-400">
              {production !== undefined ? `${Math.round(production * 100)}%` : "--"}
            </span>
          </div>
          <div className="bg-card/60 rounded px-2 py-1 border border-border">
            <span className="text-muted-foreground block text-[10px]">Nhận diện (Recognition)</span>
            <span className="font-medium text-indigo-300">
              {recognition !== undefined ? `${Math.round(recognition * 100)}%` : "--"}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
