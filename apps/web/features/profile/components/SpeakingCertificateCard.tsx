"use client";

import React from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Award,
  Sparkles,
  RefreshCw,
  Zap,
  Target,
  CheckCircle2,
  Calendar,
  Compass,
} from "lucide-react";
import { LearnerProfile } from "@/types/profile";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

interface SpeakingCertificateCardProps {
  profile: LearnerProfile | null;
  recalculating: boolean;
  onRecalculate: () => void;
}

export function SpeakingCertificateCard({
  profile,
  recalculating,
  onRecalculate,
}: SpeakingCertificateCardProps) {
  if (!profile) return null;

  const jlptLevel = profile.overall_level === "advanced" ? "N1" :
                    profile.overall_level === "upper_intermediate" ? "N2" :
                    profile.overall_level === "intermediate" ? "N3" :
                    profile.overall_level === "elementary" ? "N4" : "N5";

  const cefrLevel = profile.overall_level === "advanced" ? "C1" :
                    profile.overall_level === "upper_intermediate" ? "B2" :
                    profile.overall_level === "intermediate" ? "B1" :
                    profile.overall_level === "elementary" ? "A2" : "A1";

  const speedMs = profile.avg_response_speed_ms ? Math.round(profile.avg_response_speed_ms) : 1850;

  return (
    <div className="p-6 md:p-8 rounded-3xl border border-primary/30 bg-card washi-texture shadow-sm space-y-6 relative overflow-hidden ring-1 ring-primary/20">
      <div className="absolute top-0 right-0 h-56 w-56 bg-primary/10 rounded-full blur-3xl pointer-events-none" />

      {/* Top Bar: Title & Recalculate Button */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 relative z-10 border-b border-border/60 pb-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Badge variant="kintsugi" size="sm" className="font-bold">
              AI SPEAKING PORTFOLIO CERTIFICATE
            </Badge>
            <Badge variant="matcha" size="sm" className="font-bold">
              ĐÃ XÁC THỰC
            </Badge>
          </div>
          <h2 className="text-xl md:text-2xl font-black text-foreground tracking-tight flex items-center gap-2">
            <span>Hồ Sơ Năng Lực Hội Thoại Tiếng Nhật</span>
            <span className="text-sm font-jp font-normal text-muted-foreground">(学習者カルテ)</span>
          </h2>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            soundFX.playFurin();
            onRecalculate();
          }}
          disabled={recalculating}
          className="text-xs font-bold rounded-xl border-border self-start sm:self-auto gap-1.5"
        >
          <RefreshCw className={cn("h-3.5 w-3.5", recalculating && "animate-spin text-primary")} />
          <span>{recalculating ? "Đang tính toán..." : "Tái tổng hợp dữ liệu"}</span>
        </Button>
      </div>

      {/* Main Certificate Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative z-10">
        {/* Big JLPT & CEFR Level Badge */}
        <div className="p-6 rounded-2xl bg-muted/40 border border-border/80 flex flex-col items-center justify-center text-center space-y-2 shadow-2xs">
          <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">
            Trình Độ Ước Tính (Speaking Level)
          </span>
          <div className="flex items-baseline gap-2">
            <span className="text-4xl md:text-5xl font-black text-primary font-mono tracking-tight">
              {jlptLevel}
            </span>
            <span className="text-lg font-bold text-muted-foreground font-mono">
              / {cefrLevel}
            </span>
          </div>
          <Badge variant="outline" size="sm" className="text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 border-emerald-500/30">
            {profile.level_confidence === "high" ? "Độ tin cậy cao (High Confidence)" : "Độ tin cậy tiêu chuẩn"}
          </Badge>
        </div>

        {/* Sessions & Reflex Speed Stats */}
        <div className="md:col-span-2 grid grid-cols-2 gap-3.5">
          <div className="p-4 rounded-2xl bg-card border border-border/80 space-y-1 shadow-2xs">
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground font-semibold">
              <Compass className="h-4 w-4 text-primary" />
              <span>Tổng Số Buổi Luyện Tập</span>
            </div>
            <div className="text-2xl font-black text-foreground font-mono">
              {profile.total_sessions_analyzed || 0} <span className="text-xs font-normal text-muted-foreground">buổi</span>
            </div>
            <p className="text-[10px] text-muted-foreground">Đã quét toàn bộ 4 chuyên đề Studio</p>
          </div>

          <div className="p-4 rounded-2xl bg-card border border-border/80 space-y-1 shadow-2xs">
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground font-semibold">
              <Zap className="h-4 w-4 text-amber-500" />
              <span>Tốc Độ Phản Xạ TB</span>
            </div>
            <div className="text-2xl font-black text-foreground font-mono">
              {speedMs} <span className="text-xs font-normal text-muted-foreground">ms</span>
            </div>
            <p className="text-[10px] text-muted-foreground">Thời gian khởi động câu nói</p>
          </div>

          <div className="p-4 rounded-2xl bg-card border border-border/80 space-y-1 shadow-2xs col-span-2">
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground font-semibold">
              <Target className="h-4 w-4 text-rose-500" />
              <span>Trọng Tâm Rèn Luyện Hiện Tại</span>
            </div>
            <div className="text-xs font-bold text-foreground">
              {profile.current_focus || "Nâng cao phản xạ hội thoại và chuẩn hóa Kính ngữ công sở"}
            </div>
          </div>
        </div>
      </div>

      {/* AI Sensei Narrative Summary Quote */}
      {profile.summary && (
        <div className="p-4 rounded-2xl bg-primary/5 border border-primary/20 flex items-start gap-3 text-xs leading-relaxed text-foreground relative z-10">
          <span className="p-2 rounded-xl bg-primary/10 text-primary shrink-0 mt-0.5">
            <Sparkles className="h-4 w-4" />
          </span>
          <div className="space-y-1">
            <span className="font-bold text-primary">Nhận xét từ AI Sensei (Speaking Portfolio Summary):</span>
            <p className="text-muted-foreground">{profile.summary}</p>
          </div>
        </div>
      )}
    </div>
  );
}
