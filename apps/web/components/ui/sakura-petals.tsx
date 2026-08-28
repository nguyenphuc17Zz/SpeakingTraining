"use client";

import React from "react";

export function SakuraPetals({ count = 5 }: { count?: number }) {
  return (
    <span aria-hidden className="pointer-events-none absolute inset-0 overflow-hidden rounded-[inherit]">
      {Array.from({ length: count }).map((_, i) => (
        <span
          key={i}
          className="absolute text-rose-300/40 select-none"
          style={{
            left: `${12 + i * 18}%`,
            top: `-10px`,
            fontSize: `${10 + (i % 3) * 4}px`,
            animation: `sakura-fall ${4 + i * 0.8}s ease-in-out ${i * 0.7}s infinite`,
            animationDelay: `${i * 0.6}s`,
          }}
        >
          🌸
        </span>
      ))}
    </span>
  );
}

export function EnsoRing({ size = 120, className = "" }: { size?: number; className?: string }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      className={`pointer-events-none opacity-[0.07] ${className}`}
      aria-hidden
    >
      <circle
        cx="50"
        cy="50"
        r="42"
        fill="none"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeDasharray="264"
        strokeDashoffset="18"
        style={{ transform: "rotate(-8deg)", transformOrigin: "50% 50%" }}
        className="text-primary"
      />
    </svg>
  );
}
