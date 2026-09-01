"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import {
  Crown,
  Mic,
  Clock,
  Play,
  RotateCcw,
  Sparkles,
  BookOpen,
  Edit3,
} from "lucide-react";
import { useKeigoSession } from "@/features/keigo/hooks/useKeigoSession";
import { ReflexTimer as KeigoTimer } from "@/features/reflex/components/ReflexTimer";
import { KeigoPromptCard } from "@/features/keigo/components/KeigoPromptCard";
import { KeigoResultCard } from "@/features/keigo/components/KeigoResultCard";
import { KeigoSessionSummary } from "@/features/keigo/components/KeigoSessionSummary";
import { KeigoCheatsheetModal } from "@/features/keigo/components/KeigoCheatsheetModal";
import { KeigoLobby, KEIGO_SUB_MODES, PRESSURE_LEVELS } from "@/features/keigo/components/KeigoLobby";
import { GlobalKeybindingsModal } from "@/components/layout/global-keybindings-modal";
import { CoachPanel } from "@/features/coach";
import { usePathname } from "next/navigation";
import { useCoachCore } from "@/features/coach/hooks/useCoachCore";
import { CoachInsightCard } from "@/features/coach/components/CoachInsightCard";
import { useCoachProactive } from "@/features/coach/hooks/useCoachProactive";
import { useSystemKeybindings, formatKeyDisplay } from "@/hooks/use-system-keybindings";
import { speakJapaneseText, stopWebSpeech } from "@/features/speaking/services/web-speech";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";
import { ZenLoadingState } from "@/components/ui/zen-loading-state";
import { ZenUnifiedInputBar } from "@/components/ui/zen-unified-input-bar";

export default function KeigoPage() {
  const [subMode, setSubMode] = useState("mixed");
  const [pressure, setPressure] = useState<"infinite" | "relaxed" | "normal" | "fast" | "reflex" | "extreme">("normal");
  const [subtitleMode, setSubtitleMode] = useState<"hidden" | "japanese" | "japanese_reading" | "vietnamese">("japanese");
  const [startTrigger, setStartTrigger] = useState<"manual" | "auto">("manual");
  const [transcriptInput, setTranscriptInput] = useState("");
  const [showTextInput, setShowTextInput] = useState(false);
  const [showSummary, setShowSummary] = useState(false);
  const [showCheatsheet, setShowCheatsheet] = useState(false);
  const [showKeybindingsModal, setShowKeybindingsModal] = useState(false);
  const [duration, setDuration] = useState<0 | 3 | 5 | 10 | 20>(5);
  const [sessionRemainingSec, setSessionRemainingSec] = useState(duration * 60);
  const [elapsedSec, setElapsedSec] = useState(0);
  const [autoNext, setAutoNext] = useState(false);

  const sessionEndTimestampRef = useRef<number | null>(null);
  const sessionPausedRemainingMsRef = useRef<number>(duration * 60 * 1000);

  const { matchesAction, keybindings } = useSystemKeybindings();

  // Load preferences from localStorage on mount
  useEffect(() => {
    try {
      const savedSubMode = localStorage.getItem("speaking_keigo_submode");
      if (savedSubMode) setSubMode(savedSubMode);
      const savedPressure = localStorage.getItem("speaking_keigo_pressure");
      if (savedPressure) setPressure(savedPressure as any);
      const savedDuration = localStorage.getItem("speaking_keigo_duration");
      if (savedDuration !== null) setDuration(Number(savedDuration) as any);
      const savedSubtitle = localStorage.getItem("speaking_keigo_subtitle");
      if (savedSubtitle) setSubtitleMode(savedSubtitle as any);
      const savedTrigger = localStorage.getItem("speaking_keigo_trigger");
      if (savedTrigger) setStartTrigger(savedTrigger as any);
      const savedAutoNext = localStorage.getItem("speaking_keigo_autonext");
      if (savedAutoNext !== null) setAutoNext(savedAutoNext === "true");
    } catch (e) {}
  }, []);

  // Save preferences on change
  useEffect(() => {
    try {
      localStorage.setItem("speaking_keigo_submode", subMode);
      localStorage.setItem("speaking_keigo_pressure", pressure);
      localStorage.setItem("speaking_keigo_duration", String(duration));
      localStorage.setItem("speaking_keigo_subtitle", subtitleMode);
      localStorage.setItem("speaking_keigo_trigger", startTrigger);
      localStorage.setItem("speaking_keigo_autonext", String(autoNext));
    } catch (e) {}
  }, [subMode, pressure, duration, subtitleMode, startTrigger, autoNext]);

  const session = useKeigoSession({
    subMode,
    pressureLevel: pressure as any,
    autoNext,
    startTrigger,
  });

  useEffect(() => {
    if (session.phase === "idle" || session.phase === "summary" || showSummary) {
      setSessionRemainingSec(duration * 60);
      setElapsedSec(0);
      sessionEndTimestampRef.current = null;
      sessionPausedRemainingMsRef.current = duration * 60 * 1000;
    }
  }, [duration, session.phase, showSummary]);

  useEffect(() => {
    const isSessionActive = session.phase !== "idle" && session.phase !== "summary" && !showSummary;
    if (!isSessionActive) return;

    if (duration === 0) {
      // Endless session timer: count elapsed seconds upward
      const interval = setInterval(() => {
        setElapsedSec((prev) => prev + 1);
      }, 1000);
      return () => clearInterval(interval);
    }

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
        soundFX.playVictory();
      }
    }, 500);

    return () => clearInterval(interval);
  }, [session.phase, session.isPaused, showSummary, session.setPhase, duration]);

  const timerMs = PRESSURE_LEVELS.find((p) => p.id === pressure)?.ms ?? 5000;
  const activeExercise = session.exercise;
  const pathname = usePathname();
  const { insights, dismiss } = useCoachProactive();
  const [coachOpen, setCoachOpen] = useState(false);
  const coach = useCoachCore();

  const handleCoachSelect = (prompt: string) => {
    setCoachOpen(true);
    setTimeout(() => coach.ask(prompt, { route: pathname || "/keigo", exerciseId: (activeExercise as any)?.id }), 300);
  };

  const playedPromptExerciseIdRef = useRef<string | null>(null);

  const playPromptAudio = useCallback(
    (autoTransition = false) => {
      if (!activeExercise) return;
      const rc = activeExercise.extra_metadata?.keigo_config || {};
      const text = rc.prompt || activeExercise.prompt || activeExercise.scenario || activeExercise.title;
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
    const text = transcriptInput.trim() || session.speech.transcript.trim();
    if (!text) return;
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

      if (matchesAction(e, "openKeybindingsModal") || matchesAction(e, "drillToggleHelp")) {
        e.preventDefault();
        setShowKeybindingsModal((v) => !v);
      } else if (matchesAction(e, "keigoOpenCheatsheet")) {
        e.preventDefault();
        setShowCheatsheet((v) => !v);
      } else if (matchesAction(e, "keigoToggleInputMode")) {
        e.preventDefault();
        setShowTextInput((v) => !v);
      } else if (
        matchesAction(e, "keigoToggleHint") &&
        session.phase !== "idle" &&
        session.phase !== "summary"
      ) {
        e.preventDefault();
        soundFX.playFurin();
        session.cycleHint();
      } else if (matchesAction(e, "keigoRetry") && session.phase === "result") {
        e.preventDefault();
        soundFX.playSuikinkutsu();
        session.retry();
      } else if (matchesAction(e, "keigoSkip") && session.phase === "result") {
        e.preventDefault();
        soundFX.playSuikinkutsu();
        session.startNext();
      } else if (
        (matchesAction(e, "keigoReplayModel") ||
          matchesAction(e, "keigoListenPrompt") ||
          matchesAction(e, "drillReplayAudio")) &&
        session.phase === "result"
      ) {
        e.preventDefault();
        const canonical =
          session.result?.canonicalAnswer ||
          session.exercise?.canonical ||
          (session.exercise?.target_patterns && session.exercise.target_patterns.length > 0
            ? session.exercise.target_patterns[0]
            : "");
        if (canonical) {
          soundFX.playFurin();
          speakJapaneseText(canonical, { rate: 0.95 });
        }
      } else if (matchesAction(e, "keigoListenPrompt") && session.phase !== "idle") {
        e.preventDefault();
        playPromptAudio(false);
      } else if (e.key === "Escape") {
        if (showCheatsheet) {
          setShowCheatsheet(false);
        } else if (showKeybindingsModal) {
          setShowKeybindingsModal(false);
        } else if (session.phase !== "idle") {
          session.setPhase("idle" as any);
          setShowSummary(false);
          stopWebSpeech();
        }
      } else if (matchesAction(e, "keigoSubmitOrNext") || matchesAction(e, "drillSubmitOrNext")) {
        e.preventDefault();
        if (session.phase === "ready") {
          session.startVoiceRecording();
        } else if (session.phase === "waiting_for_speech" || session.phase === "recording") {
          handleDirectSubmit();
        } else if (session.phase === "result") {
          soundFX.playSuikinkutsu();
          session.startNext();
        }
      } else if (matchesAction(e, "keigoStartVoice")) {
        if (session.phase === "ready") {
          e.preventDefault();
          session.startVoiceRecording();
        }
      }
    };

    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [session.phase, transcriptInput, session.speech.transcript, showCheatsheet, showKeybindingsModal, matchesAction, playPromptAudio]);

  const formatSessionTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  if (showSummary || session.phase === "summary") {
    return (
      <div className="py-6 animate-in fade-in duration-300">
        <KeigoSessionSummary
          results={session.results}
          onRestart={() => {
            setShowSummary(false);
            soundFX.playSuikinkutsu();
            session.startSession();
          }}
          onToLobby={() => {
            setShowSummary(false);
            session.setPhase("idle" as any);
          }}
          onRetryWeak={() => {
            setShowSummary(false);
            soundFX.playSuikinkutsu();
            session.startSession();
          }}
        />
      </div>
    );
  }

  if (session.phase === "idle") {
    return (
      <div className="py-2">
        <KeigoLobby
          subMode={subMode}
          setSubMode={setSubMode}
          pressure={pressure}
          setPressure={setPressure}
          subtitleMode={subtitleMode}
          setSubtitleMode={setSubtitleMode}
          duration={duration}
          setDuration={setDuration}
          autoNext={autoNext}
          setAutoNext={setAutoNext}
          startTrigger={startTrigger}
          setStartTrigger={setStartTrigger}
          onStartSession={() => {
            soundFX.playKatana();
            session.startSession();
          }}
          onOpenCheatsheet={() => setShowCheatsheet(true)}
          onOpenHelp={() => setShowKeybindingsModal(true)}
          error={session.error}
        />

        <KeigoCheatsheetModal isOpen={showCheatsheet} onClose={() => setShowCheatsheet(false)} />
        <GlobalKeybindingsModal isOpen={showKeybindingsModal} onClose={() => setShowKeybindingsModal(false)} />
      </div>
    );
  }

  const isEvaluating = session.phase === "evaluating" || session.phase === "loading";
  const isRecordingOrWaiting = session.phase === "waiting_for_speech" || session.phase === "recording";
  const currentSubModeInfo = KEIGO_SUB_MODES.find((m) => m.id === subMode) || KEIGO_SUB_MODES[0];

  return (
    <div className="max-w-5xl mx-auto space-y-4 animate-in fade-in duration-300 pb-8">
      {/* Session Top Status Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 rounded-2xl bg-card border border-border/80 washi-texture shadow-xs">
        <div className="flex items-center gap-2">
          <Badge variant={currentSubModeInfo.badgeVariant} size="sm" className="font-bold">
            {currentSubModeInfo.ja} • {currentSubModeInfo.label}
          </Badge>
          <div className="hidden sm:flex items-center gap-2 text-xs font-semibold text-muted-foreground">
            <span>•</span>
            <span>Đúng: <strong className="text-emerald-600 dark:text-emerald-400">{session.stats.correct}</strong>/{session.stats.total}</span>
            <span>•</span>
            <span>TB: <strong className="text-foreground">{session.stats.avgLatency ? Math.round(session.stats.avgLatency) : "—"}ms</strong></span>
          </div>
        </div>

        <div className="flex items-center gap-3 ml-auto">
          <div
            className={cn(
              "flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-bold border shadow-2xs",
              sessionRemainingSec <= 30
                ? "bg-rose-500/10 text-rose-600 border-rose-500/30 animate-pulse"
                : "bg-muted/60 text-foreground border-border"
            )}
          >
            <Clock className="h-3.5 w-3.5 text-primary" />
            <span>{duration === 0 ? `Phiên: ${formatSessionTime(elapsedSec)} / ∞` : formatSessionTime(sessionRemainingSec)}</span>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowCheatsheet(true)}
            className="h-8 gap-1 text-xs font-bold border-amber-500/30 text-amber-700 dark:text-amber-300 hover:bg-amber-500/10"
            title="Mở Sổ tay Kính ngữ"
          >
            <BookOpen className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Sổ tay ({formatKeyDisplay(keybindings.keigoOpenCheatsheet)})</span>
          </Button>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              stopWebSpeech();
              session.setPhase("idle" as any);
              setShowSummary(false);
            }}
            className="h-8 text-xs font-bold text-muted-foreground hover:text-foreground"
          >
            Thoát (Esc)
          </Button>
        </div>
      </div>

      {/* Main Workout Grid */}
      {session.phase === "loading" || (!activeExercise && !showSummary) ? (
        <ZenLoadingState
          variant="studio"
          title="AI Đang Thiết Lập Thử Thách Kính Ngữ..."
          ja="敬語課題生成中..."
          description="AI đang thiết lập tình huống kinh doanh, đối tượng giao tiếp và ngữ cảnh tôn kính..."
        />
      ) : (
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 items-start">
        {/* Left 2 Columns: Prompt & Result Arena */}
        <div className="lg:col-span-2 space-y-4">
          <KeigoPromptCard
            exercise={activeExercise}
            subtitleMode={subtitleMode}
            onPlayAudio={() => playPromptAudio(false)}
            phase={session.phase}
            hintLevel={session.hintLevel}
            onCycleHint={session.cycleHint}
          />

          {isEvaluating && (
            <ZenLoadingState
              variant="ai"
              title="AI Đang Phân Tích Phản Xạ & Chuẩn Mực Kính Ngữ..."
              ja="敬語分析中..."
              description="Kiểm tra hướng Tôn kính / Khiêm nhường, Uchi-Soto & Nhị trùng kính ngữ..."
            />
          )}

          {session.phase === "result" && session.result && (
            <KeigoResultCard
              result={session.result}
              exercise={activeExercise}
              onNext={() => {
                soundFX.playSuikinkutsu();
                session.startNext();
              }}
              onRetry={() => {
                soundFX.playSuikinkutsu();
                session.retry();
              }}
              onAskCoach={handleCoachSelect}
              onCancelAutoNext={session.cancelAutoNext}
            />
          )}

          {session.phase === "ready" && (
            <div className="p-6 rounded-3xl border-2 border-primary/30 bg-card washi-texture text-center space-y-3 shadow-md">
              <div className="h-10 w-10 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center text-primary mx-auto">
                <Play className="h-5 w-5 fill-current ml-0.5" />
              </div>
              <div className="space-y-1">
                <h4 className="font-bold text-base text-foreground">Bạn đã sẵn sàng trả lời?</h4>
                <p className="text-xs text-muted-foreground">
                  Bấm nút bên dưới hoặc phím <kbd className="px-1.5 py-0.5 rounded bg-muted border text-[11px] font-mono font-bold">{formatKeyDisplay(keybindings.keigoStartVoice)}</kbd> để kích hoạt microphone và bắt đầu nói
                </p>
              </div>
              <Button
                variant="akane"
                size="lg"
                onClick={() => session.startVoiceRecording()}
                className="font-bold gap-2 text-sm shadow-md"
              >
                <Mic className="h-4 w-4" />
                <span>🎙️ Bắt Đầu Trả Lời</span>
              </Button>
            </div>
          )}
        </div>

        {/* Right 1 Column: Timer & Speech Controls */}
        <div className="space-y-4">
          <KeigoTimer
            remainingMs={session.timer.remainingMs}
            timerLimitMs={session.timer.isActive ? timerMs : activeExercise?.timerLimitMs ?? timerMs}
            progress={session.timer.progress}
            state={session.timer.state}
            isActive={session.timer.isActive}
          />

          <div className="p-4 rounded-3xl border border-border/80 bg-card shadow-xs washi-texture space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-foreground flex items-center gap-1.5">
                <Mic className="h-3.5 w-3.5 text-primary" />
                <span>Giọng Nói & Nhập Liệu</span>
              </span>
              <button
                onClick={() => setShowTextInput((v) => !v)}
                className="text-[11px] font-bold text-primary hover:underline flex items-center gap-1"
                title={`Đổi chế độ nhập (${formatKeyDisplay(keybindings.keigoToggleInputMode)})`}
              >
                <Edit3 className="h-3 w-3" />
                <span>{showTextInput ? "Dùng Mic" : "Gõ phím"}</span>
              </button>
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-[11px] text-muted-foreground">
                <span>Âm lượng mic:</span>
                <span className="font-bold font-mono">
                  {session.isUserSpeaking ? "Đang nói..." : `${Math.round(session.recorder.volumeLevel * 100)}%`}
                </span>
              </div>
              <div className="h-2 w-full bg-muted rounded-full overflow-hidden border border-border/60">
                <div
                  className={cn(
                    "h-full transition-all duration-75",
                    session.isUserSpeaking ? "bg-emerald-500" : "bg-primary"
                  )}
                  style={{ width: `${Math.min(100, Math.round(session.recorder.volumeLevel * 100))}%` }}
                />
              </div>
            </div>

            {/* Unified Voice & Keyboard Input Bar */}
            <ZenUnifiedInputBar
              value={transcriptInput}
              onChange={setTranscriptInput}
              onSubmit={handleDirectSubmit}
              speechTranscript={session.speech.transcript}
              isRecording={isRecordingOrWaiting}
              isEvaluating={isEvaluating}
              placeholder="Nói vào mic hoặc gõ câu kính ngữ... (VD: ご覧になります / 参ります)"
              submitButtonText={`Gửi (${formatKeyDisplay(keybindings.keigoSubmitOrNext)})`}
              autoFocus={true}
              hintText="Gõ phím thay mic khi ở văn phòng"
            />

            <div className="pt-1 flex gap-2">
              <Button
                size="sm"
                variant="outline"
                className="w-full font-bold text-xs"
                onClick={() => session.skip()}
                disabled={isEvaluating}
              >
                Bỏ qua câu này ({formatKeyDisplay(keybindings.keigoSkip)})
              </Button>
            </div>
          </div>

          {insights.length > 0 && (
            <CoachInsightCard
              insight={insights[0]}
              onDismiss={() => dismiss(insights[0].id)}
              onAction={(ins) => handleCoachSelect(ins.recommended_action || ins.description)}
            />
          )}
        </div>
      </div>
      )}

      <KeigoCheatsheetModal isOpen={showCheatsheet} onClose={() => setShowCheatsheet(false)} />
      <GlobalKeybindingsModal isOpen={showKeybindingsModal} onClose={() => setShowKeybindingsModal(false)} />

      <CoachPanel open={coachOpen} onClose={() => setCoachOpen(false)} />
    </div>
  );
}
