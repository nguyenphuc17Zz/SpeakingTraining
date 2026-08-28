"use client";

import React, { useState, useEffect } from "react";
import {
  Repeat,
  MapPin,
  Clock,
  Plus,
  Minus,
  RotateCcw,
  X,
  Sparkles,
  Play,
  Pause,
  Sliders,
  Keyboard,
  Layers,
  ChevronLeft,
  ChevronRight,
  ArrowRightLeft,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { DualRangeSlider } from "@/components/ui/DualRangeSlider";
import { TranscriptSegment } from "@/types/shadowing";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

interface ABLoopControlsProps {
  currentPlaybackTime: number;
  selectedSegment?: TranscriptSegment | null;
  videoDuration?: number;
  isLooping: boolean;
  loopRange: { start: number; end: number } | null;
  loopGap: number;
  onToggleLoop: () => void;
  onSetMarkerA: (time?: number) => void;
  onSetMarkerB: (time?: number) => void;
  onAdjustMarkerA: (delta: number) => void;
  onAdjustMarkerB: (delta: number) => void;
  onSetExactLoopRange: (start: number, end: number) => void;
  onExpandToNext?: () => void;
  onExpandToPrev?: () => void;
  onLoopCurrentSegment: () => void;
  onClearLoop: () => void;
  onSetLoopGap: (gap: number) => void;
  onSeek: (seconds: number) => void;
}

export function ABLoopControls({
  currentPlaybackTime,
  selectedSegment,
  videoDuration = 600,
  isLooping,
  loopRange,
  loopGap,
  onToggleLoop,
  onSetMarkerA,
  onSetMarkerB,
  onAdjustMarkerA,
  onAdjustMarkerB,
  onSetExactLoopRange,
  onExpandToNext,
  onExpandToPrev,
  onLoopCurrentSegment,
  onClearLoop,
  onSetLoopGap,
  onSeek,
}: ABLoopControlsProps) {
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(1);
    const formattedSecs = Number(secs) < 10 ? `0${secs}` : secs;
    return `${mins}:${formattedSecs}`;
  };

  const parseTime = (input: string): number | null => {
    const trimmed = input.trim();
    if (!trimmed) return null;
    if (trimmed.includes(":")) {
      const parts = trimmed.split(":");
      const mins = parseFloat(parts[0]);
      const secs = parseFloat(parts[1]);
      if (!isNaN(mins) && !isNaN(secs)) {
        return Math.max(0, mins * 60 + secs);
      }
    }
    const val = parseFloat(trimmed);
    return isNaN(val) ? null : Math.max(0, val);
  };

  const startVal = loopRange ? loopRange.start : (selectedSegment?.start_time ?? 0);
  const endVal = loopRange ? loopRange.end : (selectedSegment?.end_time ?? 3);
  const duration = Math.max(0, Number((endVal - startVal).toFixed(1)));

  // Input states for direct editing
  const [inputA, setInputA] = useState(formatTime(startVal));
  const [inputB, setInputB] = useState(formatTime(endVal));

  useEffect(() => {
    setInputA(formatTime(startVal));
  }, [startVal]);

  useEffect(() => {
    setInputB(formatTime(endVal));
  }, [endVal]);

  // Context range for the DualRangeSlider (zoomed around the active sentence/loop)
  const sliderMin = Math.max(0, Number((startVal - 5).toFixed(1)));
  const sliderMax = Math.min(
    videoDuration,
    Math.max(sliderMin + 15, Number((endVal + 5).toFixed(1)))
  );

  const handleApplyInputA = () => {
    const parsed = parseTime(inputA);
    if (parsed !== null && parsed < endVal) {
      onSetExactLoopRange(parsed, endVal);
    } else {
      setInputA(formatTime(startVal));
    }
  };

  const handleApplyInputB = () => {
    const parsed = parseTime(inputB);
    if (parsed !== null && parsed > startVal) {
      onSetExactLoopRange(startVal, parsed);
    } else {
      setInputB(formatTime(endVal));
    }
  };

  return (
    <div
      className={cn(
        "p-4 rounded-2xl border transition-all duration-300 space-y-4 washi-texture backdrop-blur-xl shadow-sumi-md",
        isLooping
          ? "bg-card/95 border-primary/50 ring-1 ring-primary/30 shadow-enso"
          : "bg-card/90 border-border/80"
      )}
    >
      {/* 1. Header: Title, Active Status, Sentence Loop & Clear */}
      <div className="flex items-center justify-between gap-2 border-b border-border/60 pb-2.5">
        <div className="flex items-center gap-2 min-w-0">
          <div
            className={cn(
              "p-1.5 rounded-lg border transition-all shrink-0",
              isLooping
                ? "bg-primary/20 text-primary border-primary/40 animate-pulse"
                : "bg-muted text-muted-foreground border-border"
            )}
          >
            <Repeat className="h-4 w-4" />
          </div>
          <div className="min-w-0">
            <h3 className="text-xs font-bold text-foreground font-sans tracking-wide truncate">
              Bộ Lặp Đoạn A-B (Visual Looper)
            </h3>
          </div>
          {isLooping && (
            <span className="px-2 py-0.5 rounded-full bg-primary/15 text-primary border border-primary/30 text-[10.5px] font-mono font-bold shrink-0">
              Đoạn lặp: {duration}s
            </span>
          )}
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          {/* Quick Segment Auto Loop */}
          {selectedSegment && (
            <button
              onClick={() => {
                soundFX.playTaiko();
                onLoopCurrentSegment();
              }}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold bg-primary/15 text-primary border border-primary/30 hover:bg-primary/25 transition-all shadow-xs"
              title="Khóa vòng lặp vào câu thoại đang chọn"
            >
              <Sparkles className="h-3.5 w-3.5 text-primary" />
              <span>Lặp câu này</span>
            </button>
          )}

          {isLooping && (
            <button
              onClick={() => {
                soundFX.playFurin();
                onClearLoop();
              }}
              className="p-1.5 rounded-lg text-muted-foreground hover:text-primary hover:bg-primary/10 border border-transparent hover:border-primary/20 transition-all"
              title="Hủy vòng lặp A-B"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* 2. Interactive Dual-Handle Timeline Scrubber */}
      <div className="space-y-1.5 px-1">
        <div className="flex items-center justify-between text-[11px] text-muted-foreground font-mono">
          <span>Kéo thanh trượt để chỉnh vùng lặp ({sliderMin}s ➔ {sliderMax}s):</span>
          <span className="font-bold text-foreground">{formatTime(startVal)} ── {formatTime(endVal)}</span>
        </div>
        <DualRangeSlider
          min={sliderMin}
          max={sliderMax}
          step={0.1}
          start={startVal}
          end={endVal}
          currentTime={currentPlaybackTime}
          onChange={(newStart, newEnd) => onSetExactLoopRange(newStart, newEnd)}
          formatTooltip={(v) => formatTime(v)}
        />
      </div>

      {/* 3. Direct Inputs & Multi-step Adjusters (Mốc A & Mốc B) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {/* Point A Control Card: Aizome Indigo */}
        <div
          className={cn(
            "p-3 rounded-xl border transition-all space-y-2.5",
            isLooping
              ? "bg-background/90 border-aizome-500/40 shadow-xs"
              : "bg-background/60 border-border"
          )}
        >
          <div className="flex items-center justify-between text-xs">
            <span className="flex items-center gap-1.5 font-bold text-aizome-400">
              <span className="w-4 h-4 rounded-full bg-aizome-600 text-white flex items-center justify-center text-[10px] font-mono">
                A
              </span>
              <span>Mốc bắt đầu</span>
            </span>

            {/* Direct Input */}
            <div className="flex items-center gap-1">
              <input
                type="text"
                value={inputA}
                onChange={(e) => setInputA(e.target.value)}
                onBlur={handleApplyInputA}
                onKeyDown={(e) => e.key === "Enter" && handleApplyInputA()}
                className="w-16 h-6 px-1.5 text-center text-xs font-mono font-bold rounded-md bg-card border border-border focus:border-aizome-500 focus:outline-none"
                title="Nhập số giây hoặc mm:ss rồi bấm Enter"
              />
              <button
                onClick={() => onSeek(startVal)}
                className="text-[11px] text-muted-foreground hover:text-aizome-400 transition-colors font-mono"
                title="Tua về điểm A"
              >
                Tua
              </button>
            </div>
          </div>

          {/* Stepper Buttons: Macro & Micro */}
          <div className="flex items-center gap-1">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                soundFX.playFurin();
                onSetMarkerA();
              }}
              className="flex-1 h-7 text-[11px] font-semibold rounded-lg gap-1 border-border bg-card hover:border-aizome-500/50"
              title="Đặt điểm A tại vị trí video đang phát (Phím [)"
            >
              <MapPin className="h-3 w-3 text-aizome-400" />
              <span>Đặt A</span>
            </Button>
            <button
              onClick={() => onAdjustMarkerA(-1.0)}
              className="h-7 px-1.5 rounded-lg border border-border bg-card text-[10.5px] font-mono text-muted-foreground hover:text-foreground font-bold hover:border-border/80"
              title="Lùi nhanh 1 giây"
            >
              -1s
            </button>
            <button
              onClick={() => onAdjustMarkerA(-0.2)}
              className="h-7 px-1.5 rounded-lg border border-border bg-card text-[10.5px] font-mono text-muted-foreground hover:text-foreground font-bold hover:border-border/80"
              title="Lùi 0.2 giây"
            >
              -0.2s
            </button>
            <button
              onClick={() => onAdjustMarkerA(0.2)}
              className="h-7 px-1.5 rounded-lg border border-border bg-card text-[10.5px] font-mono text-muted-foreground hover:text-foreground font-bold hover:border-border/80"
              title="Tiến 0.2 giây"
            >
              +0.2s
            </button>
            <button
              onClick={() => onAdjustMarkerA(1.0)}
              className="h-7 px-1.5 rounded-lg border border-border bg-card text-[10.5px] font-mono text-muted-foreground hover:text-foreground font-bold hover:border-border/80"
              title="Tiến nhanh 1 giây"
            >
              +1s
            </button>
          </div>
        </div>

        {/* Point B Control Card: Dynamic Primary Theme Color */}
        <div
          className={cn(
            "p-3 rounded-xl border transition-all space-y-2.5",
            isLooping
              ? "bg-background/90 border-primary/50 shadow-xs"
              : "bg-background/60 border-border"
          )}
        >
          <div className="flex items-center justify-between text-xs">
            <span className="flex items-center gap-1.5 font-bold text-primary">
              <span className="w-4 h-4 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-[10px] font-mono font-bold">
                B
              </span>
              <span>Mốc kết thúc</span>
            </span>

            {/* Direct Input */}
            <div className="flex items-center gap-1">
              <input
                type="text"
                value={inputB}
                onChange={(e) => setInputB(e.target.value)}
                onBlur={handleApplyInputB}
                onKeyDown={(e) => e.key === "Enter" && handleApplyInputB()}
                className="w-16 h-6 px-1.5 text-center text-xs font-mono font-bold rounded-md bg-card border border-border focus:border-primary focus:outline-none"
                title="Nhập số giây hoặc mm:ss rồi bấm Enter"
              />
              <button
                onClick={() => onSeek(endVal)}
                className="text-[11px] text-muted-foreground hover:text-primary transition-colors font-mono"
                title="Tua đến điểm B"
              >
                Tua
              </button>
            </div>
          </div>

          {/* Stepper Buttons: Macro & Micro */}
          <div className="flex items-center gap-1">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                soundFX.playFurin();
                onSetMarkerB();
              }}
              className="flex-1 h-7 text-[11px] font-semibold rounded-lg gap-1 border-border bg-card hover:border-primary/50"
              title="Đặt điểm B tại vị trí video đang phát (Phím ])"
            >
              <MapPin className="h-3 w-3 text-primary" />
              <span>Đặt B</span>
            </Button>
            <button
              onClick={() => onAdjustMarkerB(-1.0)}
              className="h-7 px-1.5 rounded-lg border border-border bg-card text-[10.5px] font-mono text-muted-foreground hover:text-foreground font-bold hover:border-border/80"
              title="Lùi nhanh 1 giây"
            >
              -1s
            </button>
            <button
              onClick={() => onAdjustMarkerB(-0.2)}
              className="h-7 px-1.5 rounded-lg border border-border bg-card text-[10.5px] font-mono text-muted-foreground hover:text-foreground font-bold hover:border-border/80"
              title="Lùi 0.2 giây"
            >
              -0.2s
            </button>
            <button
              onClick={() => onAdjustMarkerB(0.2)}
              className="h-7 px-1.5 rounded-lg border border-border bg-card text-[10.5px] font-mono text-muted-foreground hover:text-foreground font-bold hover:border-border/80"
              title="Tiến 0.2 giây"
            >
              +0.2s
            </button>
            <button
              onClick={() => onAdjustMarkerB(1.0)}
              className="h-7 px-1.5 rounded-lg border border-border bg-card text-[10.5px] font-mono text-muted-foreground hover:text-foreground font-bold hover:border-border/80"
              title="Tiến nhanh 1 giây"
            >
              +1s
            </button>
          </div>
        </div>
      </div>

      {/* 4. Sentence Expansion & Quick Actions */}
      <div className="flex flex-wrap items-center justify-between gap-2 pt-1">
        {/* Sentence Expansion Helpers */}
        <div className="flex items-center gap-1.5">
          {onExpandToPrev && (
            <button
              onClick={() => {
                soundFX.playFurin();
                onExpandToPrev();
              }}
              className="flex items-center gap-1 px-2.5 py-1 rounded-lg border border-border bg-background hover:bg-muted text-[11px] font-semibold text-muted-foreground hover:text-foreground transition-all shadow-xs"
              title="Mở rộng vòng lặp bao gồm cả câu trước"
            >
              <ChevronLeft className="h-3.5 w-3.5" />
              <span>+ Ghép câu trước</span>
            </button>
          )}

          {onExpandToNext && (
            <button
              onClick={() => {
                soundFX.playFurin();
                onExpandToNext();
              }}
              className="flex items-center gap-1 px-2.5 py-1 rounded-lg border border-border bg-background hover:bg-muted text-[11px] font-semibold text-muted-foreground hover:text-foreground transition-all shadow-xs"
              title="Mở rộng vòng lặp bao gồm cả câu kế tiếp"
            >
              <span>+ Ghép câu sau</span>
              <ChevronRight className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        {/* Gap Selector & Master Toggle */}
        <div className="flex items-center gap-2">
          {/* Shadowing Gap */}
          <div className="flex items-center gap-1 p-0.5 rounded-lg bg-background border border-border">
            {[
              { val: 0, label: "0s" },
              { val: 1, label: "1s ⏸" },
              { val: 2, label: "2s ⏸" },
            ].map((g) => (
              <button
                key={g.val}
                onClick={() => {
                  soundFX.playFurin();
                  onSetLoopGap(g.val);
                }}
                className={cn(
                  "px-2 py-0.5 rounded-md text-[10.5px] font-semibold transition-all",
                  loopGap === g.val
                    ? "bg-primary text-primary-foreground shadow-xs font-bold"
                    : "text-muted-foreground hover:text-foreground"
                )}
                title={`Nghỉ ${g.val} giây giữa mỗi lần lặp lại câu`}
              >
                {g.label}
              </button>
            ))}
          </div>

          {/* Master Toggle */}
          <Button
            variant={isLooping ? "primary" : "outline"}
            size="sm"
            onClick={() => {
              soundFX.playTaiko();
              onToggleLoop();
            }}
            className={cn(
              "h-8 px-3 rounded-lg text-xs font-bold gap-1.5 shadow-sm transition-all",
              isLooping
                ? "bg-primary text-primary-foreground shadow-primary/30 ring-1 ring-primary/40"
                : "border-border bg-background hover:border-primary/40 text-foreground"
            )}
            title="Bật/Tắt Lặp đoạn A-B (Phím L)"
          >
            <Repeat className={cn("h-3.5 w-3.5", isLooping && "animate-spin")} />
            <span>{isLooping ? "Đang Lặp A-B" : "Bật Lặp A-B"}</span>
          </Button>
        </div>
      </div>
    </div>
  );
}
