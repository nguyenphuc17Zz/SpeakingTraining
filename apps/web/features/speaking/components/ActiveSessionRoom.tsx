"use client";

import React, { useEffect, useState } from "react";
import { Persona } from "@/types/persona";
import {
  ConversationAnalysisSummary,
  ConversationTurn,
  CorrectionItem,
  RecordingState,
  TurnAnalysis,
  VoiceSession,
} from "../types";
import { getStatusColor } from "../state/session-state-machine";
import { AudioVisualizer } from "./AudioVisualizer";
import { ConversationTranscript } from "./ConversationTranscript";
import { CoachingFeedbackCard } from "./CoachingFeedbackCard";
import { ConversationReviewPanel } from "./ConversationReviewPanel";
import { CorrectionDetailModal } from "./CorrectionDetailModal";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Mic,
  MicOff,
  Pause,
  Play,
  Square,
  Send,
  Clock,
  Volume2,
  VolumeX,
  Sparkles,
  Zap,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";
import { analysisApi } from "../services/analysis-api";
import { useSystemKeybindings } from "@/hooks/use-system-keybindings";

interface ActiveSessionRoomProps {
  session: VoiceSession;
  persona: Persona;
  turns: ConversationTurn[];
  state: RecordingState;
  volumeLevel: number;
  isUserSpeaking: boolean;
  formattedElapsed: string;
  formattedSpeaking: string;
  isVoiceMuted?: boolean;
  onToggleVoiceMute?: () => void;
  autoEndOfSpeech?: boolean;
  onToggleAutoEndOfSpeech?: () => void;
  latestUserTranscript?: string | null;
  interimTranscript?: string;
  latestSttMetrics?: {
    model?: string;
    latency_ms?: number;
  } | null;
  isManualRecording?: boolean;
  manualSeconds?: number;
  onStartManualRecording?: () => void;
  onStopManualRecording?: () => void;
  hasPermission?: boolean | null;
  onRequestPermission?: () => Promise<boolean>;
  onSendTextTurn: (text: string) => void;
  onPause: () => void;
  onResume: () => void;
  onEndSession: () => void;
  onReplayVoice: (text: string) => void;
}

export function ActiveSessionRoom({
  session,
  persona,
  turns,
  state,
  volumeLevel,
  isUserSpeaking,
  formattedElapsed,
  formattedSpeaking,
  isVoiceMuted = false,
  onToggleVoiceMute,
  autoEndOfSpeech = true,
  onToggleAutoEndOfSpeech,
  latestUserTranscript,
  interimTranscript = "",
  latestSttMetrics,
  isManualRecording = false,
  manualSeconds = 0,
  onStartManualRecording,
  onStopManualRecording,
  hasPermission,
  onRequestPermission,
  onSendTextTurn,
  onPause,
  onResume,
  onEndSession,
  onReplayVoice,
}: ActiveSessionRoomProps) {
  const [inputText, setInputText] = useState("");
  const [analysisSummary, setAnalysisSummary] =
    useState<ConversationAnalysisSummary | null>(null);
  const [isReviewOpen, setIsReviewOpen] = useState(false);
  const [selectedCorrection, setSelectedCorrection] =
    useState<CorrectionItem | null>(null);

  const statusInfo = getStatusColor(state);

  // Poll analysis data in the background
  useEffect(() => {
    if (!session?.id) return;

    let isMounted = true;
    const fetchAnalysis = async () => {
      try {
        const data = await analysisApi.getSessionAnalysisSummary(session.id);
        if (isMounted) {
          setAnalysisSummary(data);
        }
      } catch (e) {
        // Silently catch background poll errors
      }
    };

    fetchAnalysis();
    const interval = setInterval(fetchAnalysis, 3500);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [session?.id, turns.length]);

  const handleSendText = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;
    onSendTextTurn(inputText);
    setInputText("");
  };

  // Map turn ID to TurnAnalysis
  const analysesMap: Record<string, TurnAnalysis> = {};
  if (analysisSummary?.turn_analyses) {
    for (const ta of analysisSummary.turn_analyses) {
      analysesMap[ta.turn_id] = ta;
    }
  }

  const { matchesAction, keybindings } = useSystemKeybindings();

  // Dynamic Keyboard Shortcuts for Speaking Room
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const activeElement = document.activeElement;
      const isInputActive =
        activeElement &&
        (activeElement.tagName === "INPUT" ||
          activeElement.tagName === "TEXTAREA" ||
          activeElement.getAttribute("contenteditable") === "true");

      if (isInputActive) return;

      // 1. Mic Speak / Push-to-Talk
      if (matchesAction(e, "speakingMic")) {
        e.preventDefault();
        if (state === "listening" || isManualRecording || isUserSpeaking) {
          if (!autoEndOfSpeech) {
            if (isManualRecording) {
              onStopManualRecording?.();
            } else {
              onStartManualRecording?.();
            }
          } else {
            if (isUserSpeaking || isManualRecording) {
              onStopManualRecording?.();
            } else {
              onStartManualRecording?.();
            }
          }
        }
        return;
      }

      // 2. Replay last AI turn audio
      if (matchesAction(e, "speakingReplay")) {
        e.preventDefault();
        const aiTurns = turns.filter((t) => t.speaker === "assistant");
        const lastAiTurn = aiTurns[aiTurns.length - 1];
        if (lastAiTurn?.transcript) {
          onReplayVoice(lastAiTurn.transcript);
        }
        return;
      }

      // 3. Toggle Mute
      if (matchesAction(e, "speakingMute")) {
        e.preventDefault();
        onToggleVoiceMute?.();
        return;
      }

      // 4. Toggle Speaking Mode (Hands-free / Push-to-Talk)
      if (matchesAction(e, "speakingModeToggle")) {
        e.preventDefault();
        onToggleAutoEndOfSpeech?.();
        return;
      }

      // Escape: Pause / Resume
      if (e.key === "Escape") {
        e.preventDefault();
        if (state === "paused") {
          onResume();
        } else if (state === "listening" || state === "ai_speaking") {
          onPause();
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [
    matchesAction,
    autoEndOfSpeech,
    isManualRecording,
    isUserSpeaking,
    onPause,
    onResume,
    onStartManualRecording,
    onStopManualRecording,
    onToggleAutoEndOfSpeech,
    onToggleVoiceMute,
    onReplayVoice,
    turns,
    state,
  ]);

  // Find latest coaching tip for coaching mode
  const userTurns = turns.filter((t) => t.speaker === "user");
  const lastUserTurn = userTurns[userTurns.length - 1];
  const lastAnalysis = lastUserTurn ? analysesMap[lastUserTurn.id] : null;
  const latestCorrection =
    lastAnalysis && lastAnalysis.corrections.length > 0
      ? lastAnalysis.corrections[0]
      : null;

  const totalCorrectionsCount =
    analysisSummary?.turn_analyses?.reduce(
      (acc, ta) => acc + ta.corrections.length,
      0
    ) || 0;

  return (
    <div className="space-y-4 max-w-4xl mx-auto animate-in fade-in duration-300">
      {/* Session Top Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-2xl bg-card/80 border border-border shadow-md">
        {/* Left: Persona & Mode Info */}
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-primary to-aizome-600 flex items-center justify-center text-primary-foreground font-extrabold text-sm shadow-md shadow-primary/10">
            {persona.name.charAt(0)}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold text-foreground">{persona.name}</h2>
              <Badge variant="jlpt" size="sm">
                {persona.difficulty}
              </Badge>
              <Badge variant="outline" size="sm" className="capitalize text-[10px]">
                {session.mode} Mode
              </Badge>
            </div>
            <p className="text-[11px] text-primary">
              {persona.role} • {persona.speaking_style}
            </p>
          </div>
        </div>

        {/* Right: Timer & Turn Stats & Intelligence Drawer Trigger */}
        <div className="flex items-center gap-3 text-xs font-mono text-muted-foreground self-end sm:self-center">
          <div className="flex items-center gap-1.5 bg-background px-3 py-1.5 rounded-xl border border-border">
            <Clock className="h-3.5 w-3.5 text-muted-foreground" />
            <span className="text-foreground font-bold">{formattedElapsed}</span>
          </div>

          <div className="flex items-center gap-1.5 bg-background px-3 py-1.5 rounded-xl border border-border text-[11px]">
            <span className="text-muted-foreground">Speaking:</span>
            <span className="text-emerald-400 font-bold">{formattedSpeaking}</span>
          </div>

          {/* Voice Mute / Audio Toggle Button */}
          {onToggleVoiceMute && (
            <Button
              variant="outline"
              size="sm"
              onClick={onToggleVoiceMute}
              className={`text-xs gap-1.5 ${
                isVoiceMuted
                  ? "border-amber-500/40 text-amber-400 bg-amber-500/10 hover:bg-amber-500/20"
                  : "border-border text-foreground hover:bg-muted"
              }`}
              title={isVoiceMuted ? "Bật âm thanh đối tác" : "Tắt tiếng đối tác (Tiết kiệm RAM / Nhẹ máy)"}
            >
              {isVoiceMuted ? (
                <>
                  <VolumeX className="h-3.5 w-3.5 text-amber-400" />
                  <span>Tắt tiếng</span>
                </>
              ) : (
                <>
                  <Volume2 className="h-3.5 w-3.5 text-primary" />
                  <span>Bật tiếng</span>
                </>
              )}
            </Button>
          )}

          {/* Live Intelligence Button */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsReviewOpen(true)}
            className={`text-xs gap-1.5 ${
              totalCorrectionsCount > 0
                ? "border-kintsugi-500/40 text-kintsugi-400 bg-kintsugi-500/5 hover:bg-kintsugi-500/15"
                : "border-border text-foreground hover:bg-muted"
            }`}
          >
            <Sparkles className="h-3.5 w-3.5 text-primary" />
            <span>Analysis ({totalCorrectionsCount})</span>
          </Button>
        </div>
      </div>

      {/* Main Room Card */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Left Column: Visualizer & Live Speaking Control Panel */}
        <div className="lg:col-span-5 flex flex-col justify-between p-5 rounded-2xl bg-gradient-to-b from-slate-900/90 to-slate-950 border border-border shadow-lg space-y-4">
          {/* Status Indicator Banner */}
          <div className="flex items-center justify-between pb-2 border-b border-border/80">
            <div
              className={`flex items-center gap-2 px-3 py-1 rounded-full border text-xs font-semibold ${statusInfo.badgeBg} ${statusInfo.badgeText}`}
            >
              <div className={`h-2 w-2 rounded-full ${statusInfo.dotColor}`} />
              <span>{statusInfo.label}</span>
            </div>

            {session.mode === "coaching" && (
              <span className="text-[10px] text-primary font-bold bg-primary/10 px-2 py-0.5 rounded-md border border-primary/20">
                ⚡ Realtime Coach
              </span>
            )}
          </div>

          {/* Central Pulsing Audio Orb */}
          <div className="py-1 flex flex-col items-center justify-center space-y-3">
            <AudioVisualizer
              state={state}
              volumeLevel={volumeLevel}
              isUserSpeaking={isUserSpeaking || isManualRecording}
            />

            {/* Permission Denied Warning Banner */}
            {hasPermission === false && onRequestPermission && (
              <div className="w-full p-2.5 rounded-xl bg-destructive/15 border border-destructive/40 text-destructive flex items-center justify-between gap-2 text-xs animate-bounce">
                <div className="flex items-center gap-1.5">
                  <AlertCircle className="h-4 w-4 shrink-0" />
                  <span>Chưa cấp quyền Micro</span>
                </div>
                <Button
                  size="sm"
                  variant="danger"
                  onClick={() => onRequestPermission()}
                  className="text-[11px] h-7 px-2"
                >
                  Bật Micro
                </Button>
              </div>
            )}

            {/* Speaking Mode Selector Tabs */}
            {onToggleAutoEndOfSpeech && (
              <div className="w-full flex items-center p-1 rounded-xl bg-card/70 border border-border text-xs">
                <button
                  type="button"
                  onClick={() => {
                    if (!autoEndOfSpeech) onToggleAutoEndOfSpeech();
                  }}
                  className={`flex-1 py-1.5 px-2 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition-all ${
                    autoEndOfSpeech
                      ? "bg-primary text-primary-foreground shadow-sm"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                  title="Phím tắt: T"
                >
                  <span>🗣️ Tự động (VAD)</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    if (autoEndOfSpeech) onToggleAutoEndOfSpeech();
                  }}
                  className={`flex-1 py-1.5 px-2 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition-all ${
                    !autoEndOfSpeech
                      ? "bg-primary text-primary-foreground shadow-sm"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                  title="Phím tắt: T"
                >
                  <span>🔴 Bấm nút để nói</span>
                  <span className="text-[9px] px-1 py-0.2 rounded bg-black/20 font-mono opacity-80">T</span>
                </button>
              </div>
            )}

            {/* Interactive Speaking Controller */}
            <div className="w-full space-y-2">
              {!autoEndOfSpeech ? (
                /* Mode 2: Manual Click-to-Talk */
                !isManualRecording ? (
                  <button
                    type="button"
                    onClick={onStartManualRecording}
                    disabled={state !== "listening"}
                    className="w-full py-3.5 px-4 rounded-xl bg-gradient-to-r from-primary via-primary/95 to-aizome-600 hover:from-primary/90 hover:to-aizome-700 text-primary-foreground font-bold shadow-lg shadow-primary/20 flex items-center justify-between gap-3 transition-all transform active:scale-98 cursor-pointer disabled:opacity-40"
                  >
                    <div className="flex items-center gap-2.5">
                      <div className="h-7 w-7 rounded-full bg-white/20 flex items-center justify-center">
                        <Mic className="h-4 w-4 text-white" />
                      </div>
                      <div className="text-left">
                        <div className="text-xs font-extrabold tracking-wide flex items-center gap-1.5">
                          <span>🎙️ BẤM VÀO ĐÂY ĐỂ NÓI</span>
                        </div>
                        <div className="text-[10px] text-white/80 font-normal">
                          Nói tiếng Nhật xong bấm lại để gửi
                        </div>
                      </div>
                    </div>
                    <span className="px-2 py-1 rounded-md bg-white/20 font-mono text-[10px] font-black tracking-wider uppercase border border-white/25">
                      Space
                    </span>
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={onStopManualRecording}
                    className="w-full py-3.5 px-4 rounded-xl bg-destructive hover:bg-destructive/90 text-destructive-foreground font-bold shadow-xl shadow-destructive/30 flex items-center justify-between gap-3 animate-pulse transition-all transform active:scale-98 cursor-pointer"
                  >
                    <div className="flex items-center gap-2.5">
                      <div className="h-7 w-7 rounded-full bg-white/25 flex items-center justify-center">
                        <Square className="h-3.5 w-3.5 fill-white text-white" />
                      </div>
                      <div className="text-left">
                        <div className="text-xs font-extrabold tracking-wide flex items-center gap-1.5">
                          <span>🛑 ĐANG THU ÂM... BẤM ĐỂ GỬI</span>
                        </div>
                        <div className="text-[10px] text-white/80 font-normal">
                          Dừng và chuyển giọng nói thành tiếng Nhật
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="px-1.5 py-0.5 rounded bg-black/40 font-mono text-[10px] font-black border border-white/20">
                        Space
                      </span>
                      <span className="font-mono text-xs font-black bg-black/40 px-2 py-1 rounded-md">
                        {Math.floor(manualSeconds / 60)}:
                        {(manualSeconds % 60).toString().padStart(2, "0")}
                      </span>
                    </div>
                  </button>
                )
              ) : (
                /* Mode 1: Auto VAD */
                <div
                  className={`w-full p-3 rounded-xl border flex items-center justify-between transition-all ${
                    isUserSpeaking
                      ? "bg-emerald-500/15 border-emerald-500/40 text-emerald-400 shadow-sm"
                      : state === "listening"
                      ? "bg-card/70 border-border text-foreground"
                      : "bg-card/40 border-border/50 text-muted-foreground"
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <div
                      className={`h-7 w-7 rounded-full flex items-center justify-center ${
                        isUserSpeaking
                          ? "bg-emerald-500/25 text-emerald-400"
                          : "bg-primary/10 text-primary"
                      }`}
                    >
                      <Mic className="h-3.5 w-3.5" />
                    </div>
                    <div>
                      <div className="text-xs font-bold">
                        {isUserSpeaking
                          ? "🎙️ Đang nghe giọng bạn nói..."
                          : state === "listening"
                          ? "🟢 Micro đang sẵn sàng lắng nghe"
                          : "Micro đang chờ..."}
                      </div>
                      <div className="text-[10px] text-muted-foreground">
                        {isUserSpeaking
                          ? "Dứt câu hệ thống sẽ tự động gửi đi"
                          : "Hãy nói tiếng Nhật tự nhiên vào micro"}
                      </div>
                    </div>
                  </div>
                  <span
                    className={`h-2.5 w-2.5 rounded-full ${
                      isUserSpeaking
                        ? "bg-emerald-400 animate-ping"
                        : state === "listening"
                        ? "bg-emerald-400"
                        : "bg-muted-foreground"
                    }`}
                  />
                </div>
              )}

              {/* Live Volume Meter Bar */}
              <div className="flex items-center justify-between px-3 py-1.5 bg-card/40 rounded-xl border border-border/60 text-[10px]">
                <span className="text-muted-foreground font-medium flex items-center gap-1">
                  <span>Âm lượng Mic:</span>
                </span>
                <div className="flex items-center gap-0.5">
                  {Array.from({ length: 14 }).map((_, i) => {
                    const isActive = volumeLevel * 14 > i;
                    return (
                      <div
                        key={i}
                        className={`h-2.5 w-1.5 rounded-xs transition-all duration-75 ${
                          isActive
                            ? i > 10
                              ? "bg-destructive"
                              : i > 7
                              ? "bg-amber-400"
                              : "bg-emerald-400"
                            : "bg-muted/40"
                        }`}
                      />
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Faster-Whisper Live Output Card */}
            {(latestUserTranscript || state === "processing_stt" || isUserSpeaking) && (
              <div className="w-full p-3 rounded-xl bg-card/90 border border-border shadow-sm space-y-1.5 animate-in fade-in duration-200 text-left">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-bold text-foreground flex items-center gap-1.5">
                    <Mic className="h-3.5 w-3.5 text-emerald-400" />
                    <span>Faster-Whisper Output (Lời bạn vừa nói)</span>
                  </span>
                  <div className="flex items-center gap-1 font-mono text-[10px]">
                    <span className="px-1.5 py-0.2 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      {latestSttMetrics?.model || session.stt_model_preference || "base"}
                    </span>
                    {latestSttMetrics?.latency_ms && (
                      <span className="text-muted-foreground">{latestSttMetrics.latency_ms}ms</span>
                    )}
                  </div>
                </div>

                {state === "processing_stt" ? (
                  <div className="flex items-center gap-2 text-xs text-amber-400 py-1 font-medium">
                    <span className="h-2 w-2 rounded-full bg-amber-400 animate-ping" />
                    <span>⚡ Faster-Whisper đang chuyển giọng nói thành tiếng Nhật...</span>
                  </div>
                ) : isUserSpeaking ? (
                  interimTranscript ? (
                    <div className="space-y-1">
                      <div className="flex items-center gap-1.5 text-[11px] text-emerald-400 font-medium">
                        <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                        <span>🎙️ Đang nghe giọng bạn (Live Preview):</span>
                      </div>
                      <p className="text-xs font-jp text-foreground bg-emerald-500/10 border border-emerald-500/25 p-2 rounded-lg leading-relaxed animate-pulse">
                        {interimTranscript}
                      </p>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 text-xs text-emerald-400 py-1 font-medium">
                      <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                      <span>🎙️ Đang nghe... Hãy nói tiếng Nhật tự nhiên</span>
                    </div>
                  )
                ) : (
                  <p className="text-xs font-jp text-foreground bg-muted/50 p-2 rounded-lg border border-border/60 leading-relaxed">
                    {latestUserTranscript}
                  </p>
                )}
              </div>
            )}
          </div>

          {/* Coaching Mode Live Tip Card */}
          {session.mode === "coaching" && latestCorrection && (
            <CoachingFeedbackCard
              correction={latestCorrection}
              onViewDetails={(c) => setSelectedCorrection(c)}
              onPlayCorrection={onReplayVoice}
            />
          )}

          {/* Footer Controls Bar */}
          <div className="flex items-center justify-between gap-2 pt-3 border-t border-border/80">
            {state === "paused" ? (
              <Button
                variant="primary"
                size="sm"
                onClick={onResume}
                className="gap-1 shadow-sm"
              >
                <Play className="h-3.5 w-3.5 mr-1 fill-current" />
                Resume (再開)
              </Button>
            ) : (
              <Button
                variant="outline"
                size="sm"
                onClick={onPause}
                disabled={state === "ai_thinking" || state === "processing_stt"}
              >
                <Pause className="h-3.5 w-3.5 mr-1" />
                Pause (一時停止)
              </Button>
            )}

            <Button
              variant="outline"
              size="sm"
              onClick={onEndSession}
              className="text-destructive hover:text-destructive/90 hover:border-destructive/50"
            >
              <Square className="h-3.5 w-3.5 mr-1 text-destructive" />
              End Session (終了)
            </Button>
          </div>
        </div>

        {/* Right Column: Live Transcript Stream & Fallback Text Input */}
        <div className="lg:col-span-7 flex flex-col justify-between rounded-2xl bg-background/80 border border-border shadow-lg overflow-hidden min-h-[460px]">
          {/* Transcript Area */}
          <div className="flex-1 overflow-hidden flex flex-col">
            <div className="p-3 border-b border-border bg-card/60 flex items-center justify-between text-xs font-semibold text-foreground">
              <span>Live Dialogue (会話履歴)</span>
              <span className="text-[11px] font-normal text-muted-foreground">
                {turns.length} turns recorded
              </span>
            </div>

            <ConversationTranscript
              turns={turns}
              personaName={persona.name}
              analysesMap={analysesMap}
              state={state}
              isUserSpeaking={isUserSpeaking || isManualRecording}
              interimTranscript={interimTranscript}
              sttModel={session.stt_model_preference || "base"}
              onSelectCorrection={(c) => setSelectedCorrection(c)}
              onReplayVoice={onReplayVoice}
            />
          </div>

          {/* Text Input Fallback Bar */}
          <form
            onSubmit={handleSendText}
            className="p-3 border-t border-border bg-card/40 flex items-center gap-2"
          >
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Or type Japanese here... (例: 今日は天気がいいですね)"
              disabled={state === "ai_thinking" || state === "processing_stt"}
              className="flex-1 px-3 py-2 rounded-xl bg-background border border-border text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary transition-colors"
            />
            <Button
              type="submit"
              variant="primary"
              size="sm"
              disabled={
                !inputText.trim() ||
                state === "ai_thinking" ||
                state === "processing_stt"
              }
            >
              <Send className="h-3.5 w-3.5" />
            </Button>
          </form>
        </div>
      </div>

      {/* Review Drawer Panel */}
      <ConversationReviewPanel
        isOpen={isReviewOpen}
        summary={analysisSummary}
        onClose={() => setIsReviewOpen(false)}
        onSelectCorrection={(c) => setSelectedCorrection(c)}
        onPlayCorrection={onReplayVoice}
      />

      {/* Selected Correction Detail Modal */}
      <CorrectionDetailModal
        isOpen={selectedCorrection !== null}
        correction={selectedCorrection}
        onClose={() => setSelectedCorrection(null)}
        onPlayCorrection={onReplayVoice}
      />
    </div>
  );
}
