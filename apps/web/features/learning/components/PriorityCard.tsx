"use client";

import React from "react";
import { Target, Clock, ArrowRight, Zap, HelpCircle, Flame } from "lucide-react";
import { LearningRecommendation } from "@/types/learning";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { MasteryBar } from "./MasteryBar";

interface PriorityCardProps {
  priority: LearningRecommendation;
  onPractice: (key: string) => void;
}

export const PriorityCard: React.FC<PriorityCardProps> = ({ priority, onPractice }) => {
  const getDifficultyBadgeColor = (diff: string) => {
    switch (diff.toLowerCase()) {
      case "easy":
        return "border-emerald-500/30 text-emerald-400 bg-emerald-950/20";
      case "hard":
        return "border-amber-500/30 text-amber-400 bg-amber-950/20";
      case "challenge":
        return "border-rose-500/30 text-rose-400 bg-rose-950/20";
      default:
        return "border-indigo-500/30 text-indigo-400 bg-indigo-950/20";
    }
  };

  return (
    <Card className="border border-border bg-card/80 hover:border-indigo-500/40 transition-all p-5 shadow-lg flex flex-col justify-between gap-4 group relative overflow-hidden">
      <div className="space-y-3">
        {/* Top badges */}
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <Badge variant="outline" className="text-xs capitalize bg-background/80 border-border text-foreground">
            {priority.item_type || priority.item?.item_type || "Kỹ năng"}
          </Badge>

          <div className="flex items-center gap-1.5">
            <Badge variant="outline" className={`text-[11px] capitalize ${getDifficultyBadgeColor(priority.difficulty || priority.item?.difficulty || "normal")}`}>
              {priority.difficulty || priority.item?.difficulty || "normal"}
            </Badge>
            <span className="text-[11px] text-muted-foreground flex items-center gap-1 bg-background px-2 py-0.5 rounded border border-border">
              <Clock className="w-3 h-3 text-muted-foreground" /> {priority.estimated_minutes || 5}m
            </span>
          </div>
        </div>

        {/* Title */}
        <div>
          <h3 className="text-base font-bold text-white group-hover:text-indigo-300 transition-colors">
            {priority.title || priority.item?.title || "Trọng điểm luyện tập"}
          </h3>
        </div>

        {/* Mastery Bar */}
        <MasteryBar overall={(priority.mastery_percent ?? ((priority.item?.overall_mastery || 0) * 100)) / 100} size="sm" />

        {/* Deterministic Why & How */}
        <div className="space-y-2 pt-2 border-t border-border/80 text-xs">
          <div className="space-y-0.5">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-amber-400/90 flex items-center gap-1">
              <Flame className="w-3 h-3 text-amber-400" /> Vì sao cần luyện:
            </span>
            <p className="text-foreground leading-relaxed pl-4">{priority.why}</p>
          </div>

          <div className="space-y-0.5">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-sky-400/90 flex items-center gap-1">
              <Zap className="w-3 h-3 text-sky-400" /> Phương pháp luyện:
            </span>
            <p className="text-foreground leading-relaxed pl-4">{priority.how}</p>
          </div>
        </div>
      </div>

      {/* Action Footer */}
      <div className="pt-3 border-t border-border flex items-center justify-between">
        <span className="text-[11px] text-muted-foreground">
          Lịch sử: {priority.success_count ?? priority.item?.success_count ?? 0}/{priority.attempt_count ?? priority.item?.attempt_count ?? 0} lần đạt
        </span>
        <Button
          size="sm"
          onClick={() => onPractice(priority.key || priority.item?.key || "")}
          className="bg-indigo-600/90 hover:bg-indigo-600 text-white text-xs px-3 py-1.5 h-auto flex items-center gap-1.5 shadow-md"
        >
          Luyện ngay <ArrowRight className="w-3.5 h-3.5" />
        </Button>
      </div>
    </Card>
  );
};
