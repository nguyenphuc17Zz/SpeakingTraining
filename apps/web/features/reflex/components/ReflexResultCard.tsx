"use client";

import React, { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
  CheckCircle2,
  XCircle,
  Clock,
  Zap,
  Trophy,
  RotateCcw,
  ArrowRight,
  Sparkles,
  Sliders,
  Volume2,
  Play,
  Pause,
  Mic,
  Check,
  Crown,
} from "lucide-react";
import type { ReflexResult, ReflexExercise } from "../services/reflex-api";
import { speakJapaneseText, stopWebSpeech } from "@/features/speaking/services/web-speech";
import { formatJapaneseConjugationTarget } from "./ReflexPromptCard";
import { cn } from "@/lib/utils";

interface Props {
  result: ReflexResult | null;
  exercise?: ReflexExercise | null;
  onNext?: () => void;
  onRetry?: () => void;
  onSlowMode?: () => void;
  onCancelAutoNext?: () => void;
}

export function ReflexResultCard({
  result,
  exercise,
  onNext,
  onRetry,
  onSlowMode,
  onCancelAutoNext,
}: Props) {
  const [isUserAudioPlaying, setIsUserAudioPlaying] = useState(false);
  const [userAudioCurrentTime, setUserAudioCurrentTime] = useState(0);
  const [userAudioDuration, setUserAudioDuration] = useState(0);
  const [isTTSPlaying, setIsTTSPlaying] = useState(false);

  const userAudioRef = useRef<HTMLAudioElement | null>(null);
  const autoPlayedRef = useRef<string | null>(null);

  // Sync user audio duration and state
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
  const timerLimit = result.timerLimitMs || 3000;
  const latencyRatio = latency != null ? Math.min(1, latency / timerLimit) : 1;

  // Resolve Canonical Answer & Vocabulary Context
  const isVocab = exercise?.exercise_type === "reflex_vocabulary";
  const isKeigoVocab = exercise?.exercise_type === "reflex_keigo_vocab";
  const rc = exercise?.extra_metadata?.reflex_config || {};
  const vocabDirection = rc.direction || "ja_to_vi";
  const promptText = rc.prompt || "";
  const wordReading = rc.word_reading || rc.prompt_reading || "";
  const wordMeaningVi = rc.word_meaning_vi || rc.prompt_translation || "";

  const keigoTargetType = rc.target_type || "sonkeigo";
  const keigoTargetLabel = rc.target_label_vi || "Kính ngữ";
  const tripletSonkeigo = rc.triplet_sonkeigo || "";
  const tripletKenjougo = rc.triplet_kenjougo || "";
  const explanationVi = rc.explanation_vi || "";

  const canonical =
    result.canonicalAnswer ||
    exercise?.canonical ||
    (exercise?.target_patterns && exercise.target_patterns.length > 0 ? exercise.target_patterns[0] : "") ||
    "";

  // For TTS: if ja_to_vi, the Japanese word to pronounce is promptText (e.g. 食べる)
  const ttsText = (isVocab && vocabDirection === "ja_to_vi") ? (promptText || canonical) : canonical;

  const playedExerciseIdRef = useRef<string | null>(null);

  // Auto-play model answer TTS when result is first shown
  useEffect(() => {
    if (!ttsText) return;
    const currentId = result.exerciseId || (exercise as any)?.id || "result";
    if (playedExerciseIdRef.current === currentId) return;
    playedExerciseIdRef.current = currentId;

    setIsTTSPlaying(true);
    const timer = setTimeout(() => {
      speakJapaneseText(ttsText, {
        rate: 0.95,
        onEnd: () => setIsTTSPlaying(false),
        onError: () => setIsTTSPlaying(false),
      });
    }, 100);

    return () => {
      clearTimeout(timer);
    };
  }, [result.exerciseId, (exercise as any)?.id, ttsText]);

  // Resolve acceptable variants
  const variants =
    result.acceptableVariants ||
    exercise?.acceptableVariants ||
    (exercise?.extra_metadata?.reflex_config?.acceptable_variants as string[]) ||
    [];

  const rawTarget = result.targetForm || exercise?.extra_metadata?.reflex_config?.conjugation_target || "";
  const targetLabel = formatJapaneseConjugationTarget(rawTarget);

  // User Audio Playback toggle
  const togglePlayUserAudio = () => {
    onCancelAutoNext?.();
    if (!userAudioRef.current || !result.userAudioUrl) return;

    if (isUserAudioPlaying) {
      userAudioRef.current.pause();
      setIsUserAudioPlaying(false);
    } else {
      stopWebSpeech();
      setIsTTSPlaying(false);
      userAudioRef.current.play().then(() => {
        setIsUserAudioPlaying(true);
      }).catch((e) => {
        console.warn("[ReflexResultCard] Audio play error:", e);
      });
    }
  };

  // Play Model Answer TTS
  const handlePlayModelTTS = () => {
    onCancelAutoNext?.();
    if (!ttsText) return;

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
    speakJapaneseText(ttsText, {
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

  // Status configuration
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
        label: "HOÀN HẢO (PERFECT REFLEX)",
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
      {/* Hidden HTML5 audio element for User voice playback */}
      {result.userAudioUrl && (
        <audio
          ref={userAudioRef}
          src={result.userAudioUrl}
          onLoadedMetadata={() => {
            if (userAudioRef.current) {
              setUserAudioDuration(userAudioRef.current.duration || 0);
            }
          }}
          onTimeUpdate={() => {
            if (userAudioRef.current) {
              setUserAudioCurrentTime(userAudioRef.current.currentTime || 0);
            }
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

      {/* Latency Speed Bar Indicator */}
      {latency != null && (
        <div className="space-y-1">
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
        </div>
      )}

      {/* 2. Feedback Banner with Score */}
      <div className="flex items-start gap-4 p-3.5 rounded-2xl bg-card border border-border/80 shadow-xs">
        <div className="flex flex-col items-center justify-center p-3 rounded-xl bg-muted/60 border border-border shrink-0 min-w-[68px]">
          <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Điểm số</span>
          <span className={cn("text-2xl font-black font-mono", statusConfig.scoreColor)}>
            {result.score.toFixed(0)}
          </span>
        </div>

        <div className="flex-1 min-w-0 space-y-1">
          <p className="text-sm font-bold text-foreground leading-snug">{result.feedback}</p>
          {targetLabel && (
            <p className="text-xs text-muted-foreground">
              Yêu cầu chia: <span className="font-semibold text-primary font-jp">{targetLabel}</span>
            </p>
          )}
        </div>
      </div>

      {/* 3. DUAL CORE COMPARISON: User Voice Audio vs Model Answer (Đáp Án Mẫu) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
        {/* CARD A: Bản Thu Âm & Giọng Của Bạn */}
        <div className="p-4 rounded-2xl bg-card border border-border/80 shadow-xs space-y-3 flex flex-col justify-between">
          <div className="space-y-1.5">
            <div className="flex items-center justify-between gap-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                <Mic className="h-3.5 w-3.5 text-primary" />
                <span>Bạn đã nói</span>
              </span>
              {result.transcript && (
                <span className="text-[10px] px-2 py-0.5 rounded-md bg-muted text-muted-foreground font-mono">
                  STT ja-JP
                </span>
              )}
            </div>

            <div className="text-base font-black font-jp text-foreground min-h-[1.75rem] flex items-center">
              {result.transcript ? (
                <span>“{result.transcript}”</span>
              ) : (
                <span className="text-xs text-muted-foreground italic font-sans font-normal">
                  {isTimeout ? "Không ghi nhận giọng nói (Hết giờ)" : "Không có âm thanh thu âm"}
                </span>
              )}
            </div>
          </div>

          {/* User Audio Player Widget */}
          {result.userAudioUrl ? (
            <div className="p-2.5 px-3 rounded-xl bg-muted/50 border border-border/70 flex items-center justify-between gap-3">
              <button
                type="button"
                onClick={togglePlayUserAudio}
                className={cn(
                  "h-8 w-8 rounded-full flex items-center justify-center transition-all shadow-xs shrink-0",
                  isUserAudioPlaying
                    ? "bg-primary text-primary-foreground animate-pulse"
                    : "bg-primary/10 text-primary hover:bg-primary/20"
                )}
                title={isUserAudioPlaying ? "Tạm dừng audio của bạn" : "Nghe lại giọng nói của bạn"}
              >
                {isUserAudioPlaying ? (
                  <Pause className="h-4 w-4" />
                ) : (
                  <Play className="h-4 w-4 fill-current ml-0.5" />
                )}
              </button>

              <div className="flex-1 min-w-0 space-y-1">
                <div className="flex items-center justify-between text-[10px] font-mono text-muted-foreground font-bold">
                  <span>{isUserAudioPlaying ? "Đang phát giọng bạn..." : "Bản thu âm của bạn"}</span>
                  <span>
                    {formatAudioTime(userAudioCurrentTime)} / {formatAudioTime(userAudioDuration || 0)}
                  </span>
                </div>

                {/* Animated Waveform / Progress Slider */}
                <div className="flex items-center gap-1 h-2">
                  <div className="flex-1 h-1.5 bg-muted-foreground/20 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary rounded-full transition-all duration-100"
                      style={{
                        width: userAudioDuration > 0
                          ? `${(userAudioCurrentTime / userAudioDuration) * 100}%`
                          : "0%",
                      }}
                    />
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-2.5 rounded-xl bg-muted/30 border border-dashed border-border text-[11px] text-muted-foreground text-center italic">
              Không có file ghi âm cho câu này
            </div>
          )}
        </div>

        {/* CARD B: Đáp Án Chuẩn Mẫu (Model Answer & Native TTS) */}
        <div className="p-4 rounded-2xl bg-primary/5 border border-primary/25 shadow-xs space-y-3 flex flex-col justify-between">
          <div className="space-y-1.5">
            <div className="flex items-center justify-between gap-2">
              <span className="text-[11px] font-extrabold uppercase tracking-wider text-primary flex items-center gap-1.5">
                <Check className="h-3.5 w-3.5 stroke-[3]" />
                <span>Đáp án chuẩn mẫu</span>
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-md bg-primary/10 text-primary font-bold">
                Model Answer
              </span>
            </div>

            {targetLabel && (
              <div className="text-xs text-muted-foreground font-semibold flex items-center gap-1.5 flex-wrap">
                <span className="text-[10px] font-bold tracking-wide bg-primary/10 text-primary px-2.5 py-0.5 rounded-md border border-primary/20">
                  {targetLabel}
                </span>
              </div>
            )}

            {/* Keigo Word Special 3-Way Layout */}
            {isKeigoVocab ? (
              <div className="space-y-2">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md border ${
                    keigoTargetType === "sonkeigo"
                      ? "bg-amber-500/15 border-amber-500/30 text-amber-600 dark:text-amber-400"
                      : keigoTargetType === "kenjougo"
                      ? "bg-indigo-500/15 border-indigo-500/30 text-indigo-600 dark:text-indigo-400"
                      : "bg-emerald-500/15 border-emerald-500/30 text-emerald-600 dark:text-emerald-400"
                  }`}>
                    {keigoTargetLabel}
                  </span>
                  {rc.jlpt_level && (
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-muted text-muted-foreground">
                      JLPT {rc.jlpt_level}
                    </span>
                  )}
                </div>

                <div className="text-xl md:text-2xl font-black font-jp text-primary leading-tight">
                  {canonical || "—"}
                </div>

                <div className="text-xs text-muted-foreground font-semibold flex items-center gap-1.5 flex-wrap">
                  <span>Từ gốc:</span>
                  <span className="font-bold text-foreground font-jp">{promptText}</span>
                  {wordReading && wordReading !== promptText && (
                    <span className="text-primary font-jp">({wordReading})</span>
                  )}
                  {wordMeaningVi && (
                    <span>• {wordMeaningVi}</span>
                  )}
                </div>

                {explanationVi && (
                  <p className="text-[11px] font-medium text-amber-700 dark:text-amber-300 bg-amber-500/10 border border-amber-500/20 p-2 rounded-xl">
                    💡 {explanationVi}
                  </p>
                )}

                {/* 3-Way Triplet Comparison for verbs */}
                {(tripletSonkeigo || tripletKenjougo) && (
                  <div className="mt-2 p-2.5 rounded-xl bg-card border border-border/80 grid grid-cols-2 gap-2 text-xs">
                    <div className="space-y-0.5">
                      <span className="text-[10px] font-bold text-amber-600 dark:text-amber-400 flex items-center gap-1">
                        👑 Tôn kính (Sonkei)
                      </span>
                      <p className="font-bold font-jp text-foreground">{tripletSonkeigo || "—"}</p>
                    </div>
                    <div className="space-y-0.5">
                      <span className="text-[10px] font-bold text-indigo-600 dark:text-indigo-400 flex items-center gap-1">
                        🙇 Khiêm nhường (Kenjou)
                      </span>
                      <p className="font-bold font-jp text-foreground">{tripletKenjougo || "—"}</p>
                    </div>
                  </div>
                )}
              </div>
            ) : isVocab ? (
              <div className="space-y-1">
                <div className="text-lg md:text-xl font-black font-jp text-primary leading-tight">
                  {canonical || "—"}
                </div>
                {vocabDirection === "ja_to_vi" ? (
                  <div className="text-xs text-muted-foreground font-semibold flex items-center gap-1.5 flex-wrap">
                    <span>Từ gốc:</span>
                    <span className="font-bold text-foreground font-jp">{promptText}</span>
                    {wordReading && wordReading !== promptText && (
                      <span className="text-primary font-jp">({wordReading})</span>
                    )}
                  </div>
                ) : (
                  <div className="text-xs text-muted-foreground font-semibold flex items-center gap-1.5 flex-wrap">
                    {wordReading && wordReading !== canonical && (
                      <span className="font-bold text-primary font-jp">({wordReading})</span>
                    )}
                    <span>• Nghĩa:</span>
                    <span className="font-bold text-foreground">{promptText}</span>
                  </div>
                )}
              </div>
            ) : (
              /* Standard Big Japanese Canonical Text */
              <div className="text-lg md:text-xl font-black font-jp text-primary leading-tight">
                {canonical || "—"}
              </div>
            )}

            {/* Acceptable Variants if any */}
            {variants.length > 0 && variants[0] !== canonical && (
              <div className="flex flex-wrap items-center gap-1.5 pt-1">
                <span className="text-[10px] text-muted-foreground font-semibold">Các cách khác:</span>
                {variants.map((v, i) => (
                  <span
                    key={i}
                    className="px-2 py-0.5 rounded-md bg-card border border-border text-xs font-bold font-jp text-foreground shadow-2xs"
                  >
                    {v}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Model Answer TTS Audio Button */}
          <div className="pt-1">
            <button
              type="button"
              onClick={handlePlayModelTTS}
              disabled={!canonical}
              className={cn(
                "w-full py-2 px-3 rounded-xl border flex items-center justify-center gap-2 text-xs font-bold transition-all shadow-xs",
                isTTSPlaying
                  ? "bg-primary text-primary-foreground border-primary animate-pulse"
                  : "bg-card text-foreground border-border hover:bg-primary/10 hover:border-primary/40"
              )}
            >
              <Volume2 className={cn("h-4 w-4 text-primary", isTTSPlaying && "text-white animate-bounce")} />
              <span>{isTTSPlaying ? "Đang đọc mẫu..." : "Nghe phát âm chuẩn (Native TTS)"}</span>
            </button>
          </div>
        </div>
      </div>

      {/* 4. 7-Dimension Assessment Pills */}
      {result.assessment && (
        <div className="space-y-1.5">
          <span className="text-[11px] font-bold text-muted-foreground uppercase tracking-wider">
            Phân tích 7 chiều (ReflexAssessment)
          </span>
          <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
            {[
              { label: "Accuracy", score: result.assessment.accuracy?.score ?? result.score, color: "text-emerald-600 dark:text-emerald-400" },
              { label: "Reaction", score: result.assessment.reaction?.score ?? 70, color: "text-amber-600 dark:text-amber-400" },
              { label: "Context", score: result.assessment.context_fit?.score ?? 70, color: "text-sky-600 dark:text-sky-400" },
              { label: "Natural", score: result.assessment.naturalness?.score ?? 70, color: "text-purple-600 dark:text-purple-400" },
              { label: "Fluency", score: result.assessment.fluency?.score ?? 70, color: "text-indigo-600 dark:text-indigo-400" },
              { label: "Complete", score: result.assessment.completeness?.score ?? 85, color: "text-teal-600 dark:text-teal-400" },
            ].map((dim) => (
              <div
                key={dim.label}
                className="p-2 rounded-xl bg-card border border-border/80 text-center shadow-xs"
              >
                <div className="text-[10px] font-bold tracking-tight text-muted-foreground">{dim.label}</div>
                <div className={cn("text-xs font-black font-mono mt-0.5", dim.color)}>
                  {Math.round(dim.score)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 5. Action Buttons Strip */}
      <div className="flex flex-wrap items-center gap-2.5 pt-1">
        <Button
          size="md"
          variant="akane"
          className="flex-1 font-black text-sm md:text-base h-11 rounded-2xl gap-2 shadow-md hover:shadow-lg transition-all animate-bounce ring-2 ring-primary/20"
          onClick={() => {
            stopWebSpeech();
            onNext?.();
          }}
        >
          <span>Câu Tiếp Theo</span>
          <span className="text-[11px] font-mono px-2 py-0.5 rounded-lg bg-black/20 text-white font-bold">Space / Enter</span>
          <ArrowRight className="h-4 w-4" />
        </Button>

        <Button
          size="md"
          variant="outline"
          className="h-11 px-4 rounded-2xl gap-1.5 font-bold border-border"
          onClick={() => {
            stopWebSpeech();
            onRetry?.();
          }}
          title="Luyện tập lại câu này (Phím R)"
        >
          <RotateCcw className="h-4 w-4" />
          <span>Làm lại (R)</span>
        </Button>

        <Button
          size="md"
          variant="outline"
          className="h-11 px-3.5 rounded-2xl gap-1.5 font-bold border-primary/30 text-primary hover:bg-primary/10"
          onClick={handlePlayModelTTS}
          title="Nghe lại phát âm mẫu (Phím A)"
        >
          <Volume2 className={cn("h-4 w-4 text-primary", isTTSPlaying && "animate-bounce")} />
          <span>{isTTSPlaying ? "Đang đọc..." : "Nghe lại (A)"}</span>
        </Button>

        {isTimeout && (
          <Button
            size="md"
            variant="ghost"
            className="h-11 px-3 rounded-2xl text-amber-600 dark:text-amber-400 hover:bg-amber-500/10 gap-1.5 font-bold text-xs"
            onClick={() => {
              stopWebSpeech();
              onSlowMode?.();
            }}
          >
            <Sliders className="h-3.5 w-3.5" />
            <span>Giảm độ khó</span>
          </Button>
        )}
      </div>
    </div>
  );
}

