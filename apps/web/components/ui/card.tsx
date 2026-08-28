import React from "react";
import { cn } from "@/lib/utils";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "washi" | "enso" | "glass" | "seigaiha" | "kintsugi" | "sumi";
  hoverable?: boolean;
  padded?: boolean;
  /** @deprecated use variant="glass" */
  glass?: boolean;
}

export function Card({
  className,
  variant = "default",
  hoverable = false,
  padded = false,
  glass,
  children,
  ...props
}: CardProps) {
  const effectiveVariant = glass ? "glass" : variant;
  const variantStyles = {
    default: "bg-card border-border shadow-sm",
    washi:
      "bg-card/90 border-border shadow-washi washi-texture backdrop-blur-sm",
    enso:
      "bg-card/90 border-border shadow-enso washi-texture relative overflow-hidden before:absolute before:inset-0 before:bg-enso-gradient before:opacity-50 before:pointer-events-none",
    seigaiha:
      "bg-card/90 border-border shadow-washi seigaiha-pattern relative overflow-hidden backdrop-blur-sm",
    kintsugi:
      "bg-card/95 border-kintsugi-400/40 shadow-kintsugi washi-texture relative overflow-hidden",
    sumi:
      "bg-card border-border shadow-sumi backdrop-blur-md",
    glass:
      "bg-card/75 backdrop-blur-md border-border/80 shadow-lg",
  };

  return (
    <div
      className={cn(
        "rounded-2xl border transition-all duration-200",
        variantStyles[effectiveVariant],
        hoverable && "hover:border-primary/30 hover:shadow-sumi hover:-translate-y-0.5 cursor-pointer",
        padded && "p-5",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("p-5 pb-3 flex flex-col gap-1.5", className)} {...props}>
      {children}
    </div>
  );
}

export function CardTitle({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn("text-[15px] font-bold text-foreground tracking-tight", className)}
      {...props}
    >
      {children}
    </h3>
  );
}

export function CardDescription({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p className={cn("text-sm text-muted-foreground leading-relaxed", className)} {...props}>
      {children}
    </p>
  );
}

export function CardContent({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("p-5 pt-0", className)} {...props}>
      {children}
    </div>
  );
}

export function CardFooter({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("p-5 pt-4 border-t border-border/60 flex items-center justify-between", className)}
      {...props}
    >
      {children}
    </div>
  );
}
