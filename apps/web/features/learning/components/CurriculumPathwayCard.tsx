"use client";

import React from "react";
import { Compass, CheckCircle2, Circle, ArrowRight } from "lucide-react";
import { CurriculumUnit } from "@/types/learning";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface CurriculumPathwayCardProps {
  units: CurriculumUnit[];
}

export const CurriculumPathwayCard: React.FC<CurriculumPathwayCardProps> = ({ units }) => {
  return (
    <Card className="border border-border bg-card/80 p-5 shadow-lg space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Compass className="w-4 h-4 text-purple-400" />
          <h3 className="text-base font-bold text-white tracking-tight">
            Lộ trình mục tiêu dài hạn <span className="text-xs font-normal text-muted-foreground">(Dynamic Curriculum)</span>
          </h3>
        </div>
      </div>

      <div className="space-y-3">
        {units.map((unit, idx) => {
          const progressPct = Math.round(unit.progress_ratio * 100);
          return (
            <div
              key={unit.id}
              className={`p-3.5 rounded-xl border transition-all space-y-2 ${
                unit.is_completed
                  ? "bg-background/40 border-emerald-900/40"
                  : "bg-background/70 border-border/80 hover:border-purple-500/30"
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-2">
                  {unit.is_completed ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                  ) : (
                    <div className="w-4 h-4 rounded-full border border-purple-400/60 flex items-center justify-center text-[10px] text-purple-300 font-bold shrink-0">
                      {idx + 1}
                    </div>
                  )}
                  <h4 className="text-sm font-semibold text-white">{unit.title}</h4>
                </div>

                <span className="text-xs font-bold text-purple-300 shrink-0">{progressPct}%</span>
              </div>

              <p className="text-xs text-foreground pl-6 leading-relaxed">{unit.objective}</p>

              <div className="pl-6 pt-1 flex items-center justify-between text-[11px] text-muted-foreground">
                <span>Ước tính: {unit.estimated_sessions} buổi rèn luyện</span>
                <span className="text-muted-foreground">{unit.completion_criteria}</span>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
};
