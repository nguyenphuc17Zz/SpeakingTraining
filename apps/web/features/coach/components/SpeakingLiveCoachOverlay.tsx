"use client";
import React, { useEffect, useState } from "react";
import { coachCoreApi } from "../services/coachCoreApi";
import { Lightbulb, Sparkles } from "lucide-react";

export function SpeakingLiveCoachOverlay({ sessionId, isActive }: { sessionId?: string; isActive: boolean }) {
  const [hint, setHint] = useState<string | null>(null);

  useEffect(() => {
    if (!isActive || !sessionId) return;
    // fetch once after 8s, then every 25s non-blocking
    let cancelled = false;
    const fetchHint = async () => {
      try {
        const res = await coachCoreApi.chat({
          message: "Give me a 1-sentence live hint for improving naturalness in this speaking session, based on recent turns. Keep it concise and actionable.",
          current_route: "/speaking",
          current_session_id: sessionId,
        });
        if (!cancelled && res.response) {
          // take first sentence
          setHint(res.response.split("\n")[0].slice(0, 140));
        }
      } catch {}
    };
    const t1 = setTimeout(fetchHint, 8000);
    const interval = setInterval(fetchHint, 25000);
    return () => { cancelled = true; clearTimeout(t1); clearInterval(interval); };
  }, [sessionId, isActive]);

  if (!isActive || !hint) return null;
  return (
    <div className="flex items-start gap-2.5 p-3 rounded-xl bg-aizome-500/10 dark:bg-aizome-950/40 border border-aizome-500/25 dark:border-aizome-500/35 text-xs shadow-sm animate-in fade-in">
      <span className="h-6 w-6 rounded-lg bg-aizome-600 dark:bg-aizome-500 text-white flex items-center justify-center shrink-0 shadow-sm"><Sparkles className="w-3.5 h-3.5" /></span>
      <div className="flex-1 min-w-0">
        <span className="font-bold text-aizome-700 dark:text-aizome-300 flex items-center gap-1"><Lightbulb className="w-3 h-3 text-aizome-500" /> Live Coach</span>
        <p className="text-foreground/90 dark:text-foreground/90 leading-relaxed mt-0.5 font-medium">{hint}</p>
      </div>
    </div>
  );
}

