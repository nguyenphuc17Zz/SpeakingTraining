import os

# 1. types/learning.ts
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
}

export interface LearningRecommendation {
  item: LearningItem;
  priority_score: number;
  reason: string;
  recommended_action: string;
  why: string;
  how: string;
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

# 2. services/learning-api.ts
SERVICES_LEARNING = """import { apiClient } from "@/services/api-client";
import {
  CurriculumRoadmap,
  CurriculumUnit,
  DailyPlan,
  Exercise,
  ExerciseResult,
  ExerciseStartResponse,
  LearningGoal,
  LearningItem,
  LearningRecommendation,
} from "@/types/learning";

export const learningApi = {
  async getTodayPlan(timeBudget: number = 30): Promise<DailyPlan> {
    return apiClient.get<DailyPlan>(`/learning/today?time_budget=${timeBudget}`);
  },

  async regenerateTodayPlan(timeBudget: number = 30): Promise<DailyPlan> {
    return apiClient.post<DailyPlan>("/learning/today/regenerate", {
      time_budget_minutes: timeBudget,
    });
  },

  async getPriorities(limit: number = 5): Promise<LearningRecommendation[]> {
    return apiClient.get<LearningRecommendation[]>(`/learning/priorities?limit=${limit}`);
  },

  async listItems(params?: {
    item_type?: string;
    lifecycle?: string;
    limit?: number;
  }): Promise<LearningItem[]> {
    const query = new URLSearchParams();
    if (params?.item_type) query.append("item_type", params.item_type);
    if (params?.lifecycle) query.append("lifecycle", params.lifecycle);
    if (params?.limit) query.append("limit", params.limit.toString());

    const queryString = query.toString();
    return apiClient.get<LearningItem[]>(`/learning/items${queryString ? `?${queryString}` : ""}`);
  },

  async getItem(id: string): Promise<LearningItem> {
    return apiClient.get<LearningItem>(`/learning/items/${id}`);
  },

  async startItemPractice(id: string): Promise<Exercise> {
    return apiClient.post<Exercise>(`/learning/items/${id}/practice`);
  },

  async getDueReviews(): Promise<LearningItem[]> {
    return apiClient.get<LearningItem[]>("/learning/reviews");
  },

  async listGoals(): Promise<LearningGoal[]> {
    return apiClient.get<LearningGoal[]>("/learning/goals");
  },

  async createGoal(payload: {
    title: string;
    goal_type?: string;
    description?: string;
    priority?: number;
  }): Promise<LearningGoal> {
    return apiClient.post<LearningGoal>("/learning/goals", payload);
  },

  async updateGoal(
    id: string,
    payload: {
      title?: string;
      description?: string;
      status?: string;
      priority?: number;
    }
  ): Promise<LearningGoal> {
    return apiClient.patch<LearningGoal>(`/learning/goals/${id}`, payload);
  },

  async getExercise(id: string): Promise<Exercise> {
    return apiClient.get<Exercise>(`/learning/exercises/${id}`);
  },

  async startExercise(
    id: string,
    payload: { session_id?: string; pronunciation_attempt_id?: string } = {}
  ): Promise<ExerciseStartResponse> {
    return apiClient.post<ExerciseStartResponse>(`/learning/exercises/${id}/start`, payload);
  },

  async submitExercise(
    id: string,
    payload: {
      user_transcript: string;
      turn_analysis_score?: number;
      pronunciation_score?: number;
      response_speed_ms?: number;
      used_hint?: boolean;
      plan_item_id?: string;
    }
  ): Promise<ExerciseResult> {
    return apiClient.post<ExerciseResult>(`/learning/exercises/${id}/submit`, payload);
  },

  async getCurriculum(): Promise<CurriculumUnit[]> {
    return apiClient.get<CurriculumUnit[]>("/learning/curriculum");
  },

  // Dynamic AI Milestone Roadmap
  async getRoadmap(): Promise<CurriculumRoadmap> {
    return apiClient.get<CurriculumRoadmap>("/learning/roadmap");
  },

  async generateRoadmap(payload: {
    level: string;
    target_goal: string;
    daily_minutes: number;
    custom_wish?: string;
  }): Promise<CurriculumRoadmap> {
    return apiClient.post<CurriculumRoadmap>("/learning/roadmap/generate", payload);
  },

  async toggleRoadmapNode(
    nodeId: string,
    payload: { is_completed?: boolean; score?: number } = {}
  ): Promise<CurriculumRoadmap> {
    return apiClient.post<CurriculumRoadmap>(`/learning/roadmap/nodes/${nodeId}/toggle`, payload);
  },

  async triggerRecalculate(): Promise<{ status: string; message: string }> {
    return apiClient.post<{ status: string; message: string }>("/learning/recalculate");
  },
};
"""

# 3. CurriculumOnboardingModal.tsx
ONBOARDING_MODAL = """\"use client\";

import React, { useState } from "react";
import { Modal } from "@/components/ui/modal";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Sparkles,
  Target,
  Clock,
  Wand2,
  Briefcase,
  Store,
  MessageCircle,
  Plane,
  Award,
  Edit3,
  CheckCircle2,
  Loader2,
} from "lucide-react";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

interface CurriculumOnboardingModalProps {
  isOpen: boolean;
  onClose: () => void;
  onGenerate: (data: {
    level: string;
    target_goal: string;
    daily_minutes: number;
    custom_wish?: string;
  }) => Promise<void>;
  currentLevel?: string;
  currentGoal?: string;
  currentMinutes?: number;
}

export const LEVELS = [
  { id: "beginner", label: "N5 • Sơ Cấp 1", desc: "Mới bắt đầu, phát âm & câu đơn" },
  { id: "elementary", label: "N4 • Sơ Cấp 2", desc: "Ngữ pháp căn bản & sinh hoạt" },
  { id: "intermediate", label: "N3 • Trung Cấp", desc: "Giao tiếp tự nhiên & đời sống" },
  { id: "advanced", label: "N2 • Trung Cao Cấp", desc: "Kính ngữ & môi trường công sở" },
  { id: "fluent", label: "N1 • Cao Cấp", desc: "Thuyết trình, đàm phán lưu loát" },
];

export const GOALS = [
  {
    id: "workplace",
    title: "Công Sở & Doanh Nghiệp (ビジネス)",
    desc: "Kính ngữ, báo cáo Hou-Ren-So, tiếp đối tác và viết email",
    icon: <Briefcase className="h-4 w-4 text-purple-500" />,
  },
  {
    id: "baito",
    title: "Phỏng Vấn & Làm Thêm (バイト面接)",
    desc: "Giao tiếp Konbini, nhà hàng, ứng xử lịch làm và xin phép",
    icon: <Store className="h-4 w-4 text-emerald-500" />,
  },
  {
    id: "daily",
    title: "Đời Sống & Kết Bạn (日常会話)",
    desc: "Phản xạ nhanh, mua sắm, nhà ga, kết bạn và tiệc tùng",
    icon: <MessageCircle className="h-4 w-4 text-amber-500" />,
  },
  {
    id: "travel",
    title: "Du Lịch & Định Cư (観光・生活)",
    desc: "Hỏi đường, khách sạn, y tế khẩn cấp và thủ tục hành chính",
    icon: <Plane className="h-4 w-4 text-sky-500" />,
  },
  {
    id: "exam",
    title: "Luyện Thi Kaiwa & JLPT (試験対策)",
    desc: "Tổng hợp mẫu câu trọng điểm, ngữ pháp và phát âm chuẩn",
    icon: <Award className="h-4 w-4 text-rose-500" />,
  },
];

export const MINUTES = [
  { mins: 15, label: "15 phút • Nhẹ nhàng" },
  { mins: 30, label: "30 phút • Tiêu chuẩn" },
  { mins: 45, label: "45 phút • Chuyên sâu" },
  { mins: 60, label: "60 phút • Đột phá" },
];

export function CurriculumOnboardingModal({
  isOpen,
  onClose,
  onGenerate,
  currentLevel = "intermediate",
  currentGoal = "workplace",
  currentMinutes = 30,
}: CurriculumOnboardingModalProps) {
  const [level, setLevel] = useState(currentLevel);
  const [goal, setGoal] = useState(currentGoal);
  const [dailyMinutes, setDailyMinutes] = useState(currentMinutes);
  const [customWish, setCustomWish] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    setIsSubmitting(true);
    soundFX.playKatana();
    try {
      await onGenerate({
        level,
        target_goal: goal,
        daily_minutes: dailyMinutes,
        custom_wish: customWish.trim() || undefined,
      });
      onClose();
    } catch (e) {
      console.error("Failed to generate curriculum:", e);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Thiết Lập Lộ Trình Học Nói Tiếng Nhật Cá Nhân Hóa"
      description="AI sẽ phân tích trình độ và mục tiêu để thiết kế lộ trình 4 chặng độc quyền cho bạn"
      className="max-w-3xl"
    >
      <div className="space-y-6 pt-2">
        {/* Step 1: Current Level */}
        <div className="space-y-2.5">
          <div className="flex items-center gap-2 text-xs font-bold text-foreground">
            <span className="h-5 w-5 rounded-full bg-primary/10 text-primary flex items-center justify-center text-[10px]">
              1
            </span>
            <span>Trình độ tiếng Nhật hiện tại của bạn:</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {LEVELS.map((lvl) => (
              <button
                key={lvl.id}
                type="button"
                onClick={() => {
                  soundFX.playFurin();
                  setLevel(lvl.id);
                }}
                className={cn(
                  "p-2.5 rounded-xl border text-left transition-all space-y-0.5",
                  level === lvl.id
                    ? "bg-primary/10 border-primary shadow-xs ring-1 ring-primary/30"
                    : "bg-muted/40 border-border/80 hover:border-primary/40"
                )}
              >
                <div className="text-xs font-bold text-foreground">{lvl.label}</div>
                <div className="text-[10px] text-muted-foreground">{lvl.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Step 2: Target Goal */}
        <div className="space-y-2.5">
          <div className="flex items-center gap-2 text-xs font-bold text-foreground">
            <span className="h-5 w-5 rounded-full bg-primary/10 text-primary flex items-center justify-center text-[10px]">
              2
            </span>
            <span>Mục tiêu rèn luyện trọng tâm:</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {GOALS.map((g) => (
              <button
                key={g.id}
                type="button"
                onClick={() => {
                  soundFX.playFurin();
                  setGoal(g.id);
                }}
                className={cn(
                  "p-3 rounded-xl border text-left transition-all flex items-start gap-2.5",
                  goal === g.id
                    ? "bg-primary/10 border-primary shadow-xs ring-1 ring-primary/30"
                    : "bg-muted/40 border-border/80 hover:border-primary/40"
                )}
              >
                <div className="p-1.5 rounded-lg bg-card border border-border/80 shrink-0 mt-0.5">
                  {g.icon}
                </div>
                <div className="space-y-0.5 min-w-0 flex-1">
                  <div className="text-xs font-bold text-foreground">{g.title}</div>
                  <div className="text-[11px] text-muted-foreground leading-snug">{g.desc}</div>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Step 3: Daily Minutes & Custom Wish */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs font-bold text-foreground">
              <span className="h-5 w-5 rounded-full bg-primary/10 text-primary flex items-center justify-center text-[10px]">
                3
              </span>
              <span>Thời gian rèn luyện mỗi ngày:</span>
            </div>

            <div className="grid grid-cols-2 gap-1.5">
              {MINUTES.map((m) => (
                <button
                  key={m.mins}
                  type="button"
                  onClick={() => {
                    soundFX.playFurin();
                    setDailyMinutes(m.mins);
                  }}
                  className={cn(
                    "p-2 rounded-xl border text-center text-xs font-bold transition-all",
                    dailyMinutes === m.mins
                      ? "bg-primary text-primary-foreground border-primary shadow-xs"
                      : "bg-muted/40 border-border text-muted-foreground hover:text-foreground"
                  )}
                >
                  {m.label}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs font-bold text-foreground">
              <Edit3 className="h-4 w-4 text-primary" />
              <span>Nguyện vọng riêng biệt (Tùy chọn):</span>
            </div>

            <textarea
              value={customWish}
              onChange={(e) => setCustomWish(e.target.value)}
              placeholder="VD: Muốn tập trung sửa lỗi từ đệm ano/etto và đàm phán hợp đồng IT..."
              rows={2}
              className="w-full bg-background border border-border rounded-xl p-2.5 text-xs focus:outline-none focus:border-primary resize-none placeholder:text-muted-foreground"
            />
          </div>
        </div>

        {/* Footer Actions */}
        <div className="pt-3 border-t border-border flex items-center justify-between">
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            disabled={isSubmitting}
            className="text-xs font-semibold"
          >
            Hủy bỏ
          </Button>

          <Button
            variant="akane"
            size="sm"
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="text-xs font-bold gap-2 px-6 h-10 rounded-xl shadow-md"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>AI Đang Thiết Kế Lộ Trình...</span>
              </>
            ) : (
              <>
                <Wand2 className="h-4 w-4" />
                <span>✨ Tạo Lộ Trình Độc Quyền</span>
              </>
            )}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
"""

# 4. InteractiveRoadmapView.tsx
ROADMAP_VIEW = """\"use client\";

import React from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Compass,
  CheckCircle2,
  Circle,
  Play,
  Sparkles,
  ArrowRight,
  Clock,
  BookOpen,
  Volume2,
  Crown,
  Lock,
} from "lucide-react";
import { CurriculumNode, CurriculumRoadmap, CurriculumStage } from "@/types/learning";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

interface InteractiveRoadmapViewProps {
  roadmap: CurriculumRoadmap | null;
  onSelectNode: (node: CurriculumNode) => void;
  onOpenOnboarding: () => void;
  isLoading: boolean;
}

export function InteractiveRoadmapView({
  roadmap,
  onSelectNode,
  onOpenOnboarding,
  isLoading,
}: InteractiveRoadmapViewProps) {
  if (!roadmap) {
    return (
      <div className="p-8 text-center rounded-3xl border border-dashed border-border bg-card washi-texture space-y-3">
        <Sparkles className="h-8 w-8 text-primary mx-auto animate-bounce" />
        <h3 className="text-base font-bold text-foreground">Bạn chưa có Lộ Trình Học Cá Nhân Hóa</h3>
        <p className="text-xs text-muted-foreground max-w-md mx-auto">
          Hãy để AI phân tích trình độ và mục tiêu của bạn để thiết kế lộ trình 4 chặng chi tiết.
        </p>
        <Button
          variant="akane"
          size="sm"
          onClick={onOpenOnboarding}
          className="text-xs font-bold gap-1.5 rounded-xl px-5 h-9 shadow-md"
        >
          <Sparkles className="h-3.5 w-3.5" />
          <span>Tạo Lộ Trình Bằng AI Ngay</span>
        </Button>
      </div>
    );
  }

  // Calculate total completed nodes
  let totalNodes = 0;
  let completedNodes = 0;

  roadmap.stages?.forEach((stage) => {
    stage.nodes?.forEach((node) => {
      totalNodes++;
      if (node.is_completed) completedNodes++;
    });
  });

  const progressPercent = totalNodes > 0 ? Math.round((completedNodes / totalNodes) * 100) : 0;

  return (
    <div className="space-y-6">
      {/* Top Roadmap Overview Card */}
      <div className="p-6 rounded-3xl border border-border bg-card washi-texture shadow-sm space-y-4 relative overflow-hidden">
        <div className="absolute top-0 right-0 h-40 w-40 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <Badge variant="kintsugi" size="sm" className="font-bold">
                AI DYNAMIC ROADMAP
              </Badge>
              <Badge variant="outline" size="sm" className="text-xs font-semibold">
                {roadmap.level_label || roadmap.level}
              </Badge>
              <Badge variant="matcha" size="sm" className="text-xs font-semibold">
                {roadmap.target_goal_label || roadmap.target_goal}
              </Badge>
            </div>

            <h2 className="text-xl md:text-2xl font-black text-foreground tracking-tight">
              {roadmap.title}
            </h2>
            <p className="text-xs text-muted-foreground max-w-2xl leading-relaxed">
              {roadmap.description}
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0 self-start md:self-auto">
            <div className="text-right">
              <div className="text-xs font-bold text-muted-foreground">Tiến độ toàn khóa</div>
              <div className="text-xl font-black font-mono text-primary">
                {progressPercent}% <span className="text-xs text-muted-foreground font-normal">({completedNodes}/{totalNodes} bài)</span>
              </div>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                soundFX.playFurin();
                onOpenOnboarding();
              }}
              className="text-xs font-bold gap-1.5 rounded-xl border-primary/30 text-primary hover:bg-primary/10 h-9"
            >
              <Sparkles className="h-3.5 w-3.5" />
              <span>Tinh chỉnh AI</span>
            </Button>
          </div>
        </div>

        {/* Global Progress Bar */}
        <div className="w-full h-2 rounded-full bg-muted/60 overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-primary via-emerald-500 to-amber-500 transition-all duration-500 rounded-full"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      {/* 4 Milestone Stages */}
      <div className="space-y-6">
        {roadmap.stages?.map((stage: CurriculumStage, stageIdx: number) => {
          const stageCompleted = stage.nodes?.filter((n) => n.is_completed).length || 0;
          const stageTotal = stage.nodes?.length || 0;
          const isStageFinished = stageTotal > 0 && stageCompleted === stageTotal;

          return (
            <div
              key={stage.stage_number || stageIdx}
              className="p-6 rounded-3xl border border-border bg-card washi-texture shadow-sm space-y-4 relative"
            >
              {/* Stage Header */}
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/60 pb-3.5">
                <div className="flex items-center gap-2.5">
                  <span className={cn(
                    "h-8 w-8 rounded-xl font-bold font-mono text-xs flex items-center justify-center border shadow-2xs",
                    isStageFinished
                      ? "bg-emerald-500/20 border-emerald-500 text-emerald-600 dark:text-emerald-400"
                      : "bg-primary/10 border-primary text-primary"
                  )}>
                    {isStageFinished ? <CheckCircle2 className="h-4 w-4" /> : stage.stage_number}
                  </span>

                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-bold text-foreground font-jp">{stage.title}</h3>
                      <Badge variant="outline" size="sm" className="text-[10px] font-bold">
                        {stage.badge}
                      </Badge>
                    </div>
                    <p className="text-[11px] text-muted-foreground">{stage.objective}</p>
                  </div>
                </div>

                <div className="text-xs font-mono font-bold text-muted-foreground">
                  {stageCompleted}/{stageTotal} hoàn thành
                </div>
              </div>

              {/* Lesson Nodes Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {stage.nodes?.map((node: CurriculumNode, nodeIdx: number) => {
                  return (
                    <div
                      key={node.id || nodeIdx}
                      onClick={() => {
                        soundFX.playFurin();
                        onSelectNode(node);
                      }}
                      className={cn(
                        "p-4 rounded-2xl border transition-all cursor-pointer bg-card shadow-2xs space-y-2.5 hover:shadow-md hover:border-primary/50 relative overflow-hidden group",
                        node.is_completed
                          ? "border-emerald-500/30 bg-emerald-500/5"
                          : "border-border/80 hover:bg-muted/30"
                      )}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <span className={cn(
                            "h-5 w-5 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0",
                            node.is_completed
                              ? "bg-emerald-500 text-white"
                              : "bg-muted text-muted-foreground border border-border"
                          )}>
                            {node.is_completed ? "✓" : nodeIdx + 1}
                          </span>
                          <Badge variant="fuji" size="sm" className="text-[10px] font-bold">
                            {node.mode_label}
                          </Badge>
                        </div>

                        <span className="text-[10px] font-mono font-bold text-muted-foreground">
                          {node.estimated_minutes}p
                        </span>
                      </div>

                      <div className="space-y-1">
                        <h4 className="text-xs font-bold text-foreground leading-snug group-hover:text-primary transition-colors">
                          {node.title}
                        </h4>
                        <p className="text-[11px] text-muted-foreground leading-snug line-clamp-2">
                          {node.description}
                        </p>
                      </div>

                      {/* Key Patterns Pill Tags */}
                      {node.key_patterns && node.key_patterns.length > 0 && (
                        <div className="flex flex-wrap gap-1 pt-1">
                          {node.key_patterns.map((kp, i) => (
                            <span key={i} className="px-2 py-0.5 rounded-md bg-muted text-[10px] font-mono text-muted-foreground">
                              {kp}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
"""

# 5. CurriculumNodeDetailModal.tsx
NODE_DETAIL_MODAL = """\"use client\";

import React from "react";
import { Modal } from "@/components/ui/modal";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Compass,
  Play,
  CheckCircle2,
  BookOpen,
  Sparkles,
  ArrowRight,
  Clock,
  RotateCcw,
} from "lucide-react";
import { CurriculumNode } from "@/types/learning";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";
import Link from "next/link";

interface CurriculumNodeDetailModalProps {
  node: CurriculumNode | null;
  isOpen: boolean;
  onClose: () => void;
  onToggleComplete: (nodeId: string, isCompleted: boolean) => Promise<void>;
}

export function CurriculumNodeDetailModal({
  node,
  isOpen,
  onClose,
  onToggleComplete,
}: CurriculumNodeDetailModalProps) {
  if (!node) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={node.title}
      description={`Mục tiêu rèn luyện tại phòng: ${node.mode_label}`}
      className="max-w-xl"
    >
      <div className="space-y-5 pt-2">
        {/* Header Badges */}
        <div className="flex items-center gap-2">
          <Badge variant="matcha" size="sm" className="font-bold">
            {node.mode_label}
          </Badge>
          <Badge variant="outline" size="sm" className="font-mono text-[10px]">
            Độ khó: {node.difficulty}
          </Badge>
          <span className="text-xs text-muted-foreground font-mono">
            Thời lượng ước tính: {node.estimated_minutes} phút
          </span>
        </div>

        {/* Description Box */}
        <div className="p-4 rounded-2xl bg-muted/40 border border-border/80 space-y-2">
          <div className="text-xs font-bold text-foreground">Mục Tiêu & Nội Dung Bài Học:</div>
          <p className="text-xs text-muted-foreground leading-relaxed">
            {node.description}
          </p>
        </div>

        {/* Key Linguistic Patterns */}
        {node.key_patterns && node.key_patterns.length > 0 && (
          <div className="space-y-2">
            <div className="text-xs font-bold text-foreground">Các Mẫu Trọng Điểm Cần Nắm:</div>
            <div className="flex flex-wrap gap-1.5">
              {node.key_patterns.map((pat, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1 rounded-xl bg-card border border-primary/30 text-primary text-xs font-jp font-bold shadow-2xs"
                >
                  {pat}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Footer Actions */}
        <div className="pt-3 border-t border-border flex flex-wrap items-center justify-between gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={async () => {
              soundFX.playFurin();
              await onToggleComplete(node.id, !node.is_completed);
              onClose();
            }}
            className="text-xs font-bold gap-1.5 rounded-xl"
          >
            <CheckCircle2 className={cn("h-4 w-4", node.is_completed ? "text-emerald-500" : "text-muted-foreground")} />
            <span>{node.is_completed ? "Đánh dấu chưa học" : "Đánh dấu đã hoàn thành"}</span>
          </Button>

          <Link href={node.target_mode || "/speaking"} onClick={onClose}>
            <Button
              variant="akane"
              size="sm"
              onClick={() => soundFX.playKatana()}
              className="text-xs font-bold gap-1.5 rounded-xl px-5 h-9 shadow-md"
            >
              <Play className="h-3.5 w-3.5 fill-current" />
              <span>Vào Học Bài Này Ngay ({node.mode_label})</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Button>
          </Link>
        </div>
      </div>
    </Modal>
  );
}
"""

# 6. features/learning/index.ts
FEATURES_INDEX = """export * from "./components/DailyPlanCard";
export * from "./components/PriorityCard";
export * from "./components/MasteryBar";
export * from "./components/ExerciseModal";
export * from "./components/ReviewQueueCard";
export * from "./components/CurriculumPathwayCard";
export * from "./components/CurriculumOnboardingModal";
export * from "./components/InteractiveRoadmapView";
export * from "./components/CurriculumNodeDetailModal";
export * from "@/hooks/use-learning-plan";
export * from "@/hooks/use-learning-priorities";
export * from "@/hooks/use-exercise";
"""

# 7. app/learning/page.tsx
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
            onTimeBudgetChange={setTimeBudget}
            onRegenerate={regeneratePlan}
            onStartExercise={handleStartPlanExercise}
          />
        </div>

        {/* Priorities & Due Reviews (1 Col) */}
        <div className="space-y-6">
          <PriorityCard
            recommendations={priorities}
            loading={prioritiesLoading}
            onStartPractice={handleStartPriorityPractice}
          />

          <ReviewQueueCard
            dueItems={dueReviews}
            loading={prioritiesLoading}
            onStartReview={(key) => handleStartPriorityPractice(key)}
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

FILES_MAP = {
    r"E:\SpeakingTraining\apps\web\types\learning.ts": TYPES_LEARNING,
    r"E:\SpeakingTraining\apps\web\services\learning-api.ts": SERVICES_LEARNING,
    r"E:\SpeakingTraining\apps\web\features\learning\components\CurriculumOnboardingModal.tsx": ONBOARDING_MODAL,
    r"E:\SpeakingTraining\apps\web\features\learning\components\InteractiveRoadmapView.tsx": ROADMAP_VIEW,
    r"E:\SpeakingTraining\apps\web\features\learning\components\CurriculumNodeDetailModal.tsx": NODE_DETAIL_MODAL,
    r"E:\SpeakingTraining\apps\web\features\learning\index.ts": FEATURES_INDEX,
    r"E:\SpeakingTraining\apps\web\app\learning\page.tsx": LEARNING_PAGE,
}

for filepath, content in FILES_MAP.items():
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"Successfully wrote {os.path.basename(filepath)}")

print("All Dynamic AI Curriculum & Roadmap frontend components written successfully!")
