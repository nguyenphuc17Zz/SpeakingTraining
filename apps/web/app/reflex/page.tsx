"use client";

import React, { useState, useEffect, useMemo, useRef, useCallback } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import {
  Zap,
  Mic,
  Clock,
  Settings2,
  Play,
  RotateCcw,
  Trophy,
  Shuffle,
  HelpCircle,
  Keyboard,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  Volume2,
  Flame,
  Sparkles,
  ArrowRight,
  Headphones,
  Sliders,
  CheckCircle2,
  XCircle,
  Radio,
  Check,
  MessageSquare,
  Repeat,
  Compass,
  Star,
  Activity,
} from "lucide-react";
import { useReflexSession } from "@/features/reflex/hooks/useReflexSession";
import { ReflexTimer } from "@/features/reflex/components/ReflexTimer";
import { ReflexPromptCard } from "@/features/reflex/components/ReflexPromptCard";
import { ReflexResultCard } from "@/features/reflex/components/ReflexResultCard";
import { ReflexSessionSummary } from "@/features/reflex/components/ReflexSessionSummary";
import { CoachQuickActions, CoachPanel } from "@/features/coach";
import { usePathname } from "next/navigation";
import { useCoachCore } from "@/features/coach/hooks/useCoachCore";
import { CoachInsightCard } from "@/features/coach/components/CoachInsightCard";
import { useCoachProactive } from "@/features/coach/hooks/useCoachProactive";
import { useSystemKeybindings, formatKeyDisplay } from "@/hooks/use-system-keybindings";
import { speakJapaneseText, stopWebSpeech } from "@/features/speaking/services/web-speech";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

const DEDICATED_MODES = [
  {
    id: "reflex_conjugation",
    title: "Conjugation Blitz",
    titleJa: "活用",
    icon: Zap,
    badgeVariant: "sakura" as const,
    iconColor: "text-rose-500 bg-rose-500/10 border-rose-500/20",
    accentColor: "text-rose-600 dark:text-rose-400",
    desc: "Chia thể động từ & tính từ phản xạ siêu tốc",
    source: "食べる",
    target: "食べさせる (Sai khiến)",
  },
  {
    id: "reflex_qna",
    title: "Speed Q&A",
    titleJa: "速答",
    icon: MessageSquare,
    badgeVariant: "matcha" as const,
    iconColor: "text-emerald-500 bg-emerald-500/10 border-emerald-500/20",
    accentColor: "text-emerald-600 dark:text-emerald-400",
    desc: "Hỏi - đáp tức thì câu hỏi thường ngày & công việc",
    source: "週末は何を？",
    target: "映画を見ました",
  },
  {
    id: "reflex_transformation",
    title: "Transformation",
    titleJa: "文型変換",
    icon: Repeat,
    badgeVariant: "fuji" as const,
    iconColor: "text-indigo-500 bg-indigo-500/10 border-indigo-500/20",
    accentColor: "text-indigo-600 dark:text-indigo-400",
    desc: "Đổi ngữ pháp: Lịch sự ↔ Thân mật, Phủ định, Quá khứ",
    source: "行きます",
    target: "行く (Thân mật)",
  },
  {
    id: "reflex_context",
    title: "Contextual Reaction",
    titleJa: "状況対応",
    icon: Compass,
    badgeVariant: "kintsugi" as const,
    iconColor: "text-amber-500 bg-amber-500/10 border-amber-500/20",
    accentColor: "text-amber-600 dark:text-amber-400",
    desc: "Phản xạ giao tiếp đúng vai vế và văn hóa ứng xử",
    source: "Đến muộn do trễ tàu",
    target: "大変申し訳ありません",
  },
];

const PRESSURE_LEVELS = [
  { id: "relaxed", label: "Relaxed", labelJa: "ゆっくり", icon: "🐢", ms: 6000, desc: "Dễ • An toàn cho Beginner" },
  { id: "normal", label: "Normal", labelJa: "普通", icon: "🚶", ms: 4000, desc: "Cân bằng • Nhịp tự nhiên" },
  { id: "fast", label: "Fast", labelJa: "速め", icon: "🏃", ms: 3000, desc: "Tăng tốc • Phản xạ nhanh" },
  { id: "reflex", label: "Reflex", labelJa: "瞬発", icon: "⚡", ms: 2500, desc: "Thực chiến • Nhịp bản xứ" },
  { id: "extreme", label: "Extreme", labelJa: "超速", icon: "🔥", ms: 1800, desc: "Cực hạn • Không do dự" },
] as const;

const DURATION_OPTIONS = [3, 5, 10, 20] as const;

export default function ReflexPage() {
  const [subMode, setSubMode] = useState("mixed");
  const [pressure, setPressure] = useState<"relaxed" | "normal" | "fast" | "reflex" | "extreme">("normal");
  const [subtitleMode, setSubtitleMode] = useState<"hidden" | "japanese" | "japanese_reading" | "vietnamese">("japanese");
  const [startTrigger, setStartTrigger] = useState<"manual" | "auto">("manual");
  const [transcriptInput, setTranscriptInput] = useState("");
  const [showTextInput, setShowTextInput] = useState(false);
  const [showSummary, setShowSummary] = useState(false);
  const [duration, setDuration] = useState<3 | 5 | 10 | 20>(5);
  const [sessionRemainingSec, setSessionRemainingSec] = useState(duration * 60);
  const [autoNext, setAutoNext] = useState(false);
  const [showHelp, setShowHelp] = useState(false);

  const sessionEndTimestampRef = useRef<number | null>(null);
  const sessionPausedRemainingMsRef = useRef<number>(duration * 60 * 1000);

  const { matchesAction, keybindings } = useSystemKeybindings();

  const session = useReflexSession({
    subMode,
    pressureLevel: pressure as any,
    autoNext,
    startTrigger,
  });

  // Sync duration selection in lobby
  useEffect(() => {
    if (session.phase === "idle" || session.phase === "summary" || showSummary) {
      setSessionRemainingSec(duration * 60);
      sessionEndTimestampRef.current = null;
      sessionPausedRemainingMsRef.current = duration * 60 * 1000;
    }
  }, [duration, session.phase, showSummary]);

  // Robust session duration countdown
  useEffect(() => {
    const isSessionActive = session.phase !== "idle" && session.phase !== "summary" && !showSummary;
    if (!isSessionActive) return;

    if (session.isPaused) {
      if (sessionEndTimestampRef.current !== null) {
        const remaining = Math.max(0, sessionEndTimestampRef.current - Date.now());
        sessionPausedRemainingMsRef.current = remaining;
        sessionEndTimestampRef.current = null;
      }
      return;
    }

    if (sessionEndTimestampRef.current === null) {
      sessionEndTimestampRef.current = Date.now() + sessionPausedRemainingMsRef.current;
    }

    const interval = setInterval(() => {
      if (sessionEndTimestampRef.current === null) return;
      const remainingMs = sessionEndTimestampRef.current - Date.now();
      const remainingSec = Math.max(0, Math.ceil(remainingMs / 1000));
      setSessionRemainingSec(remainingSec);

      if (remainingSec <= 0) {
        clearInterval(interval);
        sessionEndTimestampRef.current = null;
        setShowSummary(true);
        session.setPhase("summary" as any);
      }
    }, 500);

    return () => clearInterval(interval);
  }, [session.phase, session.isPaused, showSummary, session.setPhase]);

  const timerMs = PRESSURE_LEVELS.find((p) => p.id === pressure)?.ms ?? 4000;
  const activeExercise = session.exercise;
  const pathname = usePathname();
  const { insights, dismiss } = useCoachProactive();
  const [coachOpen, setCoachOpen] = useState(false);
  const coach = useCoachCore();

  const handleCoachSelect = (prompt: string) => {
    setCoachOpen(true);
    setTimeout(() => coach.ask(prompt, { route: pathname || "/reflex", exerciseId: (activeExercise as any)?.id }), 300);
  };

  const playedPromptExerciseIdRef = useRef<string | null>(null);

  const playPromptAudio = useCallback(
    (autoTransition = false) => {
      if (!activeExercise) return;
      const rc = activeExercise.extra_metadata?.reflex_config || {};
      const text =
        rc.prompt ||
        (activeExercise.exercise_type === "reflex_conjugation" && rc.verb
          ? rc.verb
          : activeExercise.scenario || activeExercise.title);
      if (text) {
        speakJapaneseText(text, {
          rate: 1.0,
          onEnd: () => {
            if (autoTransition) {
              session.onPromptAudioFinished();
            }
          },
          onError: () => {
            if (autoTransition) {
              session.onPromptAudioFinished();
            }
          },
        });
      } else if (autoTransition) {
        session.onPromptAudioFinished();
      }
    },
    [activeExercise, session.onPromptAudioFinished]
  );

  // Auto-play prompt audio in prompt_playing phase and transition after audio ends
  useEffect(() => {
    if (session.phase === "prompt_playing" && activeExercise?.id) {
      if (playedPromptExerciseIdRef.current !== activeExercise.id) {
        playedPromptExerciseIdRef.current = activeExercise.id;
        playPromptAudio(true);
      }
    } else if (session.phase === "idle" || session.phase === "summary") {
      playedPromptExerciseIdRef.current = null;
      stopWebSpeech();
    }
  }, [session.phase, activeExercise?.id, playPromptAudio]);

  // Guaranteed audio and mic release on component unmount
  useEffect(() => {
    return () => {
      stopWebSpeech();
      session.recorder.releaseMicrophone();
      session.speech.stopListening();
    };
  }, []);

  const handleDirectSubmit = async () => {
    const text =
      transcriptInput.trim() ||
      session.speech.transcript.trim() ||
      session.speech.interimTranscript.trim();
    if (!text) return;
    setTranscriptInput("");
    await session.submitWithTranscript(text);
  };

  // Calculate current consecutive correct streak
  const currentStreak = useMemo(() => {
    let streak = 0;
    for (let i = session.results.length - 1; i >= 0; i--) {
      if (session.results[i].success) streak++;
      else break;
    }
    return streak;
  }, [session.results]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName?.toLowerCase();
      if (tag === "textarea" || tag === "input") {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          if (session.phase === "waiting_for_speech" || session.phase === "recording" || session.phase === "result") {
            handleDirectSubmit();
          }
        }
        return;
      }

      // Handle Result Phase Keybindings
      if (session.phase === "result") {
        // Next Question: Space, Enter, N, ArrowRight, drillSubmitOrNext, drillSkip
        if (
          e.code === "Space" ||
          e.key === "Enter" ||
          e.key === "n" ||
          e.key === "N" ||
          e.key === "ArrowRight" ||
          matchesAction(e, "drillSubmitOrNext") ||
          matchesAction(e, "drillSkip")
        ) {
          e.preventDefault();
          stopWebSpeech();
          session.startNext();
          return;
        }

        // Retry Question: R, drillRetry
        if (e.key === "r" || e.key === "R" || matchesAction(e, "drillRetry")) {
          e.preventDefault();
          stopWebSpeech();
          session.retry();
          return;
        }

        // Replay Answer Audio: A, drillReplayAudio
        if (e.key === "a" || e.key === "A" || matchesAction(e, "drillReplayAudio")) {
          e.preventDefault();
          const canonical =
            session.result?.canonicalAnswer ||
            (activeExercise as any)?.canonical ||
            (activeExercise as any)?.target_patterns?.[0] ||
            "";
          if (canonical) {
            stopWebSpeech();
            speakJapaneseText(canonical);
          }
          return;
        }
      }

      if (matchesAction(e, "drillToggleHelp")) {
        e.preventDefault();
        setShowHelp((v) => !v);
        return;
      }

      if (matchesAction(e, "drillPauseOrResume")) {
        e.preventDefault();
        session.togglePause();
        return;
      }

      if (matchesAction(e, "drillReplayAudio")) {
        e.preventDefault();
        playPromptAudio(false);
        return;
      }

      if (matchesAction(e, "drillStartQuestion")) {
        e.preventDefault();
        stopWebSpeech();
        session.startQuestionNow();
        return;
      }

      if (matchesAction(e, "drillSubmitOrNext")) {
        e.preventDefault();
        if (session.phase === "waiting_for_speech" || session.phase === "recording") {
          handleDirectSubmit();
        }
        return;
      }

      if (e.key === "Escape") {
        if (session.phase !== "idle") {
          stopWebSpeech();
          session.recorder.releaseMicrophone();
          session.speech.stopListening();
          session.setPhase("idle" as any);
          setShowSummary(false);
        } else {
          setShowHelp(false);
        }
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [session.phase, transcriptInput, matchesAction]);

  // ==========================================
  // RENDER 1: LOBBY / SETUP SCREEN
  // ==========================================
  if (session.phase === "idle" && !showSummary) {
    const isMixedSelected = subMode === "mixed";

    return (
      <div className="space-y-8 animate-in fade-in duration-300 max-w-5xl mx-auto pb-16 px-2 sm:px-4">
        {/* Proactive Coach Insight Banner */}
        {insights.slice(0, 1).map((ins, idx) => (
          <CoachInsightCard
            key={idx}
            insight={ins}
            onDismiss={() => dismiss(ins.insight_type)}
            onAction={() => handleCoachSelect(`Luyện ${ins.recommended_action || "reflex"} cho tui`)}
          />
        ))}

        {/* Hero Header */}
        <div className="relative overflow-hidden rounded-3xl border border-border bg-card p-6 md:p-8 washi-texture shadow-sm">
          <div className="absolute -top-12 -right-12 h-56 w-56 rounded-full bg-enso-gradient opacity-30 pointer-events-none" />
          <div className="relative flex flex-col md:flex-row md:items-center justify-between gap-5">
            <div className="flex items-start gap-4">
              <span className="h-14 w-14 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary shrink-0 shadow-xs">
                <Zap className="h-7 w-7" />
              </span>
              <div className="space-y-1.5">
                <div className="flex items-center gap-2.5">
                  <h1 className="text-2xl md:text-3xl font-black font-jp tracking-tight text-foreground">
                    瞬発力スピーキング
                  </h1>
                  <Badge variant="sakura" size="sm" className="font-bold">
                    Mode 3
                  </Badge>
                </div>
                <p className="text-sm font-bold text-primary">
                  Speed Reflex Speaking — Think less. Speak faster.
                </p>
                <p className="text-xs text-muted-foreground max-w-xl leading-relaxed">
                  Rèn luyện phản xạ bật câu nói tiếng Nhật tức thì dưới áp lực thời gian, xóa bỏ hoàn toàn thói quen dịch ngầm trong đầu.
                </p>
              </div>
            </div>

            <Button
              variant="outline"
              size="sm"
              className="self-start md:self-center gap-2 rounded-2xl border-border px-4 py-2 text-xs font-bold shadow-xs hover:border-primary/40"
              onClick={() => setShowHelp(true)}
            >
              <Keyboard className="h-4 w-4 text-primary" />
              <span>Phím tắt ({formatKeyDisplay(keybindings.drillToggleHelp)})</span>
            </Button>
          </div>
        </div>

        {/* SECTION 1: CHỌN DẠNG BÀI (FULL WIDTH & SPACIOUS) */}
        <div className="space-y-4">
          <div className="flex items-center justify-between px-1">
            <div className="flex items-center gap-2">
              <span className="h-6 w-6 rounded-lg bg-primary/10 text-primary flex items-center justify-center text-xs font-bold">1</span>
              <h2 className="text-sm font-bold uppercase tracking-wider text-foreground">
                Chọn Chế Độ Luyện Phản Xạ
              </h2>
            </div>
            <span className="text-xs font-medium text-muted-foreground">5 Dạng bài phản xạ</span>
          </div>

          {/* TOP HERO CARD: Mixed Adaptive */}
          <button
            type="button"
            onClick={() => {
              soundFX.playFurin();
              setSubMode("mixed");
            }}
            className={cn(
              "w-full text-left rounded-3xl border p-6 md:p-7 transition-all duration-300 relative overflow-hidden group shadow-sm washi-texture",
              isMixedSelected
                ? "border-primary bg-primary/10 ring-2 ring-primary/30 shadow-lg shadow-primary/10"
                : "border-border/80 bg-card hover:border-primary/40 hover:bg-card/90"
            )}
          >
            <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-emerald-500 via-primary to-amber-500 opacity-90" />

            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-2xl bg-primary/15 border border-primary/25 flex items-center justify-center text-primary shrink-0 shadow-xs">
                  <Shuffle className="h-6 w-6" />
                </div>
                <div className="space-y-1">
                  <div className="flex flex-wrap items-center gap-2.5">
                    <span className="text-lg md:text-xl font-black text-foreground font-jp">
                      Mixed Adaptive
                    </span>
                    <span className="px-2.5 py-0.5 rounded-full bg-amber-500/15 border border-amber-500/30 text-amber-600 dark:text-amber-400 text-xs font-extrabold flex items-center gap-1">
                      <Star className="h-3 w-3 fill-current" />
                      KHUYÊN DÙNG
                    </span>
                    <Badge variant="kintsugi" size="sm">混合</Badge>
                  </div>
                  <p className="text-xs md:text-sm text-muted-foreground">
                    AI tự động phân tích điểm yếu & luân phiên 4 dạng bài tập trung để tối đa hóa phản xạ
                  </p>
                </div>
              </div>

              <div
                className={cn(
                  "h-7 w-7 rounded-full border-2 flex items-center justify-center shrink-0 self-end md:self-center transition-all",
                  isMixedSelected
                    ? "border-primary bg-primary text-primary-foreground shadow-sm"
                    : "border-muted-foreground/30 bg-background"
                )}
              >
                {isMixedSelected && <Check className="h-4 w-4 stroke-[3]" />}
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 pt-3 border-t border-border/60">
              <div className="p-2.5 px-3 rounded-2xl bg-card border border-border/80 flex items-center gap-2.5 text-xs shadow-2xs">
                <span className="h-2.5 w-2.5 rounded-full bg-rose-500 shrink-0" />
                <span className="font-semibold text-foreground/90">活用 Chia thể</span>
              </div>
              <div className="p-2.5 px-3 rounded-2xl bg-card border border-border/80 flex items-center gap-2.5 text-xs shadow-2xs">
                <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 shrink-0" />
                <span className="font-semibold text-foreground/90">速答 Hỏi - đáp</span>
              </div>
              <div className="p-2.5 px-3 rounded-2xl bg-card border border-border/80 flex items-center gap-2.5 text-xs shadow-2xs">
                <span className="h-2.5 w-2.5 rounded-full bg-indigo-500 shrink-0" />
                <span className="font-semibold text-foreground/90">文型 Biến đổi</span>
              </div>
              <div className="p-2.5 px-3 rounded-2xl bg-card border border-border/80 flex items-center gap-2.5 text-xs shadow-2xs">
                <span className="h-2.5 w-2.5 rounded-full bg-amber-500 shrink-0" />
                <span className="font-semibold text-foreground/90">状況 Tình huống</span>
              </div>
            </div>
          </button>

          {/* 4 DEDICATED FOCUS MODES */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {DEDICATED_MODES.map((m) => {
              const isSelected = subMode === m.id;
              const Icon = m.icon;

              return (
                <button
                  key={m.id}
                  type="button"
                  onClick={() => {
                    soundFX.playFurin();
                    setSubMode(m.id);
                  }}
                  className={cn(
                    "text-left rounded-3xl border p-6 transition-all duration-200 relative overflow-hidden group shadow-xs washi-texture flex flex-col justify-between space-y-4",
                    isSelected
                      ? "border-primary bg-primary/10 ring-2 ring-primary/30 shadow-lg shadow-primary/10"
                      : "border-border/80 bg-card hover:border-primary/40 hover:bg-card/90"
                  )}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-3.5">
                      <div
                        className={cn(
                          "h-11 w-11 rounded-2xl border flex items-center justify-center shrink-0 shadow-xs",
                          m.iconColor
                        )}
                      >
                        <Icon className="h-5 w-5" />
                      </div>
                      <div className="space-y-0.5">
                        <div className="flex items-center gap-2">
                          <span className="text-base font-black text-foreground font-jp">
                            {m.title}
                          </span>
                          <Badge variant={m.badgeVariant} size="sm">
                            {m.titleJa}
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground leading-snug">
                          {m.desc}
                        </p>
                      </div>
                    </div>

                    <div
                      className={cn(
                        "h-6 w-6 rounded-full border-2 flex items-center justify-center shrink-0 transition-all",
                        isSelected
                          ? "border-primary bg-primary text-primary-foreground shadow-xs"
                          : "border-muted-foreground/30 bg-background"
                      )}
                    >
                      {isSelected && <Check className="h-3.5 w-3.5 stroke-[3]" />}
                    </div>
                  </div>

                  <div className="p-3 px-4 rounded-2xl bg-muted/40 border border-border/80 text-xs flex items-center justify-between gap-2 font-medium">
                    <span className="text-foreground/80 font-mono font-medium truncate">
                      {m.source}
                    </span>
                    <ArrowRight className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                    <span className={cn("font-bold truncate", m.accentColor)}>
                      {m.target}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* SECTION 2: THIẾT LẬP ÁP LỰC & THỜI LƯỢNG */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
          {/* Column 1: Pressure Level Selector */}
          <div className="rounded-3xl border border-border bg-card p-6 md:p-7 space-y-4 shadow-sm washi-texture">
            <div className="flex items-center justify-between pb-1 border-b border-border/60">
              <div className="flex items-center gap-2">
                <span className="h-6 w-6 rounded-lg bg-primary/10 text-primary flex items-center justify-center text-xs font-bold">2</span>
                <label className="text-sm font-bold uppercase tracking-wider text-foreground flex items-center gap-2">
                  <Clock className="h-4 w-4 text-primary" />
                  <span>Áp Lực Thời Gian</span>
                </label>
              </div>
              <span className="font-mono text-primary font-bold text-sm bg-primary/10 px-2.5 py-0.5 rounded-full border border-primary/20">
                {timerMs / 1000}s / câu
              </span>
            </div>

            <div className="grid grid-cols-1 gap-2.5">
              {PRESSURE_LEVELS.map((p) => {
                const isSelected = pressure === p.id;
                return (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => {
                      soundFX.playFurin();
                      setPressure(p.id as any);
                    }}
                    className={cn(
                      "flex items-center justify-between p-3 px-4 rounded-2xl border text-xs font-bold transition-all shadow-xs",
                      isSelected
                        ? "border-primary bg-primary text-primary-foreground shadow-sm ring-1 ring-primary/20"
                        : "border-border/80 bg-background hover:bg-muted text-foreground"
                    )}
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-base">{p.icon}</span>
                      <div className="text-left">
                        <div className="flex items-center gap-1.5">
                          <span className="font-jp">{p.labelJa}</span>
                          <span className="opacity-90 font-normal">({p.label})</span>
                        </div>
                        <div className={cn("text-[10px] font-normal", isSelected ? "text-primary-foreground/80" : "text-muted-foreground")}>
                          {p.desc}
                        </div>
                      </div>
                    </div>
                    <span className="font-mono font-black text-sm">{p.ms / 1000}s</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Column 2: Duration, Display Mode & Launch Button */}
          <div className="rounded-3xl border border-border bg-card p-6 md:p-7 space-y-5 shadow-sm washi-texture flex flex-col justify-between">
            <div className="space-y-4">
              <div className="flex items-center justify-between pb-1 border-b border-border/60">
                <div className="flex items-center gap-2">
                  <span className="h-6 w-6 rounded-lg bg-primary/10 text-primary flex items-center justify-center text-xs font-bold">3</span>
                  <label className="text-sm font-bold uppercase tracking-wider text-foreground">
                    Cài Đặt Phiên Luyện
                  </label>
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                  Thời lượng phiên
                </label>
                <div className="grid grid-cols-4 gap-2">
                  {DURATION_OPTIONS.map((d) => (
                    <button
                      key={d}
                      type="button"
                      onClick={() => setDuration(d)}
                      className={cn(
                        "py-2.5 rounded-2xl text-xs font-bold border transition-all text-center shadow-2xs",
                        duration === d
                          ? "bg-primary text-primary-foreground border-primary font-mono shadow-xs"
                          : "bg-background border-border hover:bg-muted text-muted-foreground"
                      )}
                    >
                      {d} Phút
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                  Chế độ hiển thị đề bài
                </label>
                <select
                  value={subtitleMode}
                  onChange={(e) => setSubtitleMode(e.target.value as any)}
                  className="w-full rounded-2xl border border-border bg-background px-4 py-3 text-xs font-medium text-foreground focus:border-primary focus:outline-none shadow-2xs"
                >
                  <option value="japanese">Tiếng Nhật đầy đủ (Khuyên dùng)</option>
                  <option value="vietnamese">Tiếng Nhật kèm dịch Tiếng Việt</option>
                  <option value="hidden">Ẩn phụ đề (Audio Only - Thử thách)</option>
                </select>
              </div>

              {/* Start Trigger Mode Setting */}
              <div className="space-y-2">
                <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center justify-between">
                  <span>Chế độ xuất phát</span>
                  <span className="text-[10px] text-primary font-semibold">
                    {startTrigger === "manual" ? "🎯 Không bị dí" : "⚡ Phản xạ nhanh"}
                  </span>
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setStartTrigger("manual")}
                    className={cn(
                      "p-3 rounded-2xl text-xs font-bold border transition-all text-left flex flex-col gap-1 shadow-2xs",
                      startTrigger === "manual"
                        ? "bg-primary/10 border-primary text-foreground ring-1 ring-primary/30"
                        : "bg-background border-border hover:bg-muted text-muted-foreground"
                    )}
                  >
                    <div className="flex items-center gap-1.5 text-primary">
                      <Mic className="h-4 w-4" />
                      <span className="font-extrabold">🎯 Chủ Động</span>
                    </div>
                    <span className="text-[10px] font-normal text-muted-foreground leading-tight">
                      Nghe xong đề → Chuẩn bị → Bấm Space/Nút để bắt đầu nói
                    </span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setStartTrigger("auto")}
                    className={cn(
                      "p-3 rounded-2xl text-xs font-bold border transition-all text-left flex flex-col gap-1 shadow-2xs",
                      startTrigger === "auto"
                        ? "bg-primary/10 border-primary text-foreground ring-1 ring-primary/30"
                        : "bg-background border-border hover:bg-muted text-muted-foreground"
                    )}
                  >
                    <div className="flex items-center gap-1.5 text-amber-500">
                      <Zap className="h-4 w-4" />
                      <span className="font-extrabold">⚡ Tự Động (Blitz)</span>
                    </div>
                    <span className="text-[10px] font-normal text-muted-foreground leading-tight">
                      Nghe xong đề → Đồng hồ đếm ngược nói ngay tức thì
                    </span>
                  </button>
                </div>
              </div>

              {/* Auto-Next Setting */}
              <div className="flex items-center justify-between p-3.5 rounded-2xl border border-border bg-muted/30">
                <div className="space-y-0.5">
                  <div className="text-xs font-bold text-foreground">Tự động chuyển câu (Auto-Next)</div>
                  <div className="text-[11px] text-muted-foreground">
                    Tự chuyển câu tiếp theo sau 4.5s để bạn kịp xem đáp án & nghe lại giọng
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setAutoNext((v) => !v)}
                  className={cn(
                    "px-3 py-1.5 rounded-xl text-xs font-bold border transition-all",
                    autoNext
                      ? "bg-emerald-600 text-white border-emerald-600 shadow-xs"
                      : "bg-muted text-muted-foreground border-border hover:text-foreground"
                  )}
                >
                  {autoNext ? "BẬT" : "TẮT"}
                </button>
              </div>
            </div>

            <div className="pt-2">
              <Button
                variant="akane"
                size="lg"
                className="w-full font-black text-base rounded-2xl py-6 shadow-md hover:shadow-lg transition-all gap-2.5"
                onClick={() => {
                  soundFX.playTaiko();
                  session.startSession();
                }}
              >
                <Play className="h-5 w-5 fill-current" />
                <span>Bắt Đầu Luyện Phản Xạ ({duration} Phút)</span>
              </Button>
            </div>
          </div>
        </div>

        {/* Beginner safety guide */}
        <div className="p-4 md:p-5 rounded-3xl border border-border/80 bg-card/60 washi-texture flex items-center gap-3.5 shadow-xs">
          <ShieldCheck className="h-5 w-5 text-primary shrink-0" />
          <div className="text-xs text-muted-foreground space-y-0.5">
            <span className="font-bold text-foreground">Lời khuyên an toàn:</span> Người mới nên bắt đầu với mức <span className="font-semibold text-primary">Relaxed (6s)</span> + phụ đề tiếng Nhật để làm quen nhịp độ trước khi nâng tốc độ phản xạ.
          </div>
        </div>

        {/* Global Keybindings Modal */}
        <Modal isOpen={showHelp} onClose={() => setShowHelp(false)} title="Phím tắt Reflex Arena">
          <div className="space-y-4 text-sm">
            <p className="text-xs text-muted-foreground">
              Bạn có thể sử dụng bàn phím để thao tác siêu tốc mà không cần chạm chuột:
            </p>
            <div className="grid grid-cols-2 gap-2.5 text-xs">
              <div className="rounded-xl border bg-muted/40 p-3 space-y-1">
                <div className="font-bold font-mono text-primary">{formatKeyDisplay(keybindings.drillSubmitOrNext)}</div>
                <div className="text-muted-foreground">Nộp bài / Chuyển câu tiếp</div>
              </div>
              <div className="rounded-xl border bg-muted/40 p-3 space-y-1">
                <div className="font-bold font-mono text-amber-500">{formatKeyDisplay(keybindings.drillPauseOrResume)}</div>
                <div className="text-muted-foreground">Tạm dừng / Tiếp tục suy nghĩ</div>
              </div>
              <div className="rounded-xl border bg-muted/40 p-3 space-y-1">
                <div className="font-bold font-mono text-primary">{formatKeyDisplay(keybindings.drillStartQuestion)}</div>
                <div className="text-muted-foreground">Bắt đầu trả lời câu hỏi</div>
              </div>
              <div className="rounded-xl border bg-muted/40 p-3 space-y-1">
                <div className="font-bold font-mono text-primary">{formatKeyDisplay(keybindings.drillReplayAudio)}</div>
                <div className="text-muted-foreground">Nghe lại câu hỏi đề bài</div>
              </div>
              <div className="rounded-xl border bg-muted/40 p-3 space-y-1">
                <div className="font-bold font-mono text-primary">{formatKeyDisplay(keybindings.drillRetry)}</div>
                <div className="text-muted-foreground">Làm lại câu hiện tại (Retry)</div>
              </div>
              <div className="rounded-xl border bg-muted/40 p-3 space-y-1">
                <div className="font-bold font-mono text-primary">{formatKeyDisplay(keybindings.drillSkip)}</div>
                <div className="text-muted-foreground">Bỏ qua câu khó (Skip)</div>
              </div>
              <div className="rounded-xl border bg-muted/40 p-3 space-y-1">
                <div className="font-bold font-mono text-primary">Esc</div>
                <div className="text-muted-foreground">Tạm dừng / Thoát ra sảnh</div>
              </div>
              <div className="rounded-xl border bg-muted/40 p-3 space-y-1">
                <div className="font-bold font-mono text-primary">{formatKeyDisplay(keybindings.drillToggleHelp)}</div>
                <div className="text-muted-foreground">Mở/Đóng trợ giúp phím tắt</div>
              </div>
            </div>
          </div>
        </Modal>
      </div>
    );
  }

  // ==========================================
  // RENDER 2: ACTIVE ZEN REFLEX ARENA (NO-SCROLL VIEWPORT FIT)
  // ==========================================
  const isWaiting = session.phase === "waiting_for_speech";
  const isRecording = session.phase === "recording";
  const isEvaluating = session.phase === "evaluating" || session.phase === "loading";
  const isPromptPlaying = session.phase === "prompt_playing";
  const isReady = session.phase === "ready";
  const isResult = session.phase === "result";

  return (
    <div className="max-w-4xl mx-auto h-[calc(100vh-5.5rem)] flex flex-col justify-between animate-in fade-in duration-200 px-2 sm:px-4 overflow-hidden">
      {/* 1. Top HUD Bar */}
      <div className="p-3 px-4 rounded-2xl border border-border bg-card shadow-xs flex items-center justify-between gap-3 washi-texture shrink-0">
        <div className="flex items-center gap-2">
          <Badge variant="kintsugi" size="sm" className="font-bold">
            Câu {session.stats.total + (isResult ? 0 : 1)}
          </Badge>
          <span className="text-xs font-bold text-foreground hidden sm:inline font-jp">
            {subMode === "mixed" ? "Mixed Adaptive" : DEDICATED_MODES.find((m) => m.id === subMode)?.title}
          </span>
          <span className="text-xs font-mono text-muted-foreground">• {pressure} ({timerMs / 1000}s)</span>
        </div>

        <div className="flex items-center gap-2.5">
          {/* Live Session Countdown Clock */}
          <div
            className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-primary/10 border border-primary/25 text-primary text-xs font-mono font-bold shadow-2xs"
            title={`Thời lượng phiên: ${duration} phút`}
          >
            <Clock className="h-3.5 w-3.5" />
            <span>
              Phiên:{" "}
              {Math.floor(sessionRemainingSec / 60)
                .toString()
                .padStart(2, "0")}
              :{(sessionRemainingSec % 60).toString().padStart(2, "0")} / {duration}m
            </span>
          </div>

          {/* Quick Subtitle Mode Segmented Switcher */}
          <div className="hidden sm:flex items-center rounded-xl bg-muted/60 p-0.5 border border-border text-[11px] font-bold">
            <button
              type="button"
              onClick={() => {
                soundFX.playFurin();
                setSubtitleMode("japanese");
              }}
              className={cn(
                "px-2 py-0.5 rounded-lg transition-all",
                subtitleMode === "japanese"
                  ? "bg-card text-foreground shadow-2xs font-extrabold"
                  : "text-muted-foreground hover:text-foreground"
              )}
              title="Chỉ hiển thị tiếng Nhật"
            >
              🇯🇵 Nhật
            </button>
            <button
              type="button"
              onClick={() => {
                soundFX.playFurin();
                setSubtitleMode("vietnamese");
              }}
              className={cn(
                "px-2 py-0.5 rounded-lg transition-all",
                subtitleMode === "vietnamese"
                  ? "bg-card text-primary shadow-2xs font-extrabold"
                  : "text-muted-foreground hover:text-foreground"
              )}
              title="Tiếng Nhật kèm dịch nghĩa tiếng Việt"
            >
              🇻🇳 Dịch
            </button>
            <button
              type="button"
              onClick={() => {
                soundFX.playFurin();
                setSubtitleMode("hidden");
              }}
              className={cn(
                "px-2 py-0.5 rounded-lg transition-all",
                subtitleMode === "hidden"
                  ? "bg-card text-rose-500 shadow-2xs font-extrabold"
                  : "text-muted-foreground hover:text-foreground"
              )}
              title="Ẩn phụ đề (Audio-Only)"
            >
              🎧 Ẩn
            </button>
          </div>

          {currentStreak > 1 && (
            <div className="flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-600 dark:text-amber-400 text-xs font-bold animate-pulse">
              <Flame className="h-3.5 w-3.5 fill-current" />
              <span>{currentStreak} Streak</span>
            </div>
          )}

          {session.stats.avgLatency > 0 && (
            <div className="hidden md:flex items-center gap-1 text-xs font-mono font-bold text-muted-foreground">
              <Zap className="h-3 w-3 text-amber-500" />
              <span>TB: {Math.round(session.stats.avgLatency)}ms</span>
            </div>
          )}

          {/* HUD Start Trigger Mode Switcher */}
          <button
            type="button"
            onClick={() => setStartTrigger((v) => (v === "manual" ? "auto" : "manual"))}
            className={cn(
              "hidden sm:inline-flex items-center gap-1 px-2.5 py-1 rounded-xl text-[11px] font-bold border transition-all",
              startTrigger === "manual"
                ? "bg-primary/15 text-primary border-primary/30 shadow-2xs"
                : "bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30"
            )}
            title={startTrigger === "manual" ? "Chế độ Chủ động: Bấm Space/Nút khi sẵn sàng (Click để chuyển Tự động)" : "Chế độ Tự động: Đếm giờ ngay sau đề bài (Click để chuyển Chủ động)"}
          >
            <span>{startTrigger === "manual" ? "🎯 Chủ động" : "⚡ Tự động"}</span>
          </button>

          {/* HUD Auto-Next Switcher */}
          <button
            type="button"
            onClick={() => setAutoNext((v) => !v)}
            className={cn(
              "hidden sm:inline-flex items-center gap-1 px-2.5 py-1 rounded-xl text-[11px] font-bold border transition-all",
              autoNext
                ? "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30 shadow-2xs"
                : "bg-muted text-muted-foreground border-border hover:text-foreground"
            )}
            title={autoNext ? "Tự động chuyển câu (Bấm để tắt)" : "Chuyển câu thủ công (Bấm để bật)"}
          >
            <span>Auto</span>
            <span className="font-mono text-[10px] font-black">{autoNext ? "ON" : "OFF"}</span>
          </button>
        </div>

        <div className="flex items-center gap-1.5">
          <Button
            variant="ghost"
            size="sm"
            className="h-8 px-2 text-xs rounded-xl"
            onClick={() => setShowHelp(true)}
            title="Trợ giúp phím tắt (?)"
          >
            <HelpCircle className="h-4 w-4" />
          </Button>

          <Button
            variant="outline"
            size="sm"
            className="h-8 px-2.5 text-xs rounded-xl border-border"
            onClick={() => {
              stopWebSpeech();
              session.recorder.releaseMicrophone();
              session.speech.stopListening();
              setShowSummary(true);
              session.setPhase("summary" as any);
            }}
          >
            Tổng kết
          </Button>

          <Button
            variant="ghost"
            size="sm"
            className="h-8 px-2 text-xs rounded-xl text-muted-foreground hover:text-foreground"
            onClick={() => {
              stopWebSpeech();
              session.recorder.releaseMicrophone();
              session.speech.stopListening();
              session.setPhase("idle" as any);
              setShowSummary(false);
            }}
            title="Thoát phòng (Esc)"
          >
            Thoát
          </Button>
        </div>
      </div>

      {/* 2. Main Center Stage (Flex-1, Fits viewport) */}
      <div className="flex-1 flex flex-col justify-center py-2 md:py-3 space-y-3 min-h-0">
        {showSummary ? (
          <div className="overflow-y-auto max-h-full">
            <ReflexSessionSummary
              results={session.results as any}
              onRestart={() => {
                setShowSummary(false);
                session.startSession();
              }}
              onToPlan={() => (window.location.href = "/learning")}
            />
          </div>
        ) : isResult && session.result ? (
          /* Result Card Stage */
          <div className="animate-in fade-in zoom-in-95 duration-200">
            <ReflexResultCard
              result={session.result}
              exercise={activeExercise as any}
              onNext={() => session.startNext()}
              onRetry={() => session.retry()}
              onSlowMode={() => setPressure("relaxed")}
              onCancelAutoNext={session.cancelAutoNext}
            />
          </div>
        ) : (
          /* Active Question Stage */
          <div className="space-y-3 flex flex-col justify-center">
            {session.error && (
              <div className="p-3 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-600 dark:text-rose-400 text-xs font-bold flex items-center justify-between gap-2 animate-in fade-in duration-200">
                <span>⚠️ {session.error}</span>
                <Button
                  size="sm"
                  variant="outline"
                  className="h-7 text-xs border-rose-500/40 hover:bg-rose-500/10"
                  onClick={() => session.setError(null)}
                >
                  Đóng
                </Button>
              </div>
            )}

            {/* Prompt Card */}
            <ReflexPromptCard
              exercise={activeExercise as any}
              subtitleMode={subtitleMode}
              phase={session.phase}
              onPlayAudio={playPromptAudio}
            />

            {/* Live Web Speech Recognition Box & Countdown Timer */}
            <div className="p-4 md:p-5 rounded-3xl border border-border bg-card washi-texture shadow-sm flex flex-col items-center justify-center space-y-3">
              {/* Dynamic Countdown Ring */}
              <ReflexTimer
                remainingMs={session.timer.remainingMs}
                timerLimitMs={session.timer.totalLimitMs || timerMs}
                progress={session.timer.progress}
                state={session.timer.state}
                isActive={session.timer.isActive}
                isPaused={session.isPaused}
              />

              {/* Status Message */}
              <div className="text-center space-y-1">
                {session.isPaused ? (
                  <div className="flex items-center justify-center gap-2 text-sm md:text-base font-black text-amber-600 dark:text-amber-400 animate-pulse">
                    <Clock className="h-4 w-4" />
                    <span>⏸️ ĐANG TẠM DỪNG SUY NGHĨ — Bấm Tiếp Tục khi đã sẵn sàng!</span>
                  </div>
                ) : isPromptPlaying ? (
                  <div className="flex items-center justify-center gap-2 text-xs md:text-sm font-bold text-primary animate-pulse">
                    <Volume2 className="h-4 w-4" />
                    <span>🔊 Đang đọc câu hỏi đề bài... (Bấm [Space] để trả lời ngay)</span>
                  </div>
                ) : isReady ? (
                  <div className="flex flex-col items-center justify-center gap-1 animate-in fade-in zoom-in-95 duration-200">
                    <div className="flex items-center gap-2 text-sm md:text-base font-black text-primary animate-pulse">
                      <Sparkles className="h-4 w-4" />
                      <span>🎯 ĐÃ SẴN SÀNG! Hãy suy nghĩ câu trả lời và bắt đầu khi sẵn sàng</span>
                    </div>
                    <span className="text-[11px] text-muted-foreground font-medium">
                      Bấm phím <kbd className="px-1.5 py-0.5 rounded bg-muted border font-bold text-foreground">{formatKeyDisplay(keybindings.drillStartQuestion)}</kbd> hoặc click nút bên dưới để bật mic & tính giờ
                    </span>
                  </div>
                ) : isWaiting ? (
                  <div className="flex items-center justify-center gap-2 text-sm md:text-base font-black text-amber-600 dark:text-amber-400 animate-bounce">
                    <Zap className="h-4 w-4" />
                    <span>NÓI NGAY! Hãy bật câu trả lời bằng tiếng Nhật tức thì!</span>
                  </div>
                ) : isRecording ? (
                  <div className="flex items-center justify-center gap-2 text-sm md:text-base font-black text-rose-600 dark:text-rose-400">
                    <Activity className="h-4 w-4 animate-spin" />
                    <span>Đang ghi nhận giọng nói tiếng Nhật của bạn...</span>
                  </div>
                ) : isEvaluating ? (
                  <div className="flex items-center justify-center gap-2 text-xs md:text-sm font-bold text-primary animate-pulse">
                    <Sparkles className="h-4 w-4 animate-spin" />
                    <span>Đang phân tích phản xạ 7 chiều & chấm điểm...</span>
                  </div>
                ) : null}
              </div>

              {/* Quick Action Buttons (Start / Pause / Resume) */}
              <div className="flex items-center gap-2 pt-0.5">
                {isReady && (
                  <Button
                    size="lg"
                    variant="akane"
                    className="font-black text-sm md:text-base h-11 px-6 rounded-2xl shadow-md hover:shadow-lg transition-all gap-2 animate-bounce ring-2 ring-primary/30"
                    onClick={() => {
                      session.startQuestionNow();
                    }}
                  >
                    <Mic className="h-5 w-5" />
                    <span>🎙️ Bắt Đầu Nói ({formatKeyDisplay(keybindings.drillStartQuestion)})</span>
                  </Button>
                )}

                {isPromptPlaying && (
                  <Button
                    size="sm"
                    variant="outline"
                    className="font-bold text-xs h-8 px-4 rounded-xl shadow-xs gap-1.5 border-primary/40 text-primary hover:bg-primary/10"
                    onClick={() => {
                      stopWebSpeech();
                      session.startQuestionNow();
                    }}
                  >
                    <Play className="h-3.5 w-3.5 fill-current" />
                    <span>Bắt Đầu Trả Lời Ngay ({formatKeyDisplay(keybindings.drillStartQuestion)})</span>
                  </Button>
                )}

                {session.isPaused ? (
                  <Button
                    size="sm"
                    variant="kintsugi"
                    className="font-bold text-xs h-8 px-4 rounded-xl shadow-xs gap-1.5 animate-pulse"
                    onClick={() => session.togglePause()}
                  >
                    <Play className="h-3.5 w-3.5 fill-current" />
                    <span>Tiếp Tục Suy Nghĩ ({formatKeyDisplay(keybindings.drillPauseOrResume)})</span>
                  </Button>
                ) : (isWaiting || isRecording) ? (
                  <Button
                    size="sm"
                    variant="outline"
                    className="font-bold text-xs h-8 px-3 rounded-xl border-amber-500/40 text-amber-600 dark:text-amber-400 hover:bg-amber-500/10 gap-1.5"
                    onClick={() => session.togglePause()}
                    title="Tạm dừng đồng hồ để suy nghĩ"
                  >
                    <Clock className="h-3.5 w-3.5 text-amber-500" />
                    <span>Tạm Dừng Suy Nghĩ ({formatKeyDisplay(keybindings.drillPauseOrResume)})</span>
                  </Button>
                ) : null}
              </div>

              {/* LIVE SPEECH PREVIEW BUBBLE (Streaming Real-Time Audio Waves + Text) */}
              {(isWaiting || isRecording || session.speech.interimTranscript || session.speech.transcript) && (
                <div className="w-full max-w-xl mx-auto p-2.5 px-4 rounded-2xl bg-primary/5 border border-primary/25 shadow-xs flex items-center justify-between gap-3 animate-in fade-in zoom-in-95 duration-200">
                  <div className="flex items-center gap-2.5 min-w-0">
                    {/* Real-time Dynamic Sound Wave Bars */}
                    <div className="flex items-center gap-0.5 shrink-0 h-5 px-1.5 py-0.5 bg-primary/10 rounded-lg">
                      {[0.7, 1.2, 0.6, 1.4, 0.9].map((scale, i) => {
                        const height = Math.max(4, Math.min(18, ((session.volumeLevel || 0.05) * 50 * scale) + 4));
                        return (
                          <span
                            key={i}
                            className="w-1 bg-primary rounded-full transition-all duration-75"
                            style={{ height: `${height}px` }}
                          />
                        );
                      })}
                    </div>

                    <div className="flex flex-col min-w-0">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-primary/80 flex items-center gap-1.5">
                        <span>🎙️ Live Speech Preview</span>
                        {session.speech.interimTranscript && (
                          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-ping" />
                        )}
                      </span>
                      <span className="text-xs md:text-sm font-bold font-jp text-foreground truncate">
                        “{session.speech.interimTranscript || session.speech.transcript || "Đang lắng nghe âm thanh tiếng Nhật..."}”
                      </span>
                    </div>
                  </div>

                  <Badge variant="outline" size="sm" className="text-[10px] font-mono border-primary/30 text-primary shrink-0 hidden sm:inline-flex">
                    Google Web Speech
                  </Badge>
                </div>
              )}

              {/* UNIFIED VOICE & KEYBOARD REFLEX INPUT BAR */}
              <div className="w-full max-w-xl mx-auto rounded-2xl border border-border bg-card/95 p-1.5 pl-3 shadow-sm flex items-center gap-2 focus-within:ring-2 focus-within:ring-primary/30 focus-within:border-primary transition-all washi-texture">
                <div className="flex items-center gap-1.5 shrink-0">
                  <span
                    className={cn(
                      "h-8 w-8 rounded-xl flex items-center justify-center transition-all",
                      isRecording
                        ? "bg-rose-500 text-white animate-pulse shadow-xs"
                        : session.isPaused
                        ? "bg-amber-500/10 text-amber-600 dark:text-amber-400"
                        : "bg-primary/10 text-primary"
                    )}
                    title={isRecording ? "Đang thu âm giọng nói..." : "Sẵn sàng nhận giọng nói & phím"}
                  >
                    <Mic className="h-4 w-4" />
                  </span>
                </div>

                {/* Direct Text / Speech Live Input Field */}
                <input
                  type="text"
                  value={transcriptInput || session.speech.transcript || session.speech.interimTranscript}
                  onChange={(e) => setTranscriptInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      handleDirectSubmit();
                    }
                  }}
                  placeholder={
                    session.isPaused
                      ? "Đang tạm dừng — Bấm [P] để tiếp tục..."
                      : isWaiting
                      ? "Nói vào mic hoặc gõ câu trả lời tiếng Nhật..."
                      : activeExercise?.exercise_type === "reflex_conjugation"
                      ? "Gõ câu chia thể (ví dụ: 書かせられた)..."
                      : "Gõ câu phản xạ tiếng Nhật..."
                  }
                  className="flex-1 bg-transparent text-sm md:text-base font-bold font-jp text-foreground placeholder:text-muted-foreground/60 placeholder:text-xs placeholder:font-normal focus:outline-none min-w-0"
                  disabled={isEvaluating}
                />

                {/* Action Buttons */}
                <div className="flex items-center gap-1 shrink-0">
                  <Button
                    size="sm"
                    variant="akane"
                    className="font-bold text-xs h-8 px-3.5 rounded-xl shadow-xs gap-1"
                    onClick={handleDirectSubmit}
                    disabled={isEvaluating}
                  >
                    <span>Gửi</span>
                    <span className="text-[10px] opacity-80 font-mono hidden sm:inline">(Enter)</span>
                  </Button>

                  <Button
                    size="sm"
                    variant="ghost"
                    className="text-xs h-8 px-2 rounded-xl text-muted-foreground hover:text-foreground"
                    onClick={() => session.skip()}
                    title="Bỏ qua câu này (N)"
                  >
                    <span>Bỏ qua</span>
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 3. Bottom Minimal Shortcuts Strip */}
      <div className="shrink-0 py-1 border-t border-border/50 flex flex-wrap items-center justify-between gap-2 text-[11px] text-muted-foreground">
        <div className="flex items-center gap-3">
          <span><kbd className="px-1 py-0.5 rounded bg-muted border font-bold">Space / Enter</kbd> Bắt đầu / Câu tiếp theo</span>
          <span><kbd className="px-1 py-0.5 rounded bg-muted border font-bold">R</kbd> Làm lại</span>
          <span><kbd className="px-1 py-0.5 rounded bg-muted border font-bold">A</kbd> Nghe lại mẫu</span>
          <span><kbd className="px-1 py-0.5 rounded bg-muted border font-bold">P</kbd> Tạm dừng</span>
        </div>
        <div className="flex items-center gap-2">
          <span><kbd className="px-1 py-0.5 rounded bg-muted border font-bold">?</kbd> Phím tắt</span>
          <span><kbd className="px-1 py-0.5 rounded bg-muted border font-bold">Esc</kbd> Thoát</span>
        </div>
      </div>

      {/* Floating AI Coach Button */}
      <CoachPanel
        open={coachOpen}
        onClose={() => setCoachOpen(false)}
        route={pathname || "/reflex"}
        exerciseId={(activeExercise as any)?.id}
      />
      <button
        onClick={() => setCoachOpen(true)}
        className="fixed bottom-20 right-4 z-30 md:bottom-5 px-3 py-2 rounded-2xl bg-card border border-border shadow-xl text-xs font-bold flex items-center gap-1.5 hover:border-primary/40 transition-all"
      >
        <span className="h-5 w-5 rounded-lg bg-primary text-primary-foreground flex items-center justify-center font-bold text-xs">
          🤖
        </span>
        <span>AI Coach</span>
      </button>
    </div>
  );
}
