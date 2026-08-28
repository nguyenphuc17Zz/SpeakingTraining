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
    sakura: "bg-sakura-500/10 text-sakura-600 border-sakura-500/25 font-semibold",
    matcha: "bg-matcha-500/10 text-matcha-600 border-matcha-500/25 font-semibold",
    fuji: "bg-fuji-500/10 text-fuji-500 border-fuji-500/25 font-semibold",
    amber: "bg-amber-500/10 text-amber-600 border-amber-500/25 font-semibold",
    jlpt: "bg-gradient-to-r from-primary/10 via-accent/10 to-aizome-500/10 text-foreground border-primary/25 font-bold shadow-sm",
    akane: "bg-primary text-primary-foreground border-primary/60 font-bold shadow-sm",
    torii: "bg-primary/15 text-primary border-primary/30 font-bold",
    kintsugi: "bg-kintsugi-400/15 text-kintsugi-500 border-kintsugi-400/35 font-bold shadow-[0_0_10px_rgba(212,175,55,0.1)]",
    sumi: "bg-sumi-800/20 text-sumi-200 border-sumi-700 font-medium",
    aizome: "bg-aizome-500/15 text-aizome-400 border-aizome-500/30 font-semibold",
    washi: "bg-washi-100 text-foreground border-border font-medium",
    hanko: "hanko-badge !rounded-md !px-2 !py-0.5 !text-[10px] !tracking-widest",
  };

  const sizeStyles = {
    sm: "text-[11px] px-2.5 py-0.5",
    md: "text-xs px-3 py-1",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border font-medium tracking-wide select-none",
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
