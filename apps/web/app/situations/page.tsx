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

export default function SituationsPage() {
  const [selectedCategory, setSelectedCategory] = useState<string>("infinite");
  const [customTopic, setCustomTopic] = useState<string>("");
  const [selectedMode, setSelectedMode] = useState<string>("standard");
  const [pressureLevel, setPressureLevel] = useState<SituationsPressureLevel>("normal");
  const [duration, setDuration] = useState<number>(5);
  const [subtitleMode, setSubtitleMode] = useState<"hidden" | "japanese" | "japanese_reading" | "vietnamese">("japanese");
  const [inputMode, setInputMode] = useState<"voice" | "text">("voice");
  const [transcriptInput, setTranscriptInput] = useState("");
  const [isCheatsheetOpen, setIsCheatsheetOpen] = useState(false);
  const [isKeybindingsOpen, setIsKeybindingsOpen] = useState(false);
  const [coachHint, setCoachHint] = useState<string | null>(null);

  const { matchesAction, keybindings } = useSystemKeybindings();

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
      } else if (matchesAction(e, "situationsListenPrompt")) {
        e.preventDefault();
        soundFX.playFurin();
        playPromptAudio(false);
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
    <div className="min-h-screen bg-background text-foreground py-8 px-4 sm:px-6">
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
        <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in duration-200">
          {/* Top Session Navigation Header */}
          <div className="p-4 rounded-2xl border border-border bg-card washi-texture flex flex-wrap items-center justify-between gap-3 shadow-sm">
            <div className="flex items-center gap-3">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  soundFX.playFurin();
                  session.setPhase("idle");
                }}
                className="h-8 w-8 p-0 text-muted-foreground hover:text-foreground rounded-xl"
                title="Về Sảnh chính (Esc)"
              >
                <Home className="h-4 w-4" />
              </Button>

              <Badge variant="matcha" size="sm" className="font-bold">
                TÌNH HUỐNG THỰC CHIẾN
              </Badge>

              <span className="text-xs font-bold text-muted-foreground">
                Câu #{session.results.length + 1}
              </span>
            </div>

            {/* Middle Reflex Timer Bar */}
            <div className="w-full sm:w-64">
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

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  soundFX.playFurin();
                  setIsCheatsheetOpen(true);
                }}
                className="h-8 gap-1.5 text-xs font-bold shadow-2xs"
              >
                <BookOpen className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">Sổ tay (C)</span>
              </Button>

              <Button
                variant="ghost"
                size="sm"
                onClick={() => session.setPhase("summary")}
                className="h-8 text-xs font-bold text-muted-foreground hover:text-foreground"
              >
                Kết thúc phiên
              </Button>
            </div>
          </div>

          {/* Loading State */}
          {session.phase === "loading" && (
            <div className="p-16 rounded-3xl border border-border bg-card washi-texture flex flex-col items-center justify-center gap-3 text-center">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
              <div className="text-sm font-bold text-foreground">AI Đang Tạo Tình Huống Sống Động...</div>
              <p className="text-xs text-muted-foreground">Đang thiết lập địa điểm, nhân vật NPC và mục tiêu nhiệm vụ</p>
            </div>
          )}

          {/* Prompt Playing & Ready State */}
          {(session.phase === "prompt_playing" ||
            session.phase === "ready" ||
            session.phase === "waiting_for_speech" ||
            session.phase === "recording" ||
            session.phase === "evaluating") && (
            <div className="space-y-6">
              <SituationsPromptCard
                exercise={activeExercise}
                subtitleMode={subtitleMode}
                onPlayAudio={() => playPromptAudio(false)}
                phase={session.phase}
              />

              {/* Speech Capture Controller Box */}
              <div className="p-6 rounded-3xl border border-border bg-card washi-texture shadow-sm space-y-4 text-center">
                {session.phase === "ready" && (
                  <div className="space-y-3">
                    <p className="text-xs text-muted-foreground font-semibold">
                      NPC đã dứt lời. Nhấn nút bên dưới hoặc phím <kbd className="px-1.5 py-0.5 rounded bg-muted border text-[10px] font-bold">Space</kbd> để bắt đầu nói.
                    </p>
                    <Button
                      variant="akane"
                      size="lg"
                      onClick={() => {
                        soundFX.playFurin();
                        session.startVoiceRecording();
                      }}
                      className="gap-2 font-bold text-xs px-8 h-11 rounded-2xl shadow-md"
                    >
                      <Mic className="h-4 w-4" />
                      <span>Bắt Đầu Trả Lời (Space)</span>
                    </Button>
                  </div>
                )}

                {(session.phase === "waiting_for_speech" || session.phase === "recording") && (
                  <div className="space-y-4">
                    <div className="flex items-center justify-center gap-2">
                      <span className={cn(
                        "h-3 w-3 rounded-full animate-ping",
                        session.isUserSpeaking ? "bg-emerald-500" : "bg-rose-500"
                      )} />
                      <span className="text-xs font-bold text-foreground">
                        {session.isUserSpeaking ? "🗣️ Đang nhận diện giọng nói của bạn..." : "🎤 Hãy phát âm câu đối đáp tiếng Nhật..."}
                      </span>
                    </div>

                    {/* Speech Transcript Preview */}
                    <div className="p-4 rounded-2xl bg-muted/40 border border-border/80 min-h-[56px] flex items-center justify-center">
                      <span className="text-base font-bold font-jp text-primary">
                        {session.speech.transcript || "Đang lắng nghe..."}
                      </span>
                    </div>

                    {/* Manual Text Fallback */}
                    {inputMode === "text" && (
                      <div className="flex gap-2 max-w-lg mx-auto">
                        <input
                          value={transcriptInput}
                          onChange={(e) => setTranscriptInput(e.target.value)}
                          placeholder="Hoặc gõ câu đối đáp tiếng Nhật..."
                          className="flex-1 bg-background border border-border rounded-xl px-3.5 py-2 text-xs focus:outline-none focus:border-primary font-jp"
                        />
                        <Button
                          size="sm"
                          onClick={handleDirectSubmit}
                          className="text-xs font-bold gap-1.5 rounded-xl"
                        >
                          <Send className="h-3.5 w-3.5" />
                          <span>Gửi</span>
                        </Button>
                      </div>
                    )}

                    <div className="flex items-center justify-center gap-4 text-[11px] text-muted-foreground pt-1">
                      <button
                        onClick={() => setInputMode((m) => (m === "voice" ? "text" : "voice"))}
                        className="hover:underline flex items-center gap-1 font-semibold"
                      >
                        <Edit3 className="h-3 w-3" />
                        <span>{inputMode === "voice" ? "Chuyển sang gõ text (T)" : "Chuyển sang thu âm mic (T)"}</span>
                      </button>
                    </div>
                  </div>
                )}

                {session.phase === "evaluating" && (
                  <div className="py-6 flex flex-col items-center justify-center gap-2">
                    <Loader2 className="h-6 w-6 animate-spin text-primary" />
                    <span className="text-xs font-bold text-muted-foreground">
                      AI Đang Đánh Giá Mức Độ Đạt Mục Tiêu...
                    </span>
                  </div>
                )}
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
