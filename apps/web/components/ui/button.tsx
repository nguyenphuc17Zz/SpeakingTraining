import React from "react";
import { cn } from "@/lib/utils";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "danger" | "sakura" | "akane" | "washi" | "kintsugi" | "torii" | "sumi";
  size?: "sm" | "md" | "lg" | "icon";
  isLoading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = "primary",
      size = "md",
      isLoading = false,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    const baseStyles =
      "inline-flex items-center justify-center font-medium rounded-xl transition-all duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:opacity-50 disabled:cursor-not-allowed select-none active:scale-[0.98] min-h-[40px]";

    const variantStyles = {
      primary:
        "bg-primary hover:opacity-95 text-primary-foreground shadow-sm hover:shadow-md border border-transparent font-semibold",
      secondary:
        "bg-secondary hover:bg-secondary/80 text-secondary-foreground border border-border",
      outline:
        "bg-card hover:bg-muted text-foreground border border-border hover:border-foreground/20",
      ghost:
        "bg-transparent hover:bg-muted text-muted-foreground hover:text-foreground",
      danger:
        "bg-red-600 hover:bg-red-500 text-white shadow-sm",
      sakura:
        "bg-primary/90 hover:bg-primary text-primary-foreground shadow-md font-semibold border border-transparent",
      akane:
        "bg-primary hover:bg-primary/90 text-primary-foreground shadow-md shadow-primary/20 font-semibold border border-transparent",
      torii:
        "bg-primary hover:bg-primary/90 text-primary-foreground shadow-md shadow-primary/25 font-semibold border border-transparent",
      kintsugi:
        "bg-gradient-to-r from-kintsugi-500 to-amber-500 hover:from-kintsugi-400 hover:to-amber-400 text-black font-bold shadow-kintsugi border border-kintsugi-400/40",
      sumi:
        "bg-sumi-850 hover:bg-sumi-800 text-sumi-50 border border-sumi-700 shadow-sumi font-semibold",
      washi:
        "bg-washi-50 hover:bg-washi-100 text-foreground border border-border shadow-washi",
    };

    const sizeStyles = {
      sm: "text-xs px-3.5 py-2 gap-1.5 min-h-[36px] rounded-lg",
      md: "text-sm px-5 py-2.5 gap-2",
      lg: "text-sm px-7 py-3 gap-2.5 rounded-2xl",
      icon: "p-2.5 aspect-square min-h-[40px] min-w-[40px]",
    };

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(
          baseStyles,
          variantStyles[variant],
          sizeStyles[size],
          className
        )}
        {...props}
      >
        {isLoading && (
          <svg
            className="animate-spin -ml-1 mr-2 h-4 w-4 text-current"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        )}
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";
