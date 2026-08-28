"use client";

import React from "react";

interface SpeedSelectorProps {
  value: number;
  onChange: (speed: number) => void;
  options?: number[];
  size?: "sm" | "md";
  className?: string;
}

const DEFAULT_SPEEDS = [0.75, 0.85, 1.0, 1.1, 1.25];

export function SpeedSelector({
  value,
  onChange,
  options = DEFAULT_SPEEDS,
  size = "md",
  className = "",
}: SpeedSelectorProps) {
  const isSm = size === "sm";

  return (
    <div className={`inline-flex items-center p-0.5 rounded-lg bg-background/80 border border-border ${className}`}>
      {options.map((spd) => (
        <button
          key={spd}
          type="button"
          onClick={() => onChange(spd)}
          className={`rounded font-mono transition-all ${
            isSm ? "px-1.5 py-0.5 text-[10px]" : "px-2.5 py-1 text-xs"
          } ${
            value === spd
              ? "bg-primary text-primary-foreground font-bold shadow"
              : "text-muted-foreground hover:text-foreground"
          }`}
        >
          {spd}x
        </button>
      ))}
    </div>
  );
}
