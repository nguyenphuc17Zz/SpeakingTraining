"use client";

import React, { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  CheckCircle2,
  XCircle,
  Clock,
  Zap,
  Trophy,
  RotateCcw,
  ArrowRight,
  Volume2,
  Play,
  Pause,
  Mic,
  Crown,
  AlertTriangle,
  MessageSquare,
} from "lucide-react";
import type { KeigoResult, KeigoExercise } from "../services/keigo-api";
import { speakJapaneseText, stopWebSpeech } from "@/features/speaking/services/web-speech";
import { cn } from "@/lib/utils";

interface Props {
  result: KeigoResult | null;
  exercise?: KeigoExercise | null;
  onNext?: () => void;
  onRetry?: () => void;
  onAskCoach?: (prompt: string) => void;
  onCancelAutoNext?: () => void;
}

export function KeigoResultCard({
  result,
  exercise,
  onNext,
  onRetry,
  onAskCoach,
  onCancelAutoNext,
}: Props) {
  const [isUserAudioPlaying, setIsUserAudioPlaying] = useState(false);
  const [userAudioCurrentTime, setUserAudioCurrentTime] = useState(0);
  const [userAudioDuration, setUserAudioDuration] = useState(0);
  const [isTTSPlaying, setIsTTSPlaying] = useState(false);

  const userAudioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    setIsUserAudioPlaying(false);
    setUserAudioCurrentTime(0);
    setUserAudioDuration(0);
  }, [result]);

  if (!result) return null;

  const isPerfect = result.isPerfect;
  const isTimeout = result.timedOut;
  const isCorrect = result.success;
  const latency = result.reactionLatencyMs;
  const timerLimit = result.timerLimitMs || 5000;
  const latencyRatio = latency != null ? Math.min(1, latency / timerLimit) : 1;

  const canonical =
    result.canonicalAnswer ||
    exercise?.canonical ||
    (exercise?.target_patterns && exercise.target_patterns.length > 0 ? exercise.target_patterns[0] : "") ||
    "";

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

    return () => clearTimeout(timer);
  }, [result.exerciseId, canonical]);

  const variants =
    result.acceptableVariants ||
    exercise?.acceptableVariants ||
    (exercise?.extra_metadata?.keigo_config?.acceptable_variants as string[]) ||
    [];

  const togglePlayUserAudio = () => {
    onCancelAutoNext?.();
    if (!userAudioRef.current || !result.userAudioUrl) return;

    if (isUserAudioPlaying) {
      userAudioRef.current.pause();
      setIsUserAudioPlaying(false);
    } else {
      stopWebSpeech();
      setIsTTSPlaying(false);
      userAudioRef.current
        .play()
        .then(() => setIsUserAudioPlaying(true))
        .catch(() => setIsUserAudioPlaying(false));
    }
  };

  const handlePlayModelTTS = () => {
    onCancelAutoNext?.();
    if (!canonical) return;

    if (isUserAudioPlaying && userAudioRef.current) {
      userAudioRef.current.pause();
      setIsUserAudioPlaying(false);
    }

    if (isTTSPlaying) {
      stopWebSpeech();
      setIsTTSPlaying(false);
      return;
    }

    setIsTTSPlaying(true);
    speakJapaneseText(canonical, {
      rate: 0.95,
      onEnd: () => setIsTTSPlaying(false),
      onError: () => setIsTTSPlaying(false),
    });
  };

  const formatAudioTime = (seconds: number) => {
    const s = Math.floor(seconds % 60);
    const m = Math.floor(seconds / 60);
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  const statusConfig = isTimeout
    ? {
        label: "HẾT GIỜ (TIME'S UP)",
        icon: <Clock className="h-4 w-4" />,
        badgeClass: "bg-muted text-muted-foreground border-border",
        borderClass: "border-border/80 bg-muted/20",
        scoreColor: "text-muted-foreground",
      }
    : isPerfect
    ? {
        label: "HOÀN HẢO (PERFECT KEIGO)",
        icon: <Trophy className="h-4 w-4 text-amber-300" />,
        badgeClass: "bg-amber-500 text-sumi-950 font-black border-amber-400 shadow-md shadow-amber-500/20",
        borderClass: "border-amber-500/40 bg-amber-500/8 dark:bg-amber-950/20",
        scoreColor: "text-amber-600 dark:text-amber-400",
      }
    : isCorrect
    ? {
        label: "CHÍNH XÁC (CORRECT)",
        icon: <CheckCircle2 className="h-4 w-4" />,
        badgeClass: "bg-emerald-600 text-white font-bold border-emerald-500",
        borderClass: "border-emerald-500/30 bg-emerald-500/8 dark:bg-emerald-950/20",
        scoreColor: "text-emerald-600 dark:text-emerald-400",
      }
    : {
        label: "CẦN CỐ GẮNG (TRY AGAIN)",
        icon: <XCircle className="h-4 w-4" />,
        badgeClass: "bg-rose-600 text-white font-bold border-rose-500",
        borderClass: "border-rose-500/30 bg-rose-500/8 dark:bg-rose-950/20",
        scoreColor: "text-rose-600 dark:text-rose-400",
      };

  return (
    <div
      className={cn(
        "rounded-3xl border p-5 md:p-6 space-y-4 shadow-lg transition-all animate-in fade-in zoom-in-95 duration-200 washi-texture",
        statusConfig.borderClass
      )}
    >
      {result.userAudioUrl && (
        <audio
          ref={userAudioRef}
          src={result.userAudioUrl}
          onLoadedMetadata={() => {
            if (userAudioRef.current) setUserAudioDuration(userAudioRef.current.duration || 0);
          }}
          onTimeUpdate={() => {
            if (userAudioRef.current) setUserAudioCurrentTime(userAudioRef.current.currentTime || 0);
          }}
          onEnded={() => {
            setIsUserAudioPlaying(false);
            setUserAudioCurrentTime(0);
          }}
          onError={() => setIsUserAudioPlaying(false)}
        />
      )}

      {/* 1. Status & Latency Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <span
          className={cn(
            "inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-bold border shadow-2xs",
            statusConfig.badgeClass
          )}
        >
          {statusConfig.icon}
          <span>{statusConfig.label}</span>
        </span>

        {latency != null && (
          <div className="flex items-center gap-2 text-xs font-mono font-bold text-foreground">
            <Zap className="h-3.5 w-3.5 text-amber-500" />
            <span>Phản xạ: {Math.round(latency)}ms</span>
            <span className="text-muted-foreground font-normal">/ {timerLimit / 1000}s</span>
          </div>
        )}
      </div>

      {/* Latency Speed Bar */}
      {latency != null && (
        <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden border border-border/50">
          <div
            className={cn(
              "h-full rounded-full transition-all duration-500",
              latencyRatio < 0.5
                ? "bg-emerald-500"
                : latencyRatio < 0.75
                ? "bg-amber-500"
                : "bg-rose-500"
            )}
            style={{ width: `${latencyRatio * 100}%` }}
          />
        </div>
      )}

      {/* 2. Feedback Banner */}
      <div className="flex items-start gap-4 p-3.5 rounded-2xl bg-card border border-border/80 shadow-xs">
        <div className="flex flex-col items-center justify-center p-3 rounded-xl bg-muted/60 border border-border shrink-0 min-w-[68px]">
          <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Điểm</span>
          <span className={cn("text-2xl font-black font-mono", statusConfig.scoreColor)}>
            {result.score.toFixed(0)}
          </span>
        </div>

        <div className="flex-1 min-w-0 space-y-1">
          <p className="text-sm font-bold text-foreground leading-snug">{result.feedback}</p>
          {result.doubleKeigo && (
            <div className="flex items-center gap-1 text-xs text-amber-600 dark:text-amber-400 font-semibold">
              <AlertTriangle className="h-3.5 w-3.5" />
              <span>Cảnh báo: Phát hiện dấu hiệu lặp kính ngữ (Double Keigo)</span>
            </div>
          )}
        </div>
      </div>

      {/* 3. DUAL CORE COMPARISON */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
        {/* CARD A: Your Voice */}
        <div className="p-4 rounded-2xl bg-card border border-border/80 shadow-xs space-y-3 flex flex-col justify-between">
          <div className="space-y-1.5">
            <div className="flex items-center justify-between gap-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                <Mic className="h-3.5 w-3.5 text-primary" />
                <span>Bạn đã nói (Your Voice)</span>
              </span>
              {result.transcript && (
                <span className="text-[10px] px-2 py-0.5 rounded-md bg-muted text-muted-foreground font-mono">
                  ja-JP
                </span>
              )}
            </div>

            <div className="text-base font-black font-jp text-foreground min-h-[1.75rem] flex items-center">
              {result.transcript ? (
                <span>“{result.transcript}”</span>
              ) : (
                <span className="text-xs text-muted-foreground italic font-sans font-normal">
                  {isTimeout ? "Không nhận diện được giọng nói (Hết giờ)" : "Không có âm thanh thu âm"}
                </span>
              )}
            </div>
          </div>

          {result.userAudioUrl ? (
            <div className="pt-2 border-t border-border/60 flex items-center gap-2.5">
              <Button
                size="sm"
                variant={isUserAudioPlaying ? "sakura" : "outline"}
                onClick={togglePlayUserAudio}
                className="h-8 w-8 rounded-full p-0 shrink-0 shadow-2xs"
                title="Nghe lại giọng của bạn"
              >
                {isUserAudioPlaying ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5 ml-0.5" />}
              </Button>
              <div className="flex-1 min-w-0 space-y-1">
                <div className="flex items-center justify-between text-[10px] font-mono text-muted-foreground">
                  <span>{formatAudioTime(userAudioCurrentTime)}</span>
                  <span>{formatAudioTime(userAudioDuration || 0)}</span>
                </div>
                <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary transition-all duration-100"
                    style={{
                      width: `${userAudioDuration ? (userAudioCurrentTime / userAudioDuration) * 100 : 0}%`,
                    }}
                  />
                </div>
              </div>
            </div>
          ) : (
            <div className="pt-2 border-t border-border/60 text-[10px] text-muted-foreground italic">
              Không có bản ghi âm
            </div>
          )}
        </div>

        {/* CARD B: Model Answer */}
        <div className="p-4 rounded-2xl bg-card border border-border/80 shadow-xs space-y-3 flex flex-col justify-between">
          <div className="space-y-1.5">
            <div className="flex items-center justify-between gap-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-primary flex items-center gap-1.5">
                <Crown className="h-3.5 w-3.5 text-amber-500" />
                <span>Đáp án Kính ngữ chuẩn</span>
              </span>
              <Badge variant="matcha" size="sm" className="text-[10px]">Chuẩn công sở</Badge>
            </div>

            <div className="text-base font-black font-jp text-primary min-h-[1.75rem] flex items-center">
              {canonical ? (
                <span>“{canonical}”</span>
              ) : (
                <span className="text-xs text-muted-foreground italic font-sans font-normal">
                  Chưa có đáp án mẫu
                </span>
              )}
            </div>
          </div>

          <div className="pt-2 border-t border-border/60 flex items-center justify-between gap-2">
            <Button
              size="sm"
              variant={isTTSPlaying ? "akane" : "outline"}
              onClick={handlePlayModelTTS}
              className="gap-1.5 text-xs font-bold shrink-0"
            >
              <Volume2 className={cn("h-3.5 w-3.5", isTTSPlaying && "animate-bounce")} />
              <span>{isTTSPlaying ? "Đang phát..." : "Nghe mẫu (TTS)"}</span>
            </Button>

            {variants.length > 1 && (
              <div className="text-[10px] text-muted-foreground truncate font-jp" title={variants.join(" / ")}>
                +{variants.length - 1} cách nói khác
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 4. Bottom Action Controls */}
      <div className="pt-2 flex flex-wrap items-center gap-2">
        {onNext && (
          <Button size="sm" variant="akane" onClick={onNext} className="flex-1 gap-1.5 font-bold min-w-[130px]">
            <span>Câu tiếp theo (Enter)</span>
            <ArrowRight className="h-4 w-4" />
          </Button>
        )}

        {onRetry && (
          <Button size="sm" variant="outline" onClick={onRetry} className="gap-1.5 font-bold">
            <RotateCcw className="h-3.5 w-3.5" />
            <span>Thử lại (R)</span>
          </Button>
        )}

        {onAskCoach && canonical && (
          <Button
            size="sm"
            variant="ghost"
            onClick={() =>
              onAskCoach(`Giải thích ngắn gọn sắc thái và cách dùng kính ngữ trong câu: "${canonical}"`)
            }
            className="gap-1.5 text-xs text-primary font-bold ml-auto"
          >
            <MessageSquare className="h-3.5 w-3.5" />
            <span>Hỏi Sensei</span>
          </Button>
        )}
      </div>
    </div>
  );
}
