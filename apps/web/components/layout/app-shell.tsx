"use client";

import React, { useEffect, useState } from "react";
import { Sidebar } from "./sidebar";
import { TopNav } from "./top-nav";
import { BottomNav } from "./bottom-nav";
import { AtmosphericWeatherEngine } from "@/components/ui/atmospheric-weather-engine";
import { useRewardNotifications, RewardToast } from "@/features/gamification";
import { CoachFloatingButton, CoachPanel } from "@/features/coach";
import { useCoachProactive } from "@/features/coach/hooks/useCoachProactive";
import { SelectionLookupBubble, AIVocabularyLookupBox } from "@/features/vocabulary-lookup";
import { Menu, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useSystemKeybindings } from "@/hooks/use-system-keybindings";
import { useFuriganaSettings } from "@/hooks/use-furigana-settings";
import {
  LayoutDashboard,
  Mic,
  Tv,
  Zap,
  Crown,
  Music,
  Compass,
  Sparkles,
  TrendingUp,
  Brain,
  Swords,
  Settings,
} from "lucide-react";

const MOBILE_NAV = [
  { href: "/dashboard", label: "Trang chủ", ja: "ホーム", icon: LayoutDashboard },
  { href: "/speaking", label: "Luyện nói", ja: "会話", icon: Mic },
  { href: "/reflex", label: "Phản xạ", ja: "瞬発", icon: Zap },
  { href: "/keigo", label: "Kính ngữ", ja: "敬語", icon: Crown },
  { href: "/pitch", label: "Cao độ", ja: "高低", icon: Music },
  { href: "/situations", label: "Tình huống", ja: "場面", icon: Compass },
  { href: "/shadowing", label: "Shadowing", ja: "シャドーイング", icon: Tv },
  { href: "/learning", label: "Lộ trình học", ja: "学習", icon: Zap },
  { href: "/coach", label: "AI Coach", ja: "コーチ", icon: Sparkles },
  { href: "/progress", label: "Tiến độ", ja: "進捗", icon: TrendingUp },
  { href: "/profile", label: "Hồ sơ", ja: "カルテ", icon: Brain },
  { href: "/game", label: "Dojo", ja: "道場", icon: Swords },
  { href: "/settings", label: "Cài đặt", ja: "設定", icon: Settings },
];

function MobileDrawer({ open, onClose }: { open: boolean; onClose: () => void }) {
  const pathname = usePathname();
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 md:hidden">
      <button aria-label="Đóng menu" onClick={onClose} className="absolute inset-0 bg-black/40 backdrop-blur-sm" />
      <div className="absolute left-0 top-0 bottom-0 w-[84%] max-w-[300px] bg-card border-r border-border flex flex-col overflow-hidden shadow-2xl">
        <div className="h-[56px] flex items-center justify-between px-4 border-b border-border shrink-0">
          <Link href="/dashboard" onClick={onClose} className="flex items-center gap-2.5">
            <span className="h-9 w-9 rounded-xl bg-gradient-to-br from-akane-500 to-primary flex items-center justify-center text-white font-black">話</span>
            <span className="font-extrabold text-sm text-foreground">HANASU AI</span>
          </Link>
          <button onClick={onClose} className="h-9 w-9 rounded-xl bg-muted flex items-center justify-center">
            <X className="h-4 w-4" />
          </button>
        </div>
        <nav className="flex-1 overflow-y-auto p-3 flex flex-col gap-1">
          {MOBILE_NAV.map((it) => {
            const Icon = it.icon;
            const active = pathname === it.href || (it.href !== "/dashboard" && pathname.startsWith(it.href));
            return (
              <Link
                key={it.href}
                href={it.href}
                onClick={onClose}
                className={cn(
                  "flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-medium border",
                  active ? "bg-primary/10 text-primary border-primary/15" : "text-muted-foreground border-transparent hover:bg-muted hover:text-foreground"
                )}
              >
                <span className="flex items-center gap-2.5"><Icon className="h-4 w-4" />{it.label}</span>
                <span className="text-xs font-jp text-muted-foreground/70">{it.ja}</span>
              </Link>
            );
          })}
        </nav>
      </div>
    </div>
  );
}

function CommandPalette({ open, onClose, onAskCoach }: { open: boolean; onClose: () => void; onAskCoach?: (q: string) => void }) {
  const [q, setQ] = useState("");
  const items = [
    { label: "Trang chủ", href: "/dashboard", desc: "Tổng quan & nhiệm vụ hôm nay" },
    { label: "Luyện nói", href: "/speaking", desc: "Phòng hội thoại với AI" },
    { label: "Phản xạ", href: "/reflex", desc: "瞬発力スピーキング — Speed Reflex 4 kiểu" },
    { label: "Kính ngữ", href: "/keigo", desc: "敬語・タメ口特訓 — Keigo 7 kiểu, Uchi/Soto" },
    { label: "Cao độ", href: "/pitch", desc: "高低アクセント — Pitch & Mora Lab 5 kiểu" },
    { label: "Tình huống", href: "/situations", desc: "場面ロールプレイ — Scenario Sprint" },
    { label: "Shadowing YouTube", href: "/shadowing", desc: "Luyện theo video" },
    { label: "Lộ trình học", href: "/learning", desc: "Kế hoạch cá nhân hóa" },
    { label: "AI Coach", href: "/coach", desc: "Hỏi coach cá nhân" },
    { label: "Tiến độ & phân tích", href: "/progress", desc: "Biểu đồ & bottleneck" },
    { label: "Dojo", href: "/game", desc: "Nhiệm vụ, kỹ năng, Boss" },
    { label: "Cài đặt", href: "/settings", desc: "AI, giọng nói, giao diện" },
  ];
  const filtered = q ? items.filter((i) => (i.label + i.desc).toLowerCase().includes(q.toLowerCase())) : items;
  const isCoachQuery = q.startsWith("?") || q.toLowerCase().startsWith("ask ") || q.toLowerCase().includes("coach");

  useEffect(() => {
    if (!open) setQ("");
  }, [open]);

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-[60] flex items-start justify-center pt-[18vh] px-4">
      <button onClick={onClose} className="absolute inset-0 bg-black/40 backdrop-blur-sm" aria-label="Đóng" />
      <div className="relative w-full max-w-lg rounded-2xl bg-card border border-border shadow-2xl overflow-hidden">
        <div className="flex items-center gap-3 px-4 py-3 border-b border-border">
          <span className="text-muted-foreground">⌘</span>
          <input
            autoFocus
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && isCoachQuery && onAskCoach) {
                onAskCoach(q);
                onClose();
              }
            }}
            placeholder="Tìm trang, bài học… hoặc hỏi Coach: ? Tại sao tui nói chậm?"
            className="flex-1 bg-transparent outline-none text-sm placeholder:text-muted-foreground"
          />
          <button onClick={onClose} className="text-xs px-2 py-1 rounded bg-muted border border-border">ESC</button>
        </div>
        <div className="max-h-[50vh] overflow-y-auto p-2">
          {isCoachQuery && q.trim().length > 3 && (
            <button
              onClick={() => { onAskCoach?.(q); onClose(); }}
              className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl bg-primary/10 border border-primary/20 hover:bg-primary/15 transition-colors text-left"
            >
              <span className="h-7 w-7 rounded-lg bg-primary text-primary-foreground flex items-center justify-center shrink-0"><Sparkles className="w-4 h-4" /></span>
              <span className="flex flex-col">
                <span className="text-sm font-bold text-foreground">Ask AI Coach: “{q}”</span>
                <span className="text-xs text-muted-foreground">Coach sẽ trả lời dựa trên dữ liệu luyện tập thực tế của bạn</span>
              </span>
            </button>
          )}
          {filtered.map((it) => (
            <Link key={it.href} href={it.href} onClick={onClose} className="flex flex-col px-3 py-2.5 rounded-xl hover:bg-muted transition-colors">
              <span className="text-sm font-medium text-foreground">{it.label}</span>
              <span className="text-xs text-muted-foreground">{it.desc}</span>
            </Link>
          ))}
          {filtered.length === 0 && !isCoachQuery && <p className="text-sm text-muted-foreground text-center py-8">Không tìm thấy kết quả</p>}
        </div>
      </div>
    </div>
  );
}

import { GlobalKeybindingsModal } from "./global-keybindings-modal";
import { useGlobalAudioCleanup } from "@/hooks/use-global-audio-cleanup";

export function AppShell({ children }: { children: React.ReactNode }) {
  useGlobalAudioCleanup();
  const { currentToast, dismissToast } = useRewardNotifications();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [cmdOpen, setCmdOpen] = useState(false);
  const [coachOpen, setCoachOpen] = useState(false);
  const [keybindingsOpen, setKeybindingsOpen] = useState(false);
  const pathname = usePathname();
  const { insights } = useCoachProactive();
  const shouldShowCoach = !["/coach", "/settings", "/playground"].some((p) => pathname?.startsWith(p));

  useEffect(() => {
    const v = localStorage.getItem("hanasu-sidebar-collapsed");
    if (v === "1") setSidebarCollapsed(true);
  }, []);
  useEffect(() => {
    localStorage.setItem("hanasu-sidebar-collapsed", sidebarCollapsed ? "1" : "0");
  }, [sidebarCollapsed]);

  const { matchesAction } = useSystemKeybindings();
  const { displayMode, setDisplayMode } = useFuriganaSettings();

  // Global Keybindings Listener
  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      const activeEl = document.activeElement;
      const isInput =
        activeEl &&
        (activeEl.tagName === "INPUT" ||
          activeEl.tagName === "TEXTAREA" ||
          activeEl.getAttribute("contenteditable") === "true");

      // ⌘K or Ctrl+K or custom globalSearch -> Command palette
      if (((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") || (!isInput && matchesAction(e, "globalSearch"))) {
        e.preventDefault();
        setCmdOpen((o) => !o);
        return;
      }

      // ⌘J or Ctrl+J or custom openCoach -> AI Coach
      if (((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "j") || (!isInput && matchesAction(e, "openCoach"))) {
        e.preventDefault();
        setCoachOpen((o) => !o);
        return;
      }

      // Global '?' or custom openKeybindingsModal when not typing -> Open Keybindings Modal
      if (!isInput && (matchesAction(e, "openKeybindingsModal") || (e.key === "?" && !e.ctrlKey && !e.metaKey && !e.altKey))) {
        e.preventDefault();
        setKeybindingsOpen((o) => !o);
        return;
      }

      // Global 'f' or custom toggleFurigana when not typing -> Toggle Furigana Display Mode
      if (!isInput && matchesAction(e, "toggleFurigana")) {
        e.preventDefault();
        const nextMode =
          displayMode === "kanji_reading" ? "kanji" : displayMode === "kanji" ? "hidden" : "kanji_reading";
        setDisplayMode(nextMode);
        return;
      }

      if (e.key === "Escape") {
        setCmdOpen(false);
        setKeybindingsOpen(false);
      }
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [matchesAction, displayMode, setDisplayMode]);

  return (
    <div className="flex h-screen w-full overflow-hidden bg-background text-foreground">
      <Sidebar collapsed={sidebarCollapsed} onToggle={() => setSidebarCollapsed((v) => !v)} />
      <div className="flex flex-1 min-w-0 flex-col overflow-hidden">
        {/* Mobile top bar */}
        <div className="md:hidden h-14 border-b border-border bg-card/90 backdrop-blur-md flex items-center justify-between px-3 shrink-0">
          <button onClick={() => setMobileOpen(true)} className="h-9 w-9 rounded-xl bg-muted border border-border flex items-center justify-center" aria-label="Mở menu">
            <Menu className="h-4 w-4" />
          </button>
          <Link href="/dashboard" className="flex items-center gap-2">
            <span className="h-8 w-8 rounded-xl bg-gradient-to-br from-akane-500 to-primary flex items-center justify-center text-white font-black text-sm">話</span>
            <span className="font-extrabold text-sm">HANASU AI</span>
          </Link>
          <span className="h-9 w-9" />
        </div>

        <TopNav onOpenCommand={() => setCmdOpen(true)} />
        <main className="flex-1 overflow-y-auto bg-background">
          <div
            className={cn(
              "mx-auto",
              pathname?.startsWith("/reflex") ||
                pathname?.startsWith("/keigo") ||
                pathname?.startsWith("/pitch") ||
                pathname?.startsWith("/situations") ||
                pathname?.startsWith("/speaking")
                ? "max-w-5xl p-2 sm:p-3 md:p-4 pb-4 space-y-3"
                : "max-w-[1280px] p-3 sm:p-4 md:p-6 pb-8 space-y-4"
            )}
          >
            {children}
          </div>
        </main>
      </div>

      <MobileDrawer open={mobileOpen} onClose={() => setMobileOpen(false)} />
      <CommandPalette open={cmdOpen} onClose={() => setCmdOpen(false)} onAskCoach={(q) => setCoachOpen(true)} />
      <GlobalKeybindingsModal isOpen={keybindingsOpen} onClose={() => setKeybindingsOpen(false)} />
      {shouldShowCoach && <CoachFloatingButton onClick={() => setCoachOpen(true)} hasNotification={insights.length > 0} />}
      <CoachPanel open={coachOpen} onClose={() => setCoachOpen(false)} route={pathname || "/dashboard"} />
      <BottomNav />
      <RewardToast notification={currentToast} onDismiss={dismissToast} />
      <AtmosphericWeatherEngine />
      <SelectionLookupBubble />
      <AIVocabularyLookupBox />
    </div>
  );
}

