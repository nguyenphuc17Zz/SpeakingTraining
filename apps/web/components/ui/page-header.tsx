"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { Badge } from "./badge";

interface PageHeaderProps {
  icon?: React.ReactNode;
  badge?: string;
  title: string;
  jaTitle?: string;
  description?: string;
  actions?: React.ReactNode;
  variant?: "default" | "washi" | "hero";
  className?: string;
}

export function PageHeader({
  icon,
  badge,
  title,
  jaTitle,
  description,
  actions,
  variant = "default",
  className,
}: PageHeaderProps) {
  if (variant === "hero") {
    return (
      <div
        className={cn(
          "relative overflow-hidden rounded-[24px] border border-border bg-card washi-texture shadow-washi-lg p-6 md:p-8",
          "dark:bg-gradient-to-br dark:from-card dark:via-card dark:to-muted/20",
          className
        )}
      >
        {/* Subtle enso gradient decoration */}
        <div className="absolute -top-20 -right-20 h-64 w-64 rounded-full bg-enso-gradient opacity-60 pointer-events-none" />
        <div className="absolute inset-0 shoji-grid opacity-[0.03] pointer-events-none" />

        <div className="relative flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-3 max-w-2xl">
            {badge && (
              <Badge variant="washi" size="sm" className="font-semibold">
                {badge}
              </Badge>
            )}
            <div className="flex items-start gap-3">
              {icon && (
                <span className="h-10 w-10 rounded-xl bg-primary/10 border border-primary/15 flex items-center justify-center text-primary shrink-0 mt-0.5">
                  {icon}
                </span>
              )}
              <div>
                <h1 className="text-xl md:text-2xl font-black tracking-tight text-foreground leading-tight">
                  {title}
                  {jaTitle && (
                    <span className="ml-2 text-sm font-medium text-muted-foreground font-jp">
                      {jaTitle}
                    </span>
                  )}
                </h1>
                {description && (
                  <p className="text-sm text-muted-foreground mt-2 leading-relaxed">
                    {description}
                  </p>
                )}
              </div>
            </div>
          </div>
          {actions && <div className="flex items-center gap-2 shrink-0">{actions}</div>}
        </div>
      </div>
    );
  }

  return (
    <div className={cn("flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-border", className)}>
      <div className="space-y-1.5">
        <div className="flex items-center gap-2.5">
          {icon && <span className="text-primary">{icon}</span>}
          <h1 className="text-xl font-bold tracking-tight text-foreground">
            {title}
            {jaTitle && <span className="ml-2 text-sm font-normal text-muted-foreground font-jp">{jaTitle}</span>}
          </h1>
          {badge && <Badge variant="outline" size="sm">{badge}</Badge>}
        </div>
        {description && <p className="text-sm text-muted-foreground leading-relaxed max-w-2xl">{description}</p>}
      </div>
      {actions && <div className="flex items-center gap-2 shrink-0 flex-wrap">{actions}</div>}
    </div>
  );
}
