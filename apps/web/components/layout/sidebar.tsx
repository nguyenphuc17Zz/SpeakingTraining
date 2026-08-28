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
        title={`${item.label} — ${item.jaLabel}`}
        className={cn(
          "flex h-10 w-10 items-center justify-center rounded-xl border text-sm transition-all",
          isActive
            ? "bg-primary text-primary-foreground border-primary shadow-sm"
            : "bg-card border-border text-muted-foreground hover:text-foreground hover:bg-muted"
        )}
      >
        <Icon className="h-4.5 w-4.5" />
      </Link>
    );
  }
  return (
    <Link
      href={item.href}
      className={cn(
        "flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-medium transition-all group",
        isActive
          ? "bg-primary/10 text-primary border border-primary/15 shadow-sm"
          : "text-muted-foreground hover:text-foreground hover:bg-muted border border-transparent"
      )}
    >
      <span className="flex items-center gap-2.5">
        <Icon className={cn("h-4 w-4 shrink-0", isActive ? "text-primary" : "text-muted-foreground group-hover:text-foreground")} />
        <span className="truncate">{item.label}</span>
      </span>
      <span className={cn("text-xs font-jp ml-2 shrink-0", isActive ? "text-primary/70" : "text-muted-foreground/70")}>
        {item.jaLabel}
      </span>
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
      <aside className="hidden md:flex w-[72px] shrink-0 flex-col items-center gap-3 border-r border-border bg-card/80 backdrop-blur-sm px-2 py-4 overflow-y-auto">
        {/* Brand */}
        <Link href="/dashboard" className="h-10 w-10 rounded-xl bg-gradient-to-br from-primary via-emerald-600 to-teal-700 flex items-center justify-center text-white font-black text-lg shadow-md shrink-0">
          話
        </Link>
        <button onClick={onToggle} className="h-8 w-8 rounded-lg bg-muted hover:bg-muted/80 flex items-center justify-center text-muted-foreground" aria-label="Mở rộng menu">
          <PanelLeftOpen className="h-4 w-4" />
        </button>
        <div className="h-px w-8 bg-border my-1" />
        <div className="flex flex-col gap-1.5">
          {MAIN_ITEMS.map((it) => (
            <NavLink key={it.href} item={it} collapsed isActive={pathname === it.href || pathname.startsWith(it.href + "/")} />
          ))}
        </div>
        <div className="h-px w-8 bg-border my-1" />
        <div className="flex flex-col gap-1.5">
          {INTEL_ITEMS.map((it) => (
            <NavLink key={it.href} item={it} collapsed isActive={pathname.startsWith(it.href)} />
          ))}
        </div>
        <div className="h-px w-8 bg-border my-1" />
        {/* Dojo hub single icon */}
        <Link
          href="/game"
          className={cn(
            "h-10 w-10 rounded-xl flex items-center justify-center border",
            isDojoActive ? "bg-amber-500 text-white border-amber-600 shadow-sm" : "bg-card border-border text-muted-foreground hover:text-foreground"
          )}
          title="Dojo / Minigame"
        >
          <Swords className="h-5 w-5" />
        </Link>
        <Link href="/settings" className={cn("h-10 w-10 rounded-xl flex items-center justify-center border mt-auto", pathname.startsWith("/settings") ? "bg-primary text-primary-foreground border-primary" : "bg-card border-border text-muted-foreground")}>
          <Settings className="h-4 w-4" />
        </Link>
      </aside>
    );
  }

  // Expanded
  return (
    <aside className="hidden md:flex w-[265px] shrink-0 flex-col border-r border-border bg-card/95 backdrop-blur-md overflow-hidden z-20">
      <div className="flex-1 overflow-y-auto p-3.5 flex flex-col gap-4">
        {/* Brand */}
        <div className="flex items-center justify-between px-1 pt-1">
          <Link href="/dashboard" className="flex items-center gap-3 group">
            <span className="h-10 w-10 rounded-2xl bg-gradient-to-br from-primary via-emerald-600 to-teal-700 flex items-center justify-center text-white font-display font-black text-xl shadow-md group-hover:shadow-lg group-hover:scale-105 transition-all">
              話
            </span>
            <span>
              <span className="flex items-center gap-1.5">
                <span className="font-black text-sm tracking-tight text-foreground font-display">HANASU AI</span>
                <span className="text-[9px] px-1.5 py-0.2 rounded font-bold bg-primary/10 text-primary border border-primary/20">OS</span>
              </span>
              <span className="text-[11px] text-muted-foreground font-jp tracking-wider">にほんごスピーキング</span>
            </span>
          </Link>
          <button
            onClick={onToggle}
            className="h-8 w-8 rounded-xl bg-muted/80 hover:bg-muted flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors shrink-0"
            aria-label="Thu gọn menu"
          >
            <PanelLeftClose className="h-4 w-4" />
          </button>
        </div>

        {/* Main */}
        <div className="space-y-1">
          <div className="flex items-center justify-between px-2 py-1">
            <p className="text-[10px] font-extrabold tracking-widest text-muted-foreground/70 uppercase">Học tập</p>
            <span className="text-[9px] font-jp text-muted-foreground/50">学習</span>
          </div>
          <nav className="flex flex-col gap-1">
            {MAIN_ITEMS.map((it) => (
              <NavLink key={it.href} item={it} collapsed={false} isActive={pathname === it.href || (it.href !== "/dashboard" && pathname.startsWith(it.href))} />
            ))}
          </nav>
        </div>

        <div className="space-y-1">
          <div className="flex items-center justify-between px-2 py-1">
            <p className="text-[10px] font-extrabold tracking-widest text-muted-foreground/70 uppercase">Phân tích & AI</p>
            <span className="text-[9px] font-jp text-muted-foreground/50">分析</span>
          </div>
          <nav className="flex flex-col gap-1">
            {INTEL_ITEMS.map((it) => (
              <NavLink key={it.href} item={it} collapsed={false} isActive={pathname.startsWith(it.href)} />
            ))}
          </nav>
        </div>

        {/* Dojo hub — single collapsible */}
        <div className="space-y-1">
          <button
            onClick={() => setDojoOpen(!dojoOpen)}
            className={cn(
              "w-full flex items-center justify-between px-3 py-2.5 rounded-xl border text-sm font-semibold transition-all",
              isDojoActive ? "bg-amber-500/10 text-amber-600 border-amber-500/25 shadow-sm" : "text-muted-foreground hover:text-foreground hover:bg-muted border-transparent"
            )}
          >
            <span className="flex items-center gap-2.5">
              <span className={cn("h-7 w-7 rounded-lg flex items-center justify-center shadow-sm", isDojoActive ? "bg-amber-500 text-white" : "bg-muted text-muted-foreground")}>
                <Swords className="h-3.5 w-3.5" />
              </span>
              <span>Dojo</span>
              <span className="text-xs font-jp text-muted-foreground/70">道場</span>
              <span className="ml-1 text-[10px] px-1.5 py-0.5 rounded-full bg-amber-500/15 text-amber-600 font-bold border border-amber-500/30">Lv.{currentLevel}</span>
            </span>
            {dojoOpen ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
          </button>
          {dojoOpen && (
            <nav className="ml-3 pl-3 border-l border-border/80 flex flex-col gap-0.5 mt-1">
              {DOJO_SUB.map((it) => {
                const Icon = it.icon;
                const active = pathname === it.href || (it.href !== "/game" && pathname.startsWith(it.href));
                return (
                  <Link
                    key={it.href}
                    href={it.href}
                    className={cn(
                      "flex items-center justify-between px-2.5 py-2 rounded-lg text-sm transition-colors",
                      active ? "bg-amber-500/15 text-amber-600 border border-amber-500/25 font-semibold" : "text-muted-foreground hover:text-foreground hover:bg-muted/80"
                    )}
                  >
                    <span className="flex items-center gap-2">
                      <Icon className={cn("h-3.5 w-3.5", active ? "text-amber-500" : "text-muted-foreground")} />
                      {it.label}
                    </span>
                    <span className="text-xs font-jp text-muted-foreground/70">{it.jaLabel}</span>
                  </Link>
                );
              })}
            </nav>
          )}
        </div>

        <div className="pt-1">
          <Link
            href="/settings"
            className={cn(
              "flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-medium border transition-colors",
              pathname.startsWith("/settings") ? "bg-muted text-foreground border-border" : "text-muted-foreground hover:text-foreground hover:bg-muted border-transparent"
            )}
          >
            <span className="flex items-center gap-2.5"><Settings className="h-4 w-4" /> Cài đặt</span>
            <span className="text-xs font-jp text-muted-foreground/70">設定</span>
          </Link>
        </div>
      </div>

      {/* Footer — profile */}
      <Link href="/game" className="m-3 mt-0 block group">
        <div className="rounded-2xl border border-border bg-card/90 p-3 flex flex-col gap-2.5 group-hover:border-primary/30 group-hover:shadow-sm transition-all washi-texture">
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-2.5">
              <span className="h-8 w-8 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center font-display font-bold text-xs text-white shadow-sm">
                学
              </span>
              <span>
                <span className="text-sm font-bold text-foreground block leading-none">Bạn học</span>
                <span className="text-xs text-primary font-medium">Lv.{currentLevel} {currentRank}</span>
              </span>
            </span>
            <span className="flex items-center gap-1 text-amber-600 bg-amber-500/10 px-2 py-0.5 rounded-full border border-amber-500/25 text-xs font-bold">
              <Flame className="h-3 w-3 fill-amber-500 text-amber-500" /> {currentStreak}d
            </span>
          </div>
          <div className="space-y-1">
            <span className="flex justify-between text-[11px] text-muted-foreground font-medium">
              <span>XP {currentXp}</span>
              <span className="font-bold text-foreground">{progressPct}%</span>
            </span>
            <span className="h-1.5 w-full bg-muted rounded-full overflow-hidden block border border-border/40">
              <span className="h-full bg-gradient-to-r from-primary via-amber-500 to-kintsugi-400 block rounded-full transition-all duration-300" style={{ width: `${progressPct}%` }} />
            </span>
          </div>
        </div>
      </Link>
    </aside>
  );
}
