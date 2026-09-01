"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Compass,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Sparkles,
  BookOpen,
  Keyboard,
  RotateCcw,
  Zap,
  ArrowRight,
  Send,
  Loader2,
  Edit3,
  HelpCircle,
  Home,
  Clock,
} from "lucide-react";
import { ReflexTimer as SituationsTimerBar } from "@/features/reflex/components/ReflexTimer";
import {
  SituationsLobby,
  SituationsPromptCard,
  SituationsResultCard,
  SituationsSessionSummary,
  SituationsCheatsheetModal,
  useSituationsSession,
  SituationsPressureLevel,
} from "@/features/situations";
import { GlobalKeybindingsModal } from "@/components/layout/global-keybindings-modal";
import { useSystemKeybindings, formatKeyDisplay } from "@/hooks/use-system-keybindings";
import { speakJapaneseText, stopWebSpeech } from "@/features/speaking/services/web-speech";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";
import { ZenLoadingState } from "@/components/ui/zen-loading-state";
import { ZenUnifiedInputBar } from "@/components/ui/zen-unified-input-bar";

export default function SituationsPage() {
  const [selectedCategory, setSelectedCategory] = useState<string>("infinite");
  const [customTopic, setCustomTopic] = useState<string>("");
  const [selectedMode, setSelectedMode] = useState<string>("standard");
  const [pressureLevel, setPressureLevel] = useState<SituationsPressureLevel>("normal");
  const [duration, setDuration] = useState<number>(5);
  const [elapsedSec, setElapsedSec] = useState(0);
  const [subtitleMode, setSubtitleMode] = useState<"hidden" | "japanese" | "japanese_reading" | "vietnamese">("japanese");
  const [inputMode, setInputMode] = useState<"voice" | "text">("voice");
  const [transcriptInput, setTranscriptInput] = useState("");
  const [isCheatsheetOpen, setIsCheatsheetOpen] = useState(false);
  const [isKeybindingsOpen, setIsKeybindingsOpen] = useState(false);
  const [coachHint, setCoachHint] = useState<string | null>(null);
  const [hintTier, setHintTier] = useState<number>(0);

  const { matchesAction, keybindings } = useSystemKeybindings();

  // Load preferences from localStorage on mount
  useEffect(() => {
    try {
      const savedCat = localStorage.getItem("speaking_situations_category");
      if (savedCat) setSelectedCategory(savedCat);
      const savedTopic = localStorage.getItem("speaking_situations_customtopic");
      if (savedTopic) setCustomTopic(savedTopic);
      const savedMode = localStorage.getItem("speaking_situations_mode");
      if (savedMode) setSelectedMode(savedMode);
      const savedPressure = localStorage.getItem("speaking_situations_pressure");
      if (savedPressure) setPressureLevel(savedPressure as any);
      const savedDuration = localStorage.getItem("speaking_situations_duration");
      if (savedDuration !== null) setDuration(Number(savedDuration));
      const savedSubtitle = localStorage.getItem("speaking_situations_subtitle");
      if (savedSubtitle) setSubtitleMode(savedSubtitle as any);
    } catch (e) {}
  }, []);

  // Save preferences on change
  useEffect(() => {
    try {
      localStorage.setItem("speaking_situations_category", selectedCategory);
      localStorage.setItem("speaking_situations_customtopic", customTopic);
      localStorage.setItem("speaking_situations_mode", selectedMode);
      localStorage.setItem("speaking_situations_pressure", pressureLevel);
      localStorage.setItem("speaking_situations_duration", String(duration));
      localStorage.setItem("speaking_situations_subtitle", subtitleMode);
    } catch (e) {}
  }, [selectedCategory, customTopic, selectedMode, pressureLevel, duration, subtitleMode]);

  const session = useSituationsSession({
    category: selectedCategory,
    customTopic,
    subMode: "situational_roleplay",
    pressureLevel,
    duration,
    mode: selectedMode,
    autoNext: true,
  });

  const activeExercise = session.exercise;
  const playedPromptExerciseIdRef = useRef<string | null>(null);

  // Reset hint tier when exercise changes
  useEffect(() => {
    setHintTier(0);
  }, [session.exercise?.id]);

  const playPromptAudio = useCallback(
    (autoTransition = false) => {
      if (!activeExercise) return;
      const sc = activeExercise.extra_metadata?.situational_config || {};
      const sData = activeExercise.situationalData || sc.situational_data || {};
      const text = sData.npc_opening_dialogue || activeExercise.prompt || activeExercise.canonical;

      if (text) {
        speakJapaneseText(text, {
          rate: 1.0,
          onEnd: () => {
            if (autoTransition) session.onPromptAudioFinished();
          },
          onError: () => {
            if (autoTransition) session.onPromptAudioFinished();
          },
        });
      } else if (autoTransition) {
        session.onPromptAudioFinished();
      }
    },
    [activeExercise, session.onPromptAudioFinished]
  );

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

  useEffect(() => {
    return () => {
      stopWebSpeech();
      session.recorder.releaseMicrophone();
      session.speech.stopListening();
    };
  }, []);

  useEffect(() => {
    if (session.phase === "idle" || session.phase === "summary") {
      setElapsedSec(0);
      return;
    }
    const interval = setInterval(() => {
      setElapsedSec((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, [session.phase]);

  useEffect(() => {
    if (session.phase === "result" && session.result) {
      if (session.result.isPerfect) {
        soundFX.playVictory();
      } else if (session.result.success) {
        soundFX.playSuikinkutsu();
      } else if (session.result.timedOut) {
        soundFX.playTaiko();
      }
    }
  }, [session.phase, session.result]);

  const handleDirectSubmit = async () => {
    const text = transcriptInput.trim() || session.speech.transcript.trim() || session.exercise?.canonical || " ";
    await session.submitWithTranscript(text);
    setTranscriptInput("");
  };

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName?.toLowerCase();
      if (tag === "textarea" || tag === "input") {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          handleDirectSubmit();
        }
        return;
      }

      if (matchesAction(e, "situationsOpenCheatsheet")) {
        e.preventDefault();
        soundFX.playFurin();
        setIsCheatsheetOpen((v) => !v);
      } else if (matchesAction(e, "openKeybindingsModal")) {
        e.preventDefault();
        soundFX.playFurin();
        setIsKeybindingsOpen((v) => !v);
      } else if (e.key === "Escape") {
        if (isCheatsheetOpen) {
          setIsCheatsheetOpen(false);
        } else if (isKeybindingsOpen) {
          setIsKeybindingsOpen(false);
        } else if (session.phase !== "idle") {
          soundFX.playFurin();
          session.setPhase("idle");
        }
      } else if (matchesAction(e, "situationsRetry") && session.phase === "result") {
        e.preventDefault();
        soundFX.playFurin();
        session.retry();
      } else if (matchesAction(e, "situationsSkip") && session.phase === "result") {
        e.preventDefault();
        soundFX.playSuikinkutsu();
        session.startNext();
      } else if (
        (matchesAction(e, "situationsReplayModel") ||
          matchesAction(e, "situationsListenPrompt") ||
          matchesAction(e, "drillReplayAudio")) &&
        session.phase === "result"
      ) {
        e.preventDefault();
        const sc = session.exercise?.extra_metadata?.situational_config || {};
        const canonical = sc.canonical || session.exercise?.canonical || "";
        if (canonical) {
          soundFX.playFurin();
          speakJapaneseText(canonical, { rate: 0.95 });
        }
      } else if (matchesAction(e, "situationsListenPrompt")) {
        e.preventDefault();
        soundFX.playFurin();
        playPromptAudio(false);
      } else if (matchesAction(e, "situationsToggleHint")) {
        e.preventDefault();
        soundFX.playFurin();
        setHintTier((prev) => (prev + 1) % 4);
      } else if (matchesAction(e, "situationsToggleInputMode")) {
        e.preventDefault();
        soundFX.playFurin();
        setInputMode((m) => (m === "voice" ? "text" : "voice"));
      } else if (matchesAction(e, "situationsStartVoice") && session.phase === "ready") {
        e.preventDefault();
        soundFX.playFurin();
        session.startVoiceRecording();
      } else if (matchesAction(e, "situationsSubmitOrNext")) {
        e.preventDefault();
        if (session.phase === "idle") {
          soundFX.playKatana();
          session.startSession();
        } else if (session.phase === "waiting_for_speech" || session.phase === "recording") {
          handleDirectSubmit();
        } else if (session.phase === "result") {
          soundFX.playSuikinkutsu();
          session.startNext();
        }
      }
    };

    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [session.phase, transcriptInput, isCheatsheetOpen, isKeybindingsOpen, matchesAction, playPromptAudio]);

  return (
    <div className="w-full text-foreground space-y-3">
      {/* 1. Lobby View */}
      {session.phase === "idle" && (
        <SituationsLobby
          selectedCategory={selectedCategory}
          onSelectCategory={setSelectedCategory}
          customTopic={customTopic}
          onSelectCustomTopic={setCustomTopic}
          selectedMode={selectedMode}
          onSelectMode={setSelectedMode}
          pressureLevel={pressureLevel}
          onSelectPressureLevel={setPressureLevel}
          duration={duration}
          onSelectDuration={setDuration}
          subtitleMode={subtitleMode}
          onSelectSubtitleMode={setSubtitleMode}
          onStartSession={session.startSession}
          onOpenCheatsheet={() => setIsCheatsheetOpen(true)}
          onOpenKeybindings={() => setIsKeybindingsOpen(true)}
          isLoading={false}
        />
      )}

      {/* 2. Active Session View */}
      {session.phase !== "idle" && session.phase !== "summary" && (
        <div className="max-w-5xl mx-auto space-y-3 animate-in fade-in duration-200">
          {/* Top Session Navigation Header */}
          <div className="p-3 rounded-2xl border border-border bg-card washi-texture flex flex-wrap items-center justify-between gap-2 shadow-2xs">
            <div className="flex items-center gap-2.5">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  soundFX.playFurin();
                  session.setPhase("idle");
                }}
                className="h-7 w-7 p-0 text-muted-foreground hover:text-foreground rounded-lg"
                title="Về Sảnh chính (Esc)"
              >
                <Home className="h-3.5 w-3.5" />
              </Button>

              <Badge variant="matcha" size="sm" className="font-bold text-[10px]">
                TÌNH HUỐNG THỰC CHIẾN
              </Badge>

              <span className="text-[11px] font-bold text-muted-foreground">
                Câu #{session.results.length + 1}
              </span>

              <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-mono font-bold bg-muted/60 text-foreground border border-border shadow-2xs">
                <Clock className="h-3 w-3 text-primary" />
                <span>
                  {duration === 0
                    ? `Phiên: ${Math.floor(elapsedSec / 60)}:${String(elapsedSec % 60).padStart(2, "0")} / ∞`
                    : `Phiên: ${Math.floor(elapsedSec / 60)}:${String(elapsedSec % 60).padStart(2, "0")} / ${duration}m`}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  soundFX.playFurin();
                  setIsCheatsheetOpen(true);
                }}
                className="h-7 gap-1 text-[11px] font-bold shadow-2xs"
              >
                <BookOpen className="h-3 w-3" />
                <span className="hidden sm:inline">Sổ tay (C)</span>
              </Button>

              <Button
                variant="ghost"
                size="sm"
                onClick={() => session.setPhase("summary")}
                className="h-7 text-[11px] font-bold text-muted-foreground hover:text-foreground"
              >
                Kết thúc
              </Button>
            </div>
          </div>

          {/* Loading State */}
          {session.phase === "loading" && (
            <ZenLoadingState
              variant="ai"
              title="AI Đang Khởi Tạo Tình Huống Sống Động..."
              ja="ロールプレイ生成中..."
              description="Đang thiết lập bối cảnh thực tế, nhân vật AI bản xứ và mục tiêu giao tiếp..."
            />
          )}

          {/* Active Workout Cockpit (2-Column No-Scroll Layout) */}
          {(session.phase === "prompt_playing" ||
            session.phase === "ready" ||
            session.phase === "waiting_for_speech" ||
            session.phase === "recording" ||
            session.phase === "evaluating") && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-3.5 items-start">
              {/* Left Column: Context & Dialogue (2 cols) */}
              <div className="lg:col-span-2 space-y-3">
                <SituationsPromptCard
                  exercise={activeExercise}
                  subtitleMode={subtitleMode}
                  onPlayAudio={() => playPromptAudio(false)}
                  phase={session.phase}
                  hintTier={hintTier}
                  onSetHintTier={setHintTier}
                />
              </div>

              {/* Right Column: Interaction Cockpit (1 col) */}
              <div className="space-y-3">
                {/* Reflex Timer Bar */}
                <div className="p-3.5 rounded-2xl bg-card border border-border/80 washi-texture shadow-xs space-y-2">
                  <div className="flex items-center justify-between text-[11px] font-bold text-muted-foreground">
                    <span>Áp Lực Phản Xạ</span>
                    <span>{session.timer.isInfinite ? "∞ Vô hạn" : `${(session.timer.remainingMs / 1000).toFixed(1)}s`}</span>
                  </div>
                  <SituationsTimerBar
                    remainingMs={session.timer.remainingMs}
                    timerLimitMs={session.timer.totalLimitMs}
                    progress={session.timer.progress}
                    state={session.timer.state}
                    isActive={session.timer.isActive}
                    isPaused={session.timer.isPaused}
                    variant="bar"
                  />
                </div>

                {/* Speech Capture Controller Box */}
                <div className="p-4 rounded-2xl border border-border bg-card washi-texture shadow-xs space-y-3 text-center">
                  {session.phase === "prompt_playing" && (
                    <div className="py-4 space-y-2">
                      <div className="h-9 w-9 rounded-full bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-600 mx-auto animate-pulse">
                        <Volume2 className="h-4 w-4" />
                      </div>
                      <p className="text-xs font-bold text-foreground">NPC đang nói câu mở đầu...</p>
                      <span className="text-[11px] text-muted-foreground">Hãy lắng nghe kỹ để đối đáp phù hợp</span>
                    </div>
                  )}

                  {session.phase === "ready" && (
                    <div className="space-y-3 py-1">
                      <p className="text-[11px] text-muted-foreground font-semibold">
                        NPC đã dứt lời. Nhấn nút bên dưới hoặc phím{" "}
                        <kbd className="px-1.5 py-0.5 rounded bg-muted border text-[10px] font-bold">
                          {formatKeyDisplay(keybindings.situationsStartVoice)}
                        </kbd>{" "}
                        để bắt đầu nói.
                      </p>
                      <Button
                        variant="akane"
                        size="lg"
                        onClick={() => {
                          soundFX.playFurin();
                          session.startVoiceRecording();
                        }}
                        className="w-full gap-2 font-bold text-xs h-10 rounded-xl shadow-md"
                      >
                        <Mic className="h-4 w-4" />
                        <span>Bắt Đầu Trả Lời (Space)</span>
                      </Button>
                    </div>
                  )}

                  {(session.phase === "waiting_for_speech" || session.phase === "recording") && (
                    <div className="space-y-3">
                      <div className="flex items-center justify-center gap-2">
                        <span className={cn(
                          "h-2.5 w-2.5 rounded-full animate-ping",
                          session.isUserSpeaking ? "bg-emerald-500" : "bg-rose-500"
                        )} />
                        <span className="text-xs font-bold text-foreground">
                          {session.isUserSpeaking ? "🗣️ Đang nhận diện giọng nói..." : "🎤 Nói vào mic hoặc gõ phím bên dưới..."}
                        </span>
                      </div>

                      {/* Unified Voice & Keyboard Input Bar */}
                      <ZenUnifiedInputBar
                        value={transcriptInput}
                        onChange={setTranscriptInput}
                        onSubmit={handleDirectSubmit}
                        speechTranscript={session.speech.transcript}
                        isRecording={session.phase === "recording" || session.isUserSpeaking}
                        isEvaluating={false}
                        placeholder="Nói vào mic hoặc gõ câu đối đáp tiếng Nhật... (Enter để gửi)"
                        submitButtonText="Gửi"
                        autoFocus={true}
                        hintText="Gõ phím thoải mái khi ở văn phòng"
                      />
                    </div>
                  )}

                  {session.phase === "evaluating" && (
                    <ZenLoadingState
                      variant="ai"
                      title="AI Đang Đánh Giá Ngữ Dụng & Mục Tiêu Giao Tiếp..."
                      ja="語用論・会話目標分析中..."
                      description="Kiểm tra mức độ hoàn thành mục tiêu tình huống, phong cách giao tiếp và tính tự nhiên..."
                    />
                  )}
                </div>

                {/* Keyboard Shortcuts Helper */}
                <div className="p-2.5 rounded-xl bg-muted/40 border border-border/60 text-[10px] text-muted-foreground flex flex-wrap items-center justify-between gap-1.5">
                  <span><kbd className="px-1 py-0.2 rounded bg-muted border font-bold">Space</kbd> Nói</span>
                  <span><kbd className="px-1 py-0.2 rounded bg-muted border font-bold">H</kbd> Gợi ý</span>
                  <span><kbd className="px-1 py-0.2 rounded bg-muted border font-bold">L</kbd> Nghe</span>
                  <span><kbd className="px-1 py-0.2 rounded bg-muted border font-bold">Esc</kbd> Sảnh</span>
                </div>
              </div>
            </div>
          )}

          {/* Result State */}
          {session.phase === "result" && session.result && (
            <SituationsResultCard
              result={session.result}
              exercise={activeExercise}
              onNext={session.startNext}
              onRetry={session.retry}
              onAskCoach={(prompt) => setCoachHint(prompt)}
              onCancelAutoNext={session.cancelAutoNext}
            />
          )}
        </div>
      )}

      {/* 3. Session Summary View */}
      {session.phase === "summary" && (
        <SituationsSessionSummary
          results={session.results}
          onRestart={session.startSession}
          onToLobby={() => session.setPhase("idle")}
          onRetryWeak={session.startSession}
        />
      )}

      {/* Modals */}
      <SituationsCheatsheetModal
        isOpen={isCheatsheetOpen}
        onClose={() => setIsCheatsheetOpen(false)}
      />

      <GlobalKeybindingsModal
        isOpen={isKeybindingsOpen}
        onClose={() => setIsKeybindingsOpen(false)}
      />
    </div>
  );
}
