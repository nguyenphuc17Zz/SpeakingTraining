"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { Button } from "./button";
import { Sparkles, Compass, Inbox } from "lucide-react";

interface EmptyStateProps {
  icon?: React.ComponentType<{ className?: string }>;
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  variant?: "default" | "washi" | "enso";
  className?: string;
}

export function EmptyState({
  icon: Icon = Inbox,
  title,
  description,
  actionLabel,
  onAction,
  variant = "washi",
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center text-center p-8 md:p-10 rounded-2xl border",
        variant === "washi" && "bg-card washi-texture border-border shadow-washi",
        variant === "enso" && "bg-card border-border shadow-enso relative overflow-hidden",
        variant === "default" && "bg-muted/40 border-border/60",
        className
      )}
    >
      {/* Enso decoration */}
      <div className="relative mb-4">
        <div className="absolute inset-0 rounded-full border-2 border-dashed border-border opacity-40 scale-110" />
        <div className="relative h-16 w-16 rounded-2xl bg-primary/8 border border-primary/15 flex items-center justify-center">
          <Icon className="h-7 w-7 text-primary/70" />
        </div>
        <span className="absolute -top-1 -right-1 h-6 w-6 rounded-full bg-gradient-to-br from-rose-400 to-indigo-500 flex items-center justify-center text-[10px] text-white shadow-sm">
          話
        </span>
      </div>

      <h3 className="text-sm font-bold text-foreground">{title}</h3>
      {description && (
        <p className="text-sm text-muted-foreground mt-1.5 max-w-sm leading-relaxed">
          {description}
        </p>
      )}

      {actionLabel && onAction && (
        <Button variant="akane" size="sm" className="mt-5" onClick={onAction}>
          <Sparkles className="h-3.5 w-3.5" />
          {actionLabel}
        </Button>
      )}

      {!actionLabel && (
        <p className="text-xs text-muted-foreground/70 mt-3 flex items-center gap-1">
          <Compass className="h-3 w-3" /> Tiếp tục luyện tập để lấp đầy không gian này
        </p>
      )}
    </div>
  );
}
