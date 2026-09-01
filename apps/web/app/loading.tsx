import React from "react";
import { Sparkles } from "lucide-react";

export default function GlobalRouteLoading() {
  return (
    <div className="max-w-6xl mx-auto space-y-3 pb-6 animate-in fade-in duration-150">
      {/* 1. Header Bar Skeleton */}
      <div className="h-14 rounded-2xl border border-border/80 bg-card/60 washi-texture p-3 flex items-center justify-between animate-pulse">
        <div className="flex items-center gap-2.5">
          <div className="h-8 w-8 rounded-xl bg-muted/60" />
          <div className="h-5 w-32 rounded-lg bg-muted/60" />
          <div className="h-4 w-12 rounded-md bg-muted/40 hidden sm:block" />
        </div>
        <div className="flex items-center gap-2">
          <div className="h-7 w-20 rounded-lg bg-muted/50 hidden sm:block" />
          <div className="h-7 w-7 rounded-lg bg-muted/50" />
        </div>
      </div>

      {/* 2. Studio Layout Skeleton Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-3.5 items-start">
        {/* Left Main Arena Skeleton */}
        <div className="lg:col-span-7 space-y-3">
          <div className="p-6 rounded-2xl border border-border/70 bg-card/50 washi-texture space-y-4 relative overflow-hidden">
            <div className="flex items-center justify-between">
              <div className="h-5 w-24 rounded-lg bg-muted/60 animate-pulse" />
              <div className="h-7 w-7 rounded-lg bg-muted/40" />
            </div>

            <div className="space-y-2 py-4">
              <div className="h-6 w-3/4 rounded-lg bg-muted/60 animate-pulse" />
              <div className="h-4 w-1/2 rounded-lg bg-muted/40 animate-pulse" />
            </div>

            <div className="h-10 rounded-xl bg-primary/5 border border-primary/10 flex items-center justify-center">
              <div className="flex items-center gap-2 text-xs font-semibold text-primary/70 animate-pulse">
                <Sparkles className="h-3.5 w-3.5 animate-spin" />
                <span className="font-jp">スタジオ準備中...</span>
              </div>
            </div>
          </div>

          {/* Action Box Skeleton */}
          <div className="h-14 rounded-xl border border-border/70 bg-muted/30 animate-pulse" />
        </div>

        {/* Right Side Scaffold Skeleton */}
        <div className="lg:col-span-5 space-y-3">
          <div className="p-4 rounded-xl border border-border/70 bg-card/40 washi-texture space-y-3">
            <div className="h-6 w-28 rounded-lg bg-muted/60 animate-pulse" />
            <div className="h-16 rounded-lg bg-muted/30" />
            <div className="h-12 rounded-lg bg-muted/30" />
          </div>
          <div className="h-20 rounded-xl border border-border/60 bg-muted/20 animate-pulse" />
        </div>
      </div>
    </div>
  );
}
