"use client";

import React, { useEffect } from "react";
import { RampSessionSummary } from "@/services/ramp-api";
import {
  Trophy,
  ArrowRight,
  TrendingUp,
  Award,
  Sparkles,
  RotateCcw,
  CheckCircle2,
  Zap,
} from "lucide-react";
import { soundFX } from "@/lib/sound-fx";
import { HankoStamp } from "@/components/ui/hanko-stamp";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface RampSessionSummaryCardProps {
  summary: RampSessionSummary;
  onStartNew: () => void;
}

export function RampSessionSummaryCard({ summary, onStartNew }: RampSessionSummaryCardProps) {
  const stageAdvanced = summary.stage_end > summary.stage_start;
  const supportFaded = summary.support_level_end < summary.support_level_start;
  const earnedXP = Math.round(summary.exercises_completed * 15 + summary.independent_speaking_pct * 50);

  useEffect(() => {
    soundFX.playVictory();
  }, []);

  return (
    <div className="relative overflow-hidden p-6 md:p-8 rounded-3xl border border-border bg-card washi-texture shadow-md space-y-6 max-w-2xl mx-auto">
      {/* Hanko stamp */}
      <div className="absolute top-6 right-6 pointer-events-none opacity-85 scale-90 rotate-12">
        <HankoStamp text="修了" variant="torii" size="lg" />
      </div>

      {/* Header */}
      <div className="text-center space-y-1.5 pt-2">
        <div className="inline-flex p-3 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-500 mb-1">
          <Trophy className="h-8 w-8" />
        </div>
        <h2 className="text-2xl font-extrabold text-foreground tracking-tight">
          Hoàn Thành Phiên Luyện Phục Hồi!
        </h2>
        <p className="text-xs text-muted-foreground">
          Thời lượng: {summary.duration_minutes.toFixed(0)} phút • Hoàn thành {summary.exercises_completed} câu phát ngôn
        </p>
      </div>

      {/* XP Earned Banner */}
      <div className="p-3.5 rounded-2xl bg-gradient-to-r from-amber-500/10 via-emerald-500/10 to-amber-500/10 border border-amber-500/20 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-amber-500 animate-pulse" />
          <span className="text-xs font-bold text-foreground">Kinh nghiệm đạt được (XP)</span>
        </div>
        <Badge variant="kintsugi" className="text-sm font-extrabold px-3 py-1">
          +{earnedXP} XP
        </Badge>
      </div>

      {/* Stage / Support Progress */}
      <div className="grid grid-cols-2 gap-3">
        <div className="p-4 rounded-2xl bg-muted/30 border border-border/80 text-center space-y-1">
          <span className="text-[11px] font-bold text-muted-foreground uppercase tracking-wider block">
            Thăng Cấp Stage
          </span>
          <div className="flex items-center justify-center gap-2 text-lg font-extrabold text-foreground">
            <span>Stage {summary.stage_start}</span>
            <ArrowRight className="h-4 w-4 text-muted-foreground" />
            <span className={stageAdvanced ? "text-emerald-600 dark:text-emerald-400" : ""}>
              Stage {summary.stage_end}
            </span>
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-muted/30 border border-border/80 text-center space-y-1">
          <span className="text-[11px] font-bold text-muted-foreground uppercase tracking-wider block">
            Rút Giàn Giáo (Support)
          </span>
          <div className="flex items-center justify-center gap-2 text-lg font-extrabold text-foreground">
            <span>Cấp {summary.support_level_start}</span>
            <ArrowRight className="h-4 w-4 text-muted-foreground" />
            <span className={supportFaded ? "text-emerald-600 dark:text-emerald-400" : ""}>
              Cấp {summary.support_level_end}
            </span>
          </div>
        </div>
      </div>

      {/* Metrics Table */}
      <div className="p-4 rounded-2xl bg-muted/20 border border-border/60 space-y-2.5 text-xs">
        <MetricRow
          label="Tỷ lệ phát ngôn độc lập"
          value={`${Math.round(summary.independent_speaking_pct * 100)}%`}
        />
        <MetricRow
          label="Tỷ lệ câu nói trọn vẹn (không câu cụt)"
          value={`${Math.round(summary.full_sentence_rate * 100)}%`}
        />
        <MetricRow
          label="Tỷ lệ mở rộng câu thành công"
          value={`${Math.round(summary.elaboration_success_rate * 100)}%`}
        />
        <MetricRow
          label="Tỷ lệ kèm lý do / ví dụ cụ thể"
          value={`${Math.round(summary.reason_example_rate * 100)}%`}
        />
        {summary.avg_response_duration_ms > 0 && (
          <MetricRow
            label="Thời gian phát ngôn trung bình"
            value={`${(summary.avg_response_duration_ms / 1000).toFixed(1)} giây / câu`}
          />
        )}
      </div>

      {/* Milestones Achieved */}
      {summary.milestones_achieved.length > 0 && (
        <div className="space-y-2">
          <span className="text-xs font-bold text-foreground flex items-center gap-1.5">
            <Award className="h-4 w-4 text-amber-500" /> Cột mốc đã đạt:
          </span>
          <div className="flex flex-wrap gap-1.5">
            {summary.milestones_achieved.map((m, i) => (
              <Badge key={i} variant="kintsugi" className="text-xs py-1 px-2.5">
                🏆 {m}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Strengths & Weaknesses */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
        {summary.strengths.length > 0 && (
          <div className="p-3.5 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 space-y-1.5">
            <span className="font-bold text-emerald-700 dark:text-emerald-300 block">
              💪 Điểm làm tốt:
            </span>
            <ul className="space-y-1 text-muted-foreground">
              {summary.strengths.map((s, i) => (
                <li key={i}>• {s}</li>
              ))}
            </ul>
          </div>
        )}

        {summary.weaknesses.length > 0 && (
          <div className="p-3.5 rounded-2xl bg-amber-500/10 border border-amber-500/20 space-y-1.5">
            <span className="font-bold text-amber-700 dark:text-amber-300 block">
              🎯 Cần rèn thêm:
            </span>
            <ul className="space-y-1 text-muted-foreground">
              {summary.weaknesses.map((w, i) => (
                <li key={i}>• {w}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Next recommendation */}
      <div className="p-4 rounded-2xl bg-primary/10 border border-primary/20 text-xs space-y-1">
        <span className="font-bold text-primary flex items-center gap-1.5">
          <Sparkles className="h-4 w-4" /> Đề xuất buổi tiếp theo:
        </span>
        <p className="text-muted-foreground leading-relaxed">
          {summary.next_recommendation}
        </p>
      </div>

      {/* CTA */}
      <div className="pt-2">
        <Button
          size="lg"
          variant="primary"
          onClick={onStartNew}
          className="w-full py-5 rounded-2xl bg-primary hover:bg-primary/90 text-primary-foreground font-extrabold text-sm shadow-md flex items-center justify-center gap-2"
        >
          <RotateCcw className="h-4 w-4" />
          <span>Bắt đầu phiên luyện tập mới</span>
        </Button>
      </div>
    </div>
  );
}

function MetricRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between py-1 border-b border-border/40 last:border-0">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-bold text-foreground">{value}</span>
    </div>
  );
}
