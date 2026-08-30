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
  const isVocab = exercise?.exercise_type === "reflex_vocabulary" || result.direction !== undefined;
  const isKeigoVocab = exercise?.exercise_type === "reflex_keigo_vocab";
  const rc = exercise?.extra_metadata?.reflex_config || {};
  const vocabDirection = result.direction || rc.direction || "ja_to_vi";
  const promptText = result.promptText || rc.prompt || exercise?.prompt || "";
  const wordReading = result.promptReading || rc.word_reading || rc.prompt_reading || "";
  const wordMeaningVi = result.promptTranslation || rc.word_meaning_vi || rc.prompt_translation || "";
  const vocabCollocationJa = result.collocationJa || rc.collocation_ja || exercise?.collocationJa || "";
  const vocabCollocationVi = result.collocationVi || rc.collocation_vi || exercise?.collocationVi || "";
  const vocabExampleJa = result.exampleJa || rc.example_ja || exercise?.exampleJa || "";
  const vocabExampleVi = result.exampleVi || rc.example_vi || exercise?.exampleVi || "";
  const vocabTypeLabel = result.wordTypeLabel || rc.word_type_label || exercise?.wordTypeLabel || "";

  const keigoTargetType = result.targetType || rc.target_type || "sonkeigo";
  const keigoTargetLabel = result.targetLabel || rc.target_label_vi || "Kính ngữ";
  const tripletSonkeigo = result.tripletSonkeigo || rc.triplet_sonkeigo || "";
  const tripletKenjougo = result.tripletKenjougo || rc.triplet_kenjougo || "";
  const explanationVi = result.explanationVi || rc.explanation_vi || "";
  const keigoFormula = rc.formula || exercise?.formula || "";
  const keigoExampleJa = rc.example_ja || exercise?.exampleJa || result.exampleJa || "";
  const keigoExampleVi = rc.example_vi || exercise?.exampleVi || result.exampleVi || "";
  const keigoSubjectHint = rc.subject_hint_vi || exercise?.subjectHintVi || "";
  const isTransformation = exercise?.exercise_type === "reflex_transformation" || rc.sub_mode === "reflex_transformation";
  const transformSource = exercise?.source || rc.source || promptText || "";
  const transformTargetLabel = exercise?.targetLabel || rc.target_label || rc.targetLabel || exercise?.task || rc.task || "";
  const transformFormula = exercise?.formula || rc.formula || "";
  const transformGrammarNote = exercise?.grammarNote || rc.grammar_note || rc.grammarNote || "";

  const isContext = exercise?.exercise_type === "reflex_context" || rc.sub_mode === "reflex_context";
  const contextRole = exercise?.role || rc.role || rc.relationship || exercise?.relationship || "Đối phương";
  const contextSpeakerJa = exercise?.speakerJa || rc.speaker_ja || promptText || "";
  const contextSpeakerVi = exercise?.speakerVi || rc.speaker_vi || "";
  const contextIntent = exercise?.intent || rc.intent || "";
  const contextCulturalNote = exercise?.culturalNote || rc.cultural_note || rc.culturalNote || "";

  const isQna = exercise?.exercise_type === "reflex_qna" || rc.sub_mode === "reflex_qna";
  const multiAnswers =
    exercise?.multiAnswers ||
    rc.multi_answers ||
    rc.multiAnswers ||
    (exercise as any)?.multi_answers ||
    (exercise as any)?.multiAnswers ||
    (result as any)?.multiAnswers ||
    (result as any)?.extra_metadata?.reflex_config?.multi_answers ||
    null;

  const canonical =
    result.canonicalAnswer ||
    exercise?.canonical ||
    rc.canonical ||
    rc.expected ||
    rc.target ||
    (exercise?.target_patterns && exercise.target_patterns.length > 0 ? exercise.target_patterns[0] : "") ||
    "";

  const vocabWord = rc.word || exercise?.word || canonical || "";

  const effectiveMultiAnswers =
    multiAnswers ||
    ((isQna || isContext) && canonical
      ? {
          positive: { ja: canonical, vi: isContext ? "Nhận lời / Khẳng định chuẩn mực" : "Trả lời khẳng định / Tích cực" },
          negative: { ja: "いいえ、実はあまり...", vi: isContext ? "Từ chối khéo / Đàm phán" : "Khéo léo từ chối / Khác biệt" },
          extended: { ja: `${canonical}。`, vi: isContext ? "Mở rộng thêm giải pháp" : "Mở rộng thêm cảm xúc / Lý do" },
        }
      : null);

  // TTS ALWAYS speaks the MODEL ANSWER (canonical), NEVER the question (promptText)!
  const ttsText = canonical;

  // Auto-play model answer TTS when result is first shown
  useEffect(() => {
    if (!ttsText) return;

    setIsTTSPlaying(true);
    const timer = setTimeout(() => {
      speakJapaneseText(ttsText, {
        rate: 0.95,
        onEnd: () => setIsTTSPlaying(false),
        onError: () => setIsTTSPlaying(false),
      });
    }, 200);

    return () => {
      clearTimeout(timer);
      stopWebSpeech();
    };
  }, [ttsText]);

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
            <span className="text-muted-foreground font-normal">/ {timerLimit > 0 ? `${timerLimit / 1000}s` : "∞"}</span>
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

            {/* 1. SPEED Q&A & CONTEXTUAL REACTION: 3-Way Multi-Angle Model Answers */}
            {(isQna || isContext) && effectiveMultiAnswers ? (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-extrabold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                    <Sparkles className="h-3.5 w-3.5 text-amber-500" />
                    <span>{isContext ? "3 Hướng Phản Hồi Thực Tế (Multi-Angle):" : "3 Hướng Trả Lời Đa Chiều (Multi-Angle):"}</span>
                  </span>
                  <span className="text-[10px] text-muted-foreground font-semibold">Bấm 🔈 để Shadowing</span>
                </div>

                <div className="grid grid-cols-1 gap-2">
                  {/* Positive / Direct Answer */}
                  {effectiveMultiAnswers.positive && (
                    <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/25 flex items-start justify-between gap-2 text-left shadow-2xs">
                      <div className="space-y-0.5 min-w-0">
                        <span className="inline-block text-[9px] font-black uppercase px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-700 dark:text-emerald-300">
                          {isContext ? "🟢 Nhận lời / Khẳng định chuẩn mực" : "🟢 Khẳng định / Tích cực (Positive)"}
                        </span>
                        <p className="text-xs md:text-sm font-bold font-jp text-foreground leading-snug">
                          {effectiveMultiAnswers.positive.ja}
                        </p>
                        {effectiveMultiAnswers.positive.vi && (
                          <p className="text-[11px] text-muted-foreground">
                            {effectiveMultiAnswers.positive.vi}
                          </p>
                        )}
                      </div>
                      <button
                        type="button"
                        onClick={() => speakJapaneseText(effectiveMultiAnswers.positive.ja, { rate: 0.95 })}
                        className="p-1.5 rounded-lg bg-card border border-emerald-500/30 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500/20 shrink-0 shadow-2xs transition-colors"
                        title="Nghe câu trả lời khẳng định"
                      >
                        <Volume2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  )}

                  {/* Negative / Polite Refusal / Negotiation */}
                  {(effectiveMultiAnswers.negative || (effectiveMultiAnswers as any).negotiation) && (
                    <div className="p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/25 flex items-start justify-between gap-2 text-left shadow-2xs">
                      <div className="space-y-0.5 min-w-0">
                        <span className="inline-block text-[9px] font-black uppercase px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-700 dark:text-rose-300">
                          {isContext ? "🟡 Từ chối khéo / Đàm phán lùi hạn" : "🔴 Phủ định / Khéo léo từ chối (Refusal)"}
                        </span>
                        <p className="text-xs md:text-sm font-bold font-jp text-foreground leading-snug">
                          {(effectiveMultiAnswers as any).negotiation?.ja || effectiveMultiAnswers.negative?.ja}
                        </p>
                        {((effectiveMultiAnswers as any).negotiation?.vi || effectiveMultiAnswers.negative?.vi) && (
                          <p className="text-[11px] text-muted-foreground">
                            {(effectiveMultiAnswers as any).negotiation?.vi || effectiveMultiAnswers.negative?.vi}
                          </p>
                        )}
                      </div>
                      <button
                        type="button"
                        onClick={() => speakJapaneseText((effectiveMultiAnswers as any).negotiation?.ja || effectiveMultiAnswers.negative?.ja, { rate: 0.95 })}
                        className="p-1.5 rounded-lg bg-card border border-rose-500/30 text-rose-600 dark:text-rose-400 hover:bg-rose-500/20 shrink-0 shadow-2xs transition-colors"
                        title="Nghe câu trả lời từ chối/đàm phán"
                      >
                        <Volume2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  )}

                  {/* Extended / Reason */}
                  {effectiveMultiAnswers.extended && (
                    <div className="p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/25 flex items-start justify-between gap-2 text-left shadow-2xs">
                      <div className="space-y-0.5 min-w-0">
                        <span className="inline-block text-[9px] font-black uppercase px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-700 dark:text-indigo-300">
                          {isContext ? "🔵 Mở rộng / Báo cáo giải trình" : "🔵 Mở rộng tự nhiên / Thêm lý do (Extended)"}
                        </span>
                        <p className="text-xs md:text-sm font-bold font-jp text-foreground leading-snug">
                          {effectiveMultiAnswers.extended.ja}
                        </p>
                        {effectiveMultiAnswers.extended.vi && (
                          <p className="text-[11px] text-muted-foreground">
                            {effectiveMultiAnswers.extended.vi}
                          </p>
                        )}
                      </div>
                      <button
                        type="button"
                        onClick={() => speakJapaneseText(effectiveMultiAnswers.extended.ja, { rate: 0.95 })}
                        className="p-1.5 rounded-lg bg-card border border-indigo-500/30 text-indigo-600 dark:text-indigo-400 hover:bg-indigo-500/20 shrink-0 shadow-2xs transition-colors"
                        title="Nghe câu trả lời mở rộng"
                      >
                        <Volume2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  )}
                </div>

                {/* Cultural Nuance Takeaway */}
                {isContext && contextCulturalNote && (
                  <div className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-left shadow-2xs space-y-1">
                    <span className="text-[10px] font-extrabold uppercase tracking-wider text-amber-700 dark:text-amber-300 flex items-center gap-1">
                      💡 Bí quyết ứng xử văn hóa Nhật:
                    </span>
                    <p className="text-[11px] font-medium text-amber-900 dark:text-amber-200 leading-relaxed">
                      {contextCulturalNote}
                    </p>
                  </div>
                )}
              </div>
            ) : isKeigoVocab ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between gap-2 flex-wrap">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-md border ${
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
                  <button
                    type="button"
                    onClick={() => speakJapaneseText(canonical, { rate: 0.95 })}
                    className="p-1.5 rounded-lg bg-card border border-border/80 text-foreground hover:bg-muted shrink-0 shadow-2xs transition-colors flex items-center gap-1 text-[11px] font-bold"
                    title="Nghe phát âm từ kính ngữ"
                  >
                    <Volume2 className="h-3.5 w-3.5 text-primary" />
                    <span>Nghe từ</span>
                  </button>
                </div>

                <div className="p-3 rounded-2xl bg-card border border-border/80 space-y-2 shadow-2xs">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xl md:text-2xl font-black font-jp text-primary leading-tight">
                      {canonical || "—"}
                    </span>
                    {wordReading && wordReading !== canonical && (
                      <span className="text-sm font-bold text-muted-foreground font-jp">
                        ({wordReading})
                      </span>
                    )}
                  </div>

                  <div className="text-xs text-muted-foreground font-semibold flex items-center gap-1.5 flex-wrap">
                    <span>Từ gốc (Plain Form):</span>
                    <span className="font-bold text-foreground font-jp">{promptText}</span>
                    {wordMeaningVi && (
                      <span>• Ý nghĩa: <strong className="text-foreground">{wordMeaningVi}</strong></span>
                    )}
                  </div>

                  {keigoFormula && (
                    <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-lg bg-muted/60 border border-border/60 text-[11px] font-mono text-muted-foreground">
                      <span className="font-sans font-bold text-amber-600 dark:text-amber-400 text-[10px]">Công thức:</span>
                      <span className="font-bold font-jp text-foreground">{keigoFormula}</span>
                    </div>
                  )}
                </div>

                {/* 3-Way Triplet Comparison */}
                {(tripletSonkeigo || tripletKenjougo) && (
                  <div className="p-2.5 rounded-2xl bg-card border border-border/80 grid grid-cols-2 gap-2 text-xs shadow-2xs">
                    <div className="space-y-0.5 p-2 rounded-xl bg-amber-500/10 border border-amber-500/20">
                      <span className="text-[10px] font-bold text-amber-700 dark:text-amber-300 flex items-center gap-1">
                        👑 Tôn kính (Sếp / Khách)
                      </span>
                      <p className="font-bold font-jp text-foreground">{tripletSonkeigo || "—"}</p>
                    </div>
                    <div className="space-y-0.5 p-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20">
                      <span className="text-[10px] font-bold text-indigo-700 dark:text-indigo-300 flex items-center gap-1">
                        🙇 Khiêm nhường (Bản thân)
                      </span>
                      <p className="font-bold font-jp text-foreground">{tripletKenjougo || "—"}</p>
                    </div>
                  </div>
                )}

                {/* Business Example Sentence with Native TTS Shadowing */}
                {keigoExampleJa && (
                  <div className="p-3 rounded-2xl bg-muted/40 border border-border/80 space-y-1.5 text-left shadow-2xs">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-[10px] font-extrabold uppercase tracking-wider text-amber-600 dark:text-amber-400 flex items-center gap-1">
                        💬 Câu ví dụ giao tiếp công sở:
                      </span>
                      <button
                        type="button"
                        onClick={() => speakJapaneseText(keigoExampleJa, { rate: 0.95 })}
                        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg bg-card border border-amber-500/30 text-amber-600 dark:text-amber-400 hover:bg-amber-500/15 text-[10px] font-bold shadow-2xs transition-colors"
                        title="Nghe câu ví dụ để Shadowing"
                      >
                        <Volume2 className="h-3 w-3" />
                        <span>Shadowing</span>
                      </button>
                    </div>
                    <p className="text-xs md:text-sm font-bold font-jp text-foreground leading-snug">
                      {keigoExampleJa}
                    </p>
                    {keigoExampleVi && (
                      <p className="text-[11px] text-muted-foreground leading-relaxed">
                        {keigoExampleVi}
                      </p>
                    )}
                  </div>
                )}

                {explanationVi && (
                  <p className="text-[11px] font-medium text-amber-700 dark:text-amber-300 bg-amber-500/10 border border-amber-500/20 p-2 rounded-xl">
                    💡 {explanationVi}
                  </p>
                )}
              </div>
            ) : isVocab ? (
              <div className="space-y-3">
                {/* Header: Word + Furigana reading + Word Type + Audio */}
                <div className="p-3 rounded-2xl bg-card border border-border/80 space-y-2 shadow-2xs">
                  <div className="flex items-center justify-between gap-2 flex-wrap">
                    <div className="flex items-center gap-2">
                      <span className="text-xl md:text-2xl font-black font-jp text-primary leading-tight">
                        {canonical || vocabWord || "—"}
                      </span>
                      {wordReading && wordReading !== canonical && (
                        <span className="text-sm font-bold text-muted-foreground font-jp">
                          ({wordReading})
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-1.5">
                      {vocabTypeLabel && (
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-violet-500/10 text-violet-600 dark:text-violet-400 border border-violet-500/20">
                          {vocabTypeLabel}
                        </span>
                      )}
                      <button
                        type="button"
                        onClick={() => speakJapaneseText(canonical || vocabWord, { rate: 0.95 })}
                        className="p-1.5 rounded-lg bg-violet-500/10 hover:bg-violet-500/20 text-violet-600 dark:text-violet-400 border border-violet-500/30 transition-colors shadow-2xs"
                        title="Nghe phát âm từ vựng"
                      >
                        <Volume2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>

                  <div className="text-xs text-muted-foreground font-semibold flex items-center gap-1.5 flex-wrap">
                    <span>Nghĩa tiếng Việt:</span>
                    <span className="font-bold text-foreground">{wordMeaningVi || promptText}</span>
                  </div>

                  {/* Collocation Blueprint */}
                  {vocabCollocationJa && (
                    <div className="p-2 rounded-xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-between gap-2">
                      <div className="flex items-center gap-1.5 flex-wrap text-xs">
                        <span className="text-[10px] font-extrabold uppercase text-violet-600 dark:text-violet-400">
                          🔗 Cụm Collocation:
                        </span>
                        <span className="font-bold font-jp text-foreground">{vocabCollocationJa}</span>
                        {vocabCollocationVi && (
                          <span className="text-muted-foreground">({vocabCollocationVi})</span>
                        )}
                      </div>
                      <button
                        type="button"
                        onClick={() => speakJapaneseText(vocabCollocationJa, { rate: 0.95 })}
                        className="p-1 rounded-md bg-card border border-violet-500/30 text-violet-600 dark:text-violet-400 hover:bg-violet-500/20 shrink-0"
                        title="Nghe cụm collocation"
                      >
                        <Volume2 className="h-3 w-3" />
                      </button>
                    </div>
                  )}
                </div>

                {/* Example Sentence with Native TTS Shadowing */}
                {vocabExampleJa && (
                  <div className="p-3 rounded-2xl bg-gradient-to-br from-muted/30 to-muted/10 border border-border/70 space-y-1.5 shadow-2xs">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-[10px] font-extrabold uppercase tracking-wider text-muted-foreground flex items-center gap-1">
                        <Sparkles className="h-3 w-3 text-primary" />
                        Câu ví dụ đàm thoại thực tế:
                      </span>
                      <button
                        type="button"
                        onClick={() => speakJapaneseText(vocabExampleJa, { rate: 0.95 })}
                        className="px-2 py-0.5 rounded-lg bg-primary/10 hover:bg-primary/20 text-primary border border-primary/20 text-[10px] font-bold flex items-center gap-1 transition-colors"
                        title="Nghe câu ví dụ để Shadowing"
                      >
                        <Volume2 className="h-3 w-3" />
                        Shadowing
                      </button>
                    </div>
                    <p className="text-sm font-bold font-jp text-foreground leading-relaxed">
                      {vocabExampleJa}
                    </p>
                    {vocabExampleVi && (
                      <p className="text-xs text-muted-foreground font-medium">
                        {vocabExampleVi}
                      </p>
                    )}
                  </div>
                )}
              </div>
            ) : isTransformation ? (
              <div className="space-y-2">
                {/* Visual Before -> After Diff Box */}
                <div className="p-3 rounded-2xl bg-card border border-border/80 space-y-2 shadow-2xs">
                  {/* Before */}
                  <div className="flex items-start gap-2 text-xs">
                    <span className="px-2 py-0.5 rounded-md bg-rose-500/10 border border-rose-500/30 text-rose-600 dark:text-rose-400 font-bold text-[10px] uppercase shrink-0 mt-0.5">
                      🔻 Câu gốc
                    </span>
                    <span className="font-bold font-jp text-muted-foreground text-sm leading-relaxed">
                      {transformSource || promptText}
                    </span>
                  </div>

                  {/* After */}
                  <div className="flex items-start gap-2 text-xs pt-1 border-t border-border/50">
                    <span className="px-2 py-0.5 rounded-md bg-emerald-500/10 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400 font-bold text-[10px] uppercase shrink-0 mt-0.5">
                      🟢 Sau biến đổi
                    </span>
                    <span className="font-black font-jp text-primary text-base leading-relaxed">
                      {canonical || "—"}
                    </span>
                  </div>
                </div>

                {/* Target & Formula badge if present */}
                {(transformTargetLabel || transformFormula) && (
                  <div className="flex items-center gap-1.5 flex-wrap text-xs">
                    {transformTargetLabel && (
                      <span className="px-2 py-0.5 rounded-lg bg-primary/10 border border-primary/25 text-primary font-bold text-[11px]">
                        ⚡ {transformTargetLabel}
                      </span>
                    )}
                    {transformFormula && (
                      <span className="px-2 py-0.5 rounded-lg bg-muted text-muted-foreground font-mono text-[11px]">
                        💡 {transformFormula}
                      </span>
                    )}
                  </div>
                )}

                {/* Grammar Note Takeaway */}
                {transformGrammarNote && (
                  <p className="text-[11px] font-medium text-amber-800 dark:text-amber-300 bg-amber-500/10 border border-amber-500/20 p-2.5 rounded-xl leading-relaxed">
                    💡 <strong>Điểm ngữ pháp:</strong> {transformGrammarNote}
                  </p>
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
              disabled={!ttsText}
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

