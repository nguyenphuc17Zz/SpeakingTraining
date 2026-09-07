"use client";

import React, { useState } from "react";
import Link from "next/link";
import { StatCard } from "@/components/dashboard/stat-card";
import { SkillRadarCard } from "@/components/dashboard/skill-radar-card";
import { RecentSessions } from "@/components/dashboard/recent-sessions";
import { SpeakingHeatmap } from "@/components/dashboard/speaking-heatmap";
import { EmaGoalCard } from "@/components/dashboard/ema-goal-card";
import { StudioModesHub } from "@/components/dashboard/StudioModesHub";
import { RecommendedPersonasSection } from "@/components/dashboard/recommended-personas-section";
import { DailySenseiBriefingCard } from "@/features/coach";
import { Button } from "@/components/ui/button";
import { usePersonas } from "@/hooks/use-personas";
import {
  useGameProfile,
  useQuests,
  useStreak,
  XPBar,
  QuestCard,
} from "@/features/gamification";
import { OnboardingModal } from "@/features/onboarding";
import {
  Flame,
  Clock,
  Award,
  Swords,
  ArrowRight,
  Mic,
  Target,
  Compass,
} from "lucide-react";

export default function DashboardPage() {
  const { personas, loading: personasLoading } = usePersonas();
  const { profile, loading: profileLoading } = useGameProfile();
  const { dailyQuests, loading: questsLoading } = useQuests();
  const { streak } = useStreak();

  const currentLevel = profile?.level || 1;
  const currentRank = profile?.rank || "Beginner (初学者)";
  const currentStreakDays = streak?.current_streak ?? profile?.current_streak ?? 0;

  return (
    <div className="space-y-4 max-w-6xl mx-auto pb-8 animate-in fade-in duration-200">
      {/* 1. Hero chào mừng — Minimalist Studio */}
      <div className="rounded-2xl border border-border/70 bg-card/70 p-5 md:p-6 shadow-xs">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-5">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2.5 flex-wrap">
              <span className="h-8 w-8 rounded-xl bg-primary flex items-center justify-center text-primary-foreground font-black text-sm">
                話
              </span>
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
                Chào mừng trở lại!{" "}
                <span className="font-jp font-normal text-muted-foreground text-base sm:text-lg">
                  おかえりなさい
                </span>
              </h1>
            </div>
            <p className="text-xs sm:text-sm text-muted-foreground max-w-xl leading-relaxed">
              Tiếp tục rèn luyện phản xạ và giọng nói tiếng Nhật chuẩn Tokyo hôm nay.
            </p>
          </div>

          <div className="flex items-center gap-2.5 shrink-0 flex-wrap">
            <Link href="/learning">
              <Button variant="outline" size="md" className="gap-2 font-medium rounded-xl border-border/80">
                <Compass className="h-4 w-4 text-muted-foreground" />
                <span>Lộ trình học</span>
              </Button>
            </Link>

            <Link href="/speaking">
              <Button variant="primary" size="md" className="gap-2 rounded-xl shadow-xs">
                <Mic className="h-4 w-4" />
                <span>Bắt đầu luyện nói</span>
                <span className="text-xs font-jp opacity-80">会話</span>
              </Button>
            </Link>
          </div>
        </div>

        {profile && (
          <div className="mt-4 pt-4 border-t border-border/60">
            <XPBar levelProgress={profile.level_progress} />
          </div>
        )}
      </div>

      {/* 2. Daily Sensei Briefing */}
      <DailySenseiBriefingCard />

      {/* 3. Studio Modes Quick Hub (5 Phòng Luyện Studio Thực Chiến) */}
      <StudioModesHub />

      {/* 4. Thống kê nhanh */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3 sm:gap-4">
        <StatCard
          title="Cấp độ"
          jaTitle="レベル"
          value={`Lv. ${currentLevel}`}
          subtext={currentRank}
          icon={Swords}
          color="kintsugi"
        />
        <StatCard
          title="Chuỗi ngày"
          jaTitle="連続日数"
          value={`${currentStreakDays} ngày`}
          subtext={
            streak?.is_qualified_today
              ? "Đã giữ chuỗi hôm nay"
              : "Luyện ngay để giữ chuỗi"
          }
          icon={Flame}
          color="matcha"
        />
        <StatCard
          title="Điểm hôm nay"
          jaTitle="本日獲得"
          value={profile?.today_xp ? `+${profile.today_xp} XP` : "0 XP"}
          subtext="Tích luỹ hôm nay"
          icon={Clock}
          color="aizome"
        />
        <StatCard
          title="Nhiệm vụ"
          jaTitle="本日の目標"
          value={`${profile?.today_completed_quests || 0} / 3`}
          subtext="Mục tiêu hoàn thành"
          icon={Award}
          color="matcha"
        />
      </div>

      {/* 5. Ma Trận Giọng Nói Thực Tế & Thẻ Mục Tiêu */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <SpeakingHeatmap currentStreak={currentStreakDays} />
        </div>
        <div>
          <EmaGoalCard />
        </div>
      </div>

      {/* 6. Nhiệm vụ hôm nay */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-foreground flex items-center gap-2">
            <span className="h-6 w-6 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
              <Target className="h-3.5 w-3.5" />
            </span>
            <span>Nhiệm vụ hôm nay</span>
            <span className="text-xs font-normal text-muted-foreground font-jp">本日のクエスト</span>
          </h2>
          <Link
            href="/quests"
            className="text-xs font-medium text-primary hover:text-primary/80 flex items-center gap-1 transition-colors"
          >
            Xem tất cả <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {questsLoading ? (
            <div className="col-span-3 p-6 text-center text-sm text-muted-foreground">Đang tải nhiệm vụ…</div>
          ) : dailyQuests.length === 0 ? (
            <div className="col-span-3 p-6 text-center text-sm text-muted-foreground">Chưa có nhiệm vụ hôm nay.</div>
          ) : (
            dailyQuests.slice(0, 3).map((quest) => (
              <QuestCard key={quest.id} quest={quest} />
            ))
          )}
        </div>
      </div>

      {/* 7. Đối tác hội thoại gợi ý */}
      <RecommendedPersonasSection personas={personas} loading={personasLoading} />

      {/* 8. Analytics & Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <SkillRadarCard />
        <RecentSessions />
      </div>

      {/* First-time Learner Onboarding Flow */}
      <OnboardingModal />
    </div>
  );
}
