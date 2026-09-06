"use client";

import React, { useState, useEffect, useMemo } from "react";
import { usePathname } from "next/navigation";
import { Keyboard, ChevronDown, ChevronUp, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { useSystemKeybindings, formatKeyDisplay } from "@/hooks/use-system-keybindings";
import { soundFX } from "@/lib/sound-fx";

interface ZenHotkeyDockProps {
  onOpenKeybindingsModal?: () => void;
  className?: string;
}

interface EventSpec {
  key: string;
  code: string;
  ctrlKey?: boolean;
  metaKey?: boolean;
  altKey?: boolean;
}

interface HotkeyBadge {
  keyDisplay: string;
  label: string;
  highlight?: boolean;
  eventSpec?: EventSpec;
}

function resolveEventSpec(rawKey: string): EventSpec {
  const lower = rawKey.toLowerCase();
  if (lower === "space" || lower === " ") return { key: " ", code: "Space" };
  if (lower === "enter") return { key: "Enter", code: "Enter" };
  if (lower === "escape" || lower === "esc") return { key: "Escape", code: "Escape" };
  if (lower.length === 1 && lower >= "a" && lower <= "z") {
    return { key: lower, code: `Key${lower.toUpperCase()}` };
  }
  if (lower.length === 1 && lower >= "0" && lower <= "9") {
    return { key: lower, code: `Digit${lower}` };
  }
  return { key: rawKey, code: rawKey };
}

export function ZenHotkeyDock({ onOpenKeybindingsModal, className }: ZenHotkeyDockProps) {
  const pathname = usePathname();
  const { keybindings } = useSystemKeybindings();
  const [collapsed, setCollapsed] = useState<boolean>(false);
  const [isMounted, setIsMounted] = useState(false);
  const [activePressedKey, setActivePressedKey] = useState<string | null>(null);

  useEffect(() => {
    setIsMounted(true);
    const saved = localStorage.getItem("hanasu-zen-dock-collapsed");
    if (saved === "1") {
      setCollapsed(true);
    }
  }, []);

  const toggleCollapse = () => {
    const next = !collapsed;
    setCollapsed(next);
    soundFX.playTaiko();
    localStorage.setItem("hanasu-zen-dock-collapsed", next ? "1" : "0");
  };

  const handleBadgeTrigger = (badge: HotkeyBadge) => {
    if (!badge.eventSpec) return;
    soundFX.playTaiko();

    setActivePressedKey(badge.keyDisplay);
    setTimeout(() => setActivePressedKey(null), 180);

    const event = new KeyboardEvent("keydown", {
      key: badge.eventSpec.key,
      code: badge.eventSpec.code,
      ctrlKey: badge.eventSpec.ctrlKey ?? false,
      metaKey: badge.eventSpec.metaKey ?? false,
      altKey: badge.eventSpec.altKey ?? false,
      bubbles: true,
      cancelable: true,
    });
    window.dispatchEvent(event);
  };

  // Determine current active mode badge list based on route
  const { modeTitle, badges } = useMemo(() => {
    if (!pathname) {
      return { modeTitle: "Toàn hệ thống", badges: [] };
    }

    if (pathname.startsWith("/reflex")) {
      const kSubmit = keybindings.reflexSubmitOrNext || "space";
      const kReplay = keybindings.reflexReplayModel || "p";
      const kRetry = keybindings.reflexRetry || "r";
      return {
        modeTitle: "Phản xạ (Reflex)",
        badges: [
          { keyDisplay: formatKeyDisplay(kSubmit), label: "Mic / Gửi bài", highlight: true, eventSpec: resolveEventSpec(kSubmit) },
          { keyDisplay: formatKeyDisplay(kReplay), label: "Nghe mẫu", eventSpec: resolveEventSpec(kReplay) },
          { keyDisplay: formatKeyDisplay(kRetry), label: "Luyện lại", eventSpec: resolveEventSpec(kRetry) },
          { keyDisplay: "F", label: "Furigana", eventSpec: { key: "f", code: "KeyF" } },
          { keyDisplay: "Esc", label: "Hủy / Thoát", eventSpec: { key: "Escape", code: "Escape" } },
        ],
      };
    }

    if (pathname.startsWith("/keigo")) {
      const kSubmit = keybindings.keigoSubmitOrNext || "space";
      const kReplay = keybindings.keigoReplayModel || "p";
      const kHint = keybindings.keigoToggleHint || "h";
      const kCheat = keybindings.keigoOpenCheatsheet || "c";
      return {
        modeTitle: "Kính ngữ (Keigo)",
        badges: [
          { keyDisplay: formatKeyDisplay(kSubmit), label: "Nộp bài", highlight: true, eventSpec: resolveEventSpec(kSubmit) },
          { keyDisplay: formatKeyDisplay(kReplay), label: "Nghe mẫu", eventSpec: resolveEventSpec(kReplay) },
          { keyDisplay: formatKeyDisplay(kHint), label: "Gợi ý", eventSpec: resolveEventSpec(kHint) },
          { keyDisplay: formatKeyDisplay(kCheat), label: "Bảng tra", eventSpec: resolveEventSpec(kCheat) },
          { keyDisplay: "F", label: "Furigana", eventSpec: { key: "f", code: "KeyF" } },
        ],
      };
    }

    if (pathname.startsWith("/pitch")) {
      const kSubmit = keybindings.pitchSubmitOrNext || "space";
      const kReplay = keybindings.pitchReplayModel || "p";
      const kMetro = keybindings.pitchMetronome || "m";
      const kRetry = keybindings.pitchRetry || "r";
      return {
        modeTitle: "Pitch Accent",
        badges: [
          { keyDisplay: formatKeyDisplay(kSubmit), label: "Phát âm / Nộp", highlight: true, eventSpec: resolveEventSpec(kSubmit) },
          { keyDisplay: formatKeyDisplay(kReplay), label: "Mẫu Tokyo", eventSpec: resolveEventSpec(kReplay) },
          { keyDisplay: formatKeyDisplay(kMetro), label: "Metronome", eventSpec: resolveEventSpec(kMetro) },
          { keyDisplay: formatKeyDisplay(kRetry), label: "Luyện lại", eventSpec: resolveEventSpec(kRetry) },
          { keyDisplay: "F", label: "Furigana", eventSpec: { key: "f", code: "KeyF" } },
        ],
      };
    }

    if (pathname.startsWith("/situations")) {
      const kSubmit = keybindings.situationsSubmitOrNext || "space";
      const kReplay = keybindings.situationsReplayModel || "p";
      const kHint = keybindings.situationsToggleHint || "h";
      const kRetry = keybindings.situationsRetry || "r";
      return {
        modeTitle: "Tình huống (Situations)",
        badges: [
          { keyDisplay: formatKeyDisplay(kSubmit), label: "Nói / Nộp bài", highlight: true, eventSpec: resolveEventSpec(kSubmit) },
          { keyDisplay: formatKeyDisplay(kReplay), label: "Nghe đối tác", eventSpec: resolveEventSpec(kReplay) },
          { keyDisplay: formatKeyDisplay(kHint), label: "Gợi ý", eventSpec: resolveEventSpec(kHint) },
          { keyDisplay: formatKeyDisplay(kRetry), label: "Làm lại", eventSpec: resolveEventSpec(kRetry) },
          { keyDisplay: "F", label: "Furigana", eventSpec: { key: "f", code: "KeyF" } },
        ],
      };
    }

    if (pathname.startsWith("/shadowing")) {
      const kMic = keybindings.toggleMic || "space";
      const kReplay = keybindings.replay || "r";
      const kPrev = keybindings.prevSegment || "j";
      const kNext = keybindings.nextSegment || "l";
      return {
        modeTitle: "Shadowing",
        badges: [
          { keyDisplay: formatKeyDisplay(kMic), label: "Mic / Play", highlight: true, eventSpec: resolveEventSpec(kMic) },
          { keyDisplay: formatKeyDisplay(kReplay), label: "Nghe lại đoạn", eventSpec: resolveEventSpec(kReplay) },
          { keyDisplay: formatKeyDisplay(kPrev), label: "Câu trước", eventSpec: resolveEventSpec(kPrev) },
          { keyDisplay: formatKeyDisplay(kNext), label: "Câu kế", eventSpec: resolveEventSpec(kNext) },
          { keyDisplay: "F", label: "Furigana", eventSpec: { key: "f", code: "KeyF" } },
        ],
      };
    }

    if (pathname.startsWith("/speaking") || pathname.startsWith("/ramp")) {
      const kMic = keybindings.speakingMic || "space";
      const kReplay = keybindings.speakingReplay || "p";
      const kHint = keybindings.speakingHint || "h";
      return {
        modeTitle: "Luyện nói (Speaking)",
        badges: [
          { keyDisplay: formatKeyDisplay(kMic), label: "Thu âm", highlight: true, eventSpec: resolveEventSpec(kMic) },
          { keyDisplay: "Enter", label: "Gửi câu trả lời", eventSpec: { key: "Enter", code: "Enter" } },
          { keyDisplay: formatKeyDisplay(kReplay), label: "Nghe AI nói", eventSpec: resolveEventSpec(kReplay) },
          { keyDisplay: formatKeyDisplay(kHint), label: "Gợi ý câu", eventSpec: resolveEventSpec(kHint) },
          { keyDisplay: "F", label: "Furigana", eventSpec: { key: "f", code: "KeyF" } },
        ],
      };
    }

    // Default global shortcuts
    return {
      modeTitle: "Phím tắt thông dụng",
      badges: [
        {
          keyDisplay: "⌘K / Ctrl+K",
          label: "Tìm kiếm nhanh",
          highlight: true,
          eventSpec: { key: "k", code: "KeyK", ctrlKey: true, metaKey: true },
        },
        {
          keyDisplay: "⌘J / Ctrl+J",
          label: "AI Coach",
          eventSpec: { key: "j", code: "KeyJ", ctrlKey: true, metaKey: true },
        },
        { keyDisplay: "F", label: "Đổi Furigana", eventSpec: { key: "f", code: "KeyF" } },
        { keyDisplay: "?", label: "Tất cả phím tắt", eventSpec: { key: "?", code: "Slash" } },
      ],
    };
  }, [pathname, keybindings]);

  if (!isMounted) return null;

  return (
    <aside
      aria-label="Zen Hotkey Dock"
      className={cn(
        "hidden md:flex fixed bottom-3 left-1/2 -translate-x-1/2 z-30 items-center transition-all duration-300 pointer-events-auto",
        className
      )}
    >
      {collapsed ? (
        <button
          onClick={toggleCollapse}
          className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-card/90 hover:bg-card border border-border/70 shadow-md backdrop-blur-md text-xs font-semibold text-muted-foreground hover:text-foreground hover:scale-105 transition-all group"
          title="Mở Zen Hotkey Dock"
        >
          <Keyboard className="w-3.5 h-3.5 text-primary group-hover:rotate-12 transition-transform" />
          <span className="font-mono text-[11px]">Phím tắt ({modeTitle})</span>
          <ChevronUp className="w-3.5 h-3.5 opacity-60 group-hover:opacity-100" />
        </button>
      ) : (
        <div className="flex items-center gap-2.5 px-3 py-1.5 rounded-full bg-card/90 border border-border/80 shadow-lg shadow-black/5 dark:shadow-black/25 backdrop-blur-md washi-texture animate-in fade-in slide-in-from-bottom-2 duration-300">
          <div className="flex items-center gap-1.5 pr-1.5 border-r border-border/70 shrink-0">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary/75 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-primary" />
            </span>
            <span className="text-[11px] font-bold text-foreground/90 whitespace-nowrap flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-amber-500 hidden lg:inline" />
              {modeTitle}
            </span>
          </div>

          <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar">
            {badges.map((badge, idx) => {
              const isPressed = activePressedKey === badge.keyDisplay;
              return (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleBadgeTrigger(badge)}
                  title={`Nhấp để kích hoạt: ${badge.label} (${badge.keyDisplay})`}
                  className={cn(
                    "flex items-center gap-1.5 px-2 py-0.5 rounded-md border text-[11px] transition-all shrink-0 select-none",
                    "hover:scale-105 active:scale-95 cursor-pointer focus:outline-none focus:ring-1 focus:ring-primary/40",
                    isPressed && "scale-95 ring-2 ring-primary bg-primary/20",
                    badge.highlight
                      ? "bg-primary/10 border-primary/30 text-primary font-medium shadow-xs hover:bg-primary/20"
                      : "bg-muted/50 border-border/60 text-muted-foreground hover:text-foreground hover:bg-muted"
                  )}
                >
                  <kbd
                    className={cn(
                      "px-1.5 py-0.2 rounded text-[10px] font-mono font-bold tracking-tight border shadow-xs transition-transform",
                      isPressed && "scale-90",
                      badge.highlight
                        ? "bg-primary text-primary-foreground border-primary"
                        : "bg-background/90 text-foreground border-border/80"
                    )}
                  >
                    {badge.keyDisplay}
                  </kbd>
                  <span className="whitespace-nowrap text-[11px] font-normal">{badge.label}</span>
                </button>
              );
            })}
          </div>

          {onOpenKeybindingsModal && (
            <button
              onClick={() => {
                soundFX.playFurin();
                onOpenKeybindingsModal();
              }}
              className="px-2 py-0.5 rounded text-[11px] font-mono text-muted-foreground hover:text-primary hover:bg-primary/10 transition-colors border border-transparent hover:border-primary/20 shrink-0 cursor-pointer"
              title="Xem và tùy biến tất cả phím tắt (?)"
            >
              Tùy biến
            </button>
          )}

          <button
            onClick={toggleCollapse}
            className="h-6 w-6 rounded-full flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-muted/80 transition-colors shrink-0 ml-0.5 cursor-pointer"
            title="Thu gọn dock"
          >
            <ChevronDown className="w-3.5 h-3.5" />
          </button>
        </div>
      )}
    </aside>
  );
}
