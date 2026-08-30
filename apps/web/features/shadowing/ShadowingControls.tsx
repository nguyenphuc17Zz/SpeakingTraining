"use client";

import React from "react";
import {
  Mic,
  Square,
  Play,
  RotateCcw,
  Volume2,
  Repeat,
  Sparkles,
  Radio,
  Headphones,
  Keyboard,
  Zap,
  CheckCircle2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { ShadowingMode, TranscriptSegment } from "@/types/shadowing";
import { ShadowingKeybindings } from "@/hooks/use-shadowing-keybindings";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

export interface ShadowingControlsProps {
  segment: TranscriptSegment | null;
  playbackSpeed: number;
  onSpeedChange: (speed: number) => void;
  shadowingMode: ShadowingMode;
  onModeChange: (mode: ShadowingMode) => void;
  isLooping: boolean;
  onToggleLoop: () => void;
  onPlaySegment: () => void;
  onTriggerPractice?: () => void;
  onStartRecording?: () => void;
  onStopRecording?: () => void;
  onCancelPractice?: () => void;
  isRecording: boolean;
  isEvaluating: boolean;
  practiceStep?: "idle" | "listening" | "prompting" | "recording" | "evaluating";
  keybindings?: ShadowingKeybindings;
  onOpenKeybindings?: () => void;
  autoPilot?: boolean;
  onToggleAutoPilot?: () => void;
  onApplyPedagogicalLevel?: (level: 1 | 2 | 3 | 4) => void;
}

const SPEED_OPTIONS = [0.75, 0.9, 1.0, 1.25];

export function ShadowingControls({
  segment,
  playbackSpeed,
  onSpeedChange,
  shadowingMode,
  onModeChange,
  isLooping,
  onToggleLoop,
  onPlaySegment,
  onTriggerPractice,
  onStartRecording,
  onStopRecording,
  onCancelPractice,
  isRecording,
  isEvaluating,
  practiceStep = "idle",
  keybindings,
  onOpenKeybindings,
  autoPilot = false,
  onToggleAutoPilot,
  onApplyPedagogicalLevel,
}: ShadowingControlsProps) {
  const isListeningStep = practiceStep === "listening";
  const isPromptingStep = practiceStep === "prompting";

  const handleActionClick = () => {
    if (onTriggerPractice) {
      onTriggerPractice();
    } else if (isRecording && onStopRecording) {
      onStopRecording();
    } else if (!isRecording && onStartRecording) {
      onStartRecording();
    }
  };

  return (
    <div className="p-3.5 sm:p-4 rounded-2xl bg-card/95 border border-border/90 washi-texture shadow-xs space-y-3">
      {/* Top 4-Step Pedagogical Level Pills */}
      {onApplyPedagogicalLevel && (
        <div className="space-y-1">
          <div className="flex items-center justify-between text-[11px] font-bold text-muted-foreground">
            <span>Lộ trình 4 bước nâng trình:</span>
            {onToggleAutoPilot && (
              <button
                type="button"
                onClick={() => {
                  soundFX.playFurin();
                  onToggleAutoPilot();
                }}
                className={cn(
                  "px-2 py-0.5 rounded-full text-[10px] font-bold border transition-all flex items-center gap-1",
                  autoPilot
                    ? "bg-emerald-500/15 border-emerald-500/30 text-emerald-600 dark:text-emerald-400"
                    : "bg-muted border-border text-muted-foreground hover:text-foreground"
                )}
                title="Tự động phát mẫu -> thu âm -> chấm -> chuyển câu"
              >
                <Zap className="h-3 w-3" />
                <span>Auto-Pilot: {autoPilot ? "BẬT" : "TẮT"}</span>
              </button>
            )}
          </div>

          <div className="grid grid-cols-4 gap-1 text-[10px] font-bold">
            <button
              type="button"
              onClick={() => {
                soundFX.playFurin();
                onApplyPedagogicalLevel(1);
              }}
              className="p-1 rounded-lg border border-border hover:border-primary/40 bg-muted/40 hover:bg-muted text-foreground transition-all text-center"
              title="Bước 1: Tốc độ 0.8x, Phụ đề song ngữ"
            >
              1. Lẩm nhẩm
            </button>
            <button
              type="button"
              onClick={() => {
                soundFX.playFurin();
                onApplyPedagogicalLevel(2);
              }}
              className="p-1 rounded-lg border border-border hover:border-primary/40 bg-muted/40 hover:bg-muted text-foreground transition-all text-center"
              title="Bước 2: Tốc độ 1.0x, Kanji + Furigana"
            >
              2. Đồng thanh
            </button>
            <button
              type="button"
              onClick={() => {
                soundFX.playFurin();
                onApplyPedagogicalLevel(3);
              }}
              className="p-1 rounded-lg border border-border hover:border-primary/40 bg-muted/40 hover:bg-muted text-foreground transition-all text-center"
              title="Bước 3: Ẩn Sub (Audio Only)"
            >
              3. Blind Sub
            </button>
            <button
              type="button"
              onClick={() => {
                soundFX.playFurin();
                onApplyPedagogicalLevel(4);
              }}
              className="p-1 rounded-lg border border-border hover:border-primary/40 bg-muted/40 hover:bg-muted text-foreground transition-all text-center"
              title="Bước 4: Tốc độ 1.1x, Nghe rồi Shadow"
            >
              4. Nhập vai
            </button>
          </div>
        </div>
      )}

      {/* Row 2: Speed & Mode Controls (Segmented Bars) */}
      <div className="flex items-center justify-between gap-2 pt-1 border-t border-border/50 text-xs">
        {/* Speed Bar */}
        <div className="flex items-center gap-1 p-0.5 rounded-xl bg-muted/50 border border-border">
          {SPEED_OPTIONS.map((spd) => (
            <button
              key={spd}
              type="button"
              onClick={() => {
                soundFX.playFurin();
                onSpeedChange(spd);
              }}
              className={cn(
                "px-2 py-0.5 rounded-lg text-[10px] font-mono font-bold transition-all",
                playbackSpeed === spd
                  ? "bg-card text-foreground border border-border shadow-2xs"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              {spd}x
            </button>
          ))}
        </div>

        {/* Loop Toggle */}
        <button
          type="button"
          onClick={() => {
            soundFX.playFurin();
            onToggleLoop();
          }}
          className={cn(
            "px-2.5 py-1 rounded-xl text-[11px] font-bold border transition-all flex items-center gap-1.5",
            isLooping
              ? "bg-primary text-primary-foreground border-primary shadow-xs"
              : "bg-muted/40 border-border text-muted-foreground hover:text-foreground"
          )}
          title="Lặp lại câu này liên tục (L)"
        >
          <Repeat className="h-3 w-3" />
          <span>{isLooping ? "Đang Lặp (L)" : "Lặp câu (L)"}</span>
        </button>
      </div>

      {/* Main Big Action CTA Bar */}
      <div className="grid grid-cols-4 gap-2 pt-1">
        {/* Play Sentence Audio */}
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            soundFX.playFurin();
            onPlaySegment();
          }}
          className="col-span-1 h-11 rounded-xl border-border text-xs font-bold gap-1 shadow-2xs"
          title="Phát câu mẫu (C)"
        >
          <Volume2 className="h-4 w-4 text-primary" />
          <span className="hidden sm:inline">Mẫu (C)</span>
        </Button>

        {/* Trigger Practice / Record Button */}
        <Button
          variant={isRecording ? "danger" : "akane"}
          size="lg"
          onClick={handleActionClick}
          disabled={isEvaluating}
          className={cn(
            "col-span-3 h-11 rounded-xl font-bold text-xs shadow-md transition-all gap-2",
            isRecording && "animate-pulse ring-2 ring-rose-500/40"
          )}
        >
          {isEvaluating ? (
            <>
              <Sparkles className="h-4 w-4 animate-spin" />
              <span>Đang chấm điểm phản xạ...</span>
            </>
          ) : isRecording ? (
            <>
              <Square className="h-4 w-4 fill-current" />
              <span>Dừng & Chấm Điểm (Space/Q)</span>
            </>
          ) : isListeningStep ? (
            <>
              <Volume2 className="h-4 w-4 animate-pulse" />
              <span>Đang phát câu mẫu...</span>
            </>
          ) : isPromptingStep ? (
            <>
              <Mic className="h-4 w-4" />
              <span>Bắt Đầu Nói Câu Này (Space/Q)</span>
            </>
          ) : (
            <>
              <Mic className="h-4 w-4" />
              <span>Luyện Câu Này (Space/Q)</span>
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
