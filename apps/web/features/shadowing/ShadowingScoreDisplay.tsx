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

export interface ShadowingScoreDisplayProps {
  feedback: PracticeAttemptFeedback;
  targetSentence?: string;
  onRetry?: () => void;
  onNext?: () => void;
  onPlayReference?: () => void;
}

export function ShadowingScoreDisplay({
  feedback,
  targetSentence,
  onRetry,
  onNext,
  onPlayReference,
}: ShadowingScoreDisplayProps) {
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const getScoreTheme = (s: number) => {
    if (s >= 85) {
      return {
        badge: "bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 border-emerald-500/40",
        border: "border-emerald-500/40",
        title: "🌟 Xuất sắc! (素晴らしい)",
      };
    }
    if (s >= 70) {
      return {
        badge: "bg-sky-500/20 text-sky-600 dark:text-sky-400 border-sky-500/40",
        border: "border-sky-500/40",
        title: "👍 Rất tốt! (よくできました)",
      };
    }
    if (s >= 50) {
      return {
        badge: "bg-amber-500/20 text-amber-600 dark:text-amber-400 border-amber-500/40",
        border: "border-amber-500/40",
        title: "💪 Đạt yêu cầu (練習中)",
      };
    }
    return {
      badge: "bg-rose-500/20 text-rose-600 dark:text-rose-400 border-rose-500/40",
      border: "border-rose-500/40",
      title: "🔄 Cần luyện thêm (もう一度)",
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
    <div className={cn("p-3.5 sm:p-4 rounded-2xl bg-card/95 border washi-texture shadow-xs space-y-3 animate-in fade-in duration-200", theme.border)}>
      {/* 1. Header: Score & Verdict */}
      <div className="flex items-center justify-between gap-2 border-b border-border/50 pb-2">
        <div className="flex items-center gap-2.5">
          <div className={cn("px-2.5 py-1 rounded-xl font-mono font-black text-lg sm:text-xl border shadow-2xs", theme.badge)}>
            {Math.round(feedback.score)}đ
          </div>
          <div>
            <div className="text-xs font-bold text-foreground">{theme.title}</div>
            <div className="text-[10px] text-muted-foreground">
              {feedback.feedback || "Hoàn thành bài luyện nói Shadowing"}
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-1.5 shrink-0">
          {onRetry && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                soundFX.playFurin();
                onRetry();
              }}
              className="h-8 px-2.5 text-xs font-bold rounded-xl gap-1"
            >
              <RotateCcw className="h-3 w-3" />
              <span>Thử lại</span>
            </Button>
          )}

          {onNext && (
            <Button
              variant="akane"
              size="sm"
              onClick={() => {
                soundFX.playTaiko();
                onNext();
              }}
              className="h-8 px-3 text-xs font-bold rounded-xl gap-1 shadow-2xs"
            >
              <span>Câu tiếp</span>
              <ArrowRight className="h-3 w-3" />
            </Button>
          )}
        </div>
      </div>

      {/* 2. 4-Dimension Metric Bars (Mora, Timing, Pitch, Rhythm) */}
      <div className="grid grid-cols-4 gap-1.5 text-center">
        <div className="p-1.5 rounded-xl bg-muted/40 border border-border/60 space-y-0.5">
          <div className="text-[9px] font-bold text-muted-foreground">Âm Vị (Mora)</div>
          <div className="text-xs font-mono font-black text-foreground">
            {Math.round(feedback.accuracy_score || 0)}%
          </div>
        </div>
        <div className="p-1.5 rounded-xl bg-muted/40 border border-border/60 space-y-0.5">
          <div className="text-[9px] font-bold text-muted-foreground">Nhịp Độ (Tempo)</div>
          <div className="text-xs font-mono font-black text-foreground">
            {Math.round(feedback.timing_score || 0)}%
          </div>
        </div>
        <div className="p-1.5 rounded-xl bg-muted/40 border border-border/60 space-y-0.5">
          <div className="text-[9px] font-bold text-muted-foreground">Cao Độ (Pitch)</div>
          <div className="text-xs font-mono font-black text-foreground">
            {Math.round(feedback.pronunciation_score || 0)}%
          </div>
        </div>
        <div className="p-1.5 rounded-xl bg-muted/40 border border-border/60 space-y-0.5">
          <div className="text-[9px] font-bold text-muted-foreground">Độ Mượt (Flow)</div>
          <div className="text-xs font-mono font-black text-foreground">
            {Math.round(feedback.rhythm_score || 0)}%
          </div>
        </div>
      </div>

      {/* 3. A/B Audio Comparison Player */}
      <div className="p-2 rounded-xl bg-muted/30 border border-border/60 flex items-center justify-between gap-2">
        <span className="text-[11px] font-bold text-muted-foreground flex items-center gap-1">
          <Volume2 className="h-3.5 w-3.5 text-primary" />
          <span>Nghe đối chiếu A/B:</span>
        </span>

        <div className="flex items-center gap-1.5">
          {onPlayReference && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                soundFX.playFurin();
                onPlayReference();
              }}
              className="h-7 px-2 text-[10px] font-bold rounded-lg gap-1 border-primary/40 text-primary hover:bg-primary/10"
            >
              <Volume2 className="h-3 w-3" />
              <span>🔊 Mẫu Bản Xứ</span>
            </Button>
          )}

          {feedback.user_audio_url && (
            <Button
              variant={isPlayingAudio ? "akane" : "outline"}
              size="sm"
              onClick={handleToggleUserAudio}
              className="h-7 px-2 text-[10px] font-bold rounded-lg gap-1 border-rose-500/40 text-rose-600 dark:text-rose-400 hover:bg-rose-500/10"
            >
              <Mic className="h-3 w-3" />
              <span>{isPlayingAudio ? "⏹️ Đang phát..." : "🎙️ Giọng Của Bạn"}</span>
            </Button>
          )}
        </div>
      </div>

      {/* 4. Word Diff Highlighter */}
      {targetText && (
        <div className="space-y-1 pt-1 border-t border-border/40">
          <div className="text-[10px] font-bold text-muted-foreground">Đối chiếu phát âm từng âm tiết:</div>
          <WordDiffDisplay
            targetText={targetText}
            userText={feedback.user_transcript}
          />
        </div>
      )}
    </div>
  );
}
