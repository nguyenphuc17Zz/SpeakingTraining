"use client";

import React from "react";
import {
  Clock,
  HelpCircle,
  Flame,
  Zap,
  Volume2,
  Sparkles,
  Activity,
  Mic,
  Play,
  Sliders,
  MessageSquare,
  Repeat,
  Compass,
  BookText,
  Crown,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ZenLoadingState } from "@/components/ui/zen-loading-state";
import { ZenUnifiedInputBar } from "@/components/ui/zen-unified-input-bar";
import { ReflexTimer } from "./ReflexTimer";
import { ReflexPromptCard } from "./ReflexPromptCard";
import { ReflexResultCard } from "./ReflexResultCard";
import { ReflexSessionSummary } from "./ReflexSessionSummary";
import { DEDICATED_MODES } from "./ReflexLobby";
import { useReflexFilters } from "../hooks/useReflexFilters";
import { useReflexSession } from "../hooks/useReflexSession";
import { formatKeyDisplay } from "@/hooks/use-system-keybindings";
import { stopWebSpeech } from "@/features/speaking/services/web-speech";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

export interface ReflexArenaViewProps {
  session: ReturnType<typeof useReflexSession>;
  subMode: string;
  pressure: "infinite" | "relaxed" | "normal" | "fast" | "reflex" | "extreme";
  setPressure: (p: "infinite" | "relaxed" | "normal" | "fast" | "reflex" | "extreme") => void;
  timerMs: number;
  duration: 0 | 3 | 5 | 10 | 20;
  sessionRemainingSec: number;
  sessionElapsedSec: number;
  subtitleMode: "hidden" | "japanese" | "japanese_reading" | "vietnamese";
  setSubtitleMode: (m: "hidden" | "japanese" | "japanese_reading" | "vietnamese") => void;
  currentStreak: number;
  startTrigger: "manual" | "auto";
  setStartTrigger: React.Dispatch<React.SetStateAction<"manual" | "auto">>;
  autoNext: boolean;
  setAutoNext: React.Dispatch<React.SetStateAction<boolean>>;
  filters: ReturnType<typeof useReflexFilters>;
  keybindings: any;
  showSummary: boolean;
  setShowSummary: (s: boolean) => void;
  transcriptInput: string;
  setTranscriptInput: (t: string) => void;
  handleDirectSubmit: () => Promise<void>;
  playPromptAudio: (autoTransition?: boolean) => void;
  onOpenHelp: () => void;
}

export function ReflexArenaView({
  session,
  subMode,
  pressure,
  setPressure,
  timerMs,
  duration,
  sessionRemainingSec,
  sessionElapsedSec,
  subtitleMode,
  setSubtitleMode,
  currentStreak,
  startTrigger,
  setStartTrigger,
  autoNext,
  setAutoNext,
  filters,
  keybindings,
  showSummary,
  setShowSummary,
  transcriptInput,
  setTranscriptInput,
  handleDirectSubmit,
  playPromptAudio,
  onOpenHelp,
}: ReflexArenaViewProps) {
  const activeExercise = session.exercise;
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
          {/* Live Session Countdown Clock / Elapsed Clock */}
          <div
            className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-primary/10 border border-primary/25 text-primary text-xs font-mono font-bold shadow-2xs"
            title={duration === 0 ? "Chế độ luyện tập không giới hạn thời gian (Endless)" : `Thời lượng phiên: ${duration} phút`}
          >
            <Clock className="h-3.5 w-3.5" />
            <span>
              {duration === 0 ? (
                `Phiên: ${Math.floor(sessionElapsedSec / 60).toString().padStart(2, "0")}:${(sessionElapsedSec % 60).toString().padStart(2, "0")} / ∞`
              ) : (
                `Phiên: ${Math.floor(sessionRemainingSec / 60).toString().padStart(2, "0")}:${(sessionRemainingSec % 60).toString().padStart(2, "0")} / ${duration}m`
              )}
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

          {/* HUD Conjugation Form Filter */}
          {(subMode === "reflex_conjugation" || (activeExercise as any)?.exercise_type === "reflex_conjugation") && (
            <button
              type="button"
              onClick={() => {
                soundFX.playFurin();
                filters.setShowFormFilterModal(true);
              }}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-xl text-[11px] font-bold border border-rose-500/30 bg-rose-500/10 text-rose-700 dark:text-rose-300 hover:bg-rose-500/20 transition-all cursor-pointer shadow-2xs"
              title="Bấm để đổi bộ lọc thể chia động từ mục tiêu"
            >
              <Sliders className="h-3 w-3 text-rose-500" />
              <span>{filters.selectedForms.length === 0 ? "50 Thể" : `${filters.selectedForms.length} Thể`}</span>
            </button>
          )}

          {/* HUD Q&A Topic Filter */}
          {(subMode === "reflex_qna" || (activeExercise as any)?.exercise_type === "reflex_qna") && (
            <button
              type="button"
              onClick={() => {
                soundFX.playFurin();
                filters.setShowQnaTopicFilterModal(true);
              }}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-xl text-[11px] font-bold border border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-500/20 transition-all cursor-pointer shadow-2xs"
              title="Bấm để đổi chủ đề câu hỏi Speed Q&A"
            >
              <MessageSquare className="h-3 w-3 text-emerald-500" />
              <span>
                {filters.customKeywords.trim()
                  ? `💡 "${filters.customKeywords.trim()}"`
                  : filters.selectedQnaTopics.length === 0
                  ? "Ngẫu nhiên vô tận"
                  : `${filters.selectedQnaTopics.length} Chủ đề`}
              </span>
            </button>
          )}

          {/* HUD Transformation Category Filter */}
          {(subMode === "reflex_transformation" || (activeExercise as any)?.exercise_type === "reflex_transformation") && (
            <button
              type="button"
              onClick={() => {
                soundFX.playFurin();
                filters.setShowTransformFilterModal(true);
              }}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-xl text-[11px] font-bold border border-indigo-500/30 bg-indigo-500/10 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-500/20 transition-all cursor-pointer shadow-2xs"
              title="Bấm để đổi nhóm cấu trúc biến đổi câu mục tiêu"
            >
              <Repeat className="h-3 w-3 text-indigo-500" />
              <span>
                {filters.selectedTransformCategories.length === 0
                  ? "Ngẫu nhiên 75+ dạng"
                  : `${filters.selectedTransformCategories.length} Nhóm ngữ pháp`}
              </span>
            </button>
          )}

          {/* HUD Context Category Filter */}
          {(subMode === "reflex_context" || (activeExercise as any)?.exercise_type === "reflex_context") && (
            <button
              type="button"
              onClick={() => {
                soundFX.playFurin();
                filters.setShowContextFilterModal(true);
              }}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-xl text-[11px] font-bold border border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-300 hover:bg-amber-500/20 transition-all cursor-pointer shadow-2xs"
              title="Bấm để đổi nhóm bối cảnh giao tiếp mục tiêu"
            >
              <Compass className="h-3 w-3 text-amber-500" />
              <span>
                {filters.selectedContextCategories.length === 0
                  ? "Ngẫu nhiên 60+ tình huống"
                  : `${filters.selectedContextCategories.length} Nhóm bối cảnh`}
              </span>
            </button>
          )}

          {/* HUD Vocabulary Category Filter */}
          {(subMode === "reflex_vocabulary" || (activeExercise as any)?.exercise_type === "reflex_vocabulary") && (
            <button
              type="button"
              onClick={() => {
                soundFX.playFurin();
                filters.setShowVocabFilterModal(true);
              }}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-xl text-[11px] font-bold border border-violet-500/30 bg-violet-500/10 text-violet-700 dark:text-violet-300 hover:bg-violet-500/20 transition-all cursor-pointer shadow-2xs"
              title="Bấm để đổi nhóm từ vựng mục tiêu"
            >
              <BookText className="h-3 w-3 text-violet-500" />
              <span>
                {filters.customVocabKeywords.trim()
                  ? `Từ khóa: "${filters.customVocabKeywords.trim()}"`
                  : filters.selectedVocabCategories.length === 0
                  ? "Ngẫu nhiên 500+ từ"
                  : `${filters.selectedVocabCategories.length} Nhóm từ`}
              </span>
            </button>
          )}

          {/* HUD Keigo Category Filter */}
          {(subMode === "reflex_keigo_vocab" || (activeExercise as any)?.exercise_type === "reflex_keigo_vocab") && (
            <button
              type="button"
              onClick={() => {
                soundFX.playFurin();
                filters.setShowKeigoFilterModal(true);
              }}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-xl text-[11px] font-bold border border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-300 hover:bg-amber-500/20 transition-all cursor-pointer shadow-2xs"
              title="Bấm để đổi chuyên đề kính ngữ mục tiêu"
            >
              <Crown className="h-3 w-3 text-amber-500" />
              <span>
                {filters.customKeigoKeywords.trim()
                  ? `Kính ngữ: "${filters.customKeigoKeywords.trim()}"`
                  : filters.selectedKeigoCategories.length === 0
                  ? "Ngẫu nhiên 80+ cặp"
                  : `${filters.selectedKeigoCategories.length} Nhóm kính ngữ`}
              </span>
            </button>
          )}
        </div>

        <div className="flex items-center gap-1.5">
          <Button
            variant="ghost"
            size="sm"
            className="h-8 px-2 text-xs rounded-xl"
            onClick={onOpenHelp}
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
        ) : session.phase === "loading" || (!activeExercise && !isResult) ? (
          <div className="py-6 animate-in fade-in duration-150">
            <ZenLoadingState
              variant="studio"
              title="AI Đang Chuẩn Bị Câu Hỏi Phản Xạ..."
              ja="瞬発設問生成中..."
              description="AI đang tinh chỉnh câu hỏi ngữ pháp, từ vựng và bối cảnh phù hợp với tốc độ phản xạ của bạn..."
            />
          </div>
        ) : isResult && session.result ? (
          /* Result Card Stage */
          <div className="animate-in fade-in zoom-in-95 duration-200">
            <ReflexResultCard
              key={`${session.result.exerciseId || (activeExercise as any)?.id || "res"}_${session.stats.total}`}
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
                      Bấm phím <kbd className="px-1.5 py-0.5 rounded bg-muted border font-bold text-foreground">{formatKeyDisplay(keybindings.reflexStartVoice || keybindings.drillStartQuestion)}</kbd> hoặc click nút bên dưới để bật mic & tính giờ
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
                  <ZenLoadingState
                    variant="inline"
                    title="Đang phân tích phản xạ 7 chiều & chấm điểm..."
                    ja="反射速度・文法分析中..."
                  />
                ) : null}
              </div>

              {/* Quick Action Buttons (Start / Pause / Resume) */}
              <div className="flex items-center gap-2 pt-0.5">
                {isReady && (
                  <Button
                    size="lg"
                    variant="akane"
                    className="font-black text-sm md:text-base h-11 px-6 rounded-2xl shadow-md hover:shadow-lg transition-all gap-2 animate-bounce ring-2 ring-primary/30 cursor-pointer"
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
                    className="font-bold text-xs h-8 px-4 rounded-xl shadow-xs gap-1.5 border-primary/40 text-primary hover:bg-primary/10 cursor-pointer"
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
                    className="font-bold text-xs h-8 px-4 rounded-xl shadow-xs gap-1.5 animate-pulse cursor-pointer"
                    onClick={() => session.togglePause()}
                  >
                    <Play className="h-3.5 w-3.5 fill-current" />
                    <span>Tiếp Tục Suy Nghĩ ({formatKeyDisplay(keybindings.drillPauseOrResume)})</span>
                  </Button>
                ) : (isWaiting || isRecording) ? (
                  <Button
                    size="sm"
                    variant="outline"
                    className="font-bold text-xs h-8 px-3 rounded-xl border-amber-500/40 text-amber-600 dark:text-amber-400 hover:bg-amber-500/10 gap-1.5 cursor-pointer"
                    onClick={() => session.togglePause()}
                    title="Tạm dừng đồng hồ để suy nghĩ"
                  >
                    <Clock className="h-3.5 w-3.5 text-amber-500" />
                    <span>Tạm Dừng Suy Nghĩ ({formatKeyDisplay(keybindings.drillPauseOrResume)})</span>
                  </Button>
                ) : null}
              </div>

              {/* LIVE SPEECH PREVIEW BUBBLE */}
              {(isWaiting || isRecording || session.speech.interimTranscript || session.speech.transcript) && (
                <div className="w-full max-w-xl mx-auto p-2.5 px-4 rounded-2xl bg-primary/5 border border-primary/25 shadow-xs flex items-center justify-between gap-3 animate-in fade-in zoom-in-95 duration-200">
                  <div className="flex items-center gap-2.5 min-w-0">
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
              <div className="w-full max-w-xl mx-auto space-y-1">
                <ZenUnifiedInputBar
                  value={transcriptInput || session.speech.transcript || session.speech.interimTranscript}
                  onChange={setTranscriptInput}
                  onSubmit={() => handleDirectSubmit()}
                  placeholder={
                    session.isPaused
                      ? "Đang tạm dừng — Bấm [P] để tiếp tục..."
                      : isWaiting
                      ? "Nói vào mic hoặc gõ câu trả lời tiếng Nhật (Enter)..."
                      : activeExercise?.exercise_type === "reflex_conjugation"
                      ? "Gõ câu chia thể (ví dụ: 書かせられた)..."
                      : "Gõ câu phản xạ tiếng Nhật..."
                  }
                  submitButtonText="Nộp"
                  isEvaluating={isEvaluating}
                  hintText={isRecording ? "Đang thu âm mic hoặc gõ phím" : "Chế độ văn phòng: Gõ phím & Enter để nộp bài"}
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 3. Bottom Minimal Shortcuts Strip */}
      <div className="shrink-0 py-1 border-t border-border/50 flex flex-wrap items-center justify-between gap-2 text-[11px] text-muted-foreground">
        <div className="flex items-center gap-3">
          <span><kbd className="px-1 py-0.5 rounded bg-muted border font-bold">{formatKeyDisplay(keybindings.reflexStartVoice)} / {formatKeyDisplay(keybindings.reflexSubmitOrNext)}</kbd> Bắt đầu / Câu tiếp</span>
          <span><kbd className="px-1 py-0.5 rounded bg-muted border font-bold">{formatKeyDisplay(keybindings.reflexRetry)}</kbd> Làm lại</span>
          <span><kbd className="px-1 py-0.5 rounded bg-muted border font-bold">{formatKeyDisplay(keybindings.reflexReplayModel)}</kbd> Nghe lại mẫu</span>
          <span><kbd className="px-1 py-0.5 rounded bg-muted border font-bold">{formatKeyDisplay(keybindings.reflexPauseOrResume)}</kbd> Tạm dừng</span>
        </div>
        <div className="flex items-center gap-2">
          <span><kbd className="px-1 py-0.5 rounded bg-muted border font-bold">{formatKeyDisplay(keybindings.reflexToggleHelp)}</kbd> Phím tắt</span>
          <span><kbd className="px-1 py-0.5 rounded bg-muted border font-bold">Esc</kbd> Thoát</span>
        </div>
      </div>
    </div>
  );
}
