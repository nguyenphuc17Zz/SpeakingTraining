import os

# 1. analytics.py backend
ANALYTICS_API = '''from typing import Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.domains.ai.contracts import AIMessage, AIMessageRole, AIRequest, AITask
from app.domains.ai.router import AIRouter
from app.domains.analytics.application.analytics_snapshot_service import AnalyticsSnapshotService
from app.domains.analytics.application.bottleneck_analyzer import BottleneckAnalyzer
from app.domains.analytics.application.goal_analytics_service import GoalAnalyticsService
from app.domains.analytics.application.insight_engine import InsightEngine
from app.domains.analytics.application.metric_engine import MetricEngine
from app.domains.analytics.application.weekly_review_service import WeeklyReviewService
from app.domains.analytics.domain.metric_definitions import METRIC_REGISTRY, MetricKey
from app.domains.analytics.models import InsightRecord
from app.domains.analytics.schemas import (
    AnalyticsDashboardDTO,
    BottleneckDTO,
    GoalProgressDTO,
    InsightDTO,
    MetricValueDTO,
    PracticeDistributionDTO,
    WeeklyReviewDTO,
)
from app.domains.learning.models import ExerciseAttempt
from app.domains.users.service import UserService
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/analytics", tags=["analytics"])


async def get_user_id(db: AsyncSession = Depends(get_db)) -> str:
    """Resolve to real default user (UUID) matching all learning and practice endpoints."""
    user_service = UserService(db)
    user = await user_service.get_or_create_default_user()
    return user.id


@router.get("/dashboard", response_model=AnalyticsDashboardDTO)
async def get_analytics_dashboard(
    period: str = Query(default="30d"),
    force_refresh: bool = Query(default=False),
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = AnalyticsSnapshotService(db)
    overview = await service.get_dashboard_overview(user_id, period=period, force_refresh=force_refresh)

    # Convert to DTO
    metrics_dto: dict[str, MetricValueDTO] = {}
    for k, mv in overview.metrics.items():
        defn = METRIC_REGISTRY.get(mv.metric_key)
        metrics_dto[k] = MetricValueDTO(
            metric_key=mv.metric_key.value,
            name=defn.name if defn else mv.metric_key.value,
            ja_name=defn.ja_name if defn else "",
            unit=defn.unit if defn else "",
            category=defn.category if defn else "",
            description=defn.description if defn else "",
            value=mv.value,
            baseline=mv.baseline,
            change=mv.change,
            sample_size=mv.sample_size,
            confidence=mv.confidence.value,
            period=mv.period,
            trend=mv.trend.value,
            metric_version=mv.metric_version,
        )

    bottleneck_dto = (
        BottleneckDTO(
            candidate=overview.bottleneck.candidate,
            confidence=overview.bottleneck.confidence.value,
            description=overview.bottleneck.description,
            evidence_keys=overview.bottleneck.evidence_keys,
            suggested_focus=overview.bottleneck.suggested_focus,
        )
        if overview.bottleneck
        else None
    )

    insights_dto = [
        InsightDTO(
            id=i.id,
            insight_type=i.insight_type.value,
            title=i.title,
            description=i.description,
            confidence=i.confidence.value,
            metric_key=i.metric_key.value if i.metric_key else None,
            metric_value=i.metric_value,
            action_hint=i.action_hint,
            action_target_type=i.action_target_type,
            action_target_key=i.action_target_key,
            evidence_keys=i.evidence_keys,
            lifecycle=i.lifecycle.value,
            generated_at=i.generated_at,
        )
        for i in overview.top_insights
    ]

    goals_dto = [
        GoalProgressDTO(
            goal_id=g.goal_id,
            title=g.title,
            goal_type=g.goal_type,
            progress_ratio=g.progress_ratio,
            confidence=g.confidence.value,
            target_date=g.target_date,
            is_on_track=g.is_on_track,
        )
        for g in overview.goals
    ]

    distrib_dto = PracticeDistributionDTO(
        conversation_turns=overview.practice_distribution.conversation_turns,
        pronunciation_attempts=overview.practice_distribution.pronunciation_attempts,
        shadowing_segments=overview.practice_distribution.shadowing_segments,
        exercise_attempts=overview.practice_distribution.exercise_attempts,
        total_speaking_minutes=overview.practice_distribution.total_speaking_minutes,
    )

    return AnalyticsDashboardDTO(
        period=overview.period,
        speaking_level=overview.speaking_level or "N3",
        total_sessions_analyzed=overview.total_sessions_analyzed or len(metrics_dto),
        metrics=metrics_dto,
        bottleneck=bottleneck_dto,
        top_insights=insights_dto,
        goals=goals_dto,
        practice_distribution=distrib_dto,
        last_updated=overview.last_updated,
    )


# ── AI Sensei 360 Diagnostic Report ──
@router.get("/diagnostic")
async def get_sensei_diagnostic(
    period: str = Query(default="30d"),
    persona: str = Query(default="tanaka"),
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Synthesizes comprehensive 360-degree diagnostic report analyzing 4 speaking pillars."""
    stmt = (
        select(ExerciseAttempt)
        .where(ExerciseAttempt.user_id == user_id, ExerciseAttempt.status == "completed")
        .order_by(desc(ExerciseAttempt.started_at))
        .limit(100)
    )
    res = await db.execute(stmt)
    attempts = list(res.scalars().all())

    reflex_attempts = [a for a in attempts if "reflex" in (a.exercise_type or "")]
    keigo_attempts = [a for a in attempts if "keigo" in (a.exercise_type or "")]
    pitch_attempts = [a for a in attempts if "pitch" in (a.exercise_type or "") or "mora" in (a.exercise_type or "")]
    situational_attempts = [a for a in attempts if "situat" in (a.exercise_type or "")]

    def avg_score(items: list[ExerciseAttempt]) -> float:
        if not items:
            return 0.0
        scores = [a.score for a in items if a.score is not None]
        return round(sum(scores) / len(scores), 1) if scores else 0.0

    pillars = {
        "reflex": {
            "name": "Phản Xạ (Reflex)",
            "icon": "⚡",
            "count": len(reflex_attempts),
            "avg_score": avg_score(reflex_attempts),
            "status": "Thành thạo" if avg_score(reflex_attempts) >= 80 else "Đang cải thiện",
        },
        "keigo": {
            "name": "Kính Ngữ (Keigo)",
            "icon": "👑",
            "count": len(keigo_attempts),
            "avg_score": avg_score(keigo_attempts),
            "status": "Thành thạo" if avg_score(keigo_attempts) >= 80 else "Đang cải thiện",
        },
        "pitch": {
            "name": "Cao Độ & Phách (Pitch & Mora)",
            "icon": "🎵",
            "count": len(pitch_attempts),
            "avg_score": avg_score(pitch_attempts),
            "status": "Thành thạo" if avg_score(pitch_attempts) >= 80 else "Đang cải thiện",
        },
        "situations": {
            "name": "Tình Huống Thực Chiến (Situations)",
            "icon": "🎭",
            "count": len(situational_attempts),
            "avg_score": avg_score(situational_attempts),
            "status": "Thành thạo" if avg_score(situational_attempts) >= 80 else "Đang cải thiện",
        },
    }

    ai_router = AIRouter(db)
    prompt = (
        f"Hãy chẩn đoán năng lực nói tiếng Nhật 360 độ cho học viên dựa trên số liệu thực tế:\\n"
        f"- Tổng số lượt luyện tập: {len(attempts)}\\n"
        f"- Phản xạ: {pillars['reflex']['count']} bài (Điểm TB: {pillars['reflex']['avg_score']})\\n"
        f"- Kính ngữ: {pillars['keigo']['count']} bài (Điểm TB: {pillars['keigo']['avg_score']})\\n"
        f"- Cao độ & Phách: {pillars['pitch']['count']} bài (Điểm TB: {pillars['pitch']['avg_score']})\\n"
        f"- Tình huống thực tế: {pillars['situations']['count']} bài (Điểm TB: {pillars['situations']['avg_score']})\\n\\n"
        f"Trả về đúng định dạng JSON:\\n"
        f"{{\\n"
        f"  \\\"estimated_level\\\": \\\"N3 - Trung cấp\\\",\\n"
        f"  \\\"summary_title\\\": \\\"Tiến độ rèn luyện đa kỹ năng đang phát triển tích cực\\\",\\n"
        f"  \\\"narrative\\\": \\\"Bạn đã hoàn thành các bài luyện với độ tập trung cao.\\\",\\n"
        f"  \\\"top_strengths\\\": [\\\"Phản xạ câu đơn nhanh\\\", \\\"Nắm vững thể Desu/Masu\\\"],\\n"
        f"  \\\"core_bottleneck\\\": \\\"Cần trau chuốt thêm về tính chuẩn xác Kính ngữ và ngữ điệu câu dài.\\\",\\n"
        f"  \\\"action_plan\\\": \\\"Dành 10 phút luyện Kính ngữ và 5 phút Cao độ Tokyo mỗi ngày.\\\",\\n"
        f"  \\\"recommended_route\\\": \\\"/keigo\\\"\\n"
        f"}}"
    )

    try:
        req = AIRequest(
            messages=[AIMessage(role=AIMessageRole.USER, content=prompt)],
            system_instruction="Bạn là Trưởng ban Khảo thí tiếng Nhật. Trả về đúng JSON.",
            temperature=0.7,
        )
        resp = await ai_router.generate(task=AITask.COACH_INSIGHT, request=req, user_id=user_id)
        import json
        t = resp.text.strip()
        if t.startswith("```"):
            t = t.split("\\n", 1)[-1] if "\\n" in t else t
            if t.endswith("```"):
                t = t[:-3]
            t = t.strip()
            if t.startswith("json"):
                t = t[4:].strip()
        report = json.loads(t)
    except Exception:
        report = {
            "estimated_level": "N3 - Trung cấp",
            "summary_title": "Tiến độ rèn luyện đa kỹ năng đang phát triển tích cực",
            "narrative": f"Bạn đã hoàn thành tổng cộng {len(attempts)} bài luyện. Nền tảng phản xạ và ngữ pháp đang ổn định.",
            "top_strengths": ["Phản xạ câu đơn nhanh", "Độ chính xác ngữ pháp cơ bản"],
            "core_bottleneck": "Cần trau chuốt thêm về tính chuẩn xác Kính ngữ và ngữ điệu câu dài.",
            "action_plan": "Dành 10 phút luyện Kính ngữ và 5 phút Cao độ Tokyo mỗi ngày.",
            "recommended_route": "/keigo",
        }

    return {
        "period": period,
        "total_attempts": len(attempts),
        "pillars": pillars,
        "diagnostic_report": report,
    }
'''

# 2. SenseiDiagnosticCard.tsx
DIAGNOSTIC_CARD = """\"use client\";

import React from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Sparkles,
  Award,
  TrendingUp,
  AlertCircle,
  ArrowRight,
  Shield,
  Volume2,
  CheckCircle2,
} from "lucide-react";
import { soundFX } from "@/lib/sound-fx";
import Link from "next/link";

interface SenseiDiagnosticCardProps {
  diagnostic: any;
  loading: boolean;
}

export function SenseiDiagnosticCard({ diagnostic, loading }: SenseiDiagnosticCardProps) {
  if (loading || !diagnostic) {
    return (
      <div className="p-6 rounded-3xl border border-border bg-card washi-texture animate-pulse space-y-3">
        <div className="h-4 w-32 bg-muted rounded" />
        <div className="h-6 w-3/4 bg-muted rounded" />
        <div className="h-16 w-full bg-muted/60 rounded-2xl" />
      </div>
    );
  }

  const r = diagnostic.diagnostic_report || {};

  return (
    <div className="p-6 md:p-8 rounded-3xl border border-primary/30 bg-card washi-texture shadow-sm space-y-5 relative overflow-hidden ring-1 ring-primary/20">
      <div className="absolute top-0 right-0 h-48 w-48 bg-primary/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 relative z-10 border-b border-border/60 pb-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Badge variant="kintsugi" size="sm" className="font-bold">
              AI SENSEI 360° DIAGNOSTIC
            </Badge>
            <Badge variant="matcha" size="sm" className="font-bold font-mono">
              Ước tính: {r.estimated_level || "N3"}
            </Badge>
          </div>
          <h2 className="text-lg md:text-xl font-black text-foreground tracking-tight">
            {r.summary_title || "Báo Cáo Chẩn Đoán Năng Lực Hội Thoại Toàn Diện"}
          </h2>
        </div>

        <div className="text-xs text-muted-foreground font-mono font-semibold">
          Tổng hợp từ {diagnostic.total_attempts || 0} bài luyện
        </div>
      </div>

      {/* Narrative Evaluation */}
      <div className="text-xs text-muted-foreground leading-relaxed pl-1">
        {r.narrative}
      </div>

      {/* Strengths & Core Bottleneck Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Top Strengths */}
        <div className="p-4 rounded-2xl bg-emerald-500/5 border border-emerald-500/20 space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold text-emerald-700 dark:text-emerald-300">
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            <span>Điểm Sáng Tiến Bộ Nhất:</span>
          </div>
          <ul className="space-y-1 pl-6 list-disc text-[11px] text-muted-foreground">
            {(r.top_strengths || ["Phản xạ nhanh nhạy", "Nắm vững thể Desu/Masu"]).map((st: string, idx: number) => (
              <li key={idx}>{st}</li>
            ))}
          </ul>
        </div>

        {/* Core Bottleneck */}
        <div className="p-4 rounded-2xl bg-amber-500/5 border border-amber-500/20 space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold text-amber-700 dark:text-amber-300">
            <AlertCircle className="h-4 w-4 text-amber-500" />
            <span>Điểm Nghẽn Cần Khắc Phục:</span>
          </div>
          <p className="text-[11px] text-muted-foreground leading-snug pl-1">
            {r.core_bottleneck || "Cần nâng cao độ thuần thục Kính ngữ và ngữ điệu câu dài."}
          </p>
        </div>
      </div>

      {/* Action Plan & 1-Click Practice Launch */}
      <div className="p-4 rounded-2xl bg-muted/40 border border-border/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-2xs">
        <div className="space-y-1">
          <div className="text-xs font-bold text-foreground flex items-center gap-1.5">
            <Sparkles className="h-3.5 w-3.5 text-primary" />
            <span>Chiến Lược Hành Động Cho Bạn:</span>
          </div>
          <p className="text-[11px] text-muted-foreground leading-snug">
            {r.action_plan || "Tập trung 10 phút luyện Kính ngữ và 5 phút Cao độ Tokyo mỗi ngày."}
          </p>
        </div>

        <Link href={r.recommended_route || "/keigo"}>
          <Button
            variant="akane"
            size="sm"
            onClick={() => soundFX.playKatana()}
            className="text-xs font-bold gap-1.5 rounded-xl px-5 h-9 shrink-0 shadow-md"
          >
            <span>Khắc Phục Ngay</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Button>
        </Link>
      </div>
    </div>
  );
}
"""

# 3. FourPillarsRadarCard.tsx
PILLARS_CARD = """\"use client\";

import React from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Zap,
  Crown,
  Volume2,
  Compass,
  ArrowRight,
  Shield,
} from "lucide-react";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";
import Link from "next/link";

interface FourPillarsRadarCardProps {
  pillars: Record<string, any> | undefined;
}

export function FourPillarsRadarCard({ pillars }: FourPillarsRadarCardProps) {
  if (!pillars) return null;

  const pillarItems = [
    {
      key: "reflex",
      title: "1. Phản Xạ Nhanh",
      jaTitle: "瞬発スピーキング",
      icon: <Zap className="h-4 w-4 text-amber-500" />,
      url: "/reflex",
      color: "amber",
      data: pillars.reflex || { count: 0, avg_score: 0 },
    },
    {
      key: "keigo",
      title: "2. Kính Ngữ Công Sở",
      jaTitle: "ビジネス敬語",
      icon: <Crown className="h-4 w-4 text-purple-500" />,
      url: "/keigo",
      color: "purple",
      data: pillars.keigo || { count: 0, avg_score: 0 },
    },
    {
      key: "pitch",
      title: "3. Cao Độ & Phách",
      jaTitle: "東京アクセント",
      icon: <Volume2 className="h-4 w-4 text-sky-500" />,
      url: "/pitch",
      color: "sky",
      data: pillars.pitch || { count: 0, avg_score: 0 },
    },
    {
      key: "situations",
      title: "4. Tình Huống Thực Chiến",
      jaTitle: "場面英会話",
      icon: <Compass className="h-4 w-4 text-emerald-500" />,
      url: "/situations",
      color: "emerald",
      data: pillars.situations || { count: 0, avg_score: 0 },
    },
  ];

  return (
    <div className="p-6 rounded-3xl border border-border bg-card washi-texture shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield className="h-5 w-5 text-primary" />
          <h3 className="text-sm font-bold text-foreground">
            Ma Trận 4 Trụ Cột Năng Lực Nói Tiếng Nhật (4-Pillar Mastery Matrix)
          </h3>
        </div>
        <Badge variant="outline" size="sm" className="text-xs font-semibold">
          4 STUDIO MODES
        </Badge>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
        {pillarItems.map((p) => {
          const score = Math.round(p.data.avg_score || 0);
          return (
            <div
              key={p.key}
              className="p-4 rounded-2xl border border-border/80 bg-card shadow-2xs space-y-3 hover:border-primary/40 transition-all group"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="p-2 rounded-xl bg-muted/50 border border-border/80">
                    {p.icon}
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-foreground group-hover:text-primary transition-colors">
                      {p.title}
                    </h4>
                    <span className="text-[10px] text-muted-foreground font-jp">{p.jaTitle}</span>
                  </div>
                </div>
              </div>

              {/* Progress Bar & Stats */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-muted-foreground font-semibold">
                    {p.data.count} bài đã luyện
                  </span>
                  <span className="font-bold font-mono text-primary">{score}%</span>
                </div>

                <div className="w-full h-2 rounded-full bg-muted/60 overflow-hidden">
                  <div
                    className={cn(
                      "h-full rounded-full transition-all duration-500",
                      score >= 80 ? "bg-emerald-500" : score >= 50 ? "bg-amber-500" : "bg-primary"
                    )}
                    style={{ width: `${score}%` }}
                  />
                </div>
              </div>

              <Link href={p.url}>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => soundFX.playFurin()}
                  className="w-full text-[11px] font-bold text-muted-foreground hover:text-foreground justify-between h-7 px-2 rounded-lg"
                >
                  <span>Vào phòng luyện</span>
                  <ArrowRight className="h-3 w-3" />
                </Button>
              </Link>
            </div>
          );
        })}
      </div>
    </div>
  );
}
"""

# 4. analytics/index.ts
ANALYTICS_INDEX = """export * from "./components/MetricCard";
export * from "./components/BottleneckCard";
export * from "./components/InsightFeed";
export * from "./components/GoalProgressCard";
export * from "./components/PracticeDistributionChart";
export * from "./components/SenseiDiagnosticCard";
export * from "./components/FourPillarsRadarCard";
export * from "./hooks/useAnalyticsDashboard";
export * from "./types/analytics";
"""

# 5. app/progress/page.tsx
PROGRESS_PAGE = """\"use client\";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useAnalyticsDashboard } from "@/features/analytics/hooks/useAnalyticsDashboard";
import {
  MetricCard,
  BottleneckCard,
  InsightFeed,
  GoalProgressCard,
  PracticeDistributionChart,
  SenseiDiagnosticCard,
  FourPillarsRadarCard,
} from "@/features/analytics";
import { MetricValueDTO } from "@/features/analytics/types/analytics";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  TrendingUp,
  Sparkles,
  Calendar,
  RefreshCw,
  Target,
  Mic,
  MessageSquare,
  ArrowRight,
  Shield,
  Lightbulb,
  Sliders,
} from "lucide-react";
import { soundFX } from "@/lib/sound-fx";

export default function ProgressDashboardPage() {
  const [period, setPeriod] = useState("30d");
  const [activeTab, setActiveTab] = useState<string>("all");
  const { dashboard, loading, error, refetch } = useAnalyticsDashboard(period);
  const [diagnostic, setDiagnostic] = useState<any>(null);
  const [diagnosticLoading, setDiagnosticLoading] = useState<boolean>(true);

  const fetchDiagnostic = async () => {
    try {
      setDiagnosticLoading(true);
      const res = await fetch(`http://localhost:8000/api/v1/analytics/diagnostic?period=${period}`);
      if (res.ok) {
        const data = await res.json();
        setDiagnostic(data);
      }
    } catch (e) {
      console.warn("Failed to fetch diagnostic:", e);
    } finally {
      setDiagnosticLoading(false);
    }
  };

  useEffect(() => {
    fetchDiagnostic();
  }, [period]);

  const metrics = dashboard?.metrics || {};

  // Group metrics by categories
  const reflexKeys = ["reflex_reaction_latency", "reflex_accuracy", "reflex_automaticity", "reflex_timeout_rate"];
  const keigoKeys = ["keigo_accuracy", "keigo_naturalness", "keigo_context_fit", "keigo_double_keigo_rate"];
  const pronKeys = ["pronunciation_overall", "pitch_accuracy", "mora_timing", "intonation"];
  const convKeys = ["fluency", "naturalness", "grammar_accuracy", "vocabulary", "response_speed", "filler_rate"];

  const filteredMetrics = Object.entries(metrics).filter(([key]) => {
    if (activeTab === "all") return true;
    if (activeTab === "reflex") return reflexKeys.includes(key);
    if (activeTab === "keigo") return keigoKeys.includes(key);
    if (activeTab === "pitch") return pronKeys.includes(key);
    if (activeTab === "conversation") return convKeys.includes(key);
    return true;
  });

  return (
    <div className="space-y-8 animate-in fade-in duration-300 max-w-6xl mx-auto pb-16">
      {/* 1. Top Header Haru Washi */}
      <div className="relative overflow-hidden rounded-3xl border border-border bg-card p-6 md:p-8 washi-texture shadow-sm space-y-4">
        <div className="absolute top-0 right-0 h-48 w-48 bg-primary/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 relative z-10">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Badge variant="matcha" size="sm" className="font-bold">
                EVIDENCE-BASED SPEAKING ANALYTICS
              </Badge>
              <span className="text-xs text-muted-foreground font-semibold">
                Chẩn Đoán & Tiến Độ Học Tập Động
              </span>
            </div>
            <h1 className="text-2xl md:text-3xl font-black text-foreground tracking-tight flex items-center gap-3">
              <span className="p-2 rounded-2xl bg-primary/10 border border-primary/20 text-primary inline-flex">
                <TrendingUp className="h-6 w-6" />
              </span>
              <span>Phân Tích Tiến Độ Thực Tế (学習分析・診断)</span>
            </h1>
            <p className="text-xs md:text-sm text-muted-foreground max-w-2xl leading-relaxed">
              Toàn bộ chỉ số được tổng hợp trực tiếp từ lịch sử các bài tập tại 4 phòng luyện, giúp bạn theo dõi chính xác từng mili-giây phản xạ và độ chuẩn xác ngữ âm.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5 shrink-0 self-start lg:self-auto">
            {/* Period Selector */}
            <div className="flex items-center bg-muted/60 p-1 rounded-2xl border border-border/80 text-xs">
              {["7d", "14d", "30d", "90d"].map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => {
                    soundFX.playFurin();
                    setPeriod(p);
                  }}
                  className={`px-3 py-1.5 rounded-xl font-bold transition-all ${
                    period === p
                      ? "bg-primary text-primary-foreground shadow-xs"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                soundFX.playFurin();
                refetch();
                fetchDiagnostic();
              }}
              className="h-10 w-10 p-0 rounded-2xl border-border"
              title="Làm mới dữ liệu"
            >
              <RefreshCw className={`h-4 w-4 ${loading || diagnosticLoading ? "animate-spin text-primary" : ""}`} />
            </Button>
          </div>
        </div>
      </div>

      {/* 2. Sensei 360 Diagnostic Report */}
      <SenseiDiagnosticCard diagnostic={diagnostic} loading={diagnosticLoading} />

      {/* 3. 4-Pillar Mastery Matrix */}
      <FourPillarsRadarCard pillars={diagnostic?.pillars} />

      {/* 4. Filter Tabs & Detailed Metrics Grid */}
      <div className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Sliders className="h-4 w-4 text-primary" />
            <h3 className="text-sm font-bold text-foreground">
              Bảng Chỉ Số Chi Tiết (22+ Realtime Metrics)
            </h3>
          </div>

          {/* Metric Category Filter Pills */}
          <div className="flex flex-wrap gap-1.5">
            {[
              { id: "all", label: "Tất Cả" },
              { id: "reflex", label: "⚡ Phản Xạ" },
              { id: "keigo", label: "👑 Kính Ngữ" },
              { id: "pitch", label: "🎵 Cao Độ & Phách" },
              { id: "conversation", label: "🗣️ Hội Thoại" },
            ].map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => {
                  soundFX.playFurin();
                  setActiveTab(tab.id);
                }}
                className={`px-3 py-1 rounded-xl text-xs font-semibold border transition-all ${
                  activeTab === tab.id
                    ? "bg-primary text-primary-foreground border-primary shadow-xs"
                    : "bg-muted/40 border-border text-muted-foreground hover:text-foreground"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
          {filteredMetrics.map(([key, mv]) => (
            <MetricCard key={key} metric={mv} />
          ))}
        </div>
      </div>

      {/* 5. Bottom Insights & Goal Progress */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <InsightFeed insights={dashboard?.top_insights || []} />
          <PracticeDistributionChart distribution={dashboard?.practice_distribution} />
        </div>

        <div className="space-y-6">
          {dashboard?.bottleneck && <BottleneckCard bottleneck={dashboard.bottleneck} />}
          <GoalProgressCard goals={dashboard?.goals || []} />
        </div>
      </div>
    </div>
  );
}
"""

FILES_ANALYTICS = {
    r"E:\SpeakingTraining\apps\api\app\api\v1\analytics.py": ANALYTICS_API,
    r"E:\SpeakingTraining\apps\web\features\analytics\components\SenseiDiagnosticCard.tsx": DIAGNOSTIC_CARD,
    r"E:\SpeakingTraining\apps\web\features\analytics\components\FourPillarsRadarCard.tsx": PILLARS_CARD,
    r"E:\SpeakingTraining\apps\web\features\analytics\index.ts": ANALYTICS_INDEX,
    r"E:\SpeakingTraining\apps\web\app\progress\page.tsx": PROGRESS_PAGE,
}

for filepath, content in FILES_ANALYTICS.items():
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"Successfully wrote {os.path.basename(filepath)}")

print("All Dynamic Analytics Studio files updated successfully!")
