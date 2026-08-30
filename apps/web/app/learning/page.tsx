"use client";

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
import { coachCoreApi, DailySenseiBriefingCard } from "@/features/coach";
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
import { cn } from "@/lib/utils";

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

  const [activeTab, setActiveTab] = useState<"roadmap" | "daily_plan">("roadmap");

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
    <div className="space-y-4 animate-in fade-in duration-300 max-w-5xl mx-auto pb-8">
      {/* 1. Header Banner Haru Washi */}
      <div className="relative overflow-hidden rounded-2xl border border-border bg-card p-4 sm:p-5 washi-texture shadow-2xs space-y-3">
        <div className="absolute top-0 right-0 h-32 w-32 bg-primary/10 rounded-full blur-2xl pointer-events-none" />

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 relative z-10">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Badge variant="matcha" size="sm" className="font-bold text-[10px]">
                ADAPTIVE CURRICULUM & DAILY PLAN
              </Badge>
              <span className="text-[11px] text-muted-foreground font-semibold">
                Lộ Trình Học Động & Nhiệm Vụ Ngày
              </span>
            </div>
            <h1 className="text-xl sm:text-2xl font-black text-foreground tracking-tight flex items-center gap-2">
              <span className="p-1.5 rounded-xl bg-primary/10 border border-primary/20 text-primary inline-flex">
                <Compass className="h-5 w-5" />
              </span>
              <span>Lộ Trình Luyện Nói Cá Nhân Hóa (学習ロードマップ)</span>
            </h1>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <Button
              variant="akane"
              size="sm"
              onClick={() => {
                soundFX.playFurin();
                setIsOnboardingOpen(true);
              }}
              className="text-xs font-bold gap-1.5 shadow-md rounded-xl h-8 px-3.5"
            >
              <Wand2 className="h-3.5 w-3.5" />
              <span>Tạo Lại Lộ Trình AI</span>
            </Button>
          </div>
        </div>

        {/* Coach Sensei Tip */}
        {coachTip && (
          <div className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center gap-2 text-xs text-amber-900 dark:text-amber-100">
            <Sparkles className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400 shrink-0" />
            <div className="leading-snug truncate">
              <span className="font-bold font-jp">Sensei Tip: </span>
              {coachTip}
            </div>
          </div>
        )}
      </div>

      {/* 2. Top Segmented Navigation Switcher */}
      <div className="flex items-center gap-1.5 p-1 rounded-2xl bg-muted/60 border border-border/80 shadow-2xs">
        <button
          type="button"
          onClick={() => {
            soundFX.playFurin();
            setActiveTab("roadmap");
          }}
          className={cn(
            "flex-1 py-2 px-4 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-2",
            activeTab === "roadmap"
              ? "bg-card text-foreground border border-border shadow-xs"
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          <Layers className="h-3.5 w-3.5 text-primary" />
          <span>🗺️ Lộ Trình Toàn Diện 4 Chặng (Roadmap)</span>
        </button>

        <button
          type="button"
          onClick={() => {
            soundFX.playFurin();
            setActiveTab("daily_plan");
          }}
          className={cn(
            "flex-1 py-2 px-4 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-2",
            activeTab === "daily_plan"
              ? "bg-card text-foreground border border-border shadow-xs"
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          <Calendar className="h-3.5 w-3.5 text-emerald-500" />
          <span>📋 Nhiệm Vụ Hôm Nay (Daily Plan & Focus)</span>
          {plan?.items && (
            <Badge variant="matcha" size="sm" className="text-[9px] px-1.5 py-0">
              {plan.items.filter((i) => i.status === "completed").length}/{plan.items.length}
            </Badge>
          )}
        </button>
      </div>

      {/* Tab 1: Curriculum Roadmap View */}
      {activeTab === "roadmap" && (
        <div className="space-y-4 animate-in fade-in duration-200">
          <InteractiveRoadmapView
            roadmap={roadmap}
            onSelectNode={(node) => setSelectedNode(node)}
            onOpenOnboarding={() => setIsOnboardingOpen(true)}
            isLoading={roadmapLoading}
          />
        </div>
      )}

      {/* Tab 2: Daily Plan & Today Priorities View */}
      {activeTab === "daily_plan" && (
        <div className="space-y-4 animate-in fade-in duration-200">
          {/* AI Sensei Daily Briefing Letter */}
          <DailySenseiBriefingCard />

          {/* Today Focus Quests & Priorities Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 items-start">
            {/* Daily Plan Column (2 Cols) */}
            <div className="lg:col-span-2 space-y-4">
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
            <div className="space-y-4">
              <div className="space-y-2">
                <h3 className="text-xs font-bold text-foreground uppercase tracking-wider">
                  Mục Tiêu Ưu Tiên Khắc Phục (Priorities)
                </h3>
                {prioritiesLoading ? (
                  <div className="p-6 text-center text-xs text-muted-foreground">Đang tải gợi ý...</div>
                ) : priorities.length === 0 ? (
                  <div className="p-4 rounded-2xl border border-border bg-card text-center text-xs text-muted-foreground">
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
        </div>
      )}

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
