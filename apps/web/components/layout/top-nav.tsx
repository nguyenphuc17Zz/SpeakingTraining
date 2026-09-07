"use client";

import React, { useState } from "react";
import { useHealth } from "@/hooks/use-health";
import { Badge } from "@/components/ui/badge";
import { ThemeToggle } from "@/components/theme-toggle";
import { SoundToggle } from "@/components/ui/sound-toggle";
import { GlobalFuriganaControl } from "@/components/japanese/GlobalFuriganaControl";
import { GlobalKeybindingsModal } from "./global-keybindings-modal";
import { Search, Command, Keyboard, Sparkles } from "lucide-react";
import { soundFX } from "@/lib/sound-fx";

export function TopNav({
  onOpenCommand,
  onOpenCoach,
}: {
  onOpenCommand?: () => void;
  onOpenCoach?: () => void;
}) {
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
      <header className="h-[56px] border-b border-border/70 bg-card/90 backdrop-blur-md px-4 md:px-6 flex items-center justify-between shrink-0 gap-3 relative z-30">
        {/* Left — date + JLPT */}
        <div className="flex items-center gap-2 md:gap-3 min-w-0">
          <span className="hidden sm:flex items-center gap-2 text-sm">
            <span className="font-medium text-foreground text-xs sm:text-sm font-jp" suppressHydrationWarning>
              {jpDate || "8月25日"}
            </span>
            <span className="text-muted-foreground text-xs hidden lg:inline" suppressHydrationWarning>
              • {currentDate}
            </span>
          </span>
          <span className="hidden sm:block h-4 w-px bg-border/80" />
          <span className="text-xs font-medium text-muted-foreground bg-muted/60 px-2 py-0.5 rounded-md border border-border/60 font-jp shrink-0">
            JLPT N3
          </span>
        </div>

        {/* Center — search trigger (desktop) */}
        <button
          onClick={onOpenCommand}
          className="hidden md:flex flex-1 max-w-[380px] items-center gap-2.5 px-3.5 py-1.5 rounded-xl bg-muted/60 border border-border/70 text-xs text-muted-foreground hover:text-foreground hover:bg-muted transition-colors mx-4"
        >
          <Search className="h-3.5 w-3.5 shrink-0" />
          <span className="flex-1 text-left truncate">Tìm kiếm nhanh…</span>
          <span className="hidden lg:flex items-center gap-1 text-[10px] bg-background border border-border/80 px-1.5 py-0.5 rounded-md font-mono">
            ⌘K
          </span>
        </button>

        {/* Right */}
        <div className="flex items-center gap-2 shrink-0">
          {/* Mobile search */}
          <button
            onClick={onOpenCommand}
            className="md:hidden h-9 w-9 rounded-xl bg-muted/60 border border-border flex items-center justify-center text-muted-foreground"
            aria-label="Tìm kiếm"
          >
            <Search className="h-4 w-4" />
          </button>

          {/* AI Coach clean trigger */}
          <button
            onClick={onOpenCoach}
            className="h-8 px-2.5 rounded-lg border border-border/80 bg-muted/50 hover:bg-card hover:border-primary/40 text-xs font-semibold text-foreground flex items-center gap-1.5 transition-all shadow-xs"
            title="Mở AI Coach (⌘J)"
          >
            <Sparkles className="h-3.5 w-3.5 text-primary" />
            <span className="hidden sm:inline">AI Coach</span>
            <span className="hidden xl:inline text-[10px] text-muted-foreground font-mono bg-background px-1 py-0.2 rounded border border-border/60">
              ⌘J
            </span>
          </button>

          {/* Connection status indicator */}
          <div
            className="h-8 px-2 rounded-lg bg-muted/40 border border-border/60 flex items-center gap-1.5 text-xs text-muted-foreground"
            title={isHealthy ? "Hệ thống sẵn sàng" : "Backend ngoại tuyến"}
          >
            <span className={`h-2 w-2 rounded-full ${loading ? "bg-muted-foreground animate-pulse" : isHealthy ? "bg-emerald-500" : "bg-amber-500"}`} />
            <span className="hidden 2xl:inline text-[11px]">{isHealthy ? "Online" : "Offline"}</span>
          </div>

          {/* Keybindings Shortcut Button */}
          <button
            onClick={() => {
              soundFX.playFurin();
              setIsKeybindingsOpen(true);
            }}
            className="h-8 w-8 rounded-lg border border-border/80 bg-muted/40 hover:bg-card hover:border-primary/40 text-muted-foreground hover:text-foreground flex items-center justify-center transition-all"
            title="Phím tắt hệ thống (?)"
          >
            <Keyboard className="h-3.5 w-3.5" />
          </button>

          <GlobalFuriganaControl />
          <SoundToggle />
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
