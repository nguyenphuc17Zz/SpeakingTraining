"use client";

import React from "react";
import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

export interface StatCardProps {
  title: string;
  jaTitle: string;
  value: string | number;
  subtext?: string;
  icon: LucideIcon;
  color?: "rose" | "indigo" | "emerald" | "amber" | "torii" | "kintsugi" | "aizome" | "matcha" | "sakura";
  className?: string;
}

export function StatCard({
  title,
  jaTitle,
  value,
  subtext,
  icon: Icon,
  color = "kintsugi",
  className,
}: StatCardProps) {
  // Japanese Accent Theme Configurations
  const themes = {
    kintsugi: {
      iconBg: "bg-gradient-to-br from-amber-500/25 via-kintsugi-400/20 to-amber-600/15 text-kintsugi-500 border-kintsugi-400/40 shadow-[0_0_16px_rgba(212,175,55,0.18)]",
      badge: "bg-kintsugi-400/15 text-kintsugi-500 border-kintsugi-400/30",
      topAccent: "from-kintsugi-400/60 via-amber-500/30 to-transparent",
      valueColor: "text-foreground",
    },
    torii: {
      iconBg: "bg-gradient-to-br from-primary/25 via-emerald-500/20 to-teal-600/15 text-primary border-primary/40 shadow-[0_0_16px_rgba(16,185,129,0.18)]",
      badge: "bg-primary/15 text-primary border-primary/30",
      topAccent: "from-primary/60 via-emerald-500/30 to-transparent",
      valueColor: "text-foreground",
    },
    sakura: {
      iconBg: "bg-gradient-to-br from-pink-500/25 via-rose-400/20 to-fuji-500/15 text-rose-400 border-pink-400/40 shadow-[0_0_16px_rgba(251,113,133,0.18)]",
      badge: "bg-pink-500/15 text-pink-400 border-pink-500/30",
      topAccent: "from-pink-400/60 via-rose-400/30 to-transparent",
      valueColor: "text-foreground",
    },
    matcha: {
      iconBg: "bg-gradient-to-br from-matcha-500/25 via-emerald-500/20 to-green-600/15 text-matcha-600 border-matcha-500/40 shadow-[0_0_16px_rgba(34,197,94,0.18)]",
      badge: "bg-matcha-500/15 text-matcha-600 border-matcha-500/30",
      topAccent: "from-matcha-500/60 via-emerald-500/30 to-transparent",
      valueColor: "text-foreground",
    },
    aizome: {
      iconBg: "bg-gradient-to-br from-blue-500/25 via-indigo-500/20 to-sky-600/15 text-sky-400 border-blue-400/40 shadow-[0_0_16px_rgba(56,189,248,0.18)]",
      badge: "bg-blue-500/15 text-sky-400 border-blue-500/30",
      topAccent: "from-blue-400/60 via-indigo-500/30 to-transparent",
      valueColor: "text-foreground",
    },
    rose: {
      iconBg: "bg-gradient-to-br from-primary/25 via-primary/20 to-aizome-600/15 text-primary border-primary/40",
      badge: "bg-primary/15 text-primary border-primary/30",
      topAccent: "from-primary/60 via-primary/30 to-transparent",
      valueColor: "text-foreground",
    },
    indigo: {
      iconBg: "bg-gradient-to-br from-indigo-500/25 via-fuji-500/20 to-indigo-600/15 text-indigo-400 border-indigo-400/40",
      badge: "bg-indigo-500/15 text-indigo-400 border-indigo-500/30",
      topAccent: "from-indigo-400/60 via-fuji-500/30 to-transparent",
      valueColor: "text-foreground",
    },
    emerald: {
      iconBg: "bg-gradient-to-br from-emerald-500/25 via-teal-500/20 to-green-600/15 text-emerald-400 border-emerald-500/40",
      badge: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
      topAccent: "from-emerald-400/60 via-teal-500/30 to-transparent",
      valueColor: "text-foreground",
    },
    amber: {
      iconBg: "bg-gradient-to-br from-amber-500/25 via-orange-500/20 to-amber-600/15 text-amber-400 border-amber-400/40",
      badge: "bg-amber-500/15 text-amber-400 border-amber-500/30",
      topAccent: "from-amber-400/60 via-orange-500/30 to-transparent",
      valueColor: "text-foreground",
    },
  };

  const style = themes[color] || themes.kintsugi;

  return (
    <div
      className={cn(
        "relative rounded-[22px] border border-border/80 bg-card/95 washi-texture p-5 sm:p-5.5 min-h-[132px] flex flex-col justify-between transition-all duration-200 hover:border-border hover:shadow-sumi hover:-translate-y-0.5 group overflow-hidden",
        className
      )}
    >
      {/* Top Ambient Highlight Gradient */}
      <div className={cn("absolute top-0 left-0 right-0 h-[2.5px] bg-gradient-to-r opacity-90", style.topAccent)} />

      {/* Header Row: Title + Kanji Pill on left, Icon on right */}
      <div className="flex items-center justify-between gap-3 relative z-10">
        <div className="flex items-center gap-2 flex-wrap min-w-0">
          <span className="text-xs sm:text-[13px] font-bold text-muted-foreground tracking-tight whitespace-nowrap">
            {title}
          </span>
          <span
            className={cn(
              "text-[10px] font-jp font-bold px-2 py-0.5 rounded-full border tracking-wider shrink-0",
              style.badge
            )}
          >
            {jaTitle}
          </span>
        </div>

        {/* Icon Emblem Box */}
        <div
          className={cn(
            "h-10 w-10 sm:h-11 sm:w-11 rounded-2xl border flex items-center justify-center shrink-0 transition-transform duration-200 group-hover:scale-110 shadow-sm",
            style.iconBg
          )}
        >
          <Icon className="h-5 w-5" />
        </div>
      </div>

      {/* Main Value & Subtext Area */}
      <div className="space-y-1 relative z-10 mt-3">
        <div className="text-2xl sm:text-3xl font-black tracking-tight font-sans text-foreground leading-none">
          {value}
        </div>

        {subtext && (
          <p className="text-xs text-muted-foreground font-medium truncate pt-1">
            {subtext}
          </p>
        )}
      </div>
    </div>
  );
}
