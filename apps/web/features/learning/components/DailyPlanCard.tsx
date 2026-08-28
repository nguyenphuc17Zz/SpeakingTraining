"use client";

import React from "react";
import {
  Sparkles,
  Flame,
  Clock,
  CheckCircle2,
  Play,
  RotateCw,
  MessageSquare,
  Target,
  Headphones,
  RefreshCw,
  Compass,
} from "lucide-react";
import { DailyPlan, LearningPlanItem } from "@/types/learning";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface DailyPlanCardProps {
  plan: DailyPlan | null;
  loading: boolean;
  regenerating: boolean;
  timeBudget: number;
  onBudgetChange: (budget: number) => void;
  onStartExercise: (exerciseId: string, planItemId: string) => void;
}

const BUDGET_OPTIONS = [10, 20, 30, 45];

export const DailyPlanCard: React.FC<DailyPlanCardProps> = ({
  plan,
  loading,
  regenerating,
  timeBudget,
  onBudgetChange,
  onStartExercise,
}) => {
  const getSlotIcon = (targetType: string) => {
    switch (targetType) {
      case "conversation":
        return <MessageSquare className="w-4 h-4 text-sky-400" />;
      case "targeted_drill":
        return <Target className="w-4 h-4 text-amber-400" />;
      case "pronunciation":
        return <Headphones className="w-4 h-4 text-emerald-400" />;
      case "review":
        return <RefreshCw className="w-4 h-4 text-indigo-400" />;
      case "exploration":
        return <Compass className="w-4 h-4 text-purple-400" />;
      default:
        return <Sparkles className="w-4 h-4 text-teal-400" />;
    }
  };

  const completedCount = plan?.items.filter((i) => i.status === "completed").length || 0;
  const totalCount = plan?.items.length || 0;
  const progressPct = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

  return (
    <Card variant="washi" className="p-6 shadow-washi relative overflow-hidden">
      <div className="absolute -top-12 -right-12 h-48 w-48 rounded-full bg-enso-gradient opacity-30 pointer-events-none" />
      <div className="relative flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-border">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-primary flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5" />
              Lộ trình hôm nay
            </span>
            <span className="text-muted-foreground">•</span>
            <span className="text-xs text-muted-foreground font-medium">{plan?.plan_date || "Hôm nay"}</span>
          </div>
          <h2 className="text-2xl font-bold text-foreground tracking-tight mt-1 flex items-center gap-2">
            今日の学習 <span className="text-sm font-normal text-muted-foreground">(Kế hoạch ngày)</span>
          </h2>
        </div>

        {/* Time Budget Selector */}
        <div className="flex items-center gap-2 bg-background/70 p-1.5 rounded-lg border border-border">
          <span className="text-xs text-muted-foreground pl-2 flex items-center gap-1">
            <Clock className="w-3.5 h-3.5 text-muted-foreground" /> Thời gian:
          </span>
          <div className="flex gap-1">
            {BUDGET_OPTIONS.map((b) => (
              <button
                key={b}
                disabled={loading || regenerating}
                onClick={() => onBudgetChange(b)}
                className={`px-2.5 py-1 text-xs font-medium rounded-md transition-all ${
                  timeBudget === b
                    ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted"
                }`}
              >
                {b}m
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="relative my-5 p-4 rounded-xl bg-primary/5 border border-primary/10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <span className="flex items-center gap-1.5 text-amber-600 dark:text-amber-400 text-xs font-bold uppercase tracking-wider">
            <Flame className="w-4 h-4 fill-amber-500/20 animate-pulse" />
            Trọng tâm ưu tiên
          </span>
          <h3 className="text-base font-semibold text-foreground">
            {plan?.focus_title || "Phản xạ giao tiếp thực tế"}
          </h3>
          <p className="text-sm text-muted-foreground">
            {plan?.focus_reason || "Được đề xuất tự động dựa trên phân tích lỗi và mục tiêu của bạn."}
          </p>
        </div>
        <span className="flex items-center gap-3 w-full sm:w-auto shrink-0">
          <span className="text-right hidden sm:block">
            <span className="text-xs text-muted-foreground block">Tiến độ</span>
            <span className="text-sm font-bold text-foreground">{completedCount}/{totalCount} bài</span>
          </span>
          <span className="w-12 h-12 rounded-full border-2 border-primary/15 flex items-center justify-center bg-card text-xs font-bold text-primary">
            {progressPct}%
          </span>
        </span>
      </div>

      {/* Exercise Plan List */}
      <div className="space-y-3">
        {loading ? (
          <div className="py-12 text-center text-muted-foreground flex items-center justify-center gap-2">
            <RotateCw className="w-5 h-5 animate-spin text-indigo-400" />
            Đang tổng hợp lộ trình thích ứng...
          </div>
        ) : plan?.items && plan.items.length > 0 ? (
          plan.items.map((item, idx) => {
            const isCompleted = item.status === "completed";
            return (
              <div
                key={item.id}
                className={`p-3.5 rounded-xl border transition-all flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 ${
                  isCompleted
                    ? "bg-background/40 border-emerald-900/30 opacity-80"
                    : "bg-background/80 border-border/80 hover:border-indigo-500/40 hover:bg-card/60"
                }`}
              >
                <div className="flex items-center gap-3.5">
                  <div
                    className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold shrink-0 ${
                      isCompleted
                        ? "bg-emerald-500/10 text-emerald-600 border border-emerald-500/20 dark:text-emerald-400"
                        : "bg-muted text-foreground border border-border"
                    }`}
                  >
                    {isCompleted ? <CheckCircle2 className="w-4 h-4" /> : idx + 1}
                  </div>

                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="flex items-center gap-1 text-xs text-muted-foreground">
                        {getSlotIcon(item.target_type || "general")}
                      </span>
                      <h4 className={`text-sm font-medium ${isCompleted ? "text-muted-foreground line-through" : "text-foreground"}`}>
                        {item.title || item.exercise?.title || "Bài luyện tập trọng tâm"}
                      </h4>
                    </div>

                    <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3 text-muted-foreground" /> {item.estimated_minutes || item.exercise?.estimated_minutes || 5} phút
                      </span>
                      <span>•</span>
                      <span className="capitalize">{(item.target_type || "general").replace("_", " ")}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
                  {isCompleted ? (
                    <Badge variant="outline" className="text-emerald-400 border-emerald-800/50 bg-emerald-950/30 text-xs">
                      Đã hoàn thành ✓
                    </Badge>
                  ) : (
                    <Button
                      size="sm"
                      onClick={() => onStartExercise(item.exercise_id, item.id)}
                      className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs px-3.5 py-1.5 h-auto shadow-md shadow-indigo-600/20 flex items-center gap-1.5"
                    >
                      <Play className="w-3.5 h-3.5 fill-current" /> Luyện tập
                    </Button>
                  )}
                </div>
              </div>
            );
          })
        ) : (
          <div className="py-8 text-center text-muted-foreground">Chưa có bài tập nào được tạo.</div>
        )}
      </div>
    </Card>
  );
};
