"use client";

import React, { useState, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { HankoStamp } from "@/components/ui/hanko-stamp";
import { Mic, Flame, Calendar, Sparkles, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";

interface HeatmapDay {
  date: string;
  minutes: number;
  level: 0 | 1 | 2 | 3 | 4;
}

export function SpeakingHeatmap({
  totalMinutes: propTotalMinutes,
  currentStreak = 5,
  className,
}: {
  totalMinutes?: number;
  currentStreak?: number;
  className?: string;
}) {
  const [days, setDays] = useState<HeatmapDay[]>([]);
  const [totalMinutes, setTotalMinutes] = useState<number>(propTotalMinutes || 0);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchHeatmap = async () => {
    try {
      setLoading(true);
      const res = await fetch("http://localhost:8000/api/v1/analytics/activity-heatmap?weeks=14");
      if (res.ok) {
        const data = await res.json();
        setDays(data.days || []);
        setTotalMinutes(data.total_speaking_minutes || 0);
      }
    } catch (e) {
      console.warn("Could not fetch speaking heatmap:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHeatmap();
  }, []);

  const levelStyles = {
    0: "bg-muted/40 border-border/40 hover:border-foreground/20",
    1: "bg-emerald-500/25 border-emerald-500/30 hover:border-emerald-500",
    2: "bg-emerald-500/50 border-emerald-500/60 hover:border-emerald-500",
    3: "bg-emerald-500/75 border-emerald-500/80 hover:border-emerald-500 shadow-xs",
    4: "bg-emerald-500 border-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.4)]",
  };

  return (
    <div className={cn("p-6 rounded-3xl border border-border bg-card washi-texture shadow-sm space-y-4 relative overflow-hidden", className)}>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border/60 pb-3.5">
        <div className="flex items-center gap-2.5">
          <span className="h-8 w-8 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary shadow-2xs">
            <Mic className="h-4 w-4" />
          </span>
          <div>
            <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
              <span>Ma Trận Giọng Nói Thực Tế (98 Ngày)</span>
              <span className="text-xs font-semibold text-muted-foreground font-jp">発話ヒートマップ</span>
            </h3>
            <p className="text-[10px] text-muted-foreground">Theo dõi thời lượng luyện nói mỗi ngày từ cơ sở dữ liệu</p>
          </div>
        </div>

        <div className="flex items-center gap-3 self-start sm:self-auto">
          <div className="text-right">
            <span className="text-[10px] text-muted-foreground font-semibold uppercase">Tổng Thời Lượng</span>
            <div className="text-sm font-black text-foreground font-mono">
              {totalMinutes} <span className="text-[10px] font-normal text-muted-foreground">phút</span>
            </div>
          </div>
          <HankoStamp text="皆勤" subtext="Chăm chỉ" variant="gold" size="sm" />
        </div>
      </div>

      {/* Heatmap Grid */}
      {loading && days.length === 0 ? (
        <div className="py-8 text-center text-xs text-muted-foreground animate-pulse">
          Đang tổng hợp dữ liệu luyện tập 14 tuần...
        </div>
      ) : (
        <div className="space-y-2">
          <div className="overflow-x-auto pb-1">
            <div className="grid grid-rows-7 grid-flow-col gap-1.5 min-w-[580px]">
              {days.map((d, i) => (
                <div
                  key={i}
                  className={cn(
                    "w-3.5 h-3.5 rounded-sm border transition-all cursor-pointer",
                    levelStyles[d.level]
                  )}
                  title={`${d.date}: ${d.minutes} phút luyện nói`}
                />
              ))}
            </div>
          </div>

          {/* Legend */}
          <div className="flex items-center justify-between text-[10px] text-muted-foreground pt-1">
            <span className="flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              <span>14 tuần gần nhất</span>
            </span>
            <div className="flex items-center gap-1.5">
              <span>Ít</span>
              <span className="w-2.5 h-2.5 rounded-xs bg-muted/40 border border-border" />
              <span className="w-2.5 h-2.5 rounded-xs bg-emerald-500/25 border border-emerald-500/30" />
              <span className="w-2.5 h-2.5 rounded-xs bg-emerald-500/50 border border-emerald-500/60" />
              <span className="w-2.5 h-2.5 rounded-xs bg-emerald-500/75 border border-emerald-500/80" />
              <span className="w-2.5 h-2.5 rounded-xs bg-emerald-500 border border-emerald-400" />
              <span>Nhiều (20m+)</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
