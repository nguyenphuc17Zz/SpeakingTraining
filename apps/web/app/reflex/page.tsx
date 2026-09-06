"use client";

import React, { useState, useEffect, useMemo, useRef, useCallback } from "react";
import { usePathname } from "next/navigation";
import { GlobalKeybindingsModal } from "@/components/layout/global-keybindings-modal";
import { CoachPanel } from "@/features/coach";
import { useCoachCore } from "@/features/coach/hooks/useCoachCore";
import { useSystemKeybindings } from "@/hooks/use-system-keybindings";
import { speakJapaneseText, stopWebSpeech } from "@/features/speaking/services/web-speech";
import { useReflexSession } from "@/features/reflex/hooks/useReflexSession";
import { useReflexFilters } from "@/features/reflex/hooks/useReflexFilters";
import {
  ReflexLobby,
  PRESSURE_LEVELS,
} from "@/features/reflex/components/ReflexLobby";
import { ReflexArenaView } from "@/features/reflex/components/ReflexArenaView";
import { ReflexFilterModals } from "@/features/reflex/components/ReflexFilterModals";

export default function ReflexPage() {
  const [subMode, setSubMode] = useState("mixed");
  const [pressure, setPressure] = useState<
    "infinite" | "relaxed" | "normal" | "fast" | "reflex" | "extreme"
  >("normal");
  const [subtitleMode, setSubtitleMode] = useState<
    "hidden" | "japanese" | "japanese_reading" | "vietnamese"
  >("japanese");
  const [startTrigger, setStartTrigger] = useState<"manual" | "auto">("manual");
  const [transcriptInput, setTranscriptInput] = useState("");
  const [showSummary, setShowSummary] = useState(false);
  const [duration, setDuration] = useState<0 | 3 | 5 | 10 | 20>(5);
  const [sessionRemainingSec, setSessionRemainingSec] = useState(duration * 60);
  const [sessionElapsedSec, setSessionElapsedSec] = useState(0);
  const [autoNext, setAutoNext] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const [isReflexAdvancedOpen, setIsReflexAdvancedOpen] = useState(false);
  const [coachOpen, setCoachOpen] = useState(false);

  const sessionEndTimestampRef = useRef<number | null>(null);
  const sessionPausedRemainingMsRef = useRef<number>(duration * 60 * 1000);
  const isSettingsLoadedRef = useRef(false);

  // Extracted custom hook for all 6 filter categories
  const filters = useReflexFilters();

  // 1. Load saved lobby preferences from localStorage
  useEffect(() => {
    try {
      const saved = localStorage.getItem("speaking_training_reflex_settings_v1");
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.subMode && typeof parsed.subMode === "string") setSubMode(parsed.subMode);
        if (parsed.pressure && typeof parsed.pressure === "string") setPressure(parsed.pressure);
        if (parsed.duration !== undefined && [0, 3, 5, 10, 20].includes(parsed.duration)) {
          setDuration(parsed.duration);
        }
        if (parsed.subtitleMode && typeof parsed.subtitleMode === "string") {
          setSubtitleMode(parsed.subtitleMode);
        }
        if (parsed.startTrigger && typeof parsed.startTrigger === "string") {
          setStartTrigger(parsed.startTrigger);
        }
        if (parsed.autoNext !== undefined && typeof parsed.autoNext === "boolean") {
          setAutoNext(parsed.autoNext);
        }
      }
    } catch (e) {
      console.warn("[ReflexPage] Failed to load settings:", e);
    } finally {
      isSettingsLoadedRef.current = true;
    }
  }, []);

  // 2. Persist lobby preferences whenever changed
  useEffect(() => {
    if (!isSettingsLoadedRef.current) return;
    try {
      const settings = {
        subMode,
        pressure,
        duration,
        subtitleMode,
        startTrigger,
        autoNext,
      };
      localStorage.setItem("speaking_training_reflex_settings_v1", JSON.stringify(settings));
    } catch (e) {
      console.warn("[ReflexPage] Failed to save settings:", e);
    }
  }, [subMode, pressure, duration, subtitleMode, startTrigger, autoNext]);

  const { matchesAction, keybindings } = useSystemKeybindings();

  // Hook-driven Session Controller
  const session = useReflexSession({
    subMode,
    pressureLevel: pressure as any,
    autoNext,
    startTrigger,
    conjugationTarget: filters.conjugationTarget,
    qnaTopic: filters.qnaTopic,
    transformationCategory: filters.transformationCategory,
    contextCategory: filters.contextCategory,
    vocabCategory: filters.vocabCategory,
    keigoCategory: filters.keigoCategory,
  });

  const sessionRef = useRef(session);
  useEffect(() => {
    sessionRef.current = session;
  });

  // Sync duration selection in lobby
  useEffect(() => {
    if (session.phase === "idle" || session.phase === "summary" || showSummary) {
      setSessionRemainingSec(duration === 0 ? 0 : duration * 60);
      setSessionElapsedSec(0);
      sessionEndTimestampRef.current = null;
      sessionPausedRemainingMsRef.current = duration * 60 * 1000;
    }
  }, [duration, session.phase, showSummary]);

  // Robust session duration countdown / elapsed tracking
  useEffect(() => {
    const isSessionActive = session.phase !== "idle" && session.phase !== "summary" && !showSummary;
    if (!isSessionActive) return;

    if (duration === 0) {
      if (session.isPaused) return;
      const interval = setInterval(() => {
        setSessionElapsedSec((s) => s + 1);
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
        sessionRef.current.setPhase("summary" as any);
      }
    }, 500);

    return () => clearInterval(interval);
  }, [duration, session.phase, session.isPaused, showSummary]);

  const timerMs = PRESSURE_LEVELS.find((p) => p.id === pressure)?.ms ?? 4000;
  const activeExercise = session.exercise;
  const pathname = usePathname();
  const coach = useCoachCore();

  const handleCoachSelect = useCallback((prompt: string) => {
    setCoachOpen(true);
    setTimeout(
      () => coach.ask(prompt, { route: pathname || "/reflex", exerciseId: (activeExercise as any)?.id }),
      300
    );
  }, [activeExercise, coach, pathname]);

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
              sessionRef.current.onPromptAudioFinished();
            }
          },
          onError: () => {
            if (autoTransition) {
              sessionRef.current.onPromptAudioFinished();
            }
          },
        });
      } else if (autoTransition) {
        sessionRef.current.onPromptAudioFinished();
      }
    },
    [activeExercise]
  );

  // Auto-play prompt audio in prompt_playing phase
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
      sessionRef.current.recorder.releaseMicrophone();
      sessionRef.current.speech.stopListening();
    };
  }, []);

  const handleDirectSubmit = useCallback(async () => {
    const text =
      transcriptInput.trim() ||
      session.speech.transcript.trim() ||
      session.speech.interimTranscript.trim();
    if (!text) return;
    setTranscriptInput("");
    await sessionRef.current.submitWithTranscript(text);
  }, [transcriptInput, session.speech.transcript, session.speech.interimTranscript]);

  // Calculate current consecutive correct streak
  const currentStreak = useMemo(() => {
    let streak = 0;
    for (let i = session.results.length - 1; i >= 0; i--) {
      if (session.results[i].success) streak++;
      else break;
    }
    return streak;
  }, [session.results]);

  // Keybindings listener
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName?.toLowerCase();
      if (tag === "textarea" || tag === "input") {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          if (
            session.phase === "waiting_for_speech" ||
            session.phase === "recording" ||
            session.phase === "result"
          ) {
            handleDirectSubmit();
          }
        }
        return;
      }

      // Handle Result Phase Keybindings
      if (session.phase === "result") {
        if (
          matchesAction(e, "reflexSubmitOrNext") ||
          matchesAction(e, "reflexSkip") ||
          matchesAction(e, "drillSubmitOrNext") ||
          matchesAction(e, "drillSkip") ||
          e.code === "Space" ||
          e.key === "Enter" ||
          e.key === "ArrowRight"
        ) {
          e.preventDefault();
          stopWebSpeech();
          session.startNext();
          return;
        }

        if (matchesAction(e, "reflexRetry") || matchesAction(e, "drillRetry")) {
          e.preventDefault();
          stopWebSpeech();
          session.retry();
          return;
        }

        if (matchesAction(e, "reflexReplayModel") || matchesAction(e, "drillReplayAudio")) {
          e.preventDefault();
          const res = session.result;
          const rc = (activeExercise as any)?.extra_metadata?.reflex_config || {};
          const answerText =
            res?.canonicalAnswer ||
            (activeExercise as any)?.canonical ||
            rc.canonical ||
            rc.expected ||
            rc.target ||
            (activeExercise as any)?.target_patterns?.[0] ||
            "";
          if (answerText) {
            stopWebSpeech();
            speakJapaneseText(answerText);
          }
          return;
        }
      }

      if (
        matchesAction(e, "reflexToggleHelp") ||
        matchesAction(e, "drillToggleHelp") ||
        matchesAction(e, "openKeybindingsModal")
      ) {
        e.preventDefault();
        setShowHelp((v) => !v);
        return;
      }

      if (matchesAction(e, "reflexPauseOrResume") || matchesAction(e, "drillPauseOrResume")) {
        e.preventDefault();
        session.togglePause();
        return;
      }

      if (matchesAction(e, "reflexListenPrompt") || matchesAction(e, "drillReplayAudio")) {
        e.preventDefault();
        playPromptAudio(false);
        return;
      }

      if (matchesAction(e, "reflexStartVoice") || matchesAction(e, "drillStartQuestion")) {
        e.preventDefault();
        stopWebSpeech();
        session.startQuestionNow();
        return;
      }

      if (matchesAction(e, "reflexSubmitOrNext") || matchesAction(e, "drillSubmitOrNext")) {
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
  }, [session.phase, transcriptInput, matchesAction, handleDirectSubmit, playPromptAudio, activeExercise, session]);

  return (
    <>
      {session.phase === "idle" && !showSummary ? (
        <ReflexLobby
          subMode={subMode}
          setSubMode={setSubMode}
          pressure={pressure}
          setPressure={setPressure}
          duration={duration}
          setDuration={setDuration}
          subtitleMode={subtitleMode}
          setSubtitleMode={setSubtitleMode}
          startTrigger={startTrigger}
          setStartTrigger={setStartTrigger}
          autoNext={autoNext}
          setAutoNext={setAutoNext}
          isReflexAdvancedOpen={isReflexAdvancedOpen}
          setIsReflexAdvancedOpen={setIsReflexAdvancedOpen}
          filters={filters}
          keybindings={keybindings}
          timerMs={timerMs}
          onStartSession={() => session.startSession()}
          onOpenHelp={() => setShowHelp(true)}
          onCoachSelect={handleCoachSelect}
        />
      ) : (
        <ReflexArenaView
          session={session}
          subMode={subMode}
          pressure={pressure}
          setPressure={setPressure}
          timerMs={timerMs}
          duration={duration}
          sessionRemainingSec={sessionRemainingSec}
          sessionElapsedSec={sessionElapsedSec}
          subtitleMode={subtitleMode}
          setSubtitleMode={setSubtitleMode}
          currentStreak={currentStreak}
          startTrigger={startTrigger}
          setStartTrigger={setStartTrigger}
          autoNext={autoNext}
          setAutoNext={setAutoNext}
          filters={filters}
          keybindings={keybindings}
          showSummary={showSummary}
          setShowSummary={setShowSummary}
          transcriptInput={transcriptInput}
          setTranscriptInput={setTranscriptInput}
          handleDirectSubmit={handleDirectSubmit}
          playPromptAudio={playPromptAudio}
          onOpenHelp={() => setShowHelp(true)}
        />
      )}

      {/* Global Filter Modals (Rendered Once) */}
      <ReflexFilterModals filters={filters} />

      {/* Global Keybindings Modal */}
      <GlobalKeybindingsModal isOpen={showHelp} onClose={() => setShowHelp(false)} />

      {/* Floating AI Coach Panel & Trigger */}
      <CoachPanel
        open={coachOpen}
        onClose={() => setCoachOpen(false)}
        route={pathname || "/reflex"}
        exerciseId={(activeExercise as any)?.id}
      />
      <button
        onClick={() => setCoachOpen(true)}
        className="fixed bottom-20 right-4 z-30 md:bottom-5 px-3 py-2 rounded-2xl bg-card border border-border shadow-xl text-xs font-bold flex items-center gap-1.5 hover:border-primary/40 transition-all cursor-pointer"
      >
        <span className="h-5 w-5 rounded-lg bg-primary text-primary-foreground flex items-center justify-center font-bold text-xs">
          🤖
        </span>
        <span>AI Coach</span>
      </button>
    </>
  );
}
