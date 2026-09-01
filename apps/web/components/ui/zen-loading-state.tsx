"use client";

import React from "react";
import { Sparkles, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

export interface ZenLoadingStateProps {
  variant?: "studio" | "card" | "ai" | "inline";
  title?: string;
  ja?: string;
  description?: string;
  className?: string;
}

export function ZenLoadingState({
  variant = "studio",
  title = "Đang chuẩn bị phòng luyện...",
  ja = "スタジオ準備中...",
  description = "AI đang thiết lập đề bài và phản xạ cá nhân hóa...",
  className,
}: ZenLoadingStateProps) {
  if (variant === "inline") {
    return (
      <div className={cn("inline-flex items-center gap-2 text-xs text-primary font-medium", className)}>
        <Sparkles className="h-3.5 w-3.5 animate-spin text-primary" />
        {ja && <span className="font-jp text-[11px] text-muted-foreground">{ja}</span>}
        <span>{title}</span>
      </div>
    );
  }

  if (variant === "ai") {
    return (
      <div
        className={cn(
          "p-6 sm:p-8 rounded-3xl border border-primary/20 bg-primary/5 text-center space-y-3 washi-texture animate-pulse relative overflow-hidden",
          className
        )}
      >
        <div className="flex items-center justify-center gap-2 font-bold text-sm text-primary">
          <Sparkles className="h-5 w-5 animate-spin text-primary shrink-0" />
          <span>{title}</span>
        </div>
        {ja && (
          <p className="text-xs font-bold text-primary/80 font-jp tracking-wider">
            {ja}
          </p>
        )}
        {description && (
          <p className="text-xs text-muted-foreground max-w-md mx-auto leading-relaxed">
            {description}
          </p>
        )}
      </div>
    );
  }

  if (variant === "card") {
    return (
      <div
        className={cn(
          "p-5 rounded-2xl border border-border/80 bg-card/60 washi-texture space-y-3 animate-pulse",
          className
        )}
      >
        <div className="flex items-center justify-between">
          <div className="h-4 w-28 rounded-lg bg-muted/60" />
          <div className="h-4 w-12 rounded-lg bg-muted/40" />
        </div>
        <div className="space-y-2 py-2">
          <div className="h-5 w-3/4 rounded-lg bg-muted/60" />
          <div className="h-3.5 w-1/2 rounded-lg bg-muted/40" />
        </div>
        <div className="h-9 rounded-xl bg-muted/30" />
      </div>
    );
  }

  // Default: studio layout skeleton
  return (
    <div className={cn("max-w-6xl mx-auto space-y-3.5 pb-6 animate-in fade-in duration-200", className)}>
      {/* 1. Header Bar Skeleton */}
      <div className="h-14 rounded-2xl border border-border/80 bg-card/60 washi-texture p-3 flex items-center justify-between animate-pulse">
        <div className="flex items-center gap-2.5">
          <div className="h-8 w-8 rounded-xl bg-muted/60" />
          <div className="h-5 w-36 rounded-lg bg-muted/60" />
          <div className="h-4 w-14 rounded-md bg-muted/40 hidden sm:block" />
        </div>
        <div className="flex items-center gap-2">
          <div className="h-7 w-24 rounded-lg bg-muted/50 hidden sm:block" />
          <div className="h-7 w-7 rounded-lg bg-muted/50" />
        </div>
      </div>

      {/* 2. Studio Layout Skeleton Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-3.5 items-start">
        {/* Left Main Arena Skeleton */}
        <div className="lg:col-span-7 space-y-3">
          <div className="p-6 rounded-2xl border border-border/70 bg-card/50 washi-texture space-y-4 relative overflow-hidden">
            <div className="flex items-center justify-between">
              <div className="h-5 w-28 rounded-lg bg-muted/60 animate-pulse" />
              <div className="h-7 w-7 rounded-lg bg-muted/40" />
            </div>

            <div className="space-y-2 py-4">
              <div className="h-6 w-3/4 rounded-lg bg-muted/60 animate-pulse" />
              <div className="h-4 w-1/2 rounded-lg bg-muted/40 animate-pulse" />
            </div>

            <div className="h-11 rounded-xl bg-primary/5 border border-primary/15 flex items-center justify-center">
              <div className="flex items-center gap-2 text-xs font-semibold text-primary/80 animate-pulse">
                <Sparkles className="h-3.5 w-3.5 animate-spin" />
                <span className="font-jp">{ja}</span>
                <span>• {title}</span>
              </div>
            </div>
          </div>

          {/* Action Box Skeleton */}
          <div className="h-14 rounded-xl border border-border/70 bg-muted/30 animate-pulse" />
        </div>

        {/* Right Side Scaffold Skeleton */}
        <div className="lg:col-span-5 space-y-3">
          <div className="p-4 rounded-xl border border-border/70 bg-card/40 washi-texture space-y-3">
            <div className="h-5 w-32 rounded-lg bg-muted/60 animate-pulse" />
            <div className="h-16 rounded-lg bg-muted/30" />
            <div className="h-12 rounded-lg bg-muted/30" />
          </div>
          <div className="h-20 rounded-xl border border-border/60 bg-muted/20 animate-pulse" />
        </div>
      </div>
    </div>
  );
}
