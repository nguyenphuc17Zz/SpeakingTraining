"use client";

import React, { useState, useRef } from "react";
import {
  Award,
  CheckCircle2,
  AlertTriangle,
  TrendingUp,
  Sparkles,
  Volume2,
  RotateCcw,
  ArrowRight,
  Target,
  Mic,
  Pause,
  Play,
  Lightbulb,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { WordDiffDisplay } from "@/features/shadowing/WordDiffDisplay";
import { PracticeAttemptFeedback } from "@/types/shadowing";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

interface ShadowingScoreDisplayProps {
  feedback: PracticeAttemptFeedback;
  targetSentence?: string;
  onRetry?: () => void;
  onNext?: () => void;
}

export function ShadowingScoreDisplay({
  feedback,
  targetSentence,
  onRetry,
  onNext,
}: ShadowingScoreDisplayProps) {
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const getScoreTheme = (s: number) => {
    if (s >= 85) {
      return {
        badge: "bg-matcha-500/20 text-matcha-400 border-matcha-500/40",
        circle: "border-matcha-500 text-matcha-400 shadow-matcha-500/20 bg-matcha-950/40",
        title: "Xuất sắc! (素晴らしい)",
      };
    }
    if (s >= 70) {
      return {
        badge: "bg-aizome-500/20 text-aizome-300 border-aizome-500/40",
        circle: "border-aizome-500 text-aizome-300 shadow-aizome-500/20 bg-aizome-950/40",
        title: "Rất tốt! (よくできました)",
      };
    }
    if (s >= 50) {
      return {
        badge: "bg-kintsugi-500/20 text-kintsugi-300 border-kintsugi-500/40",
        circle: "border-kintsugi-500 text-kintsugi-300 shadow-kintsugi-500/20 bg-kintsugi-950/40",
        title: "Đã hoàn thành (練習中)",
      };
    }
    return {
      badge: "bg-rose-500/20 text-rose-300 border-rose-500/40",
      circle: "border-rose-500 text-rose-400 shadow-rose-500/20 bg-rose-950/40",
      title: "Cần luyện thêm (もう一度)",
    };
  };

  const theme = getScoreTheme(feedback.score);
  const targetText = feedback.target_text || targetSentence || "";

  const handleToggleUserAudio = () => {
    if (!feedback.user_audio_url) return;

    if (isPlayingAudio) {
      audioRef.current?.pause();
      setIsPlayingAudio(false);
    } else {
      if (!audioRef.current) {
        audioRef.current = new Audio(feedback.user_audio_url);
        audioRef.current.onended = () => setIsPlayingAudio(false);
      } else {
        audioRef.current.src = feedback.user_audio_url;
      }
      audioRef.current.play();
      setIsPlayingAudio(true);
    }
  };

  return (
    <div className="p-4 sm:p-5 rounded-3xl bg-card/95 border border-border/90 washi-texture backdrop-blur-xl shadow-sumi-lg space-y-4 animate-in fade-in zoom-in-95 duration-200">
      {/* 1. Header: Score Circle & Verdict Message */}
      <div className="flex items-center justify-between gap-3 pb-3 border-b border-border/70">
        <div className="flex items-center gap-3.5">
          {/* Big Circular Score Display */}
          <div
            className={cn(
              "w-14 h-14 sm:w-16 sm:h-16 rounded-2xl flex flex-col items-center justify-center border-2 font-mono font-black shrink-0 shadow-md",
              theme.circle
            )}
          >
            <span className="text-xl sm:text-2xl leading-none">{Math.round(feedback.score)}</span>
            <span className="text-[9.5px] uppercase font-sans tracking-tight opacity-75 mt-0.5">Điểm</span>
          </div>

          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="text-sm sm:text-base font-black text-foreground font-sans tracking-tight">
                {feedback.score === 0 ? "Không nhận diện được giọng nói" : theme.title}
              </h3>
              <Badge variant="fuji" size="sm" className="text-[10px] uppercase font-mono px-2 py-0.5">
                {feedback.mastery}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground leading-relaxed">
              {feedback.feedback}
            </p>
          </div>
        </div>

        {/* Listen Recording Button */}
        {feedback.user_audio_url && (
          <Button
            variant="outline"
            size="sm"
            onClick={handleToggleUserAudio}
            className={cn(
              "text-xs font-semibold h-10 px-3.5 rounded-xl border-border bg-background/80 hover:border-primary/50 gap-2 shrink-0 shadow-xs transition-all",
              isPlayingAudio && "border-primary text-primary ring-2 ring-primary/20 bg-primary/10"
            )}
          >
            {isPlayingAudio ? (
              <>
                <Pause className="h-4 w-4 text-primary fill-primary" />
                <span className="hidden sm:inline">Dừng phát</span>
                <span className="flex gap-0.5 items-end h-3">
                  <span className="w-1 h-3 bg-primary rounded-full animate-bounce" />
                  <span className="w-1 h-2 bg-primary rounded-full animate-bounce delay-75" />
                  <span className="w-1 h-3 bg-primary rounded-full animate-bounce delay-150" />
                </span>
              </>
            ) : (
              <>
                <Volume2 className="h-4 w-4 text-primary" />
                <span className="hidden sm:inline">Nghe lại giọng bạn</span>
              </>
            )}
          </Button>
        )}
      </div>

      {/* 2. Core Studio: What you spoke vs Native Target Diff */}
      <div className="space-y-3">
        {targetText && (
          <WordDiffDisplay
            targetText={targetText}
            userText={feedback.user_transcript}
          />
        )}
      </div>

      {/* 3. 4-Dimensional Metrics Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 pt-1">
        <div className="p-2.5 rounded-xl bg-background/80 border border-border text-center space-y-0.5 shadow-xs">
          <span className="text-[11px] text-muted-foreground font-medium block">Độ chính xác từ</span>
          <p className="text-base font-bold font-mono text-emerald-400">
            {Math.round(feedback.accuracy_score)}%
          </p>
        </div>

        <div className="p-2.5 rounded-xl bg-background/80 border border-border text-center space-y-0.5 shadow-xs">
          <span className="text-[11px] text-muted-foreground font-medium block">Tốc độ & Nhịp</span>
          <p className="text-base font-bold font-mono text-aizome-300">
            {Math.round(feedback.timing_score)}%
          </p>
        </div>

        <div className="p-2.5 rounded-xl bg-background/80 border border-border text-center space-y-0.5 shadow-xs">
          <span className="text-[11px] text-muted-foreground font-medium block">Cao độ & Ngữ điệu</span>
          <p className="text-base font-bold font-mono text-kintsugi-300">
            {Math.round(feedback.rhythm_score)}%
          </p>
        </div>

        <div className="p-2.5 rounded-xl bg-background/80 border border-border text-center space-y-0.5 shadow-xs">
          <span className="text-[11px] text-muted-foreground font-medium block">Âm vị chuẩn</span>
          <p className="text-base font-bold font-mono text-primary">
            {Math.round(feedback.pronunciation_score)}%
          </p>
        </div>
      </div>

      {/* 4. Actionable Guidance / Practice Tip (Max 2 focused issues) */}
      {feedback.top_issues && feedback.top_issues.length > 0 && (
        <div className="p-3.5 rounded-2xl bg-amber-500/10 border border-amber-500/25 space-y-2">
          <div className="flex items-center gap-1.5 text-xs font-bold text-amber-300">
            <Lightbulb className="h-4 w-4 text-amber-400 shrink-0" />
            <span>Mẹo cải thiện nhanh cho câu này:</span>
          </div>

          <div className="space-y-1.5 pl-5 text-xs text-foreground/90">
            {feedback.top_issues.slice(0, 2).map((issue, i) => (
              <div key={i} className="space-y-0.5">
                <p className="font-semibold text-amber-200">
                  • {issue.title}: <span className="font-normal text-muted-foreground">{issue.explanation}</span>
                </p>
                {issue.practice_tip && (
                  <p className="text-[11.5px] text-aizome-300 italic pl-2.5">
                    👉 {issue.practice_tip}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 5. Action Buttons Footer */}
      <div className="flex items-center justify-between pt-1 border-t border-border/60">
        {feedback.mastery_delta !== 0 ? (
          <div className="inline-flex items-center gap-1.5 text-xs font-mono text-aizome-300 font-bold">
            <TrendingUp className="h-3.5 w-3.5 text-aizome-400" />
            <span>
              {feedback.mastery_delta > 0 ? `+${(feedback.mastery_delta * 100).toFixed(0)}%` : `${(feedback.mastery_delta * 100).toFixed(0)}%`} Tiến độ
            </span>
          </div>
        ) : (
          <div />
        )}

        <div className="flex items-center gap-2">
          {onRetry && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                soundFX.playTaiko();
                onRetry();
              }}
              className="text-xs font-bold h-9 px-3.5 rounded-xl border-border bg-background hover:border-primary/50 gap-1.5"
            >
              <RotateCcw className="h-3.5 w-3.5 text-primary" />
              <span>Luyện lại câu này</span>
            </Button>
          )}

          {onNext && feedback.score >= 70 && (
            <Button
              variant="primary"
              size="sm"
              onClick={() => {
                soundFX.playTaiko();
                onNext();
              }}
              className="text-xs font-bold h-9 px-3.5 rounded-xl gap-1.5 bg-primary text-primary-foreground shadow-sm"
            >
              <span>Câu tiếp theo</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

