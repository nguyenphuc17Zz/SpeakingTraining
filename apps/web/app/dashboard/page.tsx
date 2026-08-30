"use client";

import React, { useState } from "react";
import Link from "next/link";
import { StatCard } from "@/components/dashboard/stat-card";
import { DailyMissionCard } from "@/components/dashboard/daily-mission-card";
import { SkillRadarCard } from "@/components/dashboard/skill-radar-card";
import { RecentSessions } from "@/components/dashboard/recent-sessions";
import { SpeakingHeatmap } from "@/components/dashboard/speaking-heatmap";
import { EmaGoalCard } from "@/components/dashboard/ema-goal-card";
import { StudioModesHub } from "@/components/dashboard/StudioModesHub";
import { RecommendedPersonasSection } from "@/components/dashboard/recommended-personas-section";
import { DailyOmikujiModal } from "@/components/features/daily-omikuji-modal";
import { AIAssistantChatbox } from "@/components/features/ai-assistant-chatbox";
import { DailySenseiBriefingCard } from "@/features/coach";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
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
  Sparkles,
  ArrowRight,
  Mic,
  MessageCircle,
  Target,
  Compass,
} from "lucide-react";
import { HankoStamp } from "@/components/ui/hanko-stamp";
import { SakuraPetals } from "@/components/ui/sakura-petals";

export default function DashboardPage() {
  const { personas, loading: personasLoading } = usePersonas();
  const { profile, loading: profileLoading } = useGameProfile();
  const { dailyQuests, loading: questsLoading } = useQuests();
  const { streak } = useStreak();
  const [isOmikujiOpen, setIsOmikujiOpen] = useState(false);

  const currentLevel = profile?.level || 1;
  const currentRank = profile?.rank || "Beginner (初学者)";
  const currentStreakDays = streak?.current_streak ?? profile?.current_streak ?? 0;

  return (
    <div className="space-y-5 animate-in fade-in duration-300 max-w-6xl mx-auto pb-8">
      {/* 1. Hero chào mừng — Zen Garden & Seigaiha */}
      <div className="relative overflow-hidden rounded-3xl border border-border bg-card/95 seigaiha-pattern shadow-sm p-5 md:p-6 washi-texture">
        <SakuraPetals count={4} />
        <div className="absolute -top-16 -right-16 h-48 w-48 rounded-full bg-enso-gradient opacity-60 pointer-events-none" />
        <div className="absolute inset-0 shoji-grid opacity-30 pointer-events-none" />

        <div className="relative flex flex-col lg:flex-row lg:items-center justify-between gap-5 z-10">
          <div className="space-y-2.5">
            <div className="flex items-center gap-2.5 flex-wrap">
              <span className="h-9 w-9 rounded-2xl bg-gradient-to-br from-primary via-emerald-600 to-teal-700 flex items-center justify-center text-white font-display font-black text-base shadow-md">
                話
              </span>
              <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-foreground font-display">
                Chào mừng trở lại! <span className="font-jp font-bold text-primary text-xl sm:text-2xl">おかえりなさい</span>
              </h1>
              <HankoStamp text="精進" subtext="Chăm chỉ" variant="gold" size="sm" />
            </div>
            <p className="text-xs sm:text-sm text-muted-foreground max-w-xl leading-relaxed">
              Cùng nâng trình nói tiếng Nhật hôm nay qua 4 phòng luyện Studio thực chiến và rèn giọng chuẩn Tokyo.
            </p>
          </div>

          <div className="flex items-center gap-2.5 shrink-0 flex-wrap">
            {/* Omikuji Fortune Button */}
            <Button
              variant="outline"
              size="md"
              onClick={() => setIsOmikujiOpen(true)}
              className="gap-2 font-semibold border-kintsugi-400/40 hover:bg-kintsugi-400/10 text-foreground shadow-xs rounded-xl"
              title="Rút quẻ xăm may mắn đầu ngày"
            >
              <span className="text-base">⛩️</span>
              <span className="font-jp">Quẻ Xăm おみくじ</span>
            </Button>

            <Link href="/learning">
              <Button variant="outline" size="md" className="gap-2 font-semibold rounded-xl">
                <Compass className="h-4 w-4 text-primary" />
                <span>Lộ Trình Học</span>
              </Button>
            </Link>

            <Link href="/speaking">
              <Button variant="primary" size="md" className="gap-2 shadow-md rounded-xl">
                <Mic className="h-4 w-4" />
                <span>Luyện nói ngay</span>
                <span className="text-[11px] font-jp opacity-90">会話</span>
              </Button>
            </Link>
          </div>
        </div>

        {profile && (
          <div className="relative mt-5 pt-5 border-t border-border/80 z-10">
            <XPBar levelProgress={profile.level_progress} />
          </div>
        )}
      </div>

      {/* 2. Daily Sensei Briefing Letter */}
      <DailySenseiBriefingCard />

      {/* 3. Studio Modes Quick Hub (4 Phòng Luyện Studio Thực Chiến) */}
      <StudioModesHub />

      {/* 4. Thống kê nhanh phong cách Nhật Bản */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 sm:gap-5">
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
              ? "Đã giữ chuỗi hôm nay! 🔥"
              : "Giữ lửa chăm chỉ nhé! 🔥"
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
          subtext="Mục tiêu hàng ngày"
          icon={Award}
          color="matcha"
        />
      </div>

      {/* 5. Ma Trận Giọng Nói Thực Tế & Thẻ Gỗ Ước Nguyện Ema */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
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
          <h2 className="text-sm font-bold text-foreground flex items-center gap-2">
            <span className="h-7 w-7 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary shadow-xs">
              <Target className="h-3.5 w-3.5" />
            </span>
            <span>Nhiệm vụ hôm nay</span>
            <span className="text-xs font-semibold text-muted-foreground font-jp">本日のクエスト</span>
          </h2>
          <Link
            href="/quests"
            className="text-xs font-bold text-primary hover:text-primary/80 flex items-center gap-1 transition-colors"
          >
            Xem tất cả <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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

      {/* 7. Đối tác hội thoại gợi ý nâng cao */}
      <RecommendedPersonasSection personas={personas} loading={personasLoading} />

      {/* 8. Analytics & Recent Activity Matrix */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SkillRadarCard />
        <RecentSessions />
      </div>

      {/* Daily Omikuji Fortune Drawer Modal */}
      <DailyOmikujiModal
        isOpen={isOmikujiOpen}
        onClose={() => setIsOmikujiOpen(false)}
        onXpAwarded={(xp) => {
          console.log("Omikuji XP Awarded:", xp);
        }}
      />

      {/* Floating Japanese AI Assistant Chatbox */}
      <AIAssistantChatbox streakDays={currentStreakDays} />

      {/* First-time Learner Onboarding Flow */}
      <OnboardingModal />
    </div>
  );
}
