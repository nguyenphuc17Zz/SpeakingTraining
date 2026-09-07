"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Mic,
  Tv,
  TrendingUp,
  Brain,
  Settings,
  Sparkles,
  Flame,
  Swords,
  Zap,
  Crown,
  Music,
  Compass,
  Target,
  Trophy,
  Gift,
  ChevronDown,
  ChevronRight,
  PanelLeftClose,
  PanelLeftOpen,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useGameProfile, useStreak } from "@/features/gamification";

interface NavItem {
  label: string;
  jaLabel: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

const MAIN_ITEMS: NavItem[] = [
  { label: "Trang chủ", jaLabel: "ホーム", href: "/dashboard", icon: LayoutDashboard },
  { label: "Luyện nói", jaLabel: "会話", href: "/speaking", icon: Mic },
  { label: "Phục hồi nói", jaLabel: "リハビリ", href: "/ramp", icon: Sparkles },
  { label: "Phản xạ", jaLabel: "瞬発", href: "/reflex", icon: Zap },
  { label: "Kính ngữ", jaLabel: "敬語", href: "/keigo", icon: Crown },
  { label: "Cao độ", jaLabel: "高低", href: "/pitch", icon: Music },
  { label: "Tình huống", jaLabel: "場面", href: "/situations", icon: Compass },
  { label: "Shadowing", jaLabel: "シャドーイング", href: "/shadowing", icon: Tv },
  { label: "Lộ trình học", jaLabel: "今日の学習", href: "/learning", icon: Zap },
];

const INTEL_ITEMS: NavItem[] = [
  { label: "AI Coach", jaLabel: "コーチ", href: "/coach", icon: Sparkles },
  { label: "Tiến độ", jaLabel: "進捗", href: "/progress", icon: TrendingUp },
  { label: "Hồ sơ học tập", jaLabel: "カルテ", href: "/profile", icon: Brain },
];

const DOJO_SUB: NavItem[] = [
  { label: "Tổng quan", jaLabel: "道場", href: "/game", icon: Swords },
  { label: "Nhiệm vụ", jaLabel: "クエスト", href: "/quests", icon: Target },
  { label: "Kỹ năng", jaLabel: "スキル", href: "/skills", icon: Zap },
  { label: "Thử thách Boss", jaLabel: "ボス", href: "/bosses", icon: Flame },
  { label: "Thành tích", jaLabel: "実績", href: "/achievements", icon: Trophy },
  { label: "Phần thưởng", jaLabel: "報酬", href: "/unlocks", icon: Gift },
];

function isNavActive(itemHref: string, pathname: string): boolean {
  if (itemHref === "/speaking") {
    return pathname === "/speaking" || (pathname.startsWith("/speaking/") && !["/speaking/speech", "/speaking/reflex", "/speaking/pronunciation"].some((p) => pathname.startsWith(p)));
  }
  if (itemHref === "/dashboard") {
    return pathname === "/dashboard";
  }
  return pathname === itemHref || pathname.startsWith(itemHref + "/");
}

function NavLink({
  item,
  isActive,
  collapsed,
}: {
  item: NavItem;
  isActive: boolean;
  collapsed: boolean;
}) {
  const Icon = item.icon;
  if (collapsed) {
    return (
      <Link
        href={item.href}
        prefetch={true}
        title={item.label}
        className={cn(
          "flex h-9 w-9 items-center justify-center rounded-lg text-sm transition-all",
          isActive
            ? "bg-foreground text-background shadow-sm"
            : "text-muted-foreground hover:text-foreground hover:bg-muted"
        )}
      >
        <Icon className="h-4 w-4" />
      </Link>
    );
  }
  return (
    <Link
      href={item.href}
      prefetch={true}
      className={cn(
        "flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium transition-all group",
        isActive
          ? "bg-muted text-foreground font-semibold"
          : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
      )}
    >
      <Icon className={cn("h-4 w-4 shrink-0", isActive ? "text-primary" : "text-muted-foreground group-hover:text-foreground")} />
      <span className="truncate">{item.label}</span>
      {isActive && <span className="ml-auto h-1.5 w-1.5 rounded-full bg-primary" />}
    </Link>
  );
}

export function Sidebar({
  collapsed,
  onToggle,
}: {
  collapsed: boolean;
  onToggle: () => void;
}) {
  const pathname = usePathname();
  const { profile } = useGameProfile();
  const { streak } = useStreak();

  const isDojoActive =
    pathname.startsWith("/game") ||
    pathname.startsWith("/quests") ||
    pathname.startsWith("/skills") ||
    pathname.startsWith("/bosses") ||
    pathname.startsWith("/achievements") ||
    pathname.startsWith("/unlocks");

  const [dojoOpen, setDojoOpen] = useState(isDojoActive);

  React.useEffect(() => {
    if (isDojoActive) setDojoOpen(true);
  }, [isDojoActive]);

  const currentLevel = profile?.level ?? 1;
  const currentRank = profile?.rank ?? "Sơ cấp";
  const currentStreak = streak?.current_streak ?? profile?.current_streak ?? 0;
  const currentXp = profile?.total_xp ?? 0;
  const progressPct = Math.round((profile?.level_progress?.progress_ratio ?? 0) * 100);

  // Collapsed rail — compact
  if (collapsed) {
    return (
      <aside className="hidden md:flex w-[64px] shrink-0 flex-col items-center gap-2.5 border-r border-border bg-card px-2 py-3 overflow-y-auto">
        {/* Brand */}
        <Link href="/dashboard" prefetch={true} className="h-9 w-9 rounded-lg bg-foreground text-background flex items-center justify-center font-bold text-xs tracking-tight shadow-sm shrink-0">
          JS
        </Link>
        <button onClick={onToggle} className="h-7 w-7 rounded-md hover:bg-muted flex items-center justify-center text-muted-foreground transition-colors" aria-label="Mở rộng menu">
          <PanelLeftOpen className="h-3.5 w-3.5" />
        </button>
        <div className="h-px w-6 bg-border my-1" />
        <div className="flex flex-col gap-1">
          {MAIN_ITEMS.map((it) => (
            <NavLink key={it.href} item={it} collapsed isActive={isNavActive(it.href, pathname)} />
          ))}
        </div>
        <div className="h-px w-6 bg-border my-1" />
        <div className="flex flex-col gap-1">
          {INTEL_ITEMS.map((it) => (
            <NavLink key={it.href} item={it} collapsed isActive={pathname.startsWith(it.href)} />
          ))}
        </div>
        <div className="h-px w-6 bg-border my-1" />
        {/* Dojo hub single icon */}
        <Link
          href="/game"
          prefetch={true}
          className={cn(
            "h-9 w-9 rounded-lg flex items-center justify-center transition-colors",
            isDojoActive ? "bg-muted text-foreground font-semibold" : "text-muted-foreground hover:text-foreground hover:bg-muted"
          )}
          title="Dojo / Minigame"
        >
          <Swords className="h-4 w-4" />
        </Link>
        <Link href="/settings" prefetch={true} className={cn("h-9 w-9 rounded-lg flex items-center justify-center mt-auto transition-colors", pathname.startsWith("/settings") ? "bg-muted text-foreground" : "text-muted-foreground hover:text-foreground hover:bg-muted")}>
          <Settings className="h-4 w-4" />
        </Link>
      </aside>
    );
  }

  // Expanded
  return (
    <aside className="hidden md:flex w-[240px] shrink-0 flex-col border-r border-border bg-card overflow-hidden z-20">
      <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-4">
        {/* Brand */}
        <div className="flex items-center justify-between px-1.5 pt-0.5">
          <Link href="/dashboard" className="flex items-center gap-2.5 group">
            <span className="h-8 w-8 rounded-lg bg-foreground text-background flex items-center justify-center font-bold text-xs tracking-tight shadow-sm transition-transform group-hover:scale-105">
              JS
            </span>
            <div className="flex flex-col leading-none">
              <span className="font-bold text-sm tracking-tight text-foreground">JapS</span>
              <span className="text-[10px] text-muted-foreground font-normal mt-0.5">Japanese Speaking</span>
            </div>
          </Link>
          <button
            onClick={onToggle}
            className="h-7 w-7 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted flex items-center justify-center transition-colors shrink-0"
            aria-label="Thu gọn menu"
          >
            <PanelLeftClose className="h-3.5 w-3.5" />
          </button>
        </div>

        {/* Main Navigation */}
        <div className="space-y-0.5">
          <div className="px-2 py-1">
            <p className="text-[11px] font-semibold tracking-wider text-muted-foreground/70 uppercase">Học tập</p>
          </div>
          <nav className="flex flex-col gap-0.5">
            {MAIN_ITEMS.map((it) => (
              <NavLink key={it.href} item={it} collapsed={false} isActive={isNavActive(it.href, pathname)} />
            ))}
          </nav>
        </div>

        <div className="space-y-0.5">
          <div className="px-2 py-1">
            <p className="text-[11px] font-semibold tracking-wider text-muted-foreground/70 uppercase">Phân tích & Hỗ trợ</p>
          </div>
          <nav className="flex flex-col gap-0.5">
            {INTEL_ITEMS.map((it) => (
              <NavLink key={it.href} item={it} collapsed={false} isActive={pathname.startsWith(it.href)} />
            ))}
          </nav>
        </div>

        {/* Dojo hub — single collapsible */}
        <div className="space-y-0.5">
          <button
            onClick={() => setDojoOpen(!dojoOpen)}
            className={cn(
              "w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium transition-all",
              isDojoActive ? "bg-muted text-foreground font-semibold" : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
            )}
          >
            <span className="flex items-center gap-2.5">
              <Swords className={cn("h-4 w-4", isDojoActive ? "text-primary" : "text-muted-foreground")} />
              <span>Dojo</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded font-semibold bg-muted text-muted-foreground border border-border">
                Lv.{currentLevel}
              </span>
            </span>
            {dojoOpen ? <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" /> : <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />}
          </button>
          {dojoOpen && (
            <nav className="ml-3 pl-3 border-l border-border/70 flex flex-col gap-0.5 mt-1">
              {DOJO_SUB.map((it) => {
                const Icon = it.icon;
                const active = pathname === it.href || (it.href !== "/game" && pathname.startsWith(it.href));
                return (
                  <Link
                    key={it.href}
                    href={it.href}
                    prefetch={true}
                    className={cn(
                      "flex items-center justify-between px-2.5 py-1.5 rounded-md text-sm transition-colors",
                      active ? "bg-muted text-foreground font-medium" : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
                    )}
                  >
                    <span className="flex items-center gap-2">
                      <Icon className={cn("h-3.5 w-3.5", active ? "text-primary" : "text-muted-foreground")} />
                      {it.label}
                    </span>
                  </Link>
                );
              })}
            </nav>
          )}
        </div>

        <div className="pt-1 mt-auto">
          <Link
            href="/settings"
            prefetch={true}
            className={cn(
              "flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
              pathname.startsWith("/settings") ? "bg-muted text-foreground font-semibold" : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
            )}
          >
            <Settings className="h-4 w-4" />
            <span>Cài đặt</span>
          </Link>
        </div>
      </div>

      {/* Footer — profile */}
      <div className="p-3 pt-0 border-t border-border/50">
        <Link href="/game" prefetch={true} className="block group pt-3">
          <div className="rounded-xl border border-border bg-card p-3 flex flex-col gap-2 transition-all hover:bg-muted/40">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-2">
                <span className="h-7 w-7 rounded-md bg-muted flex items-center justify-center font-bold text-xs text-foreground">
                  {currentLevel}
                </span>
                <span className="truncate">
                  <span className="text-xs font-semibold text-foreground block truncate">{profile?.user_id ?? "Học viên"}</span>
                  <span className="text-[11px] text-muted-foreground">{currentRank}</span>
                </span>
              </span>
              <span className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400 text-xs font-semibold">
                <Flame className="h-3 w-3" /> {currentStreak}d
              </span>
            </div>
            <div className="space-y-1 pt-0.5">
              <div className="flex justify-between text-[11px] text-muted-foreground">
                <span>{currentXp} XP</span>
                <span>{progressPct}%</span>
              </div>
              <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
                <div className="h-full bg-primary rounded-full transition-all duration-300" style={{ width: `${progressPct}%` }} />
              </div>
            </div>
          </div>
        </Link>
      </div>
    </aside>
  );
}
