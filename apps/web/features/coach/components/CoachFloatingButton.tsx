"use client";
import React from "react";
import { Sparkles } from "lucide-react";

export function CoachFloatingButton({ onClick, hasNotification }: { onClick: () => void; hasNotification?: boolean }) {
  return (
    <button
      onClick={onClick}
      aria-label="AI Coach"
      className="fixed bottom-[calc(5rem+env(safe-area-inset-bottom))] right-4 md:bottom-6 md:right-6 z-40 h-14 w-14 rounded-2xl bg-gradient-to-br from-indigo-600 to-rose-600 text-white shadow-2xl flex items-center justify-center hover:scale-105 transition-transform border border-white/10"
    >
      <Sparkles className="w-6 h-6" />
      {hasNotification && (
        <span className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-amber-400 border-2 border-white animate-pulse" />
      )}
    </button>
  );
}
