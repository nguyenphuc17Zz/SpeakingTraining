"use client";

import React, { useRef, useEffect } from "react";
import { Mic, Send, Keyboard, X, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export interface ZenUnifiedInputBarProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  placeholder?: string;
  isRecording?: boolean;
  isEvaluating?: boolean;
  isPaused?: boolean;
  speechTranscript?: string;
  disabled?: boolean;
  autoFocus?: boolean;
  submitButtonText?: string;
  showOfficeBadge?: boolean;
  className?: string;
  hintText?: string;
}

export function ZenUnifiedInputBar({
  value,
  onChange,
  onSubmit,
  placeholder = "Nói vào micro hoặc gõ câu trả lời tiếng Nhật... (Nhấn Enter để gửi)",
  isRecording = false,
  isEvaluating = false,
  isPaused = false,
  speechTranscript,
  disabled = false,
  autoFocus = false,
  submitButtonText = "Gửi bài",
  showOfficeBadge = true,
  className,
  hintText,
}: ZenUnifiedInputBarProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  // Sync speech transcript if user spoke and field is empty
  useEffect(() => {
    if (speechTranscript && !value.trim()) {
      onChange(speechTranscript);
    }
  }, [speechTranscript, value, onChange]);

  useEffect(() => {
    if (autoFocus && !disabled && !isEvaluating) {
      inputRef.current?.focus();
    }
  }, [autoFocus, disabled, isEvaluating]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if ((value.trim() || speechTranscript?.trim()) && !isEvaluating && !disabled) {
        onSubmit();
      }
    }
  };

  const hasContent = Boolean(value.trim() || speechTranscript?.trim());
  const effectiveValue = value || speechTranscript || "";

  return (
    <div className={cn("w-full space-y-1.5", className)}>
      <div
        className={cn(
          "w-full rounded-2xl border bg-card/95 p-1.5 pl-3 shadow-xs flex items-center gap-2",
          "focus-within:ring-2 focus-within:ring-primary/30 focus-within:border-primary",
          "transition-all washi-texture backdrop-blur-sm",
          isRecording && "border-rose-500/50 bg-rose-500/5 ring-1 ring-rose-500/20",
          isEvaluating && "opacity-75 pointer-events-none"
        )}
      >
        {/* State Indicator Icon */}
        <div className="flex items-center gap-1.5 shrink-0">
          <span
            className={cn(
              "h-8 w-8 rounded-xl flex items-center justify-center transition-all duration-300",
              isRecording
                ? "bg-rose-500 text-white animate-pulse shadow-sm shadow-rose-500/30"
                : isPaused
                ? "bg-amber-500/10 text-amber-600 dark:text-amber-400"
                : hasContent
                ? "bg-primary/15 text-primary"
                : "bg-muted text-muted-foreground"
            )}
            title={
              isRecording
                ? "Đang thu âm microphone (bạn cũng có thể gõ đè nếu muốn)"
                : "Chế độ gõ phím / Sẵn sàng nhận câu trả lời"
            }
          >
            {isRecording ? (
              <Mic className="h-4 w-4" />
            ) : (
              <Keyboard className="h-4 w-4" />
            )}
          </span>
        </div>

        {/* Text Input Box */}
        <div className="relative flex-1 min-w-0 flex items-center">
          <input
            ref={inputRef}
            type="text"
            value={effectiveValue}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              isPaused
                ? "Đang tạm dừng — Tiếp tục để nộp bài..."
                : isRecording
                ? "Đang nghe... Bạn cũng có thể gõ câu trả lời vào đây..."
                : placeholder
            }
            disabled={disabled || isEvaluating}
            className="w-full bg-transparent text-sm md:text-base font-bold font-jp text-foreground placeholder:text-muted-foreground/60 placeholder:text-xs placeholder:font-normal focus:outline-none min-w-0 pr-6"
          />

          {/* Quick Clear button */}
          {value.length > 0 && !disabled && !isEvaluating && (
            <button
              type="button"
              onClick={() => onChange("")}
              className="absolute right-0 text-muted-foreground/60 hover:text-foreground p-1 transition-colors"
              title="Xóa chữ đã nhập"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        {/* Action Button */}
        <div className="flex items-center gap-1.5 shrink-0">
          <Button
            size="sm"
            variant="akane"
            onClick={onSubmit}
            disabled={!hasContent || disabled || isEvaluating}
            className={cn(
              "font-bold text-xs h-8 px-3.5 rounded-xl shadow-xs gap-1.5 transition-all",
              hasContent
                ? "bg-primary text-primary-foreground hover:bg-primary/90 hover:scale-[1.02]"
                : "opacity-60"
            )}
          >
            <Send className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">{submitButtonText}</span>
            <kbd className="hidden md:inline-block text-[9px] uppercase font-mono px-1 py-0.2 rounded bg-black/20 text-white/90">
              Enter
            </kbd>
          </Button>
        </div>
      </div>

      {/* Sub-label badge for office users */}
      <div className="flex items-center justify-between px-2 text-[11px] text-muted-foreground">
        {showOfficeBadge ? (
          <div className="flex items-center gap-1.5 text-muted-foreground/80">
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-emerald-500" />
            <span>🏢 <strong>Office / Broken Mic Mode</strong>: Gõ phím thay mic mọi lúc mọi nơi</span>
          </div>
        ) : (
          <span />
        )}
        {hintText && (
          <span className="italic text-primary/80 flex items-center gap-1">
            <Sparkles className="h-3 w-3" />
            {hintText}
          </span>
        )}
      </div>
    </div>
  );
}
