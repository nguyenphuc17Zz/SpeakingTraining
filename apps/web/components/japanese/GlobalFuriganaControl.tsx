"use client";

import React, { useState } from "react";
import {
  useFuriganaSettings,
  FuriganaColorId,
  FURIGANA_COLORS,
} from "@/hooks/use-furigana-settings";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { soundFX } from "@/lib/sound-fx";
import { Sparkles, Palette, Eye, EyeOff, BookOpen, Settings2 } from "lucide-react";
import { cn } from "@/lib/utils";

export function GlobalFuriganaControl() {
  const {
    colorId,
    changeColor,
    activeHex,
    changeCustomColor,
    displayMode,
    setDisplayMode,
    options,
  } = useFuriganaSettings();

  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative inline-block">
      {/* Trigger Pill */}
      <button
        type="button"
        onClick={() => {
          soundFX.playFurin();
          setIsOpen((prev) => !prev);
        }}
        className={cn(
          "flex items-center gap-1.5 px-2.5 py-1 rounded-xl text-xs font-bold border transition-all shadow-2xs",
          isOpen
            ? "bg-primary text-primary-foreground border-primary"
            : "bg-card border-border/80 text-muted-foreground hover:text-foreground hover:border-primary/40"
        )}
        title="Tùy chỉnh hiển thị phiên âm Furigana toàn hệ thống"
      >
        <span className="font-jp text-primary font-black">ふ</span>
        <span className="hidden sm:inline text-[11px]">Furigana</span>
        <span
          className="w-2.5 h-2.5 rounded-full border border-black/10 shadow-2xs"
          style={{ backgroundColor: activeHex }}
        />
      </button>

      {/* Popover */}
      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 top-full mt-2 z-50 w-72 p-4 rounded-2xl bg-card border border-border/80 shadow-2xl washi-texture space-y-3.5 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between border-b border-border/60 pb-2">
              <span className="text-xs font-bold text-foreground flex items-center gap-1.5">
                <Settings2 className="h-3.5 w-3.5 text-primary" />
                <span>Phiên Âm Furigana Toàn Hệ Thống</span>
              </span>
              <Badge variant="outline" size="sm" className="text-[9px] font-mono">
                GLOBAL
              </Badge>
            </div>

            {/* Display Mode 3 Tabs */}
            <div className="space-y-1.5">
              <span className="text-[10px] text-muted-foreground font-semibold uppercase">Chế độ hiển thị:</span>
              <div className="grid grid-cols-3 gap-1 p-1 rounded-xl bg-muted/40 border border-border/60">
                <button
                  type="button"
                  onClick={() => {
                    soundFX.playFurin();
                    setDisplayMode("kanji_reading");
                  }}
                  className={cn(
                    "py-1.5 rounded-lg text-[10px] font-bold transition-all text-center",
                    displayMode === "kanji_reading"
                      ? "bg-primary text-primary-foreground shadow-2xs"
                      : "text-muted-foreground hover:text-foreground"
                  )}
                >
                  🌸 Đầy đủ
                </button>
                <button
                  type="button"
                  onClick={() => {
                    soundFX.playFurin();
                    setDisplayMode("kanji");
                  }}
                  className={cn(
                    "py-1.5 rounded-lg text-[10px] font-bold transition-all text-center",
                    displayMode === "kanji"
                      ? "bg-primary text-primary-foreground shadow-2xs"
                      : "text-muted-foreground hover:text-foreground"
                  )}
                >
                  🏯 Chỉ Kanji
                </button>
                <button
                  type="button"
                  onClick={() => {
                    soundFX.playFurin();
                    setDisplayMode("hidden");
                  }}
                  className={cn(
                    "py-1.5 rounded-lg text-[10px] font-bold transition-all text-center",
                    displayMode === "hidden"
                      ? "bg-primary text-primary-foreground shadow-2xs"
                      : "text-muted-foreground hover:text-foreground"
                  )}
                >
                  🎧 Ẩn chữ
                </button>
              </div>
            </div>

            {/* Color Palette */}
            <div className="space-y-1.5">
              <span className="text-[10px] text-muted-foreground font-semibold uppercase">Màu sắc Furigana:</span>
              <div className="grid grid-cols-3 gap-1.5">
                {options.map((opt) => (
                  <button
                    key={opt.id}
                    type="button"
                    onClick={() => {
                      soundFX.playSuikinkutsu();
                      changeColor(opt.id);
                    }}
                    className={cn(
                      "p-1.5 rounded-xl border flex items-center gap-1.5 text-[10px] font-semibold transition-all text-left",
                      colorId === opt.id
                        ? "border-primary bg-primary/10 shadow-2xs text-foreground font-bold"
                        : "border-border/60 bg-card text-muted-foreground hover:text-foreground"
                    )}
                  >
                    <span
                      className="w-3 h-3 rounded-full border border-black/10 shrink-0"
                      style={{ backgroundColor: opt.hex }}
                    />
                    <span className="truncate">{opt.name.split(" ")[0]}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
