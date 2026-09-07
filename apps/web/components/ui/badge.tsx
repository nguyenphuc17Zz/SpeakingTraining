import React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?:
    | "default"
    | "secondary"
    | "outline"
    | "sakura"
    | "matcha"
    | "fuji"
    | "amber"
    | "jlpt"
    | "akane"
    | "washi"
    | "hanko"
    | "kintsugi"
    | "torii"
    | "sumi"
    | "aizome";
  size?: "sm" | "md";
}

export function Badge({
  className,
  variant = "default",
  size = "md",
  children,
  ...props
}: BadgeProps) {
  const variantStyles = {
    default: "bg-muted text-foreground border-border",
    secondary: "bg-secondary text-secondary-foreground border-transparent",
    outline: "bg-transparent text-muted-foreground border-border",
    sakura: "bg-muted text-foreground border-border font-medium",
    matcha: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20 font-medium",
    fuji: "bg-muted text-foreground border-border font-medium",
    amber: "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20 font-medium",
    jlpt: "bg-muted text-foreground border-border font-semibold",
    akane: "bg-primary text-primary-foreground border-primary font-medium",
    torii: "bg-primary/10 text-primary border-primary/20 font-medium",
    kintsugi: "bg-muted text-foreground border-border font-medium",
    sumi: "bg-muted text-foreground border-border font-medium",
    aizome: "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20 font-medium",
    washi: "bg-muted text-foreground border-border font-medium",
    hanko: "bg-muted text-muted-foreground border-border font-medium",
  };

  const sizeStyles = {
    sm: "text-[11px] px-2 py-0.5",
    md: "text-xs px-2.5 py-0.5",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-md border text-xs font-medium select-none",
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}
