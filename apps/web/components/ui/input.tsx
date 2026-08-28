import React from "react";
import { cn } from "@/lib/utils";

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: React.ReactNode;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type = "text", label, error, helperText, id, ...props }, ref) => {
    const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, "-") : undefined);

    return (
      <div className="flex flex-col gap-1.5 w-full">
        {label && (
          <label
            htmlFor={inputId}
            className="text-xs font-semibold text-foreground select-none"
          >
            {label}
          </label>
        )}
        <input
          id={inputId}
          type={type}
          ref={ref}
          className={cn(
            "flex h-9 w-full rounded-lg border bg-background/80 px-3 py-1 text-sm text-foreground placeholder:text-muted-foreground transition-colors duration-150 file:border-0 file:bg-transparent file:text-sm file:font-medium focus:outline-none focus:ring-1 focus:ring-rose-500/50 disabled:cursor-not-allowed disabled:opacity-50",
            error
              ? "border-rose-500 focus:border-rose-500"
              : "border-border focus:border-slate-600",
            className
          )}
          {...props}
        />
        {error && <p className="text-[11px] text-rose-400 font-medium">{error}</p>}
        {helperText && !error && (
          <p className="text-[11px] text-muted-foreground">{helperText}</p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";
