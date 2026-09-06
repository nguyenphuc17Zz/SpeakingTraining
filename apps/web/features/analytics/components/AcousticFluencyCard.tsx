"use client";

import React from "react";
import Link from "next/link";
import { Mic, Activity, ArrowRight, AudioWaveform, Clock } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { soundFX } from "@/lib/sound-fx";

interface AcousticFluencyCardProps {
  metrics?: Record<string, any>;
  diagnostic?: any;
}

export const AcousticFluencyCard: React.FC<AcousticFluencyCardProps> = ({ metrics }) => {
  // Extract or fallback SLA acoustic metrics from monologue analytics
  const monologueMetrics = metrics?.fluency?.extra_metadata?.speech_metrics_core || {};
  const articulationRate = monologueMetrics.articulation_rate_mora_sec ?? 5.2;
  const meanLengthOfRun = monologueMetrics.mean_length_of_run_mora ?? 7.8;
  const phonationRatio = monologueMetrics.phonation_time_ratio ?? 66.0;
  const cefrLevel = monologueMetrics.cefr_fluency_level || (articulationRate >= 6.0 ? "B2" : "B1");

  const getCefrBadge = (level: string) => {
    switch (level) {
      case "C2":
        return { label: "C2 (Mastery)", color: "text-amber-400 border-amber-500/30 bg-amber-500/10" };
      case "C1":
        return { label: "C1 (Effective Operational)", color: "text-indigo-400 border-indigo-500/30 bg-indigo-500/10" };
      case "B2":
        return { label: "B2 (Vantage - Trên Trung Cấp)", color: "text-emerald-400 border-emerald-500/30 bg-emerald-500/10" };
      case "B1":
        return { label: "B1 (Threshold - Trung Cấp)", color: "text-sky-400 border-sky-500/30 bg-sky-500/10" };
      case "A2":
        return { label: "A2 (Waystage - Sơ Cấp)", color: "text-amber-400 border-amber-500/30 bg-amber-500/10" };
      default:
        return { label: "A1 (Breakthrough)", color: "text-muted-foreground border-border bg-muted/40" };
    }
  };

  const cefr = getCefrBadge(cefrLevel);

  // Normalized percentages for progress bars (benchmarked to native standard)
  const arPct = Math.min(100, Math.round((articulationRate / 7.5) * 100));
  const mlrPct = Math.min(100, Math.round((meanLengthOfRun / 16.0) * 100));
  const ptrPct = Math.min(100, Math.round((phonationRatio / 80.0) * 100));

  return (
    <div className="relative overflow-hidden rounded-3xl border border-border bg-card p-5 md:p-6 washi-texture shadow-sm space-y-4">
      {/* Decorative Blur */}
      <div className="absolute top-0 left-0 h-40 w-40 bg-indigo-500/10 rounded-full blur-2xl pointer-events-none" />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 relative z-10">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center shrink-0">
            <AudioWaveform className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-black text-foreground tracking-tight">
                Âm Học Độ Lưu Loát Chuẩn CEFR (流暢性プロファイル)
              </h3>
            </div>
            <p className="text-xs text-muted-foreground">
              Phân tích độ trôi chảy ngôn ngữ theo chuẩn nghiên cứu SLA quốc tế (Tavakoli & Skehan)
            </p>
          </div>
        </div>

        <div className="self-start sm:self-auto">
          <span className={`text-xs font-bold px-2.5 py-1 rounded-xl border ${cefr.color}`}>
            {cefr.label}
          </span>
        </div>
      </div>

      {/* 3 SLA Core Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5 relative z-10">
        {/* 1. Articulation Rate (AR) */}
        <div className="p-3.5 rounded-2xl bg-muted/40 border border-border/80 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-muted-foreground flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-primary" />
              Tốc Độ Phát Âm Thuần (AR)
            </span>
            <span className="text-sm font-black text-foreground font-mono">
              {articulationRate.toFixed(1)} <span className="text-[10px] text-muted-foreground font-normal">mora/s</span>
            </span>
          </div>
          <div className="h-2 w-full bg-muted rounded-full overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-primary to-emerald-400 transition-all duration-500"
              style={{ width: `${arPct}%` }}
            />
          </div>
          <p className="text-[10px] text-muted-foreground">
            Chuẩn bản ngữ: 6.0 – 7.5 mora/s (loại trừ pauses ≥ 250ms)
          </p>
        </div>

        {/* 2. Mean Length of Run (MLR) */}
        <div className="p-3.5 rounded-2xl bg-muted/40 border border-border/80 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-muted-foreground flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-indigo-400" />
              Độ Dài Mạch Câu Liền (MLR)
            </span>
            <span className="text-sm font-black text-foreground font-mono">
              {meanLengthOfRun.toFixed(1)} <span className="text-[10px] text-muted-foreground font-normal">mora/run</span>
            </span>
          </div>
          <div className="h-2 w-full bg-muted rounded-full overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-sky-400 transition-all duration-500"
              style={{ width: `${mlrPct}%` }}
            />
          </div>
          <p className="text-[10px] text-muted-foreground">
            Phản ánh năng lực ghép cụm từ ngữ pháp (Chunking)
          </p>
        </div>

        {/* 3. Phonation Time Ratio (PTR) */}
        <div className="p-3.5 rounded-2xl bg-muted/40 border border-border/80 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-muted-foreground flex items-center gap-1.5">
              <Mic className="w-3.5 h-3.5 text-amber-400" />
              Tỷ Lệ Phát Âm Thực (PTR)
            </span>
            <span className="text-sm font-black text-foreground font-mono">
              {phonationRatio.toFixed(0)}%
            </span>
          </div>
          <div className="h-2 w-full bg-muted rounded-full overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-amber-500 to-rose-400 transition-all duration-500"
              style={{ width: `${ptrPct}%` }}
            />
          </div>
          <p className="text-[10px] text-muted-foreground">
            Thời gian phát ra âm thanh so với khoảng ngắt nghỉ
          </p>
        </div>
      </div>

      {/* Footer CTA */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1 border-t border-border/60 relative z-10">
        <p className="text-xs text-muted-foreground max-w-xl leading-relaxed">
          Độ trôi chảy được ghi nhận tự động sau mỗi bài tập độc thoại thuyết trình. Giữ tỷ lệ phát âm thực trên 65% để đạt chuẩn CEFR B2.
        </p>

        <Link href="/speaking/speech" onClick={() => soundFX.playTaiko()}>
          <Button variant="outline" size="sm" className="rounded-xl gap-1.5 font-bold shadow-xs shrink-0 w-full sm:w-auto">
            <span>Luyện Thuyết Trình / Độc Thoại</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Button>
        </Link>
      </div>
    </div>
  );
};
