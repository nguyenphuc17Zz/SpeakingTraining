"use client";

import React, { useState, useEffect } from "react";
import { UniversalFurigana } from "@/components/japanese/UniversalFurigana";
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
  Lightbulb,
} from "lucide-react";
import { SituationsExercise, SituationsResult } from "../services/situations-api";
import { speakJapaneseText, stopWebSpeech } from "@/features/speaking/services/web-speech";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

interface SituationsResultCardProps {
  result: SituationsResult;
  exercise: SituationsExercise | null;
  onNext: () => void;
  onRetry: () => void;
  onAskCoach?: (prompt: string) => void;
  onCancelAutoNext?: () => void;
}

export function SituationsResultCard({
  result,
  exercise,
  onNext,
  onRetry,
  onAskCoach,
  onCancelAutoNext,
}: SituationsResultCardProps) {
  const [isTTSPlaying, setIsTTSPlaying] = useState(false);
  const isPerfect = result.isPerfect || (result.score ?? 0) >= 90;
  const isSuccess = result.success;
  const isTimeout = result.timedOut;
  const score = result.score ?? 0;
  const latency = result.reactionLatencyMs ?? 0;

  const sc = exercise?.extra_metadata?.situational_config || {};
  const sData = exercise?.situationalData || sc.situational_data || {};
  const canonical = sc.canonical || exercise?.canonical || "";
  const metrics = result.metrics || {};
  const culturalTip = result.culturalTip || sc.cultural_tip || sData.cultural_tip || exercise?.culturalTip || "";

  // Auto-play model answer TTS on result show
  useEffect(() => {
    if (!canonical) return;

    setIsTTSPlaying(true);
    const timer = setTimeout(() => {
      speakJapaneseText(canonical, {
        rate: 0.95,
        onEnd: () => setIsTTSPlaying(false),
        onError: () => setIsTTSPlaying(false),
      });
    }, 200);

    return () => {
      clearTimeout(timer);
      stopWebSpeech();
    };
  }, [canonical, result.exerciseId]);

  const taskCompletion = metrics.task_completion ?? score;
  const pragmatics = metrics.pragmatics ?? 88;
  const fluency = metrics.fluency ?? 85;
  const naturalness = metrics.naturalness ?? 87;

  return (
    <div className="p-5 md:p-6 rounded-3xl border border-border/80 bg-card shadow-md washi-texture space-y-5 animate-in fade-in zoom-in-95 duration-200">
      {/* Status Banner */}
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
                ? "🏆 XỬ LÝ TÌNH HUỐNG XUẤT SẮC"
                : isSuccess
                ? "✅ HOÀN THÀNH MỤC TIÊU ĐỐI THOẠI"
                : isTimeout
                ? "⏰ HẾT THỜI GIAN PHẢN XẠ"
                : "⚠️ CẦN BỔ SUNG MỤC TIÊU"}
            </h3>
            <p className="text-xs opacity-85">
              {result.feedback ||
                (isPerfect
                  ? "Câu trả lời đúng ngữ cảnh, đạt trọn vẹn mục tiêu và tốc độ phản xạ tự nhiên!"
                  : isSuccess
                  ? "Bạn đã hoàn thành tốt tình huống giao tiếp."
                  : isTimeout
                  ? "Hãy bấm 'Thử lại (R)' để phản xạ nhanh hơn trong ngưỡng thời gian."
                  : "Chú ý xử lý sự cố phát sinh và sử dụng mẫu câu tự nhiên hơn.")}
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

      {/* 4 Situational Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3 rounded-2xl bg-muted/40 border border-border/70 text-center space-y-1">
          <div className="text-[11px] font-bold text-muted-foreground">Độ Đạt Mục Tiêu</div>
          <div className="text-lg font-black font-mono text-emerald-600 dark:text-emerald-400">{taskCompletion}%</div>
          <div className="text-[10px] text-muted-foreground">Goal Completion</div>
        </div>

        <div className="p-3 rounded-2xl bg-muted/40 border border-border/70 text-center space-y-1">
          <div className="text-[11px] font-bold text-muted-foreground">Độ Chuẩn Ngữ Dụng</div>
          <div className="text-lg font-black font-mono text-sky-600 dark:text-sky-400">{pragmatics}%</div>
          <div className="text-[10px] text-muted-foreground">Pragmatic Match</div>
        </div>

        <div className="p-3 rounded-2xl bg-muted/40 border border-border/70 text-center space-y-1">
          <div className="text-[11px] font-bold text-muted-foreground">Tốc Độ Phản Xạ</div>
          <div className="text-lg font-black font-mono text-purple-600 dark:text-purple-400">{fluency}%</div>
          <div className="text-[10px] text-muted-foreground">Fluency Rate</div>
        </div>

        <div className="p-3 rounded-2xl bg-muted/40 border border-border/70 text-center space-y-1">
          <div className="text-[11px] font-bold text-muted-foreground">Sắc Thái Tự Nhiên</div>
          <div className="text-lg font-black font-mono text-amber-600 dark:text-amber-400">{naturalness}%</div>
          <div className="text-[10px] text-muted-foreground">Social Tone</div>
        </div>
      </div>

      {/* Dual Voice Dialogue Comparison */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* User Voice */}
        <div className="p-4 rounded-2xl bg-muted/40 border border-border/70 space-y-2">
          <div className="flex items-center justify-between text-xs font-bold text-muted-foreground">
            <span>🗣️ Câu đối đáp của bạn:</span>
          </div>
          <div className="p-3 rounded-xl bg-card border border-border/80 text-base font-bold font-jp text-foreground min-h-[3rem] flex items-center">
            {result.userTranscript ? (
              <UniversalFurigana text={result.userTranscript} fontSize="lg" />
            ) : (
              <span className="text-xs text-muted-foreground italic font-sans font-normal">
                (Đã ghi âm giọng nói)
              </span>
            )}
          </div>
        </div>

        {/* Model Voice */}
        <div className="p-4 rounded-2xl bg-emerald-500/5 border border-emerald-500/20 space-y-2">
          <div className="flex items-center justify-between text-xs font-bold text-emerald-700 dark:text-emerald-300">
            <span>👑 Đáp án mẫu tự nhiên chuẩn Nhật:</span>
            {canonical && (
              <button
                onClick={() => {
                  soundFX.playFurin();
                  speakJapaneseText(canonical, { rate: 1.0 });
                }}
                className="hover:underline flex items-center gap-1 font-bold text-primary text-[11px]"
              >
                <Volume2 className="h-3 w-3" />
                <span>Nghe mẫu</span>
              </button>
            )}
          </div>
          <div className="p-3 rounded-xl bg-card border border-emerald-500/30 text-base font-bold font-jp text-foreground min-h-[3rem] flex items-center">
            <UniversalFurigana text={canonical || "すみません、これをお願いします。"} fontSize="lg" />
          </div>
        </div>
      </div>

      {/* Cultural Nuance Pragmatics Tip */}
      {culturalTip && (
        <div className="p-3.5 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex items-start gap-2.5 text-xs text-amber-800 dark:text-amber-300">
          <Lightbulb className="h-4 w-4 text-amber-500 shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            <span className="font-bold">Mẹo văn hóa thực chiến Nhật Bản:</span>
            <p className="leading-relaxed">{culturalTip}</p>
          </div>
        </div>
      )}

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
                onAskCoach(`Hãy giải thích cách đối đáp tự nhiên và lịch sự hơn cho tình huống "${canonical}".`);
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
          <span>Tình huống tiếp theo (Enter)</span>
          <ArrowRight className="h-3.5 w-3.5" />
        </Button>
      </div>
    </div>
  );
}
