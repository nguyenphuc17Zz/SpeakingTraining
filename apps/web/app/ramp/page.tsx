"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { usePathname } from "next/navigation";
import {
  Mic,
  Square,
  Play,
  ArrowRight,
  RefreshCw,
  Settings2,
  Trophy,
  Zap,
  Target,
  BookOpen,
  ChevronLeft,
  Loader2,
  CheckCircle,
  AlertCircle,
  Volume2,
  Keyboard,
  Sparkles,
  Layers,
  Compass,
} from "lucide-react";
import dynamic from "next/dynamic";
import { useRamp } from "@/hooks/use-ramp";
import { useAudioRecorder } from "@/features/audio/hooks/useAudioRecorder";
import { RampStageIndicator } from "@/features/speaking/components/RampStageIndicator";
import { RampScaffoldPanel } from "@/features/speaking/components/RampScaffoldPanel";
import { RampFeedbackCard } from "@/features/speaking/components/RampFeedbackCard";
import { RampSessionSummaryCard } from "@/features/speaking/components/RampSessionSummary";
import { RampLobby } from "@/features/speaking/components/RampLobby";
import { CoachQuickActions } from "@/features/coach";
import { CoachInsightCard } from "@/features/coach/components/CoachInsightCard";

const RampCheatsheetModal = dynamic(
  () => import("@/features/speaking/components/RampCheatsheetModal").then((m) => m.RampCheatsheetModal),
  { ssr: false }
);
const GlobalKeybindingsModal = dynamic(
  () => import("@/components/layout/global-keybindings-modal").then((m) => m.GlobalKeybindingsModal),
  { ssr: false }
);
const CoachPanel = dynamic(
  () => import("@/features/coach").then((m) => m.CoachPanel),
  { ssr: false }
);
import { useCoachProactive } from "@/features/coach/hooks/useCoachProactive";
import { useCoachCore } from "@/features/coach/hooks/useCoachCore";
import { useSystemKeybindings } from "@/hooks/use-system-keybindings";
import { speakJapaneseText, stopWebSpeech } from "@/features/speaking/services/web-speech";
import { soundFX } from "@/lib/sound-fx";
import { SakuraPetals } from "@/components/ui/sakura-petals";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { UniversalFurigana } from "@/components/japanese/UniversalFurigana";
import { ZenLoadingState } from "@/components/ui/zen-loading-state";
import { toast } from "@/lib/toast";

function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const res = reader.result as string;
      const idx = res.indexOf(",");
      resolve(idx >= 0 ? res.slice(idx + 1) : res);
    };
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(blob);
  });
}

const EXERCISE_TYPE_LABEL: Record<string, string> = {
  speak_echo: "Echo 反復",
  speak_substitute: "代入 Substitute",
  speak_complete: "補完 Complete",
  speak_one_sentence: "一文 One Sentence",
  speak_expand: "拡張 Expand",
  speak_reason: "理由付け Reason",
  speak_example: "例示 Example",
  speak_keyword: "キーワード Keyword",
  speak_guided: "誘導 Guided",
  speak_spontaneous: "自由 Spontaneous",
  speak_followup: "フォローアップ Follow-up",
};

export default function RampPage() {
  const ramp = useRamp();
  const recorder = useAudioRecorder();
  const pathname = usePathname();

  // Coach integration
  const coach = useCoachCore();
  const { insights, dismiss } = useCoachProactive();
  const [coachOpen, setCoachOpen] = useState(false);

  // Modals & configuration
  const [selectedMinutes, setSelectedMinutes] = useState(15);
  const [selectedGoal, setSelectedGoal] = useState("general");
  const [subtitleMode, setSubtitleMode] = useState<"hidden" | "japanese" | "vietnamese">("vietnamese");
  const [showCheatsheet, setShowCheatsheet] = useState(false);
  const [showKeybindingsModal, setShowKeybindingsModal] = useState(false);

  // Session elapsed timer (supports infinite mode)
  const [sessionElapsedSec, setSessionElapsedSec] = useState(0);

  // Input & Timers
  const [transcriptInput, setTranscriptInput] = useState("");
  const [showTranscriptInput, setShowTranscriptInput] = useState(false);
  const [prepLeft, setPrepLeft] = useState(0);
  const [recElapsed, setRecElapsed] = useState(0);
  const rafRef = useRef<number | null>(null);
  const prepStartRef = useRef<number | null>(null);
  const recStartRef = useRef<number | null>(null);
  const phaseRef = useRef(ramp.phase);
  useEffect(() => { phaseRef.current = ramp.phase; }, [ramp.phase]);

  // System keybindings
  const { matchesAction } = useSystemKeybindings();

  // Load preferences from localStorage
  useEffect(() => {
    try {
      const savedGoal = localStorage.getItem("speaking_ramp_goal");
      if (savedGoal) setSelectedGoal(savedGoal);
      const savedDur = localStorage.getItem("speaking_ramp_duration");
      if (savedDur !== null && savedDur !== undefined) setSelectedMinutes(Number(savedDur));
      const savedSub = localStorage.getItem("speaking_ramp_subtitle");
      if (savedSub === "hidden" || savedSub === "japanese" || savedSub === "vietnamese") {
        setSubtitleMode(savedSub);
      }
    } catch (e) {}
  }, []);

  // Save preferences on change
  useEffect(() => {
    try {
      localStorage.setItem("speaking_ramp_goal", selectedGoal);
      localStorage.setItem("speaking_ramp_duration", String(selectedMinutes));
      localStorage.setItem("speaking_ramp_subtitle", subtitleMode);
    } catch (e) {}
  }, [selectedGoal, selectedMinutes, subtitleMode]);

  // Errors surface
  useEffect(() => { if (ramp.error) toast.error(ramp.error); }, [ramp.error]);
  useEffect(() => { if (recorder.error) toast.error(recorder.error); }, [recorder.error]);

  // Prep countdown with SoundFX
  const startPrep = useCallback((sec: number) => {
    if (sec <= 0) {
      ramp.setPhase("recording");
      return;
    }
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    const t0 = performance.now();
    prepStartRef.current = t0;
    setPrepLeft(sec);

    let lastSecBeep = sec;
    const tick = (now: number) => {
      if (phaseRef.current !== "preparing") return;
      const left = Math.max(0, sec - (now - t0) / 1000);
      setPrepLeft(left);

      const currentSec = Math.ceil(left);
      if (currentSec <= 3 && currentSec > 0 && currentSec !== lastSecBeep) {
        soundFX.playSuikinkutsu();
        lastSecBeep = currentSec;
      }

      if (left <= 0) {
        soundFX.playFurin();
        ramp.setPhase("recording");
        return;
      }
      rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
  }, [ramp]);

  // Recording timer
  useEffect(() => {
    if (ramp.phase === "recording") {
      recStartRef.current = performance.now();
      const tick = (now: number) => {
        if (phaseRef.current !== "recording") return;
        setRecElapsed((now - (recStartRef.current || now)) / 1000);
        rafRef.current = requestAnimationFrame(tick);
      };
      rafRef.current = requestAnimationFrame(tick);
    }
    return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current); };
  }, [ramp.phase]);

  // Actions
  const handleStartSession = useCallback(async () => {
    soundFX.playTaiko();
    const s = await ramp.startSession({
      desired_minutes: selectedMinutes,
      session_goal: selectedGoal,
    });
    if (s) {
      await ramp.loadNextExercise(false, false, s.id);
    }
  }, [ramp, selectedMinutes, selectedGoal]);

  const handleBeginExercise = useCallback(() => {
    soundFX.playTaiko();
    const targetSec = ramp.currentExercise?.task_spec?.target_duration_sec || 0;
    if (targetSec > 0) {
      startPrep(5); // 5s prep
    } else {
      ramp.setPhase("recording");
    }
    recorder.startRecording();
  }, [ramp, recorder, startPrep]);

  const handleStopAndSubmit = useCallback(async () => {
    soundFX.playTaiko();
    const blob = await recorder.stopRecording();
    ramp.setPhase("submitting");
    setRecElapsed(0);

    let audio_base64: string | undefined;
    const transcriptText = transcriptInput.trim();

    if (blob && blob.size > 1000) {
      try {
        audio_base64 = await blobToBase64(blob);
      } catch (e) {}
    }

    if (!transcriptText && !audio_base64) {
      toast.error("Vui lòng nói qua micro hoặc nhập văn bản câu trả lời.");
      ramp.setPhase("recording");
      return;
    }

    const result = await ramp.submitAttempt({
      user_transcript: transcriptText || "[audio-only]",
      audio_base64,
      support_level_used: ramp.supportLevel,
      used_hint: ramp.usedHint,
    });

    if (result) {
      setTranscriptInput("");
    }
  }, [recorder, ramp, transcriptInput]);

  const handleRetry = useCallback(async () => {
    soundFX.playSuikinkutsu();
    await ramp.loadNextExercise(true);
    setTranscriptInput("");
  }, [ramp]);

  const handleNext = useCallback(async () => {
    soundFX.playSuikinkutsu();
    const result = ramp.submitResult;
    const forceFollowup = result?.feedback?.followup != null;
    await ramp.loadNextExercise(false, forceFollowup);
    setTranscriptInput("");
  }, [ramp]);

  const handleComplete = useCallback(async () => {
    soundFX.playVictory();
    await ramp.completeSession();
  }, [ramp]);

  const handleNewSession = useCallback(() => {
    soundFX.playSuikinkutsu();
    ramp.setPhase("idle");
  }, [ramp]);

  const handlePlayAudio = (text: string) => {
    stopWebSpeech();
    speakJapaneseText(text);
  };

  const handleCoachSelect = (prompt: string) => {
    setCoachOpen(true);
    setTimeout(() => coach.ask(prompt, { route: pathname || "/ramp", sessionId: ramp.session?.id }), 300);
  };

  // Keyboard navigation listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (["INPUT", "TEXTAREA"].includes((e.target as HTMLElement).tagName)) {
        return;
      }

      if (e.key === "?" || (e.key === "k" && (e.ctrlKey || e.metaKey))) {
        e.preventDefault();
        setShowKeybindingsModal((prev) => !prev);
      } else if (e.key === "c" || e.key === "C") {
        e.preventDefault();
        setShowCheatsheet((prev) => !prev);
      } else if (e.code === "Space") {
        e.preventDefault();
        if (ramp.phase === "prompting") {
          handleBeginExercise();
        } else if (ramp.phase === "recording") {
          handleStopAndSubmit();
        }
      } else if (e.key === "r" || e.key === "R") {
        if (ramp.phase === "feedback") {
          e.preventDefault();
          handleRetry();
        }
      } else if (e.key === "n" || e.key === "N") {
        if (ramp.phase === "feedback") {
          e.preventDefault();
          handleNext();
        }
      } else if (e.key === "h" || e.key === "H") {
        if (ramp.phase === "prompting" || ramp.phase === "preparing") {
          e.preventDefault();
          ramp.revealHint();
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [ramp.phase, handleBeginExercise, handleStopAndSubmit, handleRetry, handleNext, ramp]);

  // Contextual data
  const task = ramp.currentExercise?.task_spec;
  const targetSec = task?.target_duration_sec || 0;
  const exercisesCompleted = ramp.session?.exercises_completed || 0;
  const exercisesTotal = ramp.session?.exercises_total || 10;
  const isSessionActive = ramp.session !== null && ramp.phase !== "idle" && ramp.phase !== "complete";

  // Session elapsed timer (counts up continuously)
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    if (isSessionActive) {
      interval = setInterval(() => {
        setSessionElapsedSec((prev) => prev + 1);
      }, 1000);
    } else {
      setSessionElapsedSec(0);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isSessionActive]);

  const formatSessionTime = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m}:${s < 10 ? "0" : ""}${s}`;
  };

  return (
    <div className="max-w-6xl mx-auto space-y-3 pb-6 animate-in fade-in duration-200">
      {/* ── Compact Session Header Bar ── */}
      <header className="flex items-center justify-between gap-3 p-3 rounded-2xl border border-border bg-card/95 washi-texture shadow-xs">
        <div className="flex items-center gap-2.5 min-w-0">
          <a
            href="/dashboard"
            className="flex h-8 w-8 items-center justify-center rounded-xl border border-border bg-card text-muted-foreground hover:text-foreground hover:bg-muted transition-all shrink-0"
            title="Quay lại Tổng quan"
          >
            <ChevronLeft className="h-4 w-4" />
          </a>
          <div className="flex items-center gap-2 min-w-0">
            <span className="font-extrabold text-xs sm:text-sm text-foreground flex items-center gap-1.5 truncate">
              <Sparkles className="h-4 w-4 text-primary shrink-0" />
              Phục Hồi Phát Ngôn
            </span>
            <Badge variant="matcha" size="sm" className="text-[9px] font-bold px-1.5 py-0 hidden sm:inline-flex">
              MODE 6
            </Badge>
          </div>
        </div>

        {/* Live Stage dots in top bar if active */}
        {isSessionActive && (
          <div className="hidden md:flex items-center gap-3 bg-muted/30 px-3 py-1.5 rounded-xl border border-border/60">
            <RampStageIndicator currentStage={ramp.stage} showLabels={false} />
            <span className="text-[11px] font-extrabold text-foreground font-mono">
              Stage {ramp.stage} • {exercisesCompleted}{selectedMinutes === 0 ? " câu" : `/${exercisesTotal}`} • {formatSessionTime(sessionElapsedSec)} / {selectedMinutes === 0 ? "∞" : `${selectedMinutes}m`}
            </span>
          </div>
        )}

        {/* Quick action buttons */}
        <div className="flex items-center gap-1.5 shrink-0">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowCheatsheet(true)}
            className="h-7.5 px-2 rounded-lg text-xs font-semibold border-border gap-1"
          >
            <BookOpen className="h-3.5 w-3.5 text-primary" />
            <span className="hidden sm:inline">Cẩm nang (C)</span>
          </Button>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowKeybindingsModal(true)}
            className="h-7.5 px-2 rounded-lg text-muted-foreground hover:text-foreground"
            title="Phím tắt (?)"
          >
            <Keyboard className="h-4 w-4" />
          </Button>

          {isSessionActive && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleComplete}
              className="h-7.5 px-2.5 rounded-lg text-xs font-bold border-primary/30 text-primary hover:bg-primary/10"
            >
              Kết thúc
            </Button>
          )}
        </div>
      </header>

      {/* ── Main Content Area ── */}
      <main>
        {/* Phase: IDLE -> Compact Lobby */}
        {ramp.phase === "idle" && (
          <RampLobby
            selectedGoal={selectedGoal}
            onGoalChange={setSelectedGoal}
            duration={selectedMinutes}
            onDurationChange={setSelectedMinutes}
            subtitleMode={subtitleMode}
            onSubtitleModeChange={setSubtitleMode}
            onStartSession={handleStartSession}
            onOpenCheatsheet={() => setShowCheatsheet(true)}
            onOpenKeybindings={() => setShowKeybindingsModal(true)}
            isLoading={ramp.isLoading}
          />
        )}

        {/* Phase: INITIALIZING WORKOUT -> Zen Studio Loading Skeleton */}
        {isSessionActive && !task && !ramp.error && (
          <ZenLoadingState
            variant="studio"
            title="Đang khởi tạo bài tập nấc thang..."
            ja="演習生成中..."
            description="AI đang thiết lập đề bài và giàn giáo phản xạ phù hợp với nấc thang của bạn..."
          />
        )}

        {/* Phase: ERROR RECOVERY */}
        {isSessionActive && !task && ramp.error && (
          <div className="p-8 rounded-3xl border border-destructive/30 bg-destructive/5 text-center space-y-3 washi-texture max-w-lg mx-auto">
            <p className="text-sm font-bold text-destructive">{ramp.error}</p>
            <div className="flex items-center justify-center gap-2">
              <Button
                variant="primary"
                size="sm"
                onClick={() => ramp.loadNextExercise(false, false, ramp.session?.id)}
              >
                <RefreshCw className="h-4 w-4 mr-1.5" /> Thử tạo lại bài tập
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleNewSession}
              >
                Quay lại sảnh
              </Button>
            </div>
          </div>
        )}

        {/* Phase: WORKOUT (2-Column Studio Grid) */}
        {isSessionActive && task && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-3.5 items-start">
            {/* ── Left Arena: 7 cols on desktop ── */}
            <div className="lg:col-span-7 space-y-3">
              {/* 1. Hero Challenge Card */}
              {(ramp.phase === "prompting" || ramp.phase === "preparing" || ramp.phase === "recording") && (
                <div className="p-4 sm:p-5 rounded-2xl border border-border/80 bg-card washi-texture shadow-xs space-y-3.5 relative overflow-hidden">
                  <SakuraPetals count={1} />

                  {/* Header: Stage Badge + Topic + Tokyo Native Audio */}
                  <div className="flex items-center justify-between gap-2 border-b border-border/60 pb-3">
                    <div className="flex items-center gap-2 flex-wrap">
                      <Badge variant="matcha" className="text-[11px] font-bold py-0.5 px-2.5 shadow-2xs">
                        Stage {task.stage || ramp.stage} • {EXERCISE_TYPE_LABEL[task.exercise_type] || task.exercise_type}
                      </Badge>
                      {task.topic && (
                        <span className="text-xs font-semibold text-muted-foreground flex items-center gap-1 font-jp">
                          <Compass className="h-3.5 w-3.5 text-primary" /> {task.topic}
                        </span>
                      )}
                    </div>

                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => handlePlayAudio(task.echo_sentence || task.template_sentence || task.prompt_jp)}
                      className="h-8 px-2.5 rounded-xl border-primary/30 text-primary hover:bg-primary/10 text-xs font-semibold gap-1.5 shrink-0 shadow-2xs"
                      title="Nghe phát âm chuẩn Tokyo (P)"
                    >
                      <Volume2 className="h-4 w-4" />
                      <span className="hidden sm:inline">Nghe mẫu (P)</span>
                    </Button>
                  </div>

                  {/* Instruction Zone */}
                  <div className="space-y-1">
                    {subtitleMode === "hidden" ? (
                      <div className="p-3 rounded-xl bg-muted/30 border border-border/60 text-center text-xs text-muted-foreground">
                        🔒 Chế độ Ẩn đề bài — Hãy lắng nghe phát âm và tự tin phát ngôn
                      </div>
                    ) : (
                      <>
                        <div className="text-base sm:text-lg font-bold text-foreground font-jp leading-relaxed">
                          <UniversalFurigana text={task.prompt_jp} fontSize="lg" />
                        </div>
                        {subtitleMode === "vietnamese" && task.prompt_vi && (
                          <p className="text-xs text-muted-foreground leading-normal">
                            {task.prompt_vi}
                          </p>
                        )}
                      </>
                    )}
                  </div>

                  {/* Target Speech Board (Tách biệt rõ ràng từng kiểu bài tập) */}
                  <div className="space-y-2 pt-1">
                    {/* A. Từ khóa cần thay thế (Substitute Slot) */}
                    {task.substitution_variable && (
                      <div className="p-3.5 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-between gap-3 shadow-2xs">
                        <div className="space-y-0.5">
                          <span className="text-[10px] font-bold text-amber-700 dark:text-amber-300 uppercase tracking-wider block">
                            🎯 Từ khóa cần thay thế vào câu:
                          </span>
                          <div className="text-base sm:text-lg font-bold font-jp text-foreground">
                            「<UniversalFurigana text={task.substitution_variable} />」
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handlePlayAudio(task.substitution_variable!)}
                          className="h-8 px-2 rounded-xl text-amber-700 dark:text-amber-300 hover:bg-amber-500/20 text-xs font-semibold gap-1 shrink-0"
                          title="Nghe phát âm từ này"
                        >
                          <Volume2 className="h-4 w-4" />
                          <span className="hidden sm:inline">Nghe từ</span>
                        </Button>
                      </div>
                    )}

                    {/* B. Mẫu câu tham chiếu (Template Sentence) */}
                    {task.template_sentence && (
                      <div className="p-4 rounded-2xl bg-card border border-border/80 shadow-xs washi-texture space-y-1">
                        <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider block">
                          Mẫu câu tham chiếu:
                        </span>
                        <div className="text-base sm:text-lg font-bold text-foreground font-jp leading-relaxed">
                          「<UniversalFurigana text={task.template_sentence} fontSize="lg" />」
                        </div>
                      </div>
                    )}

                    {/* C. Câu nhại lại (Echo Sentence) */}
                    {task.echo_sentence && (
                      <div className="p-4 rounded-2xl bg-primary/10 border border-primary/20 text-center space-y-2.5">
                        <span className="text-[11px] font-bold text-primary block">
                          Câu mẫu chuẩn Tokyo — Hãy lắng nghe và nhại lại:
                        </span>
                        <div className="text-lg sm:text-xl font-bold text-foreground font-jp leading-relaxed">
                          「<UniversalFurigana text={task.echo_sentence} fontSize="lg" />」
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handlePlayAudio(task.echo_sentence!)}
                          className="h-8 px-3 rounded-xl border-primary/30 text-primary hover:bg-primary/15 gap-1.5 mx-auto font-bold shadow-2xs"
                        >
                          <Volume2 className="h-4 w-4" />
                          <span>Nghe phát âm chuẩn (P)</span>
                        </Button>
                      </div>
                    )}

                    {/* D. Câu hạt giống cần mở rộng (Seed Sentence) */}
                    {task.seed_sentence && (
                      <div className="p-4 rounded-2xl bg-card border border-border/80 shadow-xs washi-texture space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
                            Câu gốc cần mở rộng:
                          </span>
                          {task.expansion_dimension && (
                            <Badge variant="matcha" size="sm" className="font-bold text-[10px]">
                              + Thêm thông tin: {task.expansion_dimension}
                            </Badge>
                          )}
                        </div>
                        <div className="text-base sm:text-lg font-bold text-foreground font-jp leading-relaxed">
                          「<UniversalFurigana text={task.seed_sentence} fontSize="lg" />」
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* 2. Zen Voice Capsule Arena */}
              {ramp.phase === "prompting" && (
                <div
                  id="ramp-begin-speaking-card"
                  onClick={handleBeginExercise}
                  className="p-5 sm:p-6 rounded-3xl border-2 border-primary/30 hover:border-primary/60 bg-gradient-to-b from-card via-card to-primary/5 washi-texture shadow-xs hover:shadow-md transition-all cursor-pointer text-center space-y-3 group"
                >
                  <div className="relative h-16 w-16 mx-auto flex items-center justify-center">
                    <div className="absolute inset-0 rounded-full bg-primary/10 group-hover:scale-125 transition-transform animate-ping opacity-30" />
                    <div className="relative h-14 w-14 rounded-full bg-primary/15 border-2 border-primary/40 flex items-center justify-center text-primary group-hover:scale-105 transition-transform shadow-xs">
                      <Mic className="h-6 w-6" />
                    </div>
                  </div>
                  <div className="space-y-1">
                    <h3 className="font-extrabold text-sm sm:text-base text-foreground group-hover:text-primary transition-colors flex items-center justify-center gap-2">
                      <span>Bắt Đầu Phát Ngôn</span>
                      <span className="text-xs px-2 py-0.5 rounded-md bg-primary/10 text-primary font-bold">Space</span>
                    </h3>
                    <p className="text-xs text-muted-foreground max-w-sm mx-auto">
                      Bấm vào thẻ này hoặc nhấn phím <strong className="text-foreground font-mono">Space</strong> để mở micro và nói
                    </p>
                  </div>
                </div>
              )}

              {ramp.phase === "preparing" && prepLeft > 0 && (
                <div className="p-5 rounded-3xl bg-card border-2 border-primary/30 washi-texture text-center space-y-2 shadow-xs animate-in zoom-in-95 duration-150">
                  <div className="h-14 w-14 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center mx-auto text-primary font-mono text-2xl font-extrabold animate-pulse">
                    {Math.ceil(prepLeft)}
                  </div>
                  <div className="space-y-0.5">
                    <h4 className="font-bold text-sm text-foreground">Chuẩn bị ý tưởng...</h4>
                    <p className="text-xs text-muted-foreground">Micro sẽ tự động kích hoạt sau vài giây</p>
                  </div>
                </div>
              )}

              {ramp.phase === "recording" && (
                <div className="p-5 sm:p-6 rounded-3xl border-2 border-rose-500/40 bg-card washi-texture shadow-sm space-y-4 text-center animate-in fade-in duration-150">
                  <div className="flex items-center justify-center gap-4">
                    <div className="relative h-16 w-16 flex items-center justify-center">
                      <div className="absolute inset-0 rounded-full border-2 border-rose-500/20 animate-ping opacity-30" />
                      {targetSec > 0 && (
                        <svg className="absolute inset-0 h-full w-full -rotate-90">
                          <circle
                            cx="32"
                            cy="32"
                            r="28"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="4"
                            strokeDasharray="175"
                            strokeDashoffset={175 - Math.min(1, recElapsed / targetSec) * 175}
                            className="text-rose-500 transition-all duration-100"
                          />
                        </svg>
                      )}
                      <span className="text-base font-extrabold text-foreground font-mono">
                        {Math.floor(recElapsed)}s
                      </span>
                    </div>

                    <div className="text-left space-y-0.5">
                      <span className="flex items-center gap-2 text-xs sm:text-sm font-extrabold text-rose-500 animate-pulse">
                        <span className="h-2.5 w-2.5 rounded-full bg-rose-500" />
                        Đang ghi âm microphone
                      </span>
                      <span className="text-xs text-muted-foreground block">
                        {targetSec > 0 ? `Mục tiêu phát ngôn: ~${targetSec} giây` : "Hãy phát âm câu hoàn chỉnh"}
                      </span>
                    </div>
                  </div>

                  <div className="flex flex-col gap-2 pt-1">
                    <Button
                      id="ramp-stop-submit-btn"
                      size="lg"
                      variant="danger"
                      onClick={handleStopAndSubmit}
                      className="w-full py-4.5 rounded-2xl font-extrabold text-sm shadow-sm flex items-center justify-center gap-2"
                    >
                      <Square className="h-4 w-4 fill-current" />
                      <span>Hoàn tất & Nộp bài (Phím Space)</span>
                    </Button>

                    {/* Optional text input fallback */}
                    <button
                      type="button"
                      onClick={() => setShowTranscriptInput((v) => !v)}
                      className="text-[11px] text-muted-foreground hover:text-foreground transition-colors mx-auto pt-1"
                    >
                      {showTranscriptInput ? "▲ Ẩn ô nhập văn bản" : "▼ Hoặc gõ văn bản nếu ở nơi ồn ào"}
                    </button>
                    {showTranscriptInput && (
                      <textarea
                        id="ramp-transcript-input"
                        rows={2}
                        value={transcriptInput}
                        onChange={(e) => setTranscriptInput(e.target.value)}
                        placeholder="Nhập câu tiếng Nhật của bạn tại đây..."
                        className="w-full p-2.5 rounded-xl border border-border bg-background text-xs font-jp text-foreground focus:outline-none focus:ring-1 focus:ring-primary/40 animate-in fade-in duration-150"
                      />
                    )}
                  </div>
                </div>
              )}

              {ramp.phase === "submitting" && (
                <ZenLoadingState
                  variant="ai"
                  title="AI Đang Phân Tích Phản Xạ & Nấc Thang..."
                  ja="発話・リハビリ分析中..."
                  description="Kiểm tra mức độ hoàn chỉnh câu, mở rộng ý và tính tự lập phát ngôn..."
                />
              )}

              {/* 3. Feedback Card (When finished) */}
              {ramp.phase === "feedback" && ramp.submitResult && (
                <RampFeedbackCard
                  result={ramp.submitResult}
                  onRetry={handleRetry}
                  onNext={handleNext}
                  onElaborate={handleNext}
                  stageChanged={ramp.submitResult.delta?.stage_changed}
                />
              )}
            </div>

            {/* ── Right Column: Scaffold & Sidekick (5 cols on desktop) ── */}
            <div className="lg:col-span-5 space-y-3">
              {/* Dynamic Scaffolding Panel (Ghim song song bên phải) */}
              <RampScaffoldPanel
                task={task}
                supportLevel={ramp.supportLevel}
                onRevealHint={ramp.revealHint}
                hintRevealed={ramp.usedHint}
              />

              {/* Studio Sidekick Card (AI Coach & Shortcuts) */}
              <div className="p-4 rounded-2xl bg-card border border-border/80 washi-texture space-y-3 shadow-xs">
                <div className="flex items-center justify-between border-b border-border/60 pb-2.5">
                  <span className="text-xs font-bold text-foreground flex items-center gap-1.5">
                    <Sparkles className="h-3.5 w-3.5 text-primary" />
                    AI Coach Đồng Hành
                  </span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setCoachOpen(true)}
                    className="h-6 px-2 text-[10px] text-primary hover:text-primary/80 font-bold"
                  >
                    Mở Chat ➔
                  </Button>
                </div>

                <CoachQuickActions
                  route={pathname || "/ramp"}
                  onSelect={handleCoachSelect}
                />

                {/* 1-Line Clean Keybindings Bar */}
                <div className="pt-2 border-t border-border/60 flex items-center justify-between text-[11px] text-muted-foreground flex-wrap gap-1">
                  <span>
                    <kbd className="font-mono font-bold text-foreground bg-muted px-1.5 py-0.5 rounded border">Space</kbd> Nói/Nộp
                  </span>
                  <span>
                    <kbd className="font-mono font-bold text-foreground bg-muted px-1.5 py-0.5 rounded border">R</kbd> Làm lại
                  </span>
                  <span>
                    <kbd className="font-mono font-bold text-foreground bg-muted px-1.5 py-0.5 rounded border">N</kbd> Tiếp
                  </span>
                  <span>
                    <kbd className="font-mono font-bold text-foreground bg-muted px-1.5 py-0.5 rounded border">C</kbd> Cẩm nang
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Phase: COMPLETE -> Summary */}
        {ramp.phase === "complete" && ramp.summary && (
          <RampSessionSummaryCard
            summary={ramp.summary}
            onStartNew={handleNewSession}
          />
        )}
      </main>

      {/* ── Modals & Drawers ── */}
      <RampCheatsheetModal
        isOpen={showCheatsheet}
        onClose={() => setShowCheatsheet(false)}
      />

      <GlobalKeybindingsModal
        isOpen={showKeybindingsModal}
        onClose={() => setShowKeybindingsModal(false)}
      />

      <CoachPanel
        open={coachOpen}
        onClose={() => setCoachOpen(false)}
        route={pathname || "/ramp"}
        sessionId={ramp.session?.id}
      />
    </div>
  );
}
