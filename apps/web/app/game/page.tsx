"use client";

import React from "react";
import Link from "next/link";
import {
  useGameProfile,
  useQuests,
  useStreak,
  useAchievements,
  LevelBadge,
  XPBar,
  StreakCard,
  QuestCard,
  AchievementCard,
} from "@/features/gamification";
import {
  Swords,
  Flame,
  Award,
  Sparkles,
  ArrowRight,
  Shield,
  Target,
  Trophy,
  Zap,
} from "lucide-react";

export default function GameHubPage() {
  const { profile, xpOverview, loading: profileLoading } = useGameProfile();
  const { dailyQuests, loading: questsLoading } = useQuests();
  const { streak } = useStreak();
  const { achievements } = useAchievements();

  const recentAchievements = achievements.filter((a) => a.is_unlocked).slice(0, 3);

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Header Banner — washi */}
      <div className="relative overflow-hidden rounded-[24px] border border-border bg-card washi-texture shadow-washi-lg p-6 md:p-8">
        <div className="absolute -top-16 -right-16 h-64 w-64 rounded-full bg-enso-gradient opacity-30 pointer-events-none" />
        <div className="absolute inset-0 shoji-grid opacity-[0.03] pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-500/10 text-amber-700 border border-amber-500/20 dark:text-amber-300">
              Dojo RPG <span className="font-jp">道場</span> ⚔️
            </span>
            <h1 className="text-2xl md:text-3xl font-black tracking-tight text-foreground">
              Đạo trường & Hành trình <span className="font-jp text-lg font-bold text-muted-foreground">道場と成長</span>
            </h1>
            <p className="text-sm text-muted-foreground max-w-xl leading-relaxed">
              Mỗi câu bạn nói, mỗi thử thách bạn vượt qua đều được ghi nhận thành cấp độ và kỹ năng thực thụ.
            </p>
          </div>
          {profile && (
            <div className="shrink-0">
              <LevelBadge level={profile.level} rank={profile.rank} totalXp={profile.total_xp} size="lg" />
            </div>
          )}
        </div>
        {profile && (
          <div className="relative z-10 mt-6 pt-6 border-t border-border">
            <XPBar levelProgress={profile.level_progress} />
          </div>
        )}
      </div>

      {/* Quick Access Tiles */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { href: "/skills", label: "Kỹ năng", ja: "スキル", icon: Zap, color: "text-primary bg-primary/10 border-primary/15" },
          { href: "/bosses", label: "Thử thách Boss", ja: "ボス", icon: Swords, color: "text-amber-600 bg-amber-500/10 border-amber-500/15 dark:text-amber-400" },
          { href: "/quests", label: "Nhiệm vụ", ja: "クエスト", icon: Target, color: "text-indigo-600 bg-indigo-500/10 border-indigo-500/15 dark:text-indigo-400" },
          { href: "/achievements", label: "Thành tích", ja: "実績", icon: Trophy, color: "text-purple-600 bg-purple-500/10 border-purple-500/15 dark:text-purple-400" },
        ].map((t) => {
          const Icon = t.icon;
          return (
            <Link key={t.href} href={t.href} className="group">
              <span className="p-4 rounded-2xl bg-card border border-border hover:border-border hover:shadow-washi transition-all flex items-center gap-3 washi-texture block">
                <span className={`h-10 w-10 rounded-xl border flex items-center justify-center shrink-0 ${t.color}`}>
                  <Icon className="w-5 h-5" />
                </span>
                <span>
                  <span className="text-sm font-bold text-foreground block">{t.label}</span>
                  <span className="text-xs text-muted-foreground font-jp">{t.ja}</span>
                </span>
              </span>
            </Link>
          );
        })}
      </div>

      {/* Main Grid: Streak + Quests */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Streak & Today's Stats */}
        <div className="space-y-6">
          {streak && <StreakCard streak={streak} />}

          {profile && (
            <div className="p-5 rounded-2xl bg-card border border-border shadow-washi space-y-3 washi-texture">
              <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-widest">Hôm nay</h4>
              <div className="grid grid-cols-2 gap-3">
                <span className="p-3 rounded-xl bg-muted border border-border block">
                  <span className="text-xs text-muted-foreground">XP hôm nay</span>
                  <span className="text-lg font-black text-primary font-mono block">+{profile.today_xp}</span>
                </span>
                <span className="p-3 rounded-xl bg-muted border border-border block">
                  <span className="text-xs text-muted-foreground">Nhiệm vụ xong</span>
                  <span className="text-lg font-black text-emerald-600 dark:text-emerald-400 font-mono block">{profile.today_completed_quests} / 3</span>
                </span>
              </div>
            </div>
          )}
        </div>

        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
              <span className="h-7 w-7 rounded-lg bg-primary/10 border border-primary/15 flex items-center justify-center text-primary">
                <Target className="w-4 h-4" />
              </span>
              Nhiệm vụ hôm nay
            </h3>
            <Link href="/quests" className="text-sm text-primary hover:text-primary/80 font-semibold flex items-center gap-1">
              Xem nhiệm vụ tuần <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="space-y-3">
            {questsLoading ? (
              <div className="p-8 text-center text-sm text-muted-foreground">Đang tải nhiệm vụ…</div>
            ) : dailyQuests.length === 0 ? (
              <div className="p-8 text-center text-sm text-muted-foreground">Chưa có nhiệm vụ nào.</div>
            ) : (
              dailyQuests.map((quest) => <QuestCard key={quest.id} quest={quest} />)
            )}
          </div>
        </div>
      </div>

      {recentAchievements.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
              <span className="h-7 w-7 rounded-lg bg-amber-500/10 border border-amber-500/15 flex items-center justify-center text-amber-600 dark:text-amber-400">
                <Trophy className="w-4 h-4" />
              </span>
              Thành tích mới mở
            </h3>
            <Link href="/achievements" className="text-sm text-amber-600 dark:text-amber-400 hover:opacity-80 font-semibold flex items-center gap-1">
              Xem tất cả <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {recentAchievements.map((ach) => (
              <AchievementCard key={ach.id} achievement={ach} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
