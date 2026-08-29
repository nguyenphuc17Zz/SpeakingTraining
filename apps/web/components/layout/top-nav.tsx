"use client";

import React, { useState } from "react";
import { useHealth } from "@/hooks/use-health";
import { Badge } from "@/components/ui/badge";
import { ThemeToggle } from "@/components/theme-toggle";
import { WeatherToggle } from "@/components/ui/weather-toggle";
import { GlobalFuriganaControl } from "@/components/japanese/GlobalFuriganaControl";
import { GlobalKeybindingsModal } from "./global-keybindings-modal";
import { Search, Command, Keyboard } from "lucide-react";
import { soundFX } from "@/lib/sound-fx";

export function TopNav({ onOpenCommand }: { onOpenCommand?: () => void }) {
  const { health, dbHealth, loading } = useHealth();
  const isHealthy = health?.status === "healthy" && dbHealth?.connected;
  const [currentDate, setCurrentDate] = useState<string>("");
  const [jpDate, setJpDate] = useState<string>("");
  const [isKeybindingsOpen, setIsKeybindingsOpen] = useState(false);

  React.useEffect(() => {
    const now = new Date();
    setCurrentDate(
      now.toLocaleDateString("vi-VN", {
        day: "numeric",
        month: "short",
        weekday: "short",
      })
    );
    const jpDays = ["日", "月", "火", "水", "木", "金", "土"];
    setJpDate(`${now.getMonth() + 1}月${now.getDate()}日 (${jpDays[now.getDay()]})`);
  }, []);

  return (
    <>
      <header className="h-[58px] border-b border-border bg-card/85 backdrop-blur-md px-4 md:px-6 flex items-center justify-between shrink-0 gap-3 relative z-30">
        {/* Left — date + JLPT */}
        <div className="flex items-center gap-2 md:gap-3 min-w-0">
          <span className="hidden sm:flex items-center gap-2 text-sm">
            <span className="h-7 w-7 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center text-primary font-display font-bold text-xs shadow-sm">
              今
            </span>
            <span className="font-medium text-foreground text-xs sm:text-sm font-jp" suppressHydrationWarning>
              {jpDate || "8月25日"}
            </span>
            <span className="text-muted-foreground text-xs hidden lg:inline" suppressHydrationWarning>
              • {currentDate}
            </span>
          </span>
          <span className="hidden sm:block h-4 w-px bg-border/80" />
          <Badge variant="kintsugi" size="sm" className="shrink-0 font-jp gap-1">
            <span className="text-[10px]">目標</span> JLPT N3
          </Badge>
        </div>

        {/* Center — search trigger (desktop) */}
        <button
          onClick={onOpenCommand}
          className="hidden md:flex flex-1 max-w-[420px] items-center gap-2.5 px-3.5 py-2 rounded-xl bg-muted border border-border text-sm text-muted-foreground hover:text-foreground hover:bg-muted/80 transition-colors mx-4"
        >
          <Search className="h-4 w-4 shrink-0" />
          <span className="flex-1 text-left truncate">Tìm kiếm: hội thoại, shadowing, bài học…</span>
          <span className="hidden lg:flex items-center gap-1 text-xs bg-card border border-border px-1.5 py-0.5 rounded-md">
            <Command className="h-3 w-3" /> K
          </span>
        </button>

        {/* Right */}
        <div className="flex items-center gap-2 shrink-0">
          {/* Mobile search */}
          <button
            onClick={onOpenCommand}
            className="md:hidden h-9 w-9 rounded-xl bg-muted border border-border flex items-center justify-center text-muted-foreground"
            aria-label="Tìm kiếm"
          >
            <Search className="h-4 w-4" />
          </button>

          <span
            className={`hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${
              loading
                ? "bg-muted border-border text-muted-foreground"
                : isHealthy
                ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-700 dark:text-emerald-400"
                : "bg-amber-500/10 border-amber-500/20 text-amber-700 dark:text-amber-400"
            }`}
            title={isHealthy ? "Backend đã kết nối" : "Backend chưa kết nối — chạy uvicorn app.main:app"}
          >
            <span className={`h-2 w-2 rounded-full ${loading ? "bg-muted-foreground animate-pulse" : isHealthy ? "bg-emerald-500 animate-pulse" : "bg-amber-500"}`} />
            <span className="hidden lg:inline">{loading ? "Đang kết nối…" : isHealthy ? "Đã kết nối" : "Ngoại tuyến"}</span>
          </span>

          {/* Global Keybindings Shortcut Button in Header */}
          <button
            onClick={() => {
              soundFX.playFurin();
              setIsKeybindingsOpen(true);
            }}
            className="h-9 px-2.5 rounded-xl border border-border bg-muted/60 hover:bg-card hover:border-primary/50 text-xs font-semibold text-muted-foreground hover:text-foreground flex items-center gap-1.5 transition-all shadow-sm"
            title="Cài đặt phím tắt hệ thống (Q, C, L...)"
          >
            <Keyboard className="h-4 w-4 text-primary" />
            <span className="hidden xl:inline">Phím tắt</span>
          </button>

          <GlobalFuriganaControl />
          <WeatherToggle />
          <ThemeToggle />
        </div>
      </header>

      {/* Global Keybindings Settings Modal */}
      <GlobalKeybindingsModal
        isOpen={isKeybindingsOpen}
        onClose={() => setIsKeybindingsOpen(false)}
      />
    </>
  );
}
