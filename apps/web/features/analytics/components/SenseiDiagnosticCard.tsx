"use client";

import React from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Sparkles,
  Award,
  TrendingUp,
  AlertCircle,
  ArrowRight,
  Shield,
  Volume2,
  CheckCircle2,
} from "lucide-react";
import { soundFX } from "@/lib/sound-fx";
import Link from "next/link";

interface SenseiDiagnosticCardProps {
  diagnostic: any;
  loading: boolean;
}

export function SenseiDiagnosticCard({ diagnostic, loading }: SenseiDiagnosticCardProps) {
  if (loading || !diagnostic) {
    return (
      <div className="p-6 rounded-3xl border border-border bg-card washi-texture animate-pulse space-y-3">
        <div className="h-4 w-32 bg-muted rounded" />
        <div className="h-6 w-3/4 bg-muted rounded" />
        <div className="h-16 w-full bg-muted/60 rounded-2xl" />
      </div>
    );
  }

  const r = diagnostic.diagnostic_report || {};

  return (
    <div className="p-6 md:p-8 rounded-3xl border border-primary/30 bg-card washi-texture shadow-sm space-y-5 relative overflow-hidden ring-1 ring-primary/20">
      <div className="absolute top-0 right-0 h-48 w-48 bg-primary/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 relative z-10 border-b border-border/60 pb-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Badge variant="kintsugi" size="sm" className="font-bold">
              AI SENSEI 360° DIAGNOSTIC
            </Badge>
            <Badge variant="matcha" size="sm" className="font-bold font-mono">
              Ước tính: {r.estimated_level || "N3"}
            </Badge>
          </div>
          <h2 className="text-lg md:text-xl font-black text-foreground tracking-tight">
            {r.summary_title || "Báo Cáo Chẩn Đoán Năng Lực Hội Thoại Toàn Diện"}
          </h2>
        </div>

        <div className="text-xs text-muted-foreground font-mono font-semibold">
          Tổng hợp từ {diagnostic.total_attempts || 0} bài luyện
        </div>
      </div>

      {/* Narrative Evaluation */}
      <div className="text-xs text-muted-foreground leading-relaxed pl-1">
        {r.narrative}
      </div>

      {/* Strengths & Core Bottleneck Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Top Strengths */}
        <div className="p-4 rounded-2xl bg-emerald-500/5 border border-emerald-500/20 space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold text-emerald-700 dark:text-emerald-300">
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            <span>Điểm Sáng Tiến Bộ Nhất:</span>
          </div>
          <ul className="space-y-1 pl-6 list-disc text-[11px] text-muted-foreground">
            {(r.top_strengths || ["Phản xạ nhanh nhạy", "Nắm vững thể Desu/Masu"]).map((st: string, idx: number) => (
              <li key={idx}>{st}</li>
            ))}
          </ul>
        </div>

        {/* Core Bottleneck */}
        <div className="p-4 rounded-2xl bg-amber-500/5 border border-amber-500/20 space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold text-amber-700 dark:text-amber-300">
            <AlertCircle className="h-4 w-4 text-amber-500" />
            <span>Điểm Nghẽn Cần Khắc Phục:</span>
          </div>
          <p className="text-[11px] text-muted-foreground leading-snug pl-1">
            {r.core_bottleneck || "Cần nâng cao độ thuần thục Kính ngữ và ngữ điệu câu dài."}
          </p>
        </div>
      </div>

      {/* Action Plan & 1-Click Practice Launch */}
      <div className="p-4 rounded-2xl bg-muted/40 border border-border/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-2xs">
        <div className="space-y-1">
          <div className="text-xs font-bold text-foreground flex items-center gap-1.5">
            <Sparkles className="h-3.5 w-3.5 text-primary" />
            <span>Chiến Lược Hành Động Cho Bạn:</span>
          </div>
          <p className="text-[11px] text-muted-foreground leading-snug">
            {r.action_plan || "Tập trung 10 phút luyện Kính ngữ và 5 phút Cao độ Tokyo mỗi ngày."}
          </p>
        </div>

        <Link href={r.recommended_route || "/keigo"}>
          <Button
            variant="akane"
            size="sm"
            onClick={() => soundFX.playKatana()}
            className="text-xs font-bold gap-1.5 rounded-xl px-5 h-9 shrink-0 shadow-md"
          >
            <span>Khắc Phục Ngay</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Button>
        </Link>
      </div>
    </div>
  );
}
