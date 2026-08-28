"use client";

import React, { useRef, useState, useCallback } from "react";
import { cn } from "@/lib/utils";

interface DualRangeSliderProps {
  min: number;
  max: number;
  step?: number;
  start: number;
  end: number;
  currentTime?: number;
  onChange: (start: number, end: number) => void;
  className?: string;
  formatTooltip?: (val: number) => string;
}

export function DualRangeSlider({
  min,
  max,
  step = 0.1,
  start,
  end,
  currentTime,
  onChange,
  className,
  formatTooltip = (v) => `${v.toFixed(1)}s`,
}: DualRangeSliderProps) {
  const trackRef = useRef<HTMLDivElement | null>(null);
  const [activeHandle, setActiveHandle] = useState<"start" | "end" | "middle" | null>(null);
  const [dragOffset, setDragOffset] = useState<number>(0);

  // Clamp values within min/max bounds
  const clampedStart = Math.max(min, Math.min(end - step, start));
  const clampedEnd = Math.min(max, Math.max(start + step, end));

  const totalRange = Math.max(0.1, max - min);
  const startPercent = Math.max(0, Math.min(100, ((clampedStart - min) / totalRange) * 100));
  const endPercent = Math.max(0, Math.min(100, ((clampedEnd - min) / totalRange) * 100));
  const currentPercent =
    currentTime !== undefined
      ? Math.max(0, Math.min(100, ((currentTime - min) / totalRange) * 100))
      : null;

  const getValueFromX = useCallback(
    (clientX: number): number => {
      if (!trackRef.current) return min;
      const rect = trackRef.current.getBoundingClientRect();
      const ratio = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width));
      const rawValue = min + ratio * totalRange;
      return Math.round(rawValue / step) * step;
    },
    [min, totalRange, step]
  );

  const handlePointerDown = (handle: "start" | "end" | "middle", e: React.PointerEvent) => {
    e.preventDefault();
    e.stopPropagation();
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
    setActiveHandle(handle);

    if (handle === "middle") {
      const clickVal = getValueFromX(e.clientX);
      setDragOffset(clickVal - clampedStart);
    }
  };

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!activeHandle || !trackRef.current) return;
    const newVal = getValueFromX(e.clientX);

    if (activeHandle === "start") {
      const validStart = Math.max(min, Math.min(clampedEnd - step, newVal));
      onChange(Number(validStart.toFixed(2)), clampedEnd);
    } else if (activeHandle === "end") {
      const validEnd = Math.min(max, Math.max(clampedStart + step, newVal));
      onChange(clampedStart, Number(validEnd.toFixed(2)));
    } else if (activeHandle === "middle") {
      const loopLength = clampedEnd - clampedStart;
      let newStart = newVal - dragOffset;
      let newEnd = newStart + loopLength;

      if (newStart < min) {
        newStart = min;
        newEnd = min + loopLength;
      }
      if (newEnd > max) {
        newEnd = max;
        newStart = max - loopLength;
      }

      onChange(Number(newStart.toFixed(2)), Number(newEnd.toFixed(2)));
    }
  };

  const handlePointerUp = (e: React.PointerEvent) => {
    if (activeHandle) {
      try {
        (e.target as HTMLElement).releasePointerCapture(e.pointerId);
      } catch (err) {}
      setActiveHandle(null);
    }
  };

  return (
    <div className={cn("relative w-full py-4 select-none touch-none", className)}>
      {/* Background Track: Sumi Charcoal */}
      <div
        ref={trackRef}
        className="relative w-full h-3 rounded-full bg-sumi-800/90 border border-sumi-700/80 overflow-visible cursor-pointer shadow-inner"
        onPointerDown={(e) => {
          const clickVal = getValueFromX(e.clientX);
          const distToStart = Math.abs(clickVal - clampedStart);
          const distToEnd = Math.abs(clickVal - clampedEnd);

          if (distToStart < distToEnd) {
            handlePointerDown("start", e);
          } else {
            handlePointerDown("end", e);
          }
        }}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
      >
        {/* Active Loop Range Bar: Aizome to Theme Primary Gradient */}
        <div
          className={cn(
            "absolute top-0 bottom-0 rounded-full cursor-grab active:cursor-grabbing transition-all",
            "bg-gradient-to-r from-aizome-600 via-aizome-500 to-primary shadow-md",
            activeHandle === "middle" && "ring-2 ring-primary/80 brightness-110"
          )}
          style={{
            left: `${startPercent}%`,
            width: `${Math.max(1, endPercent - startPercent)}%`,
          }}
          onPointerDown={(e) => handlePointerDown("middle", e)}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
        />

        {/* Current Playback Time Indicator Needle: Kintsugi Gold */}
        {currentPercent !== null && (
          <div
            className="absolute -top-1 bottom-0 w-1 bg-kintsugi-400 rounded-full pointer-events-none shadow-md z-10 -translate-x-1/2 transition-all duration-75"
            style={{ left: `${currentPercent}%`, height: "20px" }}
          >
            <div className="w-2.5 h-2.5 bg-kintsugi-400 rounded-full -translate-x-[3px] -translate-y-1 shadow-xs border border-sumi-900" />
          </div>
        )}

        {/* Handle A: Japanese Aizome (藍染) */}
        <div
          className={cn(
            "absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-6 h-6 rounded-full border-2 border-white shadow-xl cursor-ew-resize z-20 flex items-center justify-center transition-transform",
            "bg-aizome-600 hover:scale-110 active:scale-125 focus:outline-none ring-2 ring-aizome-500/40",
            activeHandle === "start" && "scale-125 ring-aizome-400 shadow-aizome-500/50"
          )}
          style={{ left: `${startPercent}%` }}
          onPointerDown={(e) => handlePointerDown("start", e)}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
        >
          <span className="text-[10px] font-black text-white font-mono pointer-events-none">A</span>

          {/* Floating Tooltip */}
          <div className="absolute -top-8 px-2 py-0.5 rounded-md bg-sumi-900/95 border border-aizome-500/50 text-aizome-200 text-[10px] font-mono font-bold whitespace-nowrap pointer-events-none shadow-md">
            {formatTooltip(clampedStart)}
          </div>
        </div>

        {/* Handle B: Active Theme Primary Accent */}
        <div
          className={cn(
            "absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-6 h-6 rounded-full border-2 border-white shadow-xl cursor-ew-resize z-20 flex items-center justify-center transition-transform",
            "bg-primary hover:scale-110 active:scale-125 focus:outline-none ring-2 ring-primary/40",
            activeHandle === "end" && "scale-125 ring-primary shadow-primary/50"
          )}
          style={{ left: `${endPercent}%` }}
          onPointerDown={(e) => handlePointerDown("end", e)}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
        >
          <span className="text-[10px] font-black text-primary-foreground font-mono pointer-events-none">B</span>

          {/* Floating Tooltip */}
          <div className="absolute -top-8 px-2 py-0.5 rounded-md bg-sumi-900/95 border border-primary/50 text-primary text-[10px] font-mono font-bold whitespace-nowrap pointer-events-none shadow-md">
            {formatTooltip(clampedEnd)}
          </div>
        </div>
      </div>
    </div>
  );
}
