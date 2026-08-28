import React from "react";
import { cn } from "@/lib/utils";

export interface HankoStampProps extends React.HTMLAttributes<HTMLDivElement> {
  text?: string;
  subtext?: string;
  variant?: "primary" | "torii" | "gold" | "matcha" | "aizome";
  shape?: "square" | "circle" | "badge";
  size?: "sm" | "md" | "lg";
  animate?: boolean;
}

export function HankoStamp({
  text = "合格",
  subtext,
  variant = "primary",
  shape = "square",
  size = "md",
  animate = false,
  className,
  ...props
}: HankoStampProps) {
  const variantStyles = {
    primary: "text-primary border-primary bg-primary/10 shadow-[inset_0_0_0_1px_rgba(16,185,129,0.2)]",
    torii: "text-primary border-primary bg-primary/10 shadow-[inset_0_0_0_1px_rgba(16,185,129,0.2)]",
    gold: "text-[#d4af37] border-[#d4af37] bg-[#d4af37]/10 shadow-[inset_0_0_0_1px_rgba(212,175,55,0.2)]",
    matcha: "text-[#10b981] border-[#10b981] bg-[#10b981]/10 shadow-[inset_0_0_0_1px_rgba(16,185,129,0.2)]",
    aizome: "text-[#60a5fa] border-[#60a5fa] bg-[#60a5fa]/10 shadow-[inset_0_0_0_1px_rgba(96,165,250,0.2)]",
  };

  const shapeStyles = {
    square: "rounded-md",
    circle: "rounded-full aspect-square",
    badge: "rounded-lg",
  };

  const sizeStyles = {
    sm: "text-[10px] px-1.5 py-0.5 border-[1.5px] font-extrabold",
    md: "text-xs px-2.5 py-1 border-[2px] font-black",
    lg: "text-sm px-3.5 py-1.5 border-[2px] font-black",
  };

  return (
    <div
      className={cn(
        "inline-flex flex-col items-center justify-center font-display select-none tracking-widest leading-none",
        "transform -rotate-2 hover:rotate-0 hover:scale-105 transition-all duration-200",
        variantStyles[variant],
        shapeStyles[shape],
        sizeStyles[size],
        animate && "animate-in zoom-in-50 duration-300",
        className
      )}
      title={`Hanko: ${text}${subtext ? ` (${subtext})` : ""}`}
      {...props}
    >
      <span className="font-display font-black">{text}</span>
      {subtext && (
        <span className="text-[8px] font-sans font-semibold tracking-normal mt-0.5 opacity-90">
          {subtext}
        </span>
      )}
    </div>
  );
}
