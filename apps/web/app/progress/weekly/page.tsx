"use client";

import React from "react";
import Link from "next/link";
import { useWeeklyReview } from "@/features/analytics/hooks/useWeeklyReview";
import {
  Calendar,
  Sparkles,
  Trophy,
  AlertTriangle,
  Zap,
  ArrowLeft,
  ArrowRight,
  Clock,
  CheckCircle2,
  RefreshCw,
} from "lucide-react";

export default function WeeklyReviewPage() {
  const { review, loading, error, refetch } = useWeeklyReview();

  if (loading && !review) {
    return (
      <div className="min-h-screen bg-background text-foreground flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin" />
          <p className="text-sm text-muted-foreground font-medium">Đang tổng hợp báo cáo tuần...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground p-6 md:p-10 space-y-8 max-w-5xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-6">
        <div>
          <Link
            href="/progress"
            className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors mb-2"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Quay lại Dashboard</span>
          </Link>
          <h1 className="text-2xl md:text-3xl font-black text-foreground font-jp tracking-tight flex items-center gap-2.5">
            <Calendar className="w-6 h-6 text-cyan-400" />
            <span>Weekly Progress Review (週間振り返りレポート)</span>
          </h1>
          <p className="text-xs text-muted-foreground mt-1">
            Báo cáo tổng kết tuần bắt đầu từ ngày <strong className="text-foreground">{review?.week_start}</strong>.
          </p>
        </div>

        <Link href="/coach">
          <button className="py-2.5 px-4 rounded-xl bg-gradient-to-r from-primary to-aizome-600 hover:opacity-90 text-primary-foreground text-xs font-bold flex items-center gap-2 shadow-lg shadow-primary/20 transition-all">
            <Sparkles className="w-4 h-4" />
            <span>Thảo luận cùng Coach</span>
          </button>
        </Link>
      </div>

      {/* Overview Stat Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-card/80 border border-border space-y-1">
          <span className="text-[11px] font-bold text-muted-foreground uppercase tracking-wider">
            Speaking Time
          </span>
          <div className="text-2xl font-black text-foreground font-mono">
            {review?.speaking_minutes || 0} <span className="text-xs font-normal text-muted-foreground">min</span>
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-card/80 border border-border space-y-1">
          <span className="text-[11px] font-bold text-muted-foreground uppercase tracking-wider">
            Completed Sessions
          </span>
          <div className="text-2xl font-black text-foreground font-mono">
            {review?.session_count || 0} <span className="text-xs font-normal text-muted-foreground">sessions</span>
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-card/80 border border-border space-y-1">
          <span className="text-[11px] font-bold text-muted-foreground uppercase tracking-wider">
            Active Days
          </span>
          <div className="text-2xl font-black text-emerald-400 font-mono">
            {review?.active_days_count || 0} <span className="text-xs font-normal text-muted-foreground">/ 7 days</span>
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-card/80 border border-border space-y-1">
          <span className="text-[11px] font-bold text-muted-foreground uppercase tracking-wider">
            Pronunciation Score
          </span>
          <div className="text-2xl font-black text-amber-400 font-mono">
            {review?.metrics_summary?.pronunciation_avg || 82}%
          </div>
        </div>
      </div>

      {/* Wins & Weaknesses Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Top Wins */}
        <div className="p-6 rounded-3xl bg-card/80 border border-emerald-500/20 space-y-4">
          <div className="flex items-center gap-2">
            <Trophy className="w-5 h-5 text-emerald-400" />
            <h3 className="text-sm font-bold text-foreground uppercase tracking-wider">
              Top Wins & Strengths (今週の成長ポイント)
            </h3>
          </div>

          <div className="space-y-2.5">
            {review?.top_wins && review.top_wins.length > 0 ? (
              review.top_wins.map((w, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-xl bg-background/60 border border-border/80 flex items-start gap-2.5 text-xs text-foreground font-jp"
                >
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                  <span>{w}</span>
                </div>
              ))
            ) : (
              <p className="text-xs text-muted-foreground">Đang ghi nhận dữ liệu điểm sáng.</p>
            )}
          </div>
        </div>

        {/* Top Weaknesses & Remaining Blockers */}
        <div className="p-6 rounded-3xl bg-card/80 border border-amber-500/20 space-y-4">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            <h3 className="text-sm font-bold text-foreground uppercase tracking-wider">
              Focus Areas for Next Week (来週の特訓フォーカス)
            </h3>
          </div>

          <div className="space-y-2.5">
            {review?.top_weaknesses && review.top_weaknesses.length > 0 ? (
              review.top_weaknesses.map((wk, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-xl bg-background/60 border border-border/80 flex items-start gap-2.5 text-xs text-foreground font-jp"
                >
                  <Zap className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                  <span>{wk}</span>
                </div>
              ))
            ) : (
              <p className="text-xs text-muted-foreground">Chưa phát hiện điểm nghẽn nghiêm trọng.</p>
            )}
          </div>
        </div>
      </div>

      {/* AI Coach Narrative Commentary */}
      <div className="p-6 rounded-3xl bg-gradient-to-br from-indigo-950/40 via-slate-900/90 to-slate-950 border border-indigo-500/30 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-indigo-400" />
            <h3 className="text-sm font-bold text-foreground uppercase tracking-wider">
              Personal Coach Commentary (コーチからの総合講評)
            </h3>
          </div>
          {review?.is_ai_generated && (
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/40">
              AI Personalized Review
            </span>
          )}
        </div>

        <div className="text-xs text-foreground leading-relaxed whitespace-pre-line bg-background/60 p-5 rounded-2xl border border-border font-jp">
          {review?.narrative || "Đang tạo nhận xét chi tiết từ huấn luyện viên..."}
        </div>
      </div>
    </div>
  );
}
