"use client";

import React from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Trophy,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  ArrowRight,
  Sparkles,
  Volume2,
  Clock,
} from "lucide-react";
import { PitchExercise, PitchResult } from "../services/pitch-api";
import { speakJapaneseText } from "@/features/speaking/services/web-speech";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

interface PitchResultCardProps {
  result: PitchResult;
  exercise: PitchExercise | null;
  onNext: () => void;
  onRetry: () => void;
  onAskCoach?: (prompt: string) => void;
  onCancelAutoNext?: () => void;
}

export function PitchResultCard({
  result,
  exercise,
  onNext,
  onRetry,
  onAskCoach,
  onCancelAutoNext,
}: PitchResultCardProps) {
  const isPerfect = result.isPerfect || (result.score ?? 0) >= 90;
  const isSuccess = result.success;
  const isTimeout = result.timedOut;
  const score = result.score ?? 0;
  const latency = result.reactionLatencyMs ?? 0;

  const pc = exercise?.extra_metadata?.pitch_config || {};
  const canonical = pc.canonical || exercise?.canonical || "";
  const metrics = result.pitchMetrics || {};

  const pitchAccuracy = metrics.pitch_accuracy ?? score;
  const moraScore = metrics.mora_score ?? 90;
  const devoicingScore = metrics.devoicing_score ?? 88;
  const naturalnessScore = metrics.naturalness_score ?? 85;

  return (
    <div className="p-6 rounded-3xl border border-border/80 bg-card shadow-md washi-texture space-y-6 animate-in fade-in zoom-in-95 duration-200">
      {/* Result Status Banner */}
      <div
        className={cn(
          "p-4 rounded-2xl border flex flex-col sm:flex-row sm:items-center justify-between gap-3",
          isPerfect
            ? "bg-amber-500/10 border-amber-500/30 text-amber-900 dark:text-amber-100"
            : isSuccess
            ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-900 dark:text-emerald-100"
            : isTimeout
            ? "bg-rose-500/10 border-rose-500/30 text-rose-900 dark:text-rose-100"
            : "bg-amber-500/10 border-amber-500/30 text-amber-900 dark:text-amber-100"
        )}
      >
        <div className="flex items-center gap-3">
          <div
            className={cn(
              "h-10 w-10 rounded-xl flex items-center justify-center shrink-0 border",
              isPerfect
                ? "bg-amber-500/20 border-amber-500/40 text-amber-600 dark:text-amber-400"
                : isSuccess
                ? "bg-emerald-500/20 border-emerald-500/40 text-emerald-600 dark:text-emerald-400"
                : "bg-rose-500/20 border-rose-500/40 text-rose-600 dark:text-rose-400"
            )}
          >
            {isPerfect ? (
              <Trophy className="h-5 w-5 fill-current" />
            ) : isSuccess ? (
              <CheckCircle2 className="h-5 w-5" />
            ) : (
              <AlertTriangle className="h-5 w-5" />
            )}
          </div>
          <div>
            <h3 className="font-black text-sm">
              {isPerfect
                ? "🏆 CAO ĐỘ HOÀN HẢO (PERFECT PITCH)"
                : isSuccess
                ? "✅ CHÍNH XÁC (CORRECT ACCENT)"
                : isTimeout
                ? "⏰ HẾT THỜI GIAN PHẢN XẠ"
                : "⚠️ CẦN ĐIỀU CHỈNH CAO ĐỘ"}
            </h3>
            <p className="text-xs opacity-85">
              {isPerfect
                ? "Đường cao độ F0 và độ đều phách đạt chuẩn giọng Tokyo bản xứ!"
                : isSuccess
                ? "Phát âm tốt, tiếp tục duy trì cao độ ổn định nhé."
                : isTimeout
                ? "Hãy bấm 'Thử lại (R)' để phản xạ nhanh hơn trong ngưỡng thời gian."
                : "Chú ý vị trí hạ giọng (downstep) hoặc độ dài phách trường âm."}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 self-end sm:self-auto shrink-0 font-mono text-xs font-bold">
          <div className="flex items-center gap-1 bg-background/60 px-3 py-1.5 rounded-xl border border-border/80">
            <Clock className="h-3.5 w-3.5 text-primary" />
            <span>Phản xạ: {latency ? `${Math.round(latency)}ms` : "—"}</span>
          </div>
          <div className="flex items-center gap-1 bg-background/60 px-3 py-1.5 rounded-xl border border-border/80">
            <Sparkles className="h-3.5 w-3.5 text-amber-500" />
            <span>Điểm: {score}/100</span>
          </div>
        </div>
      </div>

      {/* 4 Phonetic Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3 rounded-2xl bg-muted/40 border border-border/70 text-center space-y-1">
          <div className="text-[11px] font-bold text-muted-foreground">Độ Chuẩn Cao Độ</div>
          <div className="text-lg font-black font-mono text-sky-600 dark:text-sky-400">{pitchAccuracy}%</div>
          <div className="text-[10px] text-muted-foreground">Tokyo Semitone</div>
        </div>

        <div className="p-3 rounded-2xl bg-muted/40 border border-border/70 text-center space-y-1">
          <div className="text-[11px] font-bold text-muted-foreground">Độ Đều Phách</div>
          <div className="text-lg font-black font-mono text-emerald-600 dark:text-emerald-400">{moraScore}%</div>
          <div className="text-[10px] text-muted-foreground">Mora Timing</div>
        </div>

        <div className="p-3 rounded-2xl bg-muted/40 border border-border/70 text-center space-y-1">
          <div className="text-[11px] font-bold text-muted-foreground">Vô Thanh Hóa</div>
          <div className="text-lg font-black font-mono text-purple-600 dark:text-purple-400">{devoicingScore}%</div>
          <div className="text-[10px] text-muted-foreground">Devoicing i/u</div>
        </div>

        <div className="p-3 rounded-2xl bg-muted/40 border border-border/70 text-center space-y-1">
          <div className="text-[11px] font-bold text-muted-foreground">Độ Tự Nhiên</div>
          <div className="text-lg font-black font-mono text-amber-600 dark:text-amber-400">{naturalnessScore}%</div>
          <div className="text-[10px] text-muted-foreground">Acoustic Balance</div>
        </div>
      </div>

      {/* Dual Voice Comparison */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* User Voice */}
        <div className="p-4 rounded-2xl bg-muted/40 border border-border/70 space-y-2">
          <div className="flex items-center justify-between text-xs font-bold text-muted-foreground">
            <span>🗣️ Bạn đã phát âm (Your Voice):</span>
          </div>
          <div className="p-3 rounded-xl bg-card border border-border/80 text-base font-bold font-jp text-foreground">
            {result.userTranscript || "(Đã ghi âm giọng nói)"}
          </div>
        </div>

        {/* Model Voice */}
        <div className="p-4 rounded-2xl bg-sky-500/5 border border-sky-500/20 space-y-2">
          <div className="flex items-center justify-between text-xs font-bold text-sky-700 dark:text-sky-300">
            <span>👑 Phát âm chuẩn Tokyo (Model Pitch):</span>
            <button
              onClick={() => {
                soundFX.playFurin();
                speakJapaneseText(canonical, { rate: 1.0 });
              }}
              className="hover:underline flex items-center gap-1 font-bold text-primary text-[11px]"
            >
              <Volume2 className="h-3 w-3" />
              <span>Nghe lại</span>
            </button>
          </div>
          <div className="p-3 rounded-xl bg-card border border-sky-500/30 text-base font-bold font-jp text-foreground">
            {canonical}
          </div>
        </div>
      </div>

      {/* Action Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-border">
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              soundFX.playFurin();
              onRetry();
            }}
            className="text-xs font-bold gap-1.5 shadow-2xs"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            <span>Thử lại (R)</span>
          </Button>

          {onAskCoach && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                soundFX.playFurin();
                if (onCancelAutoNext) onCancelAutoNext();
                onAskCoach(`Hãy hướng dẫn cách phát âm chuẩn cao độ Tokyo cho từ "${canonical}".`);
              }}
              className="text-xs font-bold text-amber-700 dark:text-amber-300 hover:bg-amber-500/10 gap-1.5"
            >
              <Sparkles className="h-3.5 w-3.5 text-amber-500" />
              <span>Hỏi Sensei</span>
            </Button>
          )}
        </div>

        <Button
          variant="akane"
          size="sm"
          onClick={() => {
            soundFX.playSuikinkutsu();
            onNext();
          }}
          className="text-xs font-bold gap-1.5 shadow-md ml-auto"
        >
          <span>Câu tiếp theo (Enter)</span>
          <ArrowRight className="h-3.5 w-3.5" />
        </Button>
      </div>
    </div>
  );
}
