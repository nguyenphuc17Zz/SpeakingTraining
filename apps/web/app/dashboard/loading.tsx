import React from "react";
import { Sparkles } from "lucide-react";

export default function DashboardLoading() {
  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-8 animate-in fade-in duration-150">
      {/* 1. Hero Banner Skeleton */}
      <div className="p-6 md:p-8 rounded-3xl border border-border/80 bg-card/60 washi-texture space-y-4 animate-pulse">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-2xl bg-muted/60" />
          <div className="space-y-1.5">
            <div className="h-6 w-48 rounded-lg bg-muted/60" />
            <div className="h-4 w-72 rounded-lg bg-muted/40" />
          </div>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-16 rounded-2xl bg-muted/40 border border-border/50" />
          ))}
        </div>
      </div>

      {/* 2. Studio Modes Hub Skeleton */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="h-5 w-48 rounded-lg bg-muted/60 animate-pulse" />
          <div className="h-5 w-24 rounded-lg bg-muted/40" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div
              key={i}
              className="p-5 rounded-3xl border border-border/70 bg-card/50 washi-texture space-y-3 animate-pulse"
            >
              <div className="flex items-center justify-between">
                <div className="h-10 w-10 rounded-2xl bg-muted/60" />
                <div className="h-5 w-16 rounded-md bg-muted/40" />
              </div>
              <div className="space-y-1.5 py-1">
                <div className="h-5 w-3/4 rounded-lg bg-muted/60" />
                <div className="h-3.5 w-1/2 rounded-lg bg-muted/40" />
              </div>
              <div className="h-12 rounded-xl bg-muted/20" />
              <div className="h-9 rounded-xl bg-muted/30 pt-2" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
