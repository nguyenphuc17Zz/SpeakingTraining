"use client";
import React, { useEffect, useState } from "react";
import { coachCoreApi } from "../services/coachCoreApi";
import { Sparkles, ArrowRight } from "lucide-react";

export function CoachQuickActions({ route, exerciseId, onSelect }: { route: string; exerciseId?: string; onSelect: (prompt: string, action?: string) => void }) {
  const [actions, setActions] = useState<any[]>([]);
  const [mode, setMode] = useState<string>("");

  useEffect(() => {
    coachCoreApi.getQuickActions(route, exerciseId).then((res) => {
      setActions(res.actions || []);
      setMode(res.mode || "");
    }).catch(() => {});
  }, [route, exerciseId]);

  if (!actions.length) return null;

  return (
    <div className="flex flex-wrap gap-2" role="list" aria-label="Coach quick actions">
      {actions.map((a, idx) => (
        <button
          key={idx}
          role="listitem"
          aria-label={a.label}
          onClick={() => onSelect(a.prompt, a.intent)}
          className="px-3 py-2 rounded-xl bg-card border border-border hover:bg-muted text-xs font-medium flex items-center gap-1.5 transition-colors focus:outline-none focus:ring-2 focus:ring-primary/30"
          title={a.prompt}
        >
          <Sparkles className="w-3 h-3 text-primary" aria-hidden />
          {a.label}
        </button>
      ))}
    </div>
  );
}
