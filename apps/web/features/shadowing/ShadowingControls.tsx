"use client";

import React from "react";
import {
  Mic,
  Square,
  Play,
  RotateCcw,
  Volume2,
  FastForward,
  Repeat,
  Sparkles,
  Radio,
  Headphones,
  Keyboard,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { ShadowingMode, TranscriptSegment } from "@/types/shadowing";
import { ShadowingKeybindings } from "@/hooks/use-shadowing-keybindings";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

interface ShadowingControlsProps {
  segment: TranscriptSegment | null;
  playbackSpeed: number;
  onSpeedChange: (speed: number) => void;
  shadowingMode: ShadowingMode;
  onModeChange: (mode: ShadowingMode) => void;
  isLooping: boolean;
  onToggleLoop: () => void;
  onPlaySegment: () => void;
  onStartRecording: () => void;
  onStopRecording: () => void;
  onCancelPractice?: () => void;
  isRecording: boolean;
  isEvaluating: boolean;
  practiceStep?: "idle" | "listening" | "prompting" | "recording" | "evaluating";
  keybindings?: ShadowingKeybindings;
  onOpenKeybindings?: () => void;
}

const SPEED_OPTIONS = [0.75, 0.9, 1.0, 1.1, 1.25];

export function ShadowingControls({
  segment,
  playbackSpeed,
  onSpeedChange,
  shadowingMode,
  onModeChange,
  isLooping,
  onToggleLoop,
  onPlaySegment,
  onStartRecording,
  onStopRecording,
  onCancelPractice,
  isRecording,
  isEvaluating,
  practiceStep = "idle",
  keybindings,
  onOpenKeybindings,
}: ShadowingControlsProps) {
  const isListeningStep = practiceStep === "listening";

  const keyMic = keybindings?.toggleMic?.toUpperCase() || "Q";
  const keyReplay = keybindings?.replay?.toUpperCase() || "C";
  const keyLoop = keybindings?.toggleLoop?.toUpperCase() || "L";

  return (
    <div className="p-4 sm:p-5 rounded-2xl bg-card/90 border border-border/80 washi-texture backdrop-blur-xl shadow-sumi-lg space-y-4">
      {/* Top Bar: Playback Speed & Mode Selectors & Keybindings */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-border/70">
        {/* Speed Selector */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-muted-foreground hidden sm:inline">Tốc độ:</span>
          <div className="flex items-center gap-1 p-0.5 rounded-xl bg-background/90 border border-border">
            {SPEED_OPTIONS.map((spd) => (
              <button
                key={spd}
                onClick={() => {
                  soundFX.playFurin();
                  onSpeedChange(spd);
                }}
                className={cn(
                  "px-2.5 py-1 rounded-lg text-xs font-mono font-bold transition-all",
                  playbackSpeed === spd
                    ? "bg-primary text-primary-foreground shadow-sm font-bold"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                {spd}x
              </button>
            ))}
          </div>
        </div>

        {/* Shadowing Mode Selector */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-muted-foreground hidden sm:inline">Chế độ:</span>
          <div className="flex items-center gap-1 p-0.5 rounded-xl bg-background/90 border border-border text-xs">
            <button
              onClick={() => {
                soundFX.playFurin();
                onModeChange("repeat");
              }}
              className={cn(
                "px-3 py-1 rounded-lg font-semibold transition-all flex items-center gap-1.5",
                shadowingMode === "repeat"
                  ? "bg-primary text-primary-foreground shadow-sm font-bold"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              <Repeat className="h-3 w-3" />
              <span>Lặp lại câu</span>
            </button>
            <button
              onClick={() => {
                soundFX.playFurin();
                onModeChange("listen_shadow");
              }}
              className={cn(
                "px-3 py-1 rounded-lg font-semibold transition-all flex items-center gap-1.5",
                shadowingMode === "listen_shadow"
                  ? "bg-primary text-primary-foreground shadow-sm font-bold"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              <Headphones className="h-3 w-3" />
              <span>Nghe → Shadow</span>
            </button>
            <button
              onClick={() => {
                soundFX.playFurin();
                onModeChange("shadow");
              }}
              className={cn(
                "px-3 py-1 rounded-lg font-semibold transition-all flex items-center gap-1.5",
                shadowingMode === "shadow"
                  ? "bg-primary text-primary-foreground shadow-sm font-bold"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              <Mic className="h-3 w-3" />
              <span>Shadowing trực tiếp</span>
            </button>
          </div>
        </div>
      </div>

      {/* Dynamic Mode Guidance Banner */}
      {isListeningStep && (
        <div className="p-3 rounded-xl bg-cyan-950/40 border border-cyan-500/40 text-cyan-200 text-xs font-semibold flex items-center justify-between gap-2 animate-in fade-in">
          <div className="flex items-center gap-2">
            <Headphones className="h-4 w-4 text-cyan-400 animate-pulse" />
            <span>
              {shadowingMode === "repeat"
                ? "🎧 Đang nghe câu mẫu... Video sẽ tự dừng khi hết câu để bạn sẵn sàng đọc lại."
                : "🎧 Vòng 1: Đang nghe ngữ điệu mẫu... Hết câu sẽ tự động tua lại để bạn nói đuổi."}
            </span>
          </div>
          {onCancelPractice && (
            <button
              onClick={onCancelPractice}
              className="text-[11px] text-cyan-300 hover:underline shrink-0"
            >
              Hủy
            </button>
          )}
        </div>
      )}

      {practiceStep === "prompting" && (
        <div className="p-3 rounded-xl bg-amber-950/40 border border-amber-500/40 text-amber-200 text-xs font-semibold flex items-center justify-between gap-2 animate-in fade-in">
          <div className="flex items-center gap-2">
            <Mic className="h-4 w-4 text-amber-400 animate-bounce" />
            <span>
              🎙️ Đã nghe xong câu mẫu! Hãy nhấn phím <kbd className="px-1.5 py-0.5 rounded bg-amber-900 border border-amber-500 text-amber-200 font-mono font-bold">{keyMic}</kbd> hoặc bấm nút bên dưới để bắt đầu thu âm khi bạn sẵn sàng.
            </span>
          </div>
        </div>
      )}

      {/* Main Action Controls: Play Segment / A-B Loop / Record User Voice */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        {/* Left: Play reference segment & loop */}
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="md"
            onClick={() => {
              soundFX.playFurin();
              onPlaySegment();
            }}
            disabled={!segment || isRecording || isListeningStep}
            className="flex-1 sm:flex-initial text-xs sm:text-sm font-semibold h-11 px-4 rounded-xl border-border bg-background hover:border-primary/50 shadow-sm gap-2"
          >
            <Play className="h-4 w-4 text-primary fill-primary/30" />
            <span>Nghe câu mẫu</span>
            <kbd className="px-1.5 py-0.5 text-[10px] font-mono bg-muted/80 border border-border/80 rounded text-muted-foreground font-bold shadow-xs">
              {keyReplay}
            </kbd>
          </Button>

          <Button
            variant={isLooping ? "primary" : "outline"}
            size="md"
            onClick={() => {
              soundFX.playTaiko();
              onToggleLoop();
            }}
            disabled={!segment || isListeningStep}
            className={cn(
              "flex-1 sm:flex-initial text-xs sm:text-sm font-semibold h-11 px-4 rounded-xl shadow-sm gap-2 transition-all",
              isLooping
                ? "bg-primary text-primary-foreground border-primary shadow-primary/30 ring-2 ring-primary/30"
                : "border-border bg-background hover:border-primary/40 text-foreground"
            )}
          >
            <Repeat className={cn("h-4 w-4", isLooping ? "animate-spin text-primary-foreground" : "text-primary")} />
            <span>{isLooping ? "Đang Lặp A-B" : "Lặp đoạn A-B"}</span>
            <kbd className={cn(
              "px-1.5 py-0.5 text-[10px] font-mono rounded font-bold shadow-xs",
              isLooping ? "bg-white/20 border border-white/30 text-white" : "bg-muted/80 border border-border/80 text-muted-foreground"
            )}>
              {keyLoop}
            </kbd>
          </Button>
        </div>

        {/* Right: Record & Submit */}
        <div className="flex items-center">
          {isRecording ? (
            <Button
              variant="danger"
              size="lg"
              onClick={() => {
                soundFX.playTaiko();
                onStopRecording();
              }}
              className="w-full sm:w-auto h-12 px-6 rounded-xl font-bold text-sm shadow-lg shadow-destructive/30 animate-pulse gap-2.5"
            >
              <Square className="h-4 w-4 fill-current" />
              <span>Dừng & Chấm điểm (完了)</span>
              <kbd className="px-1.5 py-0.5 text-[10px] font-mono bg-white/20 border border-white/30 rounded text-white font-bold shadow-xs">
                {keyMic}
              </kbd>
            </Button>
          ) : isListeningStep ? (
            <Button
              variant="outline"
              size="lg"
              onClick={() => {
                soundFX.playFurin();
                onCancelPractice?.();
              }}
              className="w-full sm:w-auto h-12 px-6 rounded-xl font-bold text-sm border-cyan-500/50 bg-cyan-950/30 text-cyan-200 gap-2.5"
            >
              <Headphones className="h-4 w-4 animate-bounce text-cyan-400" />
              <span>Đang nghe mẫu... (Hủy)</span>
              <kbd className="px-1.5 py-0.5 text-[10px] font-mono bg-cyan-900/60 border border-cyan-500/40 rounded text-cyan-200 font-bold shadow-xs">
                Esc
              </kbd>
            </Button>
          ) : practiceStep === "prompting" ? (
            <Button
              variant="primary"
              size="lg"
              onClick={() => {
                soundFX.playTaiko();
                onStartRecording();
              }}
              disabled={!segment || isEvaluating}
              className="w-full sm:w-auto h-12 px-6 rounded-xl font-bold text-sm shadow-lg shadow-primary/30 gap-2.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:opacity-95 text-white animate-pulse"
            >
              <Mic className="h-4 w-4" />
              <span>Bắt đầu thu âm giọng bạn</span>
              <kbd className="px-1.5 py-0.5 text-[10px] font-mono bg-white/20 border border-white/30 rounded text-white font-bold shadow-xs">
                {keyMic}
              </kbd>
            </Button>
          ) : (
            <Button
              variant="primary"
              size="lg"
              onClick={() => {
                soundFX.playTaiko();
                onStartRecording();
              }}
              disabled={!segment || isEvaluating}
              className="w-full sm:w-auto h-12 px-6 rounded-xl font-bold text-sm shadow-sumi-md gap-2.5 bg-gradient-to-r from-primary via-primary/90 to-aizome-600 hover:opacity-95 text-primary-foreground"
            >
              {isEvaluating ? (
                <>
                  <Radio className="h-4 w-4 animate-spin text-primary-foreground" />
                  <span>Đang phân tích phát âm...</span>
                </>
              ) : shadowingMode === "repeat" ? (
                <>
                  <Repeat className="h-4 w-4" />
                  <span>Bắt đầu Lặp lại câu (リピート)</span>
                  <kbd className="px-1.5 py-0.5 text-[10px] font-mono bg-white/20 border border-white/30 rounded text-white font-bold shadow-xs">
                    {keyMic}
                  </kbd>
                </>
              ) : shadowingMode === "listen_shadow" ? (
                <>
                  <Headphones className="h-4 w-4" />
                  <span>Bắt đầu Nghe → Shadow</span>
                  <kbd className="px-1.5 py-0.5 text-[10px] font-mono bg-white/20 border border-white/30 rounded text-white font-bold shadow-xs">
                    {keyMic}
                  </kbd>
                </>
              ) : (
                <>
                  <Mic className="h-4 w-4" />
                  <span>Bắt đầu thu âm (録音)</span>
                  <kbd className="px-1.5 py-0.5 text-[10px] font-mono bg-white/20 border border-white/30 rounded text-white font-bold shadow-xs">
                    {keyMic}
                  </kbd>
                </>
              )}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
