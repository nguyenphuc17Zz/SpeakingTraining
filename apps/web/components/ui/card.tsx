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
    default: "bg-card border-border shadow-xs",
    washi: "bg-card border-border shadow-xs",
    enso: "bg-card border-border shadow-xs",
    seigaiha: "bg-card border-border shadow-xs",
    kintsugi: "bg-card border-border shadow-xs",
    sumi: "bg-card border-border shadow-xs",
    glass: "bg-card/90 backdrop-blur-md border-border shadow-xs",
  };

  return (
    <div
      className={cn(
        "rounded-xl border transition-colors duration-150",
        variantStyles[effectiveVariant],
        hoverable && "hover:border-foreground/20 cursor-pointer",
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
