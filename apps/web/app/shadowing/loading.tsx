import React from "react";
import { Sparkles } from "lucide-react";

export default function ShadowingLoading() {
  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-8 animate-in fade-in duration-150">
      <div className="p-6 rounded-3xl border border-border/80 bg-card/60 washi-texture space-y-3 animate-pulse">
        <div className="flex items-center justify-between">
          <div className="h-6 w-48 rounded-lg bg-muted/60" />
          <div className="h-9 w-32 rounded-xl bg-muted/40" />
        </div>
        <div className="h-4 w-72 rounded-lg bg-muted/40" />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div
            key={i}
            className="rounded-2xl border border-border/70 bg-card/50 washi-texture overflow-hidden space-y-3 p-3 animate-pulse"
          >
            <div className="aspect-video w-full rounded-xl bg-muted/50" />
            <div className="space-y-1.5 px-1">
              <div className="h-4 w-3/4 rounded bg-muted/60" />
              <div className="h-3 w-1/2 rounded bg-muted/40" />
            </div>
            <div className="h-8 rounded-lg bg-muted/30" />
          </div>
        ))}
      </div>
    </div>
  );
}
