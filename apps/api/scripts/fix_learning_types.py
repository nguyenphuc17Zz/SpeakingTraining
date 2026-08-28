import os

TYPES_LEARNING = """export type LearningGoalType =
  | "speaking"
  | "pronunciation"
  | "conversation"
  | "workplace"
  | "travel"
  | "interview"
  | "jlpt"
  | "naturalness"
  | "fluency";

export type LearningGoalStatus = "active" | "paused" | "completed" | "archived";

export interface LearningGoal {
  id: string;
  title: string;
  description: string | null;
  goal_type: LearningGoalType;
  priority: number;
  status: LearningGoalStatus;
  target_date: string | null;
  created_at: string;
  updated_at: string;
}

export type LearningItemLifecycle =
  | "discovered"
  | "active"
  | "practicing"
  | "improving"
  | "mastered"
  | "maintenance"
  | "regressed";

export interface LearningItem {
  id: string;
  key: string;
  item_type: string;
  title: string;
  description: string | null;
  difficulty: string;
  lifecycle: LearningItemLifecycle;
  status: string;
  overall_mastery: number;
  recognition_mastery: number;
  production_mastery: number;
  spontaneous_mastery: number;
  context_variety_score: number;
  confidence: number;
  priority_score: number;
  attempt_count: number;
  success_count: number;
  review_streak: number;
  review_interval_days: number;
  last_practiced_at: string | null;
  next_review_at: string | null;
}

export interface SpeechSupport {
  keywords: string[];
  grammar_structures: string[];
  sentence_starters: string[];
  sample_dialogue_turns: { speaker: string; text: string; translation?: string }[];
}

export interface Exercise {
  id: string;
  exercise_type: string;
  title: string;
  objective: string;
  scenario: string | null;
  instructions: string;
  constraints: string[];
  target_patterns: string[];
  difficulty: string;
  scaffold_level: string;
  scaffold_hint: string | null;
  estimated_minutes: number;
  created_at: string;
  canonical?: string;
  acceptable_variants?: string[];
  prompt?: string;
  extra_metadata?: any;
}

export interface ExerciseResult {
  exercise_id: string;
  user_id: string;
  score: number;
  success: boolean;
  confidence: number;
  target_mastery_delta: Record<string, number>;
  feedback: string;
  evidence: string[];
  metrics: Record<string, any>;
  independence: string;
  response_speed_ms: number | null;
  target_usage: string;
  pronunciation_score: number | null;
  grammar_score: number | null;
  naturalness_score: number | null;
  attempt_id: string | null;
}

export interface ExerciseStartResponse {
  exercise: Exercise;
  session_id?: string;
  pronunciation_attempt_id?: string;
  initial_context?: Record<string, any>;
}

export interface LearningPlanItem {
  id: string;
  plan_id: string;
  exercise_id: string;
  planned_order: number;
  status: "pending" | "in_progress" | "completed" | "skipped";
  duration_minutes: number;
  priority_score: number;
  exercise?: Exercise;
  target_type?: string;
  title?: string;
  estimated_minutes?: number;
}

export interface DailyPlan {
  id: string;
  user_id: string;
  plan_date: string;
  total_duration_minutes: number;
  estimated_minutes: number;
  status: "active" | "completed" | "archived";
  items: LearningPlanItem[];
  created_at: string;
  focus_title?: string;
  focus_reason?: string;
}

export interface LearningRecommendation {
  item?: LearningItem;
  priority_score: number;
  reason: string;
  recommended_action: string;
  why: string;
  how: string;
  // Flat properties for backward compatibility
  item_type?: string;
  difficulty?: string;
  estimated_minutes?: number;
  title?: string;
  mastery_percent?: number;
  success_count?: number;
  attempt_count?: number;
  key?: string;
}

export interface CurriculumUnit {
  id: string;
  title: string;
  objective: string;
  target_learning_items: string[];
  recommended_exercise_types: string[];
  completion_criteria: string;
  estimated_sessions: number;
  is_completed: boolean;
  progress_ratio: number;
}

// 4-Stage Interactive Dynamic AI Roadmap Models
export interface CurriculumNode {
  id: string;
  title: string;
  description: string;
  target_mode: string; // '/pitch' | '/keigo' | '/situations' | '/shadowing' | '/speaking' | '/bosses'
  mode_label: string;
  difficulty: string;
  key_patterns: string[];
  estimated_minutes: number;
  is_completed: boolean;
  score?: number;
}

export interface CurriculumStage {
  stage_number: number;
  title: string;
  badge: string;
  color: "sky" | "emerald" | "purple" | "amber" | string;
  objective: string;
  nodes: CurriculumNode[];
}

export interface CurriculumRoadmap {
  curriculum_id: string;
  title: string;
  description: string;
  level: string;
  level_label: string;
  target_goal: string;
  target_goal_label: string;
  daily_minutes: number;
  estimated_weeks: number;
  total_lessons: number;
  stages: CurriculumStage[];
}
"""

LEARNING_PAGE = """\"use client\";

import React, { useState, useEffect, useCallback } from "react";
import {
  Sparkles,
  Flame,
  Target,
  RefreshCw,
  Compass,
  ArrowRight,
  RotateCw,
  Wand2,
  Calendar,
  Layers,
} from "lucide-react";
import Link from "next/link";
import { coachCoreApi } from "@/features/coach/services/coachCoreApi";
import {
  DailyPlanCard,
  PriorityCard,
  ReviewQueueCard,
  CurriculumPathwayCard,
  ExerciseModal,
  InteractiveRoadmapView,
  CurriculumOnboardingModal,
  CurriculumNodeDetailModal,
  useLearningPlan,
  useLearningPriorities,
  useExercise,
} from "@/features/learning";
import { learningApi } from "@/services/learning-api";
import { CurriculumNode, CurriculumRoadmap } from "@/types/learning";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { soundFX } from "@/lib/sound-fx";

export default function LearningDashboardPage() {
  const {
    plan,
    timeBudget,
    loading: planLoading,
    regenerating: planRegenerating,
    setTimeBudget,
    refreshPlan,
    regeneratePlan,
  } = useLearningPlan(30);

  const {
    priorities,
    dueReviews,
    goals,
    curriculum,
    loading: prioritiesLoading,
    refresh: refreshPriorities,
  } = useLearningPriorities();

  const {
    activeExercise,
    result,
    loading: exerciseLoading,
    submitting,
    showHint,
    startExercise,
    revealHint,
    submitTranscript,
    resetExercise,
  } = useExercise();

  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [activePlanItemId, setActivePlanItemId] = useState<string | undefined>();

  // Dynamic AI Roadmap state
  const [roadmap, setRoadmap] = useState<CurriculumRoadmap | null>(null);
  const [roadmapLoading, setRoadmapLoading] = useState<boolean>(true);
  const [isOnboardingOpen, setIsOnboardingOpen] = useState<boolean>(false);
  const [selectedNode, setSelectedNode] = useState<CurriculumNode | null>(null);

  const fetchRoadmap = useCallback(async () => {
    try {
      setRoadmapLoading(true);
      const data = await learningApi.getRoadmap();
      setRoadmap(data);
    } catch (e) {
      console.warn("Failed to fetch roadmap:", e);
    } finally {
      setRoadmapLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRoadmap();
  }, [fetchRoadmap]);

  const handleGenerateRoadmap = async (data: {
    level: string;
    target_goal: string;
    daily_minutes: number;
    custom_wish?: string;
  }) => {
    const updated = await learningApi.generateRoadmap(data);
    setRoadmap(updated);
    refreshPriorities();
    refreshPlan();
  };

  const handleToggleNode = async (nodeId: string, isCompleted: boolean) => {
    const updated = await learningApi.toggleRoadmapNode(nodeId, { is_completed: isCompleted });
    setRoadmap(updated);
  };

  const handleStartPlanExercise = async (exerciseId: string, planItemId: string) => {
    setActivePlanItemId(planItemId);
    setIsModalOpen(true);
    await startExercise(exerciseId);
  };

  const handleStartPriorityPractice = async (key: string) => {
    const match = plan?.items.find((i) => i.exercise?.target_patterns?.includes(key));
    if (match) {
      await handleStartPlanExercise(match.exercise_id, match.id);
    } else {
      if (plan?.items && plan.items.length > 0) {
        await handleStartPlanExercise(plan.items[0].exercise_id, plan.items[0].id);
      }
    }
  };

  const handleSubmitResponse = async (transcript: string) => {
    const res = await submitTranscript(transcript, {
      plan_item_id: activePlanItemId,
    });
    if (res) {
      refreshPlan();
      refreshPriorities();
      fetchRoadmap();
    }
  };

  const handleNextExercise = () => {
    resetExercise();
    setIsModalOpen(false);
  };

  const [coachTip, setCoachTip] = useState<string | null>(null);
  useEffect(() => {
    const CK = "coach_tip_learning";
    const cached = sessionStorage.getItem(CK);
    if (cached) {
      setCoachTip(cached);
      return;
    }
    coachCoreApi
      .chat({
        message: "Cho 1 lời khuyên ngắn (1 câu) về phương pháp rèn luyện nói hôm nay.",
        current_route: "/learning",
      })
      .then((d) => {
        if (d.response) {
          setCoachTip(d.response);
          try {
            sessionStorage.setItem(CK, d.response);
          } catch {}
        }
      })
      .catch(() => {});
  }, []);

  return (
    <div className="space-y-8 animate-in fade-in duration-300 max-w-6xl mx-auto pb-16">
      {/* 1. Header Banner Haru Washi */}
      <div className="relative overflow-hidden rounded-3xl border border-border bg-card p-6 md:p-8 washi-texture shadow-sm space-y-4">
        <div className="absolute top-0 right-0 h-48 w-48 bg-primary/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Badge variant="matcha" size="sm" className="font-bold">
                ADAPTIVE CURRICULUM & DAILY PLAN
              </Badge>
              <span className="text-xs text-muted-foreground font-semibold">
                Lộ Trình Học Động & Nhiệm Vụ Hôm Nay
              </span>
            </div>
            <h1 className="text-2xl md:text-3xl font-black text-foreground tracking-tight flex items-center gap-3">
              <span className="p-2 rounded-2xl bg-primary/10 border border-primary/20 text-primary inline-flex">
                <Compass className="h-6 w-6" />
              </span>
              <span>Lộ Trình Luyện Nói Cá Nhân Hóa (学習ロードマップ)</span>
            </h1>
            <p className="text-xs md:text-sm text-muted-foreground max-w-2xl leading-relaxed">
              Lộ trình 4 chặng do AI thiết kế riêng cho mục tiêu của bạn. Tự động đồng bộ tiến độ sau mỗi lần luyện nói.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5 shrink-0 self-start md:self-auto">
            <Button
              variant="akane"
              size="sm"
              onClick={() => {
                soundFX.playFurin();
                setIsOnboardingOpen(true);
              }}
              className="text-xs font-bold gap-1.5 shadow-md rounded-xl h-9 px-4"
            >
              <Wand2 className="h-4 w-4" />
              <span>Tạo Lại Lộ Trình AI</span>
            </Button>
          </div>
        </div>

        {/* Coach Sensei Tip */}
        {coachTip && (
          <div className="p-3.5 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-start gap-2.5 text-xs text-amber-900 dark:text-amber-100">
            <Sparkles className="h-4 w-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
            <div className="leading-relaxed">
              <span className="font-bold font-jp">Sensei Tip: </span>
              {coachTip}
            </div>
          </div>
        )}
      </div>

      {/* 2. Interactive Milestone Roadmap (4 Stages & Nodes) */}
      <InteractiveRoadmapView
        roadmap={roadmap}
        onSelectNode={(node) => setSelectedNode(node)}
        onOpenOnboarding={() => setIsOnboardingOpen(true)}
        isLoading={roadmapLoading}
      />

      {/* 3. Today Focus Quests & Priorities Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Daily Plan Column (2 Cols) */}
        <div className="lg:col-span-2 space-y-6">
          <DailyPlanCard
            plan={plan}
            loading={planLoading}
            regenerating={planRegenerating}
            timeBudget={timeBudget}
            onBudgetChange={setTimeBudget}
            onStartExercise={handleStartPlanExercise}
          />
        </div>

        {/* Priorities & Due Reviews (1 Col) */}
        <div className="space-y-6">
          <div className="space-y-3">
            <h3 className="text-xs font-bold text-foreground uppercase tracking-wider">
              Mục Tiêu Ưu Tiên Khắc Phục (Priorities)
            </h3>
            {prioritiesLoading ? (
              <div className="p-8 text-center text-xs text-muted-foreground">Đang tải gợi ý...</div>
            ) : priorities.length === 0 ? (
              <div className="p-6 rounded-2xl border border-border bg-card text-center text-xs text-muted-foreground">
                Chưa có điểm yếu cần ưu tiên đặc biệt.
              </div>
            ) : (
              priorities.map((item, idx) => (
                <PriorityCard
                  key={idx}
                  priority={item}
                  onPractice={handleStartPriorityPractice}
                />
              ))
            )}
          </div>

          <ReviewQueueCard
            dueReviews={dueReviews}
            onStartReview={(id) => handleStartPriorityPractice(id)}
          />
        </div>
      </div>

      {/* Modals */}
      <CurriculumOnboardingModal
        isOpen={isOnboardingOpen}
        onClose={() => setIsOnboardingOpen(false)}
        onGenerate={handleGenerateRoadmap}
        currentLevel={roadmap?.level || "intermediate"}
        currentGoal={roadmap?.target_goal || "workplace"}
        currentMinutes={roadmap?.daily_minutes || 30}
      />

      <CurriculumNodeDetailModal
        node={selectedNode}
        isOpen={Boolean(selectedNode)}
        onClose={() => setSelectedNode(null)}
        onToggleComplete={handleToggleNode}
      />

      <ExerciseModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        exercise={activeExercise}
        result={result}
        loading={exerciseLoading}
        submitting={submitting}
        showHint={showHint}
        onRevealHint={revealHint}
        onSubmitTranscript={handleSubmitResponse}
        onNextExercise={handleNextExercise}
      />
    </div>
  );
}
"""

with open(r"E:\SpeakingTraining\apps\web\types\learning.ts", "w", encoding="utf-8") as f:
    f.write(TYPES_LEARNING.strip() + "\n")
with open(r"E:\SpeakingTraining\apps\web\app\learning\page.tsx", "w", encoding="utf-8") as f:
    f.write(LEARNING_PAGE.strip() + "\n")

print("Updated types and page.tsx successfully!")
