import os

# 1. profile_service.py
PROFILE_SERVICE = '''from datetime import datetime, timezone
from typing import Any
import json

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import logger
from app.domains.ai.contracts import AIMessage, AIMessageRole, AIRequest, AITask
from app.domains.ai.router import AIRouter
from app.domains.conversation.models import ConversationSession, ConversationTurn
from app.domains.conversation_intelligence.models import SessionAnalysis, TurnAnalysis
from app.domains.learning.models import ExerciseAttempt
from app.domains.pronunciation.models import PronunciationAttempt
from app.domains.learner_memory.level_assessor import LevelAssessor
from app.domains.learner_memory.mastery import MasteryEstimator
from app.domains.learner_memory.models import LearnerMemory, LearnerProfile, MemoryEvidence
from app.domains.learner_memory.scorer import MemoryScorer
from app.domains.learner_memory.trend_analyzer import TrendAnalyzer


class LearnerProfileService:
    """Orchestrates long-term learner profile recalculation, scoring updates, and AI learner summary synthesis."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_router = AIRouter(db)

    async def get_or_create_profile(self, user_id: str) -> LearnerProfile:
        """Retrieves existing profile or creates a clean starting profile."""
        stmt = select(LearnerProfile).where(LearnerProfile.user_id == user_id)
        res = await self.db.execute(stmt)
        profile = res.scalar_one_or_none()

        if not profile:
            profile = LearnerProfile(
                user_id=user_id,
                overall_level="intermediate",
                speaking_level="intermediate",
                fluency_level="intermediate",
                grammar_level="intermediate",
                vocabulary_level="intermediate",
                naturalness_level="intermediate",
                confidence_score=0.35,
                level_confidence="insufficient_evidence",
                total_sessions_analyzed=0,
                total_turns_analyzed=0,
                strengths=[],
                weaknesses=[],
                learning_goals=["Giao tiếp tự nhiên trong hội thoại đời sống và công việc"],
                summary="Người học đang bắt đầu lộ trình luyện nói tiếng Nhật phản xạ.",
                summary_version=1,
                last_recalculated_at=datetime.now(timezone.utc),
            )
            self.db.add(profile)
            await self.db.flush()

        return profile

    async def recalculate_profile(
        self,
        user_id: str,
        generate_ai_summary: bool = True,
    ) -> LearnerProfile:
        """Fully recalculates all user memories, scoring, mastery, trends, levels, and profile synthesis."""
        profile = await self.get_or_create_profile(user_id)

        # 1. Fetch all user sessions and attempts across ALL 4 Studio modes
        sessions_stmt = select(ConversationSession).where(
            ConversationSession.user_id == user_id,
            ConversationSession.status == "completed",
        )
        s_res = await self.db.execute(sessions_stmt)
        sessions = s_res.scalars().all()
        session_ids = [s.id for s in sessions]

        # Fetch all studio exercise attempts
        attempts_stmt = (
            select(ExerciseAttempt)
            .options(selectinload(ExerciseAttempt.exercise))
            .where(
                ExerciseAttempt.user_id == user_id,
                ExerciseAttempt.status == "completed",
            )
        )
        att_res = await self.db.execute(attempts_stmt)
        attempts = list(att_res.scalars().all())

        # Fetch pronunciation attempts
        pron_stmt = select(PronunciationAttempt).where(
            PronunciationAttempt.user_id == user_id,
            PronunciationAttempt.analysis_status == "completed",
        )
        pron_res = await self.db.execute(pron_stmt)
        pron_attempts = list(pron_res.scalars().all())

        total_sessions = len(sessions) + len(attempts)
        total_turns = len(sessions) * 6 + len(attempts)

        # 2. Compute 4 core skill scores (0 - 100)
        latencies = []
        for a in attempts:
            rm = (a.metrics_json or {}).get("reflex", {}) if a.metrics_json else {}
            lat = rm.get("reaction_latency_ms", a.response_speed_ms)
            if lat is not None and lat > 0:
                latencies.append(float(lat))
        avg_latency = float(sum(latencies) / len(latencies)) if latencies else 1850.0

        fluency_score = max(30.0, min(95.0, round(100.0 - (avg_latency / 3000.0 * 50.0), 1)))

        correct_count = sum(1 for a in attempts if a.success)
        grammar_score = (
            round(correct_count / len(attempts) * 100.0, 1)
            if attempts
            else 75.0
        )

        pron_scores = [p.overall_score for p in pron_attempts if p.overall_score is not None]
        pron_score = round(sum(pron_scores) / len(pron_scores), 1) if pron_scores else 78.0

        vocab_score = max(50.0, min(95.0, round((grammar_score * 0.5) + (fluency_score * 0.5), 1)))
        composite_score = round((fluency_score + grammar_score + pron_score + vocab_score) / 4.0, 1)

        # 3. Determine JLPT & CEFR Level
        if composite_score >= 88.0:
            jlpt_level = "N1"
            cefr_level = "C1"
            overall_level_label = "advanced"
        elif composite_score >= 78.0:
            jlpt_level = "N2"
            cefr_level = "B2"
            overall_level_label = "upper_intermediate"
        elif composite_score >= 65.0:
            jlpt_level = "N3"
            cefr_level = "B1"
            overall_level_label = "intermediate"
        elif composite_score >= 50.0:
            jlpt_level = "N4"
            cefr_level = "A2"
            overall_level_label = "elementary"
        else:
            jlpt_level = "N5"
            cefr_level = "A1"
            overall_level_label = "beginner"

        # 4. Fetch and recalculate all user memories
        memories_stmt = (
            select(LearnerMemory)
            .where(LearnerMemory.user_id == user_id)
            .execution_options(populate_existing=True)
        )
        m_res = await self.db.execute(memories_stmt)
        memories = m_res.scalars().all()

        for mem in memories:
            ev_stmt = (
                select(MemoryEvidence)
                .where(MemoryEvidence.memory_id == mem.id)
                .order_by(MemoryEvidence.created_at)
            )
            ev_res = await self.db.execute(ev_stmt)
            evidences = ev_res.scalars().all()

            unique_sessions = len({e.session_id for e in evidences})
            mem.evidence_count = len(evidences)
            mem.contexts_used = list({e.context_tag for e in evidences if e.context_tag})
            mem.confidence = MemoryScorer.calculate_confidence(
                evidence_count=len(evidences),
                unique_sessions_count=unique_sessions,
            )
            mem.mastery = MasteryEstimator.estimate_mastery(mem)
            trend, status = TrendAnalyzer.analyze_trend(mem, evidences)
            mem.trend = trend.value
            if mem.status not in ("dismissed", "archived"):
                mem.status = status

            if mem.memory_type == "strength":
                mem.priority_score = MemoryScorer.calculate_strength_score(
                    mem, unique_sessions, max(1, total_sessions)
                )
            else:
                mem.priority_score = MemoryScorer.calculate_weakness_priority(
                    mem, unique_sessions, max(1, total_sessions)
                )

        await self.db.flush()

        weaknesses_pool = [
            m for m in memories
            if m.memory_type in ("grammar", "particle", "conjugation", "politeness", "filler", "word_choice", "vocabulary", "naturalness")
            and m.status not in ("dismissed", "archived")
        ]
        weaknesses_pool.sort(key=lambda m: (m.priority_score, m.last_seen), reverse=True)

        top_weaknesses_data = []
        for w in weaknesses_pool[:5]:
            top_weaknesses_data.append({
                "id": w.id,
                "key": w.key,
                "statement": w.statement,
                "category": w.category or w.memory_type,
                "priority_score": round(w.priority_score, 2),
                "mastery": round(w.mastery, 2),
                "trend": w.trend,
                "evidence_count": w.evidence_count,
                "is_regression": w.is_regression,
                "severity": w.severity,
                "last_seen": w.last_seen.isoformat() if w.last_seen else None,
            })

        strengths_pool = [
            m for m in memories
            if m.memory_type == "strength" and m.status not in ("dismissed", "archived")
        ]
        strengths_pool.sort(key=lambda m: (m.priority_score, m.last_seen), reverse=True)

        top_strengths_data = []
        for s in strengths_pool[:5]:
            top_strengths_data.append({
                "id": s.id,
                "key": s.key,
                "statement": s.statement,
                "priority_score": round(s.priority_score, 2),
                "mastery": round(s.mastery, 2),
                "evidence_count": s.evidence_count,
                "last_seen": s.last_seen.isoformat() if s.last_seen else None,
            })

        goals_pool = [m.statement for m in memories if m.memory_type == "goal" and m.status != "dismissed"]
        learning_goals = goals_pool if goals_pool else (profile.learning_goals or ["Giao tiếp tự nhiên trong đời sống và công việc"])

        profile.overall_level = overall_level_label
        profile.speaking_level = overall_level_label
        profile.fluency_level = "upper_intermediate" if fluency_score >= 75 else "intermediate"
        profile.grammar_level = "upper_intermediate" if grammar_score >= 75 else "intermediate"
        profile.vocabulary_level = "upper_intermediate" if vocab_score >= 75 else "intermediate"
        profile.naturalness_level = "upper_intermediate" if pron_score >= 75 else "intermediate"
        profile.confidence_score = 0.85 if total_sessions >= 10 else 0.55
        profile.level_confidence = "high" if total_sessions >= 10 else "medium"
        profile.total_sessions_analyzed = total_sessions
        profile.total_turns_analyzed = total_turns
        profile.avg_response_speed_ms = avg_latency
        profile.weaknesses = top_weaknesses_data
        profile.strengths = top_strengths_data
        profile.learning_goals = learning_goals

        if top_weaknesses_data:
            profile.current_focus = f"Khắc phục {top_weaknesses_data[0]['statement']}"
        else:
            profile.current_focus = "Nâng cao phản xạ hội thoại và chuẩn hóa Kính ngữ công sở"

        # 5. Synthesize AI Learner Summary
        if generate_ai_summary and total_sessions >= 1:
            try:
                prompt = (
                    f"Hãy soạn một bản nhận xét năng lực hội thoại tổng quan (Speaking Portfolio Certificate Summary) cho học viên:\\n"
                    f"- Tổng số lượt luyện tập: {total_sessions} buổi\\n"
                    f"- Điểm Trôi chảy: {fluency_score}% (Độ trễ trung bình: {int(avg_latency)}ms)\\n"
                    f"- Điểm Ngữ pháp: {grammar_score}%\\n"
                    f"- Điểm Ngữ âm: {pron_score}%\\n"
                    f"- Ước tính cấp độ: {jlpt_level} ({cefr_level})\\n"
                    f"- Điểm mạnh: {', '.join([s['statement'] for s in top_strengths_data]) if top_strengths_data else 'Phản xạ câu đơn tốt'}\\n"
                    f"- Cần cải thiện: {', '.join([w['statement'] for w in top_weaknesses_data]) if top_weaknesses_data else 'Kính ngữ và ngữ điệu'}\\n\\n"
                    f"Yêu cầu: Viết 2-3 câu nhận xét truyền cảm hứng, chuẩn phong cách Nhật Bản, ghi nhận nỗ lực rèn luyện của học viên."
                )
                req = AIRequest(
                    messages=[AIMessage(role=AIMessageRole.USER, content=prompt)],
                    system_instruction="Bạn là AI Sensei cố vấn ngôn ngữ tiếng Nhật. Viết nhận xét ngắn gọn, ấm áp, sâu sắc.",
                    temperature=0.7,
                )
                resp = await self.ai_router.generate(task=AITask.COACH_INSIGHT, request=req, user_id=user_id)
                profile.summary = resp.text.strip()
                profile.summary_version += 1
                profile.summary_generated_at = datetime.now(timezone.utc)
            except Exception as e:
                logger.warning(f"[LearnerProfileService] AI summary fallback: {e}")
                profile.summary = f"Học viên đã hoàn thành {total_sessions} buổi luyện với tốc độ phản xạ {int(avg_latency)}ms. Năng lực hội thoại ước tính đạt chuẩn {jlpt_level} ({cefr_level})."

        profile.last_recalculated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(profile)
        logger.info(f"[LearnerProfileService] Recalculated profile for user '{user_id}' (JLPT: {jlpt_level})")
        return profile
'''

# 2. SpeakingCertificateCard.tsx
CERTIFICATE_CARD = """\"use client\";

import React from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Award,
  Sparkles,
  RefreshCw,
  Zap,
  Target,
  CheckCircle2,
  Calendar,
  Compass,
} from "lucide-react";
import { LearnerProfile } from "@/types/profile";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

interface SpeakingCertificateCardProps {
  profile: LearnerProfile | null;
  recalculating: boolean;
  onRecalculate: () => void;
}

export function SpeakingCertificateCard({
  profile,
  recalculating,
  onRecalculate,
}: SpeakingCertificateCardProps) {
  if (!profile) return null;

  const jlptLevel = profile.overall_level === "advanced" ? "N1" :
                    profile.overall_level === "upper_intermediate" ? "N2" :
                    profile.overall_level === "intermediate" ? "N3" :
                    profile.overall_level === "elementary" ? "N4" : "N5";

  const cefrLevel = profile.overall_level === "advanced" ? "C1" :
                    profile.overall_level === "upper_intermediate" ? "B2" :
                    profile.overall_level === "intermediate" ? "B1" :
                    profile.overall_level === "elementary" ? "A2" : "A1";

  const speedMs = profile.avg_response_speed_ms ? Math.round(profile.avg_response_speed_ms) : 1850;

  return (
    <div className="p-6 md:p-8 rounded-3xl border border-primary/30 bg-card washi-texture shadow-sm space-y-6 relative overflow-hidden ring-1 ring-primary/20">
      <div className="absolute top-0 right-0 h-56 w-56 bg-primary/10 rounded-full blur-3xl pointer-events-none" />

      {/* Top Bar: Title & Recalculate Button */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 relative z-10 border-b border-border/60 pb-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Badge variant="kintsugi" size="sm" className="font-bold">
              AI SPEAKING PORTFOLIO CERTIFICATE
            </Badge>
            <Badge variant="matcha" size="sm" className="font-bold">
              ĐÃ XÁC THỰC
            </Badge>
          </div>
          <h2 className="text-xl md:text-2xl font-black text-foreground tracking-tight flex items-center gap-2">
            <span>Hồ Sơ Năng Lực Hội Thoại Tiếng Nhật</span>
            <span className="text-sm font-jp font-normal text-muted-foreground">(学習者カルテ)</span>
          </h2>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            soundFX.playFurin();
            onRecalculate();
          }}
          disabled={recalculating}
          className="text-xs font-bold rounded-xl border-border self-start sm:self-auto gap-1.5"
        >
          <RefreshCw className={cn("h-3.5 w-3.5", recalculating && "animate-spin text-primary")} />
          <span>{recalculating ? "Đang tính toán..." : "Tái tổng hợp dữ liệu"}</span>
        </Button>
      </div>

      {/* Main Certificate Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative z-10">
        {/* Big JLPT & CEFR Level Badge */}
        <div className="p-6 rounded-2xl bg-muted/40 border border-border/80 flex flex-col items-center justify-center text-center space-y-2 shadow-2xs">
          <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">
            Trình Độ Ước Tính (Speaking Level)
          </span>
          <div className="flex items-baseline gap-2">
            <span className="text-4xl md:text-5xl font-black text-primary font-mono tracking-tight">
              {jlptLevel}
            </span>
            <span className="text-lg font-bold text-muted-foreground font-mono">
              / {cefrLevel}
            </span>
          </div>
          <Badge variant="outline" size="sm" className="text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 border-emerald-500/30">
            {profile.level_confidence === "high" ? "Độ tin cậy cao (High Confidence)" : "Độ tin cậy tiêu chuẩn"}
          </Badge>
        </div>

        {/* Sessions & Reflex Speed Stats */}
        <div className="md:col-span-2 grid grid-cols-2 gap-3.5">
          <div className="p-4 rounded-2xl bg-card border border-border/80 space-y-1 shadow-2xs">
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground font-semibold">
              <Compass className="h-4 w-4 text-primary" />
              <span>Tổng Số Buổi Luyện Tập</span>
            </div>
            <div className="text-2xl font-black text-foreground font-mono">
              {profile.total_sessions_analyzed || 0} <span className="text-xs font-normal text-muted-foreground">buổi</span>
            </div>
            <p className="text-[10px] text-muted-foreground">Đã quét toàn bộ 4 chuyên đề Studio</p>
          </div>

          <div className="p-4 rounded-2xl bg-card border border-border/80 space-y-1 shadow-2xs">
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground font-semibold">
              <Zap className="h-4 w-4 text-amber-500" />
              <span>Tốc Độ Phản Xạ TB</span>
            </div>
            <div className="text-2xl font-black text-foreground font-mono">
              {speedMs} <span className="text-xs font-normal text-muted-foreground">ms</span>
            </div>
            <p className="text-[10px] text-muted-foreground">Thời gian khởi động câu nói</p>
          </div>

          <div className="p-4 rounded-2xl bg-card border border-border/80 space-y-1 shadow-2xs col-span-2">
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground font-semibold">
              <Target className="h-4 w-4 text-rose-500" />
              <span>Trọng Tâm Rèn Luyện Hiện Tại</span>
            </div>
            <div className="text-xs font-bold text-foreground">
              {profile.current_focus || "Nâng cao phản xạ hội thoại và chuẩn hóa Kính ngữ công sở"}
            </div>
          </div>
        </div>
      </div>

      {/* AI Sensei Narrative Summary Quote */}
      {profile.summary && (
        <div className="p-4 rounded-2xl bg-primary/5 border border-primary/20 flex items-start gap-3 text-xs leading-relaxed text-foreground relative z-10">
          <span className="p-2 rounded-xl bg-primary/10 text-primary shrink-0 mt-0.5">
            <Sparkles className="h-4 w-4" />
          </span>
          <div className="space-y-1">
            <span className="font-bold text-primary">Nhận xét từ AI Sensei (Speaking Portfolio Summary):</span>
            <p className="text-muted-foreground">{profile.summary}</p>
          </div>
        </div>
      )}
    </div>
  );
}
"""

# 3. FourSkillGaugesCard.tsx
SKILL_GAUGES = """\"use client\";

import React from "react";
import { Badge } from "@/components/ui/badge";
import {
  Waves,
  Ruler,
  Volume2,
  BookOpen,
  Shield,
} from "lucide-react";
import { LearnerProfile } from "@/types/profile";
import { cn } from "@/lib/utils";

interface FourSkillGaugesCardProps {
  profile: LearnerProfile | null;
}

export function FourSkillGaugesCard({ profile }: FourSkillGaugesCardProps) {
  if (!profile) return null;

  const levelToScore = (lvl: string) => {
    switch (lvl) {
      case "advanced": return 92;
      case "upper_intermediate": return 82;
      case "intermediate": return 72;
      case "elementary": return 58;
      default: return 45;
    }
  };

  const skills = [
    {
      title: "1. Độ Trôi Chảy & Tốc Độ",
      jaTitle: "流暢さ・瞬発力",
      score: levelToScore(profile.fluency_level),
      icon: <Waves className="h-4 w-4 text-sky-500" />,
      desc: "Thời gian suy nghĩ và độ liên tục khi phát ngôn",
      color: "sky",
    },
    {
      title: "2. Độ Chuẩn Ngữ Pháp",
      jaTitle: "文法正確性",
      score: levelToScore(profile.grammar_level),
      icon: <Ruler className="h-4 w-4 text-emerald-500" />,
      desc: "Chia thể động từ, trợ từ và cấu trúc câu phức",
      color: "emerald",
    },
    {
      title: "3. Ngữ Âm & Cao Độ Tokyo",
      jaTitle: "発音・ピッチ",
      score: levelToScore(profile.naturalness_level),
      icon: <Volume2 className="h-4 w-4 text-purple-500" />,
      desc: "Cao độ từ vựng, phách Mora và ngữ điệu câu",
      color: "purple",
    },
    {
      title: "4. Vốn Từ & Biểu Đạt",
      jaTitle: "語彙力・表現",
      score: levelToScore(profile.vocabulary_level),
      icon: <BookOpen className="h-4 w-4 text-amber-500" />,
      desc: "Độ phong phú từ vựng và Kính ngữ theo ngữ cảnh",
      color: "amber",
    },
  ];

  return (
    <div className="p-6 rounded-3xl border border-border bg-card washi-texture shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield className="h-5 w-5 text-primary" />
          <h3 className="text-sm font-bold text-foreground">
            Bảng Đánh Giá 4 Trục Kỹ Năng Cốt Lõi (Core Skill Competencies)
          </h3>
        </div>
        <Badge variant="outline" size="sm" className="text-xs font-semibold">
          EVALUATED
        </Badge>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {skills.map((s, idx) => (
          <div
            key={idx}
            className="p-4 rounded-2xl border border-border/80 bg-card shadow-2xs space-y-3"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-xl bg-muted/50 border border-border/80">
                  {s.icon}
                </div>
                <div>
                  <h4 className="text-xs font-bold text-foreground">{s.title}</h4>
                  <span className="text-[10px] text-muted-foreground font-jp">{s.jaTitle}</span>
                </div>
              </div>
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-muted-foreground font-semibold">{s.desc}</span>
                <span className="font-bold font-mono text-primary">{s.score}%</span>
              </div>

              <div className="w-full h-2 rounded-full bg-muted/60 overflow-hidden">
                <div
                  className={cn(
                    "h-full rounded-full transition-all duration-500",
                    s.score >= 80 ? "bg-emerald-500" : s.score >= 65 ? "bg-primary" : "bg-amber-500"
                  )}
                  style={{ width: `${s.score}%` }}
                />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
"""

# 4. profile/index.ts
PROFILE_INDEX = """export * from "./components/SpeakingCertificateCard";
export * from "./components/FourSkillGaugesCard";
"""

# 5. app/profile/page.tsx
PROFILE_PAGE = """\"use client\";

import React, { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { profileApi } from "@/services/profile-api";
import {
  LearnerMemory,
  LearnerMemoryDetail,
  LearnerProfile,
  LearningPriority,
  MemoryEvidence,
} from "@/types/profile";
import { SpeakingCertificateCard, FourSkillGaugesCard } from "@/features/profile";
import { coachCoreApi } from "@/features/coach/services/coachCoreApi";
import {
  Brain,
  TrendingUp,
  TrendingDown,
  Minus,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  Eye,
  XCircle,
  HelpCircle,
  Clock,
  Award,
  Zap,
  Target,
  ArrowRight,
  RotateCcw,
  Sliders,
} from "lucide-react";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";
import Link from "next/link";

export default function LearnerProfilePage() {
  const [profile, setProfile] = useState<LearnerProfile | null>(null);
  const [weaknesses, setWeaknesses] = useState<LearnerMemory[]>([]);
  const [strengths, setStrengths] = useState<LearnerMemory[]>([]);
  const [priorities, setPriorities] = useState<LearningPriority[]>([]);
  const [selectedMemory, setSelectedMemory] = useState<LearnerMemoryDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [recalculating, setRecalculating] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"weaknesses" | "strengths" | "priorities">("weaknesses");

  const loadData = async () => {
    try {
      setLoading(true);
      const [profData, weakData, strData, prioData] = await Promise.all([
        profileApi.getProfile(),
        profileApi.getTopWeaknesses(10),
        profileApi.getTopStrengths(10),
        profileApi.getLearningPriorities(5),
      ]);
      setProfile(profData);
      setWeaknesses(weakData);
      setStrengths(strData);
      setPriorities(prioData);
    } catch (err) {
      console.error("Failed to load learner profile:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRecalculate = async () => {
    try {
      setRecalculating(true);
      const updated = await profileApi.recalculateProfile();
      setProfile(updated);
      const [weakData, strData, prioData] = await Promise.all([
        profileApi.getTopWeaknesses(10),
        profileApi.getTopStrengths(10),
        profileApi.getLearningPriorities(5),
      ]);
      setWeaknesses(weakData);
      setStrengths(strData);
      setPriorities(prioData);
    } catch (err) {
      console.error("Failed to recalculate profile:", err);
    } finally {
      setRecalculating(false);
    }
  };

  const handleOpenEvidence = async (memoryId: string) => {
    try {
      setDetailLoading(true);
      const detail = await profileApi.getMemoryDetail(memoryId);
      setSelectedMemory(detail);
    } catch (err) {
      console.error("Failed to load memory detail:", err);
    } finally {
      setDetailLoading(false);
    }
  };

  const getTrendBadge = (trend: string, isRegression: boolean) => {
    if (isRegression) {
      return (
        <Badge variant="sakura" size="sm" className="gap-1 animate-pulse">
          <RotateCcw className="h-3 w-3" />
          <span>Tái phát (Regression)</span>
        </Badge>
      );
    }
    switch (trend) {
      case "improving":
        return (
          <Badge variant="matcha" size="sm" className="gap-1">
            <TrendingUp className="h-3 w-3 text-emerald-400" />
            <span>Đang tiến bộ</span>
          </Badge>
        );
      case "worsening":
        return (
          <Badge variant="sakura" size="sm" className="gap-1">
            <TrendingDown className="h-3 w-3 text-rose-400" />
            <span>Cần chú ý</span>
          </Badge>
        );
      case "resolved":
        return (
          <Badge variant="fuji" size="sm" className="gap-1">
            <CheckCircle2 className="h-3 w-3 text-indigo-400" />
            <span>Đã khắc phục</span>
          </Badge>
        );
      default:
        return (
          <Badge variant="outline" size="sm" className="gap-1 text-muted-foreground">
            <Minus className="h-3 w-3" />
            <span>Ổn định</span>
          </Badge>
        );
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300 max-w-6xl mx-auto pb-16">
      {/* 1. Speaking Certificate Card */}
      <SpeakingCertificateCard
        profile={profile}
        recalculating={recalculating}
        onRecalculate={handleRecalculate}
      />

      {/* 2. Four Skill Competency Gauges */}
      <FourSkillGaugesCard profile={profile} />

      {/* 3. Error Memory & Linguistic Strengths Intelligence */}
      <div className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-primary" />
            <h3 className="text-sm font-bold text-foreground">
              Sổ Tay Trí Tuệ Lỗi & Điểm Sáng Ngôn Ngữ (Learner Memory Intelligence)
            </h3>
          </div>

          {/* Filter Pills */}
          <div className="flex items-center gap-1.5">
            <button
              type="button"
              onClick={() => {
                soundFX.playFurin();
                setActiveTab("weaknesses");
              }}
              className={cn(
                "px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all",
                activeTab === "weaknesses"
                  ? "bg-primary text-primary-foreground border-primary shadow-xs"
                  : "bg-muted/40 border-border text-muted-foreground hover:text-foreground"
              )}
            >
              ⚠️ Điểm Cần Khắc Phục ({weaknesses.length})
            </button>

            <button
              type="button"
              onClick={() => {
                soundFX.playFurin();
                setActiveTab("strengths");
              }}
              className={cn(
                "px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all",
                activeTab === "strengths"
                  ? "bg-primary text-primary-foreground border-primary shadow-xs"
                  : "bg-muted/40 border-border text-muted-foreground hover:text-foreground"
              )}
            >
              ✨ Điểm Sáng Ngôn Ngữ ({strengths.length})
            </button>

            <button
              type="button"
              onClick={() => {
                soundFX.playFurin();
                setActiveTab("priorities");
              }}
              className={cn(
                "px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all",
                activeTab === "priorities"
                  ? "bg-primary text-primary-foreground border-primary shadow-xs"
                  : "bg-muted/40 border-border text-muted-foreground hover:text-foreground"
              )}
            >
              🎯 Ưu Tiên Ôn Tập ({priorities.length})
            </button>
          </div>
        </div>

        {/* Tab Content */}
        {loading ? (
          <div className="p-8 text-center text-xs text-muted-foreground animate-pulse">
            Đang tải trí tuệ lỗi từ cơ sở dữ liệu...
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
            {activeTab === "weaknesses" && (
              weaknesses.length === 0 ? (
                <div className="col-span-2 p-8 text-center text-xs text-muted-foreground border rounded-2xl">
                  Chưa ghi nhận lỗi sai nào lặp lại. Tuyệt vời!
                </div>
              ) : (
                weaknesses.map((w) => (
                  <div
                    key={w.id}
                    className="p-4 rounded-2xl border border-border/80 bg-card shadow-2xs space-y-2.5 hover:border-primary/40 transition-all"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="space-y-1">
                        <span className="text-xs font-bold text-foreground font-jp">{w.statement}</span>
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] text-muted-foreground uppercase font-mono">{w.category || w.memory_type}</span>
                          <span className="text-[10px] text-muted-foreground">• {w.evidence_count} lần ghi nhận</span>
                        </div>
                      </div>
                      {getTrendBadge(w.trend, w.is_regression)}
                    </div>

                    <div className="flex items-center justify-between pt-1 border-t border-border/60">
                      <button
                        type="button"
                        onClick={() => handleOpenEvidence(w.id)}
                        className="text-[11px] font-bold text-primary flex items-center gap-1 hover:underline"
                      >
                        <Eye className="h-3.5 w-3.5" />
                        <span>Xem bằng chứng ({w.evidence_count})</span>
                      </button>

                      <Link href="/learning">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 text-[11px] font-bold text-muted-foreground hover:text-foreground gap-1 px-2"
                        >
                          <span>Luyện bài khắc phục</span>
                          <ArrowRight className="h-3 w-3" />
                        </Button>
                      </Link>
                    </div>
                  </div>
                ))
              )
            )}

            {activeTab === "strengths" && (
              strengths.map((s) => (
                <div
                  key={s.id}
                  className="p-4 rounded-2xl border border-emerald-500/20 bg-emerald-500/5 shadow-2xs space-y-2"
                >
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                    <span className="text-xs font-bold text-foreground font-jp">{s.statement}</span>
                  </div>
                  <div className="text-[10px] text-muted-foreground pl-6">
                    Đã kiểm chứng qua {s.evidence_count} lượt hội thoại thành công.
                  </div>
                </div>
              ))
            )}

            {activeTab === "priorities" && (
              priorities.map((p, idx) => (
                <div
                  key={idx}
                  className="p-4 rounded-2xl border border-amber-500/20 bg-amber-500/5 shadow-2xs space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-foreground">{p.recommended_focus}</span>
                    <Badge variant="outline" size="sm" className="text-[10px] text-amber-600 dark:text-amber-400 font-mono">
                      Ưu tiên {Math.round(p.priority_score * 100)}%
                    </Badge>
                  </div>
                  <p className="text-[11px] text-muted-foreground leading-snug">{p.reason}</p>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* Evidence Detail Modal */}
      {selectedMemory && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs" role="dialog">
          <div className="bg-card border border-border rounded-3xl max-w-lg w-full p-6 space-y-4 shadow-2xl washi-texture">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div className="space-y-0.5">
                <span className="text-[10px] text-muted-foreground uppercase font-mono font-bold">BẰNG CHỨNG LỖI NGỮ CẢNH</span>
                <h3 className="text-sm font-bold text-foreground">{selectedMemory.statement}</h3>
              </div>
              <button
                type="button"
                onClick={() => setSelectedMemory(null)}
                className="p-1 rounded-lg hover:bg-muted text-muted-foreground"
              >
                <XCircle className="h-5 w-5" />
              </button>
            </div>

            <div className="max-h-80 overflow-y-auto space-y-2.5 pr-1">
              {selectedMemory.evidences?.map((e) => (
                <div key={e.id} className="p-3 rounded-xl bg-muted/40 border border-border/80 space-y-1.5 text-xs">
                  {e.original_snippet && (
                    <div className="text-rose-600 dark:text-rose-400 font-mono">
                      ❌ Câu bạn nói: "{e.original_snippet}"
                    </div>
                  )}
                  {e.corrected_snippet && (
                    <div className="text-emerald-600 dark:text-emerald-400 font-mono">
                      ✨ Gợi ý chuẩn: "{e.corrected_snippet}"
                    </div>
                  )}
                  <div className="text-[10px] text-muted-foreground">
                    Ngữ cảnh: {e.context_tag || "Hội thoại"} • {new Date(e.created_at).toLocaleDateString("vi-VN")}
                  </div>
                </div>
              ))}
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setSelectedMemory(null)}
              className="w-full text-xs font-bold rounded-xl"
            >
              Đóng
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
"""

FILES_PROFILE = {
    r"E:\SpeakingTraining\apps\api\app\domains\learner_memory\profile_service.py": PROFILE_SERVICE,
    r"E:\SpeakingTraining\apps\web\features\profile\components\SpeakingCertificateCard.tsx": CERTIFICATE_CARD,
    r"E:\SpeakingTraining\apps\web\features\profile\components\FourSkillGaugesCard.tsx": SKILL_GAUGES,
    r"E:\SpeakingTraining\apps\web\features\profile\index.ts": PROFILE_INDEX,
    r"E:\SpeakingTraining\apps\web\app\profile\page.tsx": PROFILE_PAGE,
}

for filepath, content in FILES_PROFILE.items():
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"Successfully wrote {os.path.basename(filepath)}")

print("All Profile files written successfully!")
