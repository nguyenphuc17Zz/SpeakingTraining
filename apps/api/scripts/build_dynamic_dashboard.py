import os

# 1. Add /analytics/activity-heatmap endpoint in analytics.py
HEATMAP_ENDPOINT = '''
# ── Real Activity Speaking Heatmap Endpoint ──
@router.get("/activity-heatmap")
async def get_speaking_activity_heatmap(
    weeks: int = Query(default=14, ge=4, le=52),
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves real daily speaking practice duration for the past N weeks."""
    from datetime import datetime, timedelta, timezone
    from app.domains.gamification.models import DailyStreakActivity
    from app.domains.learning.models import ExerciseAttempt

    now = datetime.now(timezone.utc)
    total_days = weeks * 7
    start_date = (now - timedelta(days=total_days - 1)).date()

    # Query streak activities
    streak_stmt = (
        select(DailyStreakActivity)
        .where(
            DailyStreakActivity.user_id == user_id,
            DailyStreakActivity.activity_date >= start_date,
        )
    )
    s_res = await db.execute(streak_stmt)
    streak_activities = list(s_res.scalars().all())

    # Query exercise attempts
    att_stmt = (
        select(ExerciseAttempt)
        .where(
            ExerciseAttempt.user_id == user_id,
            ExerciseAttempt.started_at >= datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc),
            ExerciseAttempt.status == "completed",
        )
    )
    a_res = await db.execute(att_stmt)
    attempts = list(a_res.scalars().all())

    # Aggregate minutes by date string YYYY-MM-DD
    daily_minutes: dict[str, int] = {}
    for sa in streak_activities:
        d_str = sa.activity_date.strftime("%Y-%m-%d")
        daily_minutes[d_str] = daily_minutes.get(d_str, 0) + (sa.minutes_practiced or 5)

    for att in attempts:
        if att.started_at:
            d_str = att.started_at.strftime("%Y-%m-%d")
            # Estimate minutes from duration or default 3 min
            mins = max(1, round((att.duration_seconds or 180) / 60))
            daily_minutes[d_str] = daily_minutes.get(d_str, 0) + mins

    # Build the full date list
    days_list = []
    total_mins = 0
    for i in range(total_days - 1, -1, -1):
        d = (now - timedelta(days=i)).date()
        d_str = d.strftime("%Y-%m-%d")
        mins = daily_minutes.get(d_str, 0)
        total_mins += mins

        level = 0
        if mins >= 20:
            level = 4
        elif mins >= 12:
            level = 3
        elif mins >= 5:
            level = 2
        elif mins > 0:
            level = 1

        days_list.append({
            "date": d_str,
            "minutes": mins,
            "level": level,
        })

    return {
        "weeks": weeks,
        "total_days": total_days,
        "total_speaking_minutes": total_mins,
        "days": days_list,
    }
'''

# 2. StudioModesHub.tsx
STUDIO_HUB = """\"use client\";

import React from "react";
import Link from "next/link";
import {
  Zap,
  Crown,
  Volume2,
  Compass,
  ArrowRight,
  Sparkles,
  Layers,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

const STUDIO_MODES = [
  {
    id: "reflex",
    title: "1. Phản Xạ 3 Giây",
    jaTitle: "瞬発スピーキング",
    tag: "Tốc Độ & Tư Duy Không Dịch",
    desc: "Chuyển ý nghĩ thành câu nói tiếng Nhật dưới 3 giây. Rèn phản xạ không qua bước dịch tiếng Việt.",
    icon: <Zap className="h-5 w-5 text-amber-500" />,
    url: "/reflex",
    color: "amber",
    submodes: ["Mẫu câu cơ bản", "Hội thoại nhanh", "Thử thách áp lực"],
    accentBg: "from-amber-500/10 via-amber-500/5 to-transparent",
  },
  {
    id: "keigo",
    title: "2. Kính Ngữ Công Sở",
    jaTitle: "ビジネス敬語スタジオ",
    tag: "Tôn Kính & Khiêm Nhường",
    desc: "Thực hành Sonkeigo, Kenjougo, quy tắc Uchi/Soto và văn hóa doanh nghiệp Nhật chuẩn mực.",
    icon: <Crown className="h-5 w-5 text-purple-500" />,
    url: "/keigo",
    color: "purple",
    submodes: ["Tôn kính ngữ", "Khiêm nhường ngữ", "Lịch sự trang trọng"],
    accentBg: "from-purple-500/10 via-purple-500/5 to-transparent",
  },
  {
    id: "pitch",
    title: "3. Cao Độ Chuẩn Tokyo",
    jaTitle: "東京アクセント・拍感覚",
    tag: "Cao Độ & Phách Mora",
    desc: "Luyện 4 mô hình cao độ Tokyo, phân biệt cặp từ tối thiểu (雨/飴), trường âm và vô thanh hóa.",
    icon: <Volume2 className="h-5 w-5 text-sky-500" />,
    url: "/pitch",
    color: "sky",
    submodes: ["Cặp từ tối thiểu", "Phách trường âm", "Vô thanh hóa"],
    accentBg: "from-sky-500/10 via-sky-500/5 to-transparent",
  },
  {
    id: "situations",
    title: "4. Tình Huống Vô Tận",
    jaTitle: "場面英会話・無限生成",
    tag: "AI Roleplay Vô Tận",
    desc: "Hàng trăm bối cảnh đối thoại sinh động do Gemini AI tạo mới không giới hạn kèm phản hồi NPC tức thì.",
    icon: <Compass className="h-5 w-5 text-emerald-500" />,
    url: "/situations",
    color: "emerald",
    submodes: ["Công sở & Phỏng vấn", "Đời sống Nhật", "Tùy biến AI"],
    accentBg: "from-emerald-500/10 via-emerald-500/5 to-transparent",
  },
];

export function StudioModesHub() {
  return (
    <div className="space-y-4">
      {/* Header Bar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="h-7 w-7 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary shadow-xs">
            <Layers className="h-4 w-4" />
          </span>
          <div>
            <h2 className="text-sm font-bold text-foreground flex items-center gap-2">
              <span>4 Phòng Luyện Studio Thực Chiến</span>
              <span className="text-xs font-semibold text-muted-foreground font-jp">実践スタジオ</span>
            </h2>
          </div>
        </div>

        <Badge variant="kintsugi" size="sm" className="font-bold text-[10px]">
          100% DYNAMIC AI
        </Badge>
      </div>

      {/* 4 Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {STUDIO_MODES.map((mode) => (
          <div
            key={mode.id}
            className="p-5 rounded-3xl border border-border/80 bg-card washi-texture shadow-xs hover:border-primary/40 hover:shadow-md transition-all flex flex-col justify-between group relative overflow-hidden"
          >
            <div className={cn("absolute top-0 right-0 h-32 w-32 bg-gradient-to-bl rounded-full blur-2xl pointer-events-none opacity-60", mode.accentBg)} />

            <div className="space-y-3 relative z-10">
              <div className="flex items-center justify-between">
                <div className="p-2.5 rounded-2xl bg-muted/60 border border-border/80 shadow-2xs group-hover:scale-105 transition-transform">
                  {mode.icon}
                </div>
                <Badge variant="outline" size="sm" className="text-[10px] font-semibold text-muted-foreground">
                  {mode.tag.split("&")[0]}
                </Badge>
              </div>

              <div className="space-y-1">
                <h3 className="text-sm font-bold text-foreground group-hover:text-primary transition-colors">
                  {mode.title}
                </h3>
                <p className="text-[10px] text-muted-foreground font-jp font-medium">
                  {mode.jaTitle}
                </p>
              </div>

              <p className="text-xs text-muted-foreground leading-relaxed line-clamp-3">
                {mode.desc}
              </p>

              {/* Sub-modes tags */}
              <div className="flex flex-wrap gap-1 pt-1">
                {mode.submodes.map((sub, idx) => (
                  <span
                    key={idx}
                    className="text-[10px] px-2 py-0.5 rounded-md bg-muted/40 text-muted-foreground border border-border/60"
                  >
                    {sub}
                  </span>
                ))}
              </div>
            </div>

            {/* Launch Button */}
            <div className="pt-4 mt-2 border-t border-border/60 relative z-10">
              <Link href={mode.url} className="w-full block">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => soundFX.playKatana()}
                  className="w-full text-xs font-bold justify-between rounded-xl h-8.5 hover:bg-primary hover:text-primary-foreground hover:border-primary transition-all shadow-2xs"
                >
                  <span>Vào phòng luyện</span>
                  <ArrowRight className="h-3.5 w-3.5 group-hover:translate-x-0.5 transition-transform" />
                </Button>
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
"""

# 3. SpeakingHeatmap.tsx (Real API data)
HEATMAP_TSX = """\"use client\";

import React, { useState, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { HankoStamp } from "@/components/ui/hanko-stamp";
import { Mic, Flame, Calendar, Sparkles, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";

interface HeatmapDay {
  date: string;
  minutes: number;
  level: 0 | 1 | 2 | 3 | 4;
}

export function SpeakingHeatmap({
  totalMinutes: propTotalMinutes,
  currentStreak = 5,
  className,
}: {
  totalMinutes?: number;
  currentStreak?: number;
  className?: string;
}) {
  const [days, setDays] = useState<HeatmapDay[]>([]);
  const [totalMinutes, setTotalMinutes] = useState<number>(propTotalMinutes || 0);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchHeatmap = async () => {
    try {
      setLoading(true);
      const res = await fetch("http://localhost:8000/api/v1/analytics/activity-heatmap?weeks=14");
      if (res.ok) {
        const data = await res.json();
        setDays(data.days || []);
        setTotalMinutes(data.total_speaking_minutes || 0);
      }
    } catch (e) {
      console.warn("Could not fetch speaking heatmap:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHeatmap();
  }, []);

  const levelStyles = {
    0: "bg-muted/40 border-border/40 hover:border-foreground/20",
    1: "bg-emerald-500/25 border-emerald-500/30 hover:border-emerald-500",
    2: "bg-emerald-500/50 border-emerald-500/60 hover:border-emerald-500",
    3: "bg-emerald-500/75 border-emerald-500/80 hover:border-emerald-500 shadow-xs",
    4: "bg-emerald-500 border-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.4)]",
  };

  return (
    <div className={cn("p-6 rounded-3xl border border-border bg-card washi-texture shadow-sm space-y-4 relative overflow-hidden", className)}>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border/60 pb-3.5">
        <div className="flex items-center gap-2.5">
          <span className="h-8 w-8 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary shadow-2xs">
            <Mic className="h-4 w-4" />
          </span>
          <div>
            <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
              <span>Ma Trận Giọng Nói Thực Tế (98 Ngày)</span>
              <span className="text-xs font-semibold text-muted-foreground font-jp">発話ヒートマップ</span>
            </h3>
            <p className="text-[10px] text-muted-foreground">Theo dõi thời lượng luyện nói mỗi ngày từ cơ sở dữ liệu</p>
          </div>
        </div>

        <div className="flex items-center gap-3 self-start sm:self-auto">
          <div className="text-right">
            <span className="text-[10px] text-muted-foreground font-semibold uppercase">Tổng Thời Lượng</span>
            <div className="text-sm font-black text-foreground font-mono">
              {totalMinutes} <span className="text-[10px] font-normal text-muted-foreground">phút</span>
            </div>
          </div>
          <HankoStamp text="皆勤" subtext="Chăm chỉ" variant="gold" size="sm" />
        </div>
      </div>

      {/* Heatmap Grid */}
      {loading && days.length === 0 ? (
        <div className="py-8 text-center text-xs text-muted-foreground animate-pulse">
          Đang tổng hợp dữ liệu luyện tập 14 tuần...
        </div>
      ) : (
        <div className="space-y-2">
          <div className="overflow-x-auto pb-1">
            <div className="grid grid-rows-7 grid-flow-col gap-1.5 min-w-[580px]">
              {days.map((d, i) => (
                <div
                  key={i}
                  className={cn(
                    "w-3.5 h-3.5 rounded-sm border transition-all cursor-pointer",
                    levelStyles[d.level]
                  )}
                  title={`${d.date}: ${d.minutes} phút luyện nói`}
                />
              ))}
            </div>
          </div>

          {/* Legend */}
          <div className="flex items-center justify-between text-[10px] text-muted-foreground pt-1">
            <span className="flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              <span>14 tuần gần nhất</span>
            </span>
            <div className="flex items-center gap-1.5">
              <span>Ít</span>
              <span className="w-2.5 h-2.5 rounded-xs bg-muted/40 border border-border" />
              <span className="w-2.5 h-2.5 rounded-xs bg-emerald-500/25 border border-emerald-500/30" />
              <span className="w-2.5 h-2.5 rounded-xs bg-emerald-500/50 border border-emerald-500/60" />
              <span className="w-2.5 h-2.5 rounded-xs bg-emerald-500/75 border border-emerald-500/80" />
              <span className="w-2.5 h-2.5 rounded-xs bg-emerald-500 border border-emerald-400" />
              <span>Nhiều (20m+)</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
"""

# 4. dashboard/page.tsx
DASHBOARD_PAGE = """\"use client\";

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
    <div className="space-y-8 animate-in fade-in duration-300 max-w-6xl mx-auto pb-16">
      {/* 1. Hero chào mừng — Zen Garden & Seigaiha */}
      <div className="relative overflow-hidden rounded-3xl border border-border bg-card/95 seigaiha-pattern shadow-sm p-6 md:p-8 washi-texture">
        <SakuraPetals count={4} />
        <div className="absolute -top-16 -right-16 h-52 w-52 rounded-full bg-enso-gradient opacity-60 pointer-events-none" />
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
"""

FILES_DASHBOARD = {
    r"E:\SpeakingTraining\apps\web\components\dashboard\StudioModesHub.tsx": STUDIO_HUB,
    r"E:\SpeakingTraining\apps\web\components\dashboard\speaking-heatmap.tsx": HEATMAP_TSX,
    r"E:\SpeakingTraining\apps\web\app\dashboard\page.tsx": DASHBOARD_PAGE,
}

for filepath, content in FILES_DASHBOARD.items():
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"Successfully wrote {os.path.basename(filepath)}")

# Append heatmap endpoint to analytics.py if not present
analytics_path = r"E:\SpeakingTraining\apps\api\app\api\v1\analytics.py"
with open(analytics_path, "r", encoding="utf-8") as f:
    text = f.read()

if "activity-heatmap" not in text:
    with open(analytics_path, "a", encoding="utf-8") as f:
        f.write(HEATMAP_ENDPOINT + "\n")
    print("Successfully appended activity-heatmap endpoint to analytics.py")

print("All Dashboard Dynamic files created successfully!")
