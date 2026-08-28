"use client";

import React, { useState, useRef, useEffect } from "react";
import { Sparkles, Check, ChevronDown, Palette } from "lucide-react";
import { useTheme, JapaneseThemeId } from "./theme-provider";
import { cn } from "@/lib/utils";

export function ThemeToggle({ className }: { className?: string }) {
  const { theme, activeThemeMeta, themes, setTheme } = useTheme();
  const [isOpen, setIsOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Close on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen]);

  const displayMeta = (mounted && activeThemeMeta) || themes[0];

  return (
    <div className={cn("relative inline-block text-left", className)} ref={dropdownRef}>
      {/* Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Thay đổi phong cách giao diện Nhật Bản"
        aria-expanded={isOpen}
        className={cn(
          "h-9 px-2.5 sm:px-3 rounded-xl border flex items-center justify-center gap-2 text-xs font-semibold transition-all duration-200",
          "bg-card/90 hover:bg-muted border-border text-foreground shadow-sm hover:shadow-md",
          "focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/40",
          isOpen && "ring-2 ring-primary/40 border-primary/50"
        )}
        title={`Giao diện hiện tại: ${displayMeta.name} (${displayMeta.kanji})`}
        suppressHydrationWarning
      >
        <span className="text-sm leading-none" suppressHydrationWarning>{displayMeta.emoji}</span>
        <span className="hidden md:inline-flex items-center gap-1.5 font-jp" suppressHydrationWarning>
          <span className="font-bold">{displayMeta.name}</span>
          <span className="text-[10px] text-muted-foreground">({displayMeta.kanji})</span>
        </span>
        <span
          className="w-2.5 h-2.5 rounded-full border border-black/10 shrink-0"
          style={{ backgroundColor: displayMeta.primaryColor }}
          suppressHydrationWarning
        />
        <ChevronDown className={cn("h-3.5 w-3.5 text-muted-foreground transition-transform duration-200", isOpen && "rotate-180")} />
      </button>

      {/* Japanese Theme Dropdown Popover */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-72 sm:w-80 rounded-2xl border border-border bg-card/95 backdrop-blur-xl shadow-sumi-lg p-2 z-50 animate-in fade-in zoom-in-95 duration-150">
          <div className="px-3 py-2 border-b border-border/70 flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-xs font-bold text-foreground">
              <Palette className="h-3.5 w-3.5 text-primary" />
              <span>Phong cách Nhật Bản</span>
              <span className="text-[10px] font-jp text-muted-foreground font-normal">和風テーマ</span>
            </div>
            <span className="text-[10px] font-medium text-muted-foreground bg-muted px-1.5 py-0.5 rounded-md">
              4 giao diện
            </span>
          </div>

          <div className="mt-1 space-y-1">
            {themes.map((t) => {
              const isActive = theme === t.id;
              return (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => {
                    setTheme(t.id as JapaneseThemeId);
                    setIsOpen(false);
                  }}
                  className={cn(
                    "w-full text-left p-2.5 rounded-xl border transition-all flex items-start gap-2.5 group",
                    isActive
                      ? "bg-primary/10 border-primary/30 shadow-sm"
                      : "border-transparent hover:bg-muted/70 hover:border-border/60"
                  )}
                >
                  <span className="text-lg leading-none mt-0.5 shrink-0">{t.emoji}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-1">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="text-xs font-bold text-foreground">{t.name}</span>
                        <span className="text-[10px] font-jp font-semibold text-primary">{t.kanji}</span>
                      </div>
                      <div className="flex items-center gap-1 shrink-0">
                        {/* Theme Swatch Dots */}
                        <span
                          className="w-2.5 h-2.5 rounded-full border border-black/20"
                          style={{ backgroundColor: t.bgHex }}
                          title={`Màu nền: ${t.bgHex}`}
                        />
                        <span
                          className="w-2.5 h-2.5 rounded-full border border-black/20"
                          style={{ backgroundColor: t.primaryColor }}
                          title={`Màu nhấn: ${t.primaryColor}`}
                        />
                        <span
                          className="w-2.5 h-2.5 rounded-full border border-black/20"
                          style={{ backgroundColor: t.accentColor }}
                          title={`Màu phụ: ${t.accentColor}`}
                        />
                        {isActive && <Check className="h-3.5 w-3.5 text-primary ml-1 shrink-0" />}
                      </div>
                    </div>
                    <p className="text-[11px] font-medium text-muted-foreground mt-0.5 line-clamp-1">
                      {t.subtitle}
                    </p>
                    <p className="text-[10px] text-muted-foreground/80 leading-relaxed mt-0.5">
                      {t.description}
                    </p>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
