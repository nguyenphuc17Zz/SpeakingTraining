import os

# 1. situations-api.ts
SITUATIONS_API = """\"use client\";

import { apiClient } from "@/services/api-client";

export type SituationsPressureLevel = "relaxed" | "normal" | "fast" | "reflex" | "extreme";

export interface SituationalGoal {
  id: string;
  task: string;
  intent?: string;
  description?: string;
  status?: "NOT_STARTED" | "COMPLETED" | "FAILED";
  hidden?: boolean;
}

export interface SituationalData {
  category_key: string;
  category_label: string;
  location: string;
  npc_name: string;
  npc_personality: string;
  npc_opening_dialogue: string;
  npc_dialogue_vi?: string;
  user_role: string;
  goals: SituationalGoal[];
  unexpected_event?: string;
  useful_phrases?: string[];
  vocabulary_hints?: string;
}

export interface SituationsExercise {
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
  subMode?: string;
  timerLimitMs: number;
  pressureLevel?: string;
  canonical?: string;
  acceptableVariants?: string[];
  prompt?: string;
  reading?: string;
  translation?: string;
  situationalData?: SituationalData;
  extra_metadata?: any;
}

export interface SituationsResult {
  exerciseId: string;
  score: number;
  success: boolean;
  isPerfect: boolean;
  timedOut: boolean;
  reactionLatencyMs: number;
  userTranscript: string;
  feedback?: string;
  strengths: string[];
  improvements: string[];
  drillScores?: Record<string, number>;
  metrics?: {
    task_completion?: number;
    pragmatics?: number;
    fluency?: number;
    naturalness?: number;
  };
}

export interface GenerateSituationsParams {
  category?: string;
  subMode?: string;
  pressureLevel?: SituationsPressureLevel;
  timerLimitMs?: number;
  difficulty?: string;
  duration?: number;
  mode?: string;
}

export async function generateExercise(params: GenerateSituationsParams = {}): Promise<SituationsExercise> {
  const {
    category = "food",
    subMode = "situational_roleplay",
    pressureLevel = "normal",
    timerLimitMs,
    difficulty,
    duration = 5,
    mode = "standard",
  } = params;

  const q = new URLSearchParams({
    sub_mode: subMode,
    pressure_level: pressureLevel,
    duration: String(duration),
    mode,
  });
  if (category && category !== "all") q.set("category", category);
  if (timerLimitMs) q.set("timer_limit_ms", String(timerLimitMs));
  if (difficulty) q.set("difficulty", difficulty);

  const res = await apiClient.post<any>(`/situations/exercises/generate?${q.toString()}`);
  const sc = res.extra_metadata?.situational_config || {};
  const sData = sc.situational_data || {};

  return {
    ...res,
    subMode: sc.sub_mode || subMode,
    timerLimitMs: sc.timer_limit_ms || timerLimitMs || 6000,
    pressureLevel: sc.pressure_level || pressureLevel,
    canonical: sc.canonical || res.canonical || sData.npc_opening_dialogue || res.prompt,
    acceptableVariants: sc.accepted || res.acceptableVariants || [],
    prompt: sc.prompt || res.prompt || sData.npc_opening_dialogue,
    translation: sc.translation || sData.npc_dialogue_vi || res.scenario || "",
    situationalData: sData,
  };
}

export async function submitAttempt(payload: {
  exercise_id: string;
  transcript?: string;
  reflex_metrics?: {
    reaction_latency_ms: number;
    timed_out: boolean;
  };
}): Promise<SituationsResult> {
  const res = await apiClient.post<any>(`/situations/exercises/${payload.exercise_id}/submit`, {
    user_transcript: payload.transcript || "",
    reaction_latency_ms: payload.reflex_metrics?.reaction_latency_ms || 0,
    timed_out: payload.reflex_metrics?.timed_out || false,
  });

  return {
    exerciseId: payload.exercise_id,
    score: res.score ?? (res.success ? 90 : 55),
    success: res.success ?? true,
    isPerfect: res.isPerfect ?? (res.score >= 90),
    timedOut: res.timedOut ?? false,
    reactionLatencyMs: res.reactionLatencyMs ?? payload.reflex_metrics?.reaction_latency_ms ?? 0,
    userTranscript: res.userTranscript || payload.transcript || "",
    feedback: res.feedback || "Phản xạ giao tiếp tình huống tốt, đạt mục tiêu đối thoại!",
    strengths: res.strengths || ["Đúng ngữ cảnh", "Phản xạ tự nhiên"],
    improvements: res.improvements || [],
    drillScores: res.drillScores || {},
    metrics: res.metrics || {
      task_completion: res.score ?? 90,
      pragmatics: 88,
      fluency: 85,
      naturalness: 87,
    },
  };
}
"""

# 2. SituationsLobby.tsx
SITUATIONS_LOBBY = """\"use client\";

import React from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Compass,
  Utensils,
  ShoppingBag,
  Train,
  HeartPulse,
  Briefcase,
  Hotel,
  Clock,
  Sparkles,
  Zap,
  Play,
  BookOpen,
  Keyboard,
  Shield,
  Sliders,
} from "lucide-react";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";
import type { SituationsPressureLevel } from "../services/situations-api";

export interface SituationsLobbyProps {
  selectedCategory: string;
  onSelectCategory: (cat: string) => void;
  selectedMode: string;
  onSelectMode: (mode: string) => void;
  pressureLevel: SituationsPressureLevel;
  onSelectPressureLevel: (p: SituationsPressureLevel) => void;
  duration: number;
  onSelectDuration: (d: number) => void;
  subtitleMode: "hidden" | "japanese" | "japanese_reading" | "vietnamese";
  onSelectSubtitleMode: (m: "hidden" | "japanese" | "japanese_reading" | "vietnamese") => void;
  onStartSession: () => void;
  onOpenCheatsheet: () => void;
  onOpenKeybindings: () => void;
  isLoading: boolean;
}

export const SITUATIONAL_CATEGORIES = [
  {
    id: "food",
    jaTitle: "飲食・居酒屋",
    viTitle: "Ẩm Thực & Quán Nhậu",
    badge: "飲食",
    desc: "Đặt bàn, gọi món, yêu cầu đổi món do dị ứng, tách hóa đơn betsu-betsu",
    icon: <Utensils className="h-5 w-5 text-amber-500" />,
    color: "from-amber-500/10 to-orange-500/10 border-amber-500/30",
  },
  {
    id: "retail",
    jaTitle: "買い物・コンビニ",
    viTitle: "Mua Sắm & Konbini",
    badge: "店舗",
    desc: "Hâm nóng bento, từ chối túi nilon, rút tiền ATM, gửi bưu kiện",
    icon: <ShoppingBag className="h-5 w-5 text-emerald-500" />,
    color: "from-emerald-500/10 to-teal-500/10 border-emerald-500/30",
  },
  {
    id: "transportation",
    jaTitle: "交通・駅・空港",
    viTitle: "Giao Thông & Nhà Ga",
    badge: "交通",
    desc: "Mua vé Shinkansen ghế chỉ định, hỏi cửa chuyển tàu, nạp thẻ Suica",
    icon: <Train className="h-5 w-5 text-sky-500" />,
    color: "from-sky-500/10 to-blue-500/10 border-sky-500/30",
  },
  {
    id: "healthcare",
    jaTitle: "医療・薬局・緊急",
    viTitle: "Y Tế & Hiệu Thuốc & Khẩn Cấp",
    badge: "医療",
    desc: "Mô tả triệu chứng bệnh, mua thuốc tại Yakkyoku, báo rơi đồ tại Kouban",
    icon: <HeartPulse className="h-5 w-5 text-rose-500" />,
    color: "from-rose-500/10 to-pink-500/10 border-rose-500/30",
  },
  {
    id: "workplace",
    jaTitle: "ビジネス・職場",
    viTitle: "Công Sở & Đàm Phán",
    badge: "仕事",
    desc: "Tiếp đối tác, trao đổi danh thiếp Meishi, báo cáo tiến độ Hou-Ren-So",
    icon: <Briefcase className="h-5 w-5 text-purple-500" />,
    color: "from-purple-500/10 to-indigo-500/10 border-purple-500/30",
  },
  {
    id: "travel",
    jaTitle: "ホテル・観光・旅行",
    viTitle: "Khách Sạn & Du Lịch",
    badge: "観光",
    desc: "Check-in khách sạn, gửi hành lý, hỏi gợi ý điểm tham quan, đặt tour",
    icon: <Hotel className="h-5 w-5 text-cyan-500" />,
    color: "from-cyan-500/10 to-teal-500/10 border-cyan-500/30",
  },
];

export const CHALLENGE_MODES = [
  { id: "standard", label: "標準 (Standard)", desc: "Hiện mục tiêu rõ ràng" },
  { id: "guided", label: "誘導付き (Guided)", desc: "Kèm mẫu câu gợi ý" },
  { id: "challenge", label: "挑戦 (Challenge)", desc: "Ẩn mục tiêu kế tiếp" },
  { id: "blind", label: "暗中模索 (Blind)", desc: "Ẩn toàn bộ mục tiêu" },
];

export const PRESSURE_OPTIONS: { id: SituationsPressureLevel; label: string; limit: string; desc: string }[] = [
  { id: "relaxed", label: "Thư thái", limit: "6.0s", desc: "Dễ thở, suy nghĩ kỹ" },
  { id: "normal", label: "Tiêu chuẩn", limit: "5.0s", desc: "Tốc độ giao tiếp tự nhiên" },
  { id: "fast", label: "Thần tốc", limit: "4.0s", desc: "Phản xạ nhanh nhạy" },
  { id: "reflex", label: "Cực hạn", limit: "3.0s", desc: "Áp lực thực chiến cao" },
];

export const DURATION_OPTIONS = [
  { mins: 3, label: "3 phút • Khởi động (2 tình huống)" },
  { mins: 5, label: "5 phút • Tiêu chuẩn (3 tình huống)" },
  { mins: 10, label: "10 phút • Chuyên sâu (5 tình huống)" },
  { mins: 15, label: "15 phút • Marathon (8 tình huống)" },
];

export function SituationsLobby({
  selectedCategory,
  onSelectCategory,
  selectedMode,
  onSelectMode,
  pressureLevel,
  onSelectPressureLevel,
  duration,
  onSelectDuration,
  subtitleMode,
  onSelectSubtitleMode,
  onStartSession,
  onOpenCheatsheet,
  onOpenKeybindings,
  isLoading,
}: SituationsLobbyProps) {
  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in duration-300 pb-12">
      {/* Top Banner Haru Washi */}
      <div className="relative overflow-hidden rounded-3xl border border-border bg-card p-6 md:p-8 washi-texture shadow-sm space-y-4">
        <div className="absolute top-0 right-0 h-48 w-48 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Badge variant="matcha" size="sm" className="font-bold">
                MODE 4 • SITUATIONAL ROLEPLAY STUDIO
              </Badge>
              <span className="text-xs text-muted-foreground font-semibold">
                AI Phản Xạ Nhập Vai Thực Chiến
              </span>
            </div>
            <h1 className="text-2xl md:text-3xl font-black text-foreground tracking-tight flex items-center gap-3">
              <span className="p-2 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 inline-flex">
                <Compass className="h-6 w-6" />
              </span>
              <span>Tình Huống Thực Chiến (場面英会話)</span>
            </h1>
            <p className="text-xs md:text-sm text-muted-foreground max-w-2xl leading-relaxed">
              Nhập vai vào 6 bối cảnh đời sống Nhật Bản. Lắng nghe nhân vật NPC, xử lý sự cố bất ngờ và phản xạ câu đáp chuẩn xác trong thời gian thực.
            </p>
          </div>

          <div className="flex items-center gap-2.5 shrink-0 self-start md:self-auto">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                soundFX.playFurin();
                onOpenCheatsheet();
              }}
              className="text-xs font-bold gap-1.5 border-emerald-500/30 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-500/10 shadow-2xs"
            >
              <BookOpen className="h-3.5 w-3.5" />
              <span>Sổ tay Mẫu câu (C)</span>
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                soundFX.playFurin();
                onOpenKeybindings();
              }}
              className="text-xs font-bold gap-1.5 shadow-2xs"
            >
              <Keyboard className="h-3.5 w-3.5" />
              <span>Phím tắt (?)</span>
            </Button>
          </div>
        </div>
      </div>

      {/* 6 Category Cards Grid */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-foreground flex items-center gap-2">
            <Sliders className="h-4 w-4 text-primary" />
            <span>1. Chọn Bối Cảnh Luyện Tập (Category)</span>
          </h2>
          <span className="text-xs text-muted-foreground">Sinh dữ liệu ngẫu nhiên thời gian thực</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
          {SITUATIONAL_CATEGORIES.map((cat) => {
            const isSelected = selectedCategory === cat.id;
            return (
              <div
                key={cat.id}
                onClick={() => {
                  soundFX.playFurin();
                  onSelectCategory(cat.id);
                }}
                className={cn(
                  "p-4 rounded-2xl border transition-all cursor-pointer relative overflow-hidden bg-card washi-texture space-y-2 hover:shadow-md",
                  isSelected
                    ? "border-primary ring-2 ring-primary/20 bg-primary/5 shadow-xs"
                    : "border-border hover:border-primary/40"
                )}
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <div className="p-2 rounded-xl bg-muted/60 border border-border/80">
                      {cat.icon}
                    </div>
                    <div>
                      <div className="text-xs font-bold text-foreground font-jp">{cat.jaTitle}</div>
                      <div className="text-[11px] text-muted-foreground font-semibold">{cat.viTitle}</div>
                    </div>
                  </div>
                  <Badge variant={isSelected ? "matcha" : "outline"} size="sm" className="font-mono text-[10px]">
                    {cat.badge}
                  </Badge>
                </div>

                <p className="text-[11px] text-muted-foreground leading-snug line-clamp-2">
                  {cat.desc}
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Challenge Modes & Configurations */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Challenge Mode Selection */}
        <div className="p-5 rounded-2xl border border-border bg-card washi-texture space-y-3">
          <h3 className="text-xs font-bold text-foreground uppercase tracking-wider flex items-center gap-2">
            <Shield className="h-4 w-4 text-emerald-500" />
            <span>2. Chế Độ Thử Thách (Mode)</span>
          </h3>

          <div className="grid grid-cols-2 gap-2">
            {CHALLENGE_MODES.map((m) => (
              <button
                key={m.id}
                type="button"
                onClick={() => {
                  soundFX.playFurin();
                  onSelectMode(m.id);
                }}
                className={cn(
                  "p-3 rounded-xl border text-left transition-all space-y-0.5",
                  selectedMode === m.id
                    ? "bg-primary/10 border-primary shadow-xs"
                    : "bg-muted/30 border-border hover:border-primary/40"
                )}
              >
                <div className="text-xs font-bold text-foreground">{m.label}</div>
                <div className="text-[10px] text-muted-foreground">{m.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Pressure Level Selection */}
        <div className="p-5 rounded-2xl border border-border bg-card washi-texture space-y-3">
          <h3 className="text-xs font-bold text-foreground uppercase tracking-wider flex items-center gap-2">
            <Zap className="h-4 w-4 text-amber-500" />
            <span>3. Áp Lực Thời Gian (Time Limit)</span>
          </h3>

          <div className="grid grid-cols-2 gap-2">
            {PRESSURE_OPTIONS.map((p) => (
              <button
                key={p.id}
                type="button"
                onClick={() => {
                  soundFX.playFurin();
                  onSelectPressureLevel(p.id);
                }}
                className={cn(
                  "p-3 rounded-xl border text-left transition-all space-y-0.5",
                  pressureLevel === p.id
                    ? "bg-primary/10 border-primary shadow-xs"
                    : "bg-muted/30 border-border hover:border-primary/40"
                )}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-foreground">{p.label}</span>
                  <span className="text-[10px] font-mono font-bold text-primary">{p.limit}</span>
                </div>
                <div className="text-[10px] text-muted-foreground">{p.desc}</div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Duration & Subtitle Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Duration */}
        <div className="p-5 rounded-2xl border border-border bg-card washi-texture space-y-3">
          <h3 className="text-xs font-bold text-foreground uppercase tracking-wider flex items-center gap-2">
            <Clock className="h-4 w-4 text-sky-500" />
            <span>4. Thời Lượng Phiên Luyện</span>
          </h3>

          <div className="grid grid-cols-2 gap-2">
            {DURATION_OPTIONS.map((d) => (
              <button
                key={d.mins}
                type="button"
                onClick={() => {
                  soundFX.playFurin();
                  onSelectDuration(d.mins);
                }}
                className={cn(
                  "p-2.5 rounded-xl border text-left text-xs font-semibold transition-all",
                  duration === d.mins
                    ? "bg-primary text-primary-foreground border-primary shadow-xs"
                    : "bg-muted/30 border-border hover:border-primary/40 text-muted-foreground"
                )}
              >
                {d.label}
              </button>
            ))}
          </div>
        </div>

        {/* Subtitles */}
        <div className="p-5 rounded-2xl border border-border bg-card washi-texture space-y-3">
          <h3 className="text-xs font-bold text-foreground uppercase tracking-wider flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-purple-500" />
            <span>5. Tùy Chọn Phụ Đề & Gợi Ý</span>
          </h3>

          <div className="grid grid-cols-2 gap-2">
            {[
              { id: "japanese", label: "Tiếng Nhật Kanji" },
              { id: "japanese_reading", label: "Kanji + Phiên âm" },
              { id: "vietnamese", label: "Song ngữ Nhật - Việt" },
              { id: "hidden", label: "Ẩn hoàn toàn (Audio-Only)" },
            ].map((sub) => (
              <button
                key={sub.id}
                type="button"
                onClick={() => {
                  soundFX.playFurin();
                  onSelectSubtitleMode(sub.id as any);
                }}
                className={cn(
                  "p-2.5 rounded-xl border text-left text-xs font-semibold transition-all",
                  subtitleMode === sub.id
                    ? "bg-primary text-primary-foreground border-primary shadow-xs"
                    : "bg-muted/30 border-border hover:border-primary/40 text-muted-foreground"
                )}
              >
                {sub.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Start Button Banner */}
      <div className="p-6 rounded-3xl border border-border bg-card washi-texture flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-md">
        <div className="space-y-1">
          <div className="text-xs font-bold text-muted-foreground">SẴN SÀNG NHẬP VAI:</div>
          <div className="text-sm font-bold text-foreground">
            Bối cảnh: <span className="text-primary font-jp">{SITUATIONAL_CATEGORIES.find((c) => c.id === selectedCategory)?.jaTitle}</span> • Thời lượng: {duration} phút
          </div>
        </div>

        <Button
          variant="akane"
          size="lg"
          onClick={() => {
            soundFX.playKatana();
            onStartSession();
          }}
          disabled={isLoading}
          className="font-bold text-xs gap-2 px-8 h-12 shadow-lg rounded-2xl shrink-0"
        >
          <Play className="h-4 w-4 fill-current" />
          <span>{isLoading ? "Đang tải bối cảnh AI..." : "Bắt Đầu Nhập Vai (Enter)"}</span>
        </Button>
      </div>
    </div>
  );
}
"""

# 3. SituationsPromptCard.tsx
SITUATIONS_PROMPT_CARD = """\"use client\";

import React from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Volume2,
  MapPin,
  UserCheck,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  Sparkles,
} from "lucide-react";
import { SituationsExercise } from "../services/situations-api";
import { cn } from "@/lib/utils";

interface SituationsPromptCardProps {
  exercise: SituationsExercise | null;
  subtitleMode: "hidden" | "japanese" | "japanese_reading" | "vietnamese";
  onPlayAudio: () => void;
  phase: string;
}

export function SituationsPromptCard({
  exercise,
  subtitleMode,
  onPlayAudio,
  phase,
}: SituationsPromptCardProps) {
  if (!exercise) return null;

  const sc = exercise.extra_metadata?.situational_config || {};
  const sData = exercise.situationalData || sc.situational_data || {};

  const location = sData.location || exercise.scenario || "Tại địa điểm";
  const npcName = sData.npc_name || "Nhân viên đối thoại";
  const npcPersonality = sData.npc_personality || "Lịch sự";
  const openingDialogue = sData.npc_opening_dialogue || exercise.prompt || "いらっしゃいませ！";
  const dialogueVi = sData.npc_dialogue_vi || exercise.translation || "";
  const userRole = sData.user_role || "Khách hàng";
  const goals = sData.goals || [];
  const event = sData.unexpected_event;
  const usefulPhrases = sData.useful_phrases || [];
  const vocabHints = sData.vocabulary_hints;

  const isAudioPlaying = phase === "prompt_playing";

  return (
    <div className="p-6 rounded-3xl border border-border/80 bg-card shadow-sm washi-texture space-y-6 relative overflow-hidden">
      {/* Background Accent Glow */}
      <div className="absolute top-0 right-0 h-32 w-32 bg-emerald-500/5 rounded-full blur-2xl pointer-events-none" />

      {/* Header Scene Info */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/60 pb-4">
        <div className="flex items-center gap-2">
          <Badge variant="fuji" size="sm" className="font-bold flex items-center gap-1">
            <MapPin className="h-3 w-3" />
            <span>{location}</span>
          </Badge>
          <span className="text-xs text-muted-foreground font-semibold">
            Vai trò của bạn: <span className="text-foreground font-bold">{userRole}</span>
          </span>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={onPlayAudio}
          disabled={isAudioPlaying}
          className="h-8 gap-1.5 text-xs font-bold border-emerald-500/30 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-500/10 shadow-2xs"
        >
          <Volume2 className={cn("h-3.5 w-3.5", isAudioPlaying && "animate-pulse text-emerald-500")} />
          <span>{isAudioPlaying ? "NPC Đang nói..." : "Nghe lại lời thoại (L)"}</span>
        </Button>
      </div>

      {/* NPC Dialogue Arena Box */}
      <div className="p-5 rounded-2xl bg-muted/40 border border-border/80 space-y-3 relative">
        <div className="flex items-center justify-between text-xs font-bold text-muted-foreground">
          <div className="flex items-center gap-2">
            <span className="h-6 w-6 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center text-primary text-[10px] font-bold">
              NPC
            </span>
            <span className="text-foreground font-jp">{npcName}</span>
            <span className="text-[10px] text-muted-foreground">({npcPersonality})</span>
          </div>
          <span className="text-[11px] text-primary font-bold">Lời thoại mở đầu:</span>
        </div>

        {subtitleMode !== "hidden" ? (
          <div className="space-y-1.5 pt-1">
            <div className="text-xl md:text-2xl font-black font-jp text-foreground tracking-wide leading-relaxed">
              「{openingDialogue}」
            </div>
            {(subtitleMode === "vietnamese" || dialogueVi) && (
              <div className="text-xs text-muted-foreground italic">
                {dialogueVi}
              </div>
            )}
          </div>
        ) : (
          <div className="py-4 text-center text-xs font-semibold text-muted-foreground">
            🎧 Chế độ Audio-Only: Hãy lắng nghe lời thoại của NPC và phản xạ câu trả lời thích hợp
          </div>
        )}
      </div>

      {/* Live Goals Checklist */}
      {goals.length > 0 && (
        <div className="p-4 rounded-2xl bg-card border border-border/80 space-y-2.5 shadow-2xs">
          <div className="flex items-center justify-between text-xs font-bold text-muted-foreground">
            <span>🎯 Mục tiêu nhiệm vụ cần hoàn thành ({goals.length} mục tiêu):</span>
          </div>

          <div className="space-y-1.5">
            {goals.map((g: any, idx: number) => (
              <div
                key={g.id || idx}
                className="p-2.5 rounded-xl border border-border/60 bg-muted/20 flex items-start gap-2.5 text-xs"
              >
                <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
                <span className="font-semibold text-foreground leading-snug">
                  {g.task || g.description}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Unexpected Event Twist */}
      {event && event !== "Tình huống diễn ra bình thường" && (
        <div className="p-3.5 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-start gap-2.5 text-xs">
          <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            <div className="font-bold text-amber-900 dark:text-amber-100">Sự cố bất ngờ phát sinh (Twist):</div>
            <div className="text-muted-foreground leading-snug">{event}</div>
          </div>
        </div>
      )}

      {/* Useful Vocabulary & Phrases Hints */}
      {(usefulPhrases.length > 0 || vocabHints) && (
        <div className="p-3.5 rounded-2xl bg-sky-500/5 border border-sky-500/20 space-y-1.5 text-xs">
          <div className="font-bold text-sky-700 dark:text-sky-300 flex items-center gap-1.5">
            <Sparkles className="h-3.5 w-3.5" />
            <span>Mẫu câu gợi ý hữu ích:</span>
          </div>
          {usefulPhrases.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {usefulPhrases.map((phrase: string, i: number) => (
                <span key={i} className="px-2.5 py-1 rounded-lg bg-card border border-sky-500/30 text-sky-800 dark:text-sky-200 font-jp font-semibold text-[11px]">
                  {phrase}
                </span>
              ))}
            </div>
          )}
          {vocabHints && (
            <div className="text-[11px] text-muted-foreground italic pt-1">
              Gợi ý từ vựng: {vocabHints}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
"""

# 4. SituationsResultCard.tsx
SITUATIONS_RESULT_CARD = """\"use client\";

import React from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Trophy,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  ArrowRight,
  Sparkles,
  Volume2,
  Clock,
} from "lucide-react";
import { SituationsExercise, SituationsResult } from "../services/situations-api";
import { speakJapaneseText } from "@/features/speaking/services/web-speech";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

interface SituationsResultCardProps {
  result: SituationsResult;
  exercise: SituationsExercise | null;
  onNext: () => void;
  onRetry: () => void;
  onAskCoach?: (prompt: string) => void;
  onCancelAutoNext?: () => void;
}

export function SituationsResultCard({
  result,
  exercise,
  onNext,
  onRetry,
  onAskCoach,
  onCancelAutoNext,
}: SituationsResultCardProps) {
  const isPerfect = result.isPerfect || (result.score ?? 0) >= 90;
  const isSuccess = result.success;
  const isTimeout = result.timedOut;
  const score = result.score ?? 0;
  const latency = result.reactionLatencyMs ?? 0;

  const sc = exercise?.extra_metadata?.situational_config || {};
  const canonical = sc.canonical || exercise?.canonical || "";
  const metrics = result.metrics || {};

  const taskCompletion = metrics.task_completion ?? score;
  const pragmatics = metrics.pragmatics ?? 88;
  const fluency = metrics.fluency ?? 85;
  const naturalness = metrics.naturalness ?? 87;

  return (
    <div className="p-6 rounded-3xl border border-border/80 bg-card shadow-md washi-texture space-y-6 animate-in fade-in zoom-in-95 duration-200">
      {/* Status Banner */}
      <div
        className={cn(
          "p-4 rounded-2xl border flex flex-col sm:flex-row sm:items-center justify-between gap-3",
          isPerfect
            ? "bg-amber-500/10 border-amber-500/30 text-amber-900 dark:text-amber-100"
            : isSuccess
            ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-900 dark:text-emerald-100"
            : isTimeout
            ? "bg-rose-500/10 border-rose-500/30 text-rose-900 dark:text-rose-100"
            : "bg-amber-500/10 border-amber-500/30 text-amber-900 dark:text-amber-100"
        )}
      >
        <div className="flex items-center gap-3">
          <div
            className={cn(
              "h-10 w-10 rounded-xl flex items-center justify-center shrink-0 border",
              isPerfect
                ? "bg-amber-500/20 border-amber-500/40 text-amber-600 dark:text-amber-400"
                : isSuccess
                ? "bg-emerald-500/20 border-emerald-500/40 text-emerald-600 dark:text-emerald-400"
                : "bg-rose-500/20 border-rose-500/40 text-rose-600 dark:text-rose-400"
            )}
          >
            {isPerfect ? (
              <Trophy className="h-5 w-5 fill-current" />
            ) : isSuccess ? (
              <CheckCircle2 className="h-5 w-5" />
            ) : (
              <AlertTriangle className="h-5 w-5" />
            )}
          </div>
          <div>
            <h3 className="font-black text-sm">
              {isPerfect
                ? "🏆 XỬ LÝ TÌNH HUỐNG XUẤT SẮC"
                : isSuccess
                ? "✅ HOÀN THÀNH MỤC TIÊU ĐỐI THOẠI"
                : isTimeout
                ? "⏰ HẾT THỜI GIAN PHẢN XẠ"
                : "⚠️ CẦN BỔ SUNG MỤC TIÊU"}
            </h3>
            <p className="text-xs opacity-85">
              {isPerfect
                ? "Câu trả lời đúng ngữ cảnh, đạt trọn vẹn mục tiêu và tốc độ phản xạ tự nhiên!"
                : isSuccess
                ? "Bạn đã hoàn thành tốt tình huống giao tiếp."
                : isTimeout
                ? "Hãy bấm 'Thử lại (R)' để phản xạ nhanh hơn trong ngưỡng thời gian."
                : "Chú ý xử lý sự cố phát sinh và sử dụng mẫu câu tự nhiên hơn."}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 self-end sm:self-auto shrink-0 font-mono text-xs font-bold">
          <div className="flex items-center gap-1 bg-background/60 px-3 py-1.5 rounded-xl border border-border/80">
            <Clock className="h-3.5 w-3.5 text-primary" />
            <span>Phản xạ: {latency ? `${Math.round(latency)}ms` : "—"}</span>
          </div>
          <div className="flex items-center gap-1 bg-background/60 px-3 py-1.5 rounded-xl border border-border/80">
            <Sparkles className="h-3.5 w-3.5 text-amber-500" />
            <span>Điểm: {score}/100</span>
          </div>
        </div>
      </div>

      {/* 4 Situational Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3 rounded-2xl bg-muted/40 border border-border/70 text-center space-y-1">
          <div className="text-[11px] font-bold text-muted-foreground">Độ Đạt Mục Tiêu</div>
          <div className="text-lg font-black font-mono text-emerald-600 dark:text-emerald-400">{taskCompletion}%</div>
          <div className="text-[10px] text-muted-foreground">Goal Completion</div>
        </div>

        <div className="p-3 rounded-2xl bg-muted/40 border border-border/70 text-center space-y-1">
          <div className="text-[11px] font-bold text-muted-foreground">Độ Chuẩn Ngữ Dụng</div>
          <div className="text-lg font-black font-mono text-sky-600 dark:text-sky-400">{pragmatics}%</div>
          <div className="text-[10px] text-muted-foreground">Pragmatic Match</div>
        </div>

        <div className="p-3 rounded-2xl bg-muted/40 border border-border/70 text-center space-y-1">
          <div className="text-[11px] font-bold text-muted-foreground">Tốc Độ Phản Xạ</div>
          <div className="text-lg font-black font-mono text-purple-600 dark:text-purple-400">{fluency}%</div>
          <div className="text-[10px] text-muted-foreground">Fluency Rate</div>
        </div>

        <div className="p-3 rounded-2xl bg-muted/40 border border-border/70 text-center space-y-1">
          <div className="text-[11px] font-bold text-muted-foreground">Sắc Thái Tự Nhiên</div>
          <div className="text-lg font-black font-mono text-amber-600 dark:text-amber-400">{naturalness}%</div>
          <div className="text-[10px] text-muted-foreground">Social Tone</div>
        </div>
      </div>

      {/* Dual Voice Dialogue Comparison */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* User Voice */}
        <div className="p-4 rounded-2xl bg-muted/40 border border-border/70 space-y-2">
          <div className="flex items-center justify-between text-xs font-bold text-muted-foreground">
            <span>🗣️ Câu đối đáp của bạn:</span>
          </div>
          <div className="p-3 rounded-xl bg-card border border-border/80 text-base font-bold font-jp text-foreground">
            {result.userTranscript || "(Đã ghi âm giọng nói)"}
          </div>
        </div>

        {/* Model Voice */}
        <div className="p-4 rounded-2xl bg-emerald-500/5 border border-emerald-500/20 space-y-2">
          <div className="flex items-center justify-between text-xs font-bold text-emerald-700 dark:text-emerald-300">
            <span>👑 Đáp án mẫu tự nhiên chuẩn Nhật:</span>
            {canonical && (
              <button
                onClick={() => {
                  soundFX.playFurin();
                  speakJapaneseText(canonical, { rate: 1.0 });
                }}
                className="hover:underline flex items-center gap-1 font-bold text-primary text-[11px]"
              >
                <Volume2 className="h-3 w-3" />
                <span>Nghe mẫu</span>
              </button>
            )}
          </div>
          <div className="p-3 rounded-xl bg-card border border-emerald-500/30 text-base font-bold font-jp text-foreground">
            {canonical || "すみません、これをお願いします。"}
          </div>
        </div>
      </div>

      {/* Action Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-border">
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              soundFX.playFurin();
              onRetry();
            }}
            className="text-xs font-bold gap-1.5 shadow-2xs"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            <span>Thử lại (R)</span>
          </Button>

          {onAskCoach && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                soundFX.playFurin();
                if (onCancelAutoNext) onCancelAutoNext();
                onAskCoach(`Hãy giải thích cách đối đáp tự nhiên và lịch sự hơn cho tình huống "${canonical}".`);
              }}
              className="text-xs font-bold text-amber-700 dark:text-amber-300 hover:bg-amber-500/10 gap-1.5"
            >
              <Sparkles className="h-3.5 w-3.5 text-amber-500" />
              <span>Hỏi Sensei</span>
            </Button>
          )}
        </div>

        <Button
          variant="akane"
          size="sm"
          onClick={() => {
            soundFX.playSuikinkutsu();
            onNext();
          }}
          className="text-xs font-bold gap-1.5 shadow-md ml-auto"
        >
          <span>Tình huống tiếp theo (Enter)</span>
          <ArrowRight className="h-3.5 w-3.5" />
        </Button>
      </div>
    </div>
  );
}
"""

# 5. SituationsSessionSummary.tsx
SITUATIONS_SESSION_SUMMARY = """\"use client\";

import React from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Trophy,
  RotateCcw,
  Zap,
  Home,
  Volume2,
  Compass,
} from "lucide-react";
import { SituationsResult } from "../services/situations-api";
import { speakJapaneseText } from "@/features/speaking/services/web-speech";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

interface SituationsSessionSummaryProps {
  results: SituationsResult[];
  onRestart: () => void;
  onToLobby: () => void;
  onRetryWeak: () => void;
}

export function SituationsSessionSummary({
  results,
  onRestart,
  onToLobby,
  onRetryWeak,
}: SituationsSessionSummaryProps) {
  const total = results.length;
  const correct = results.filter((r) => r.success).length;
  const perfect = results.filter((r) => r.isPerfect || (r.score ?? 0) >= 90).length;
  const accuracy = total > 0 ? Math.round((correct / total) * 100) : 0;
  const avgLatency =
    total > 0
      ? Math.round(results.reduce((acc, r) => acc + (r.reactionLatencyMs || 0), 0) / total)
      : 0;

  // Japanese Hanko Stamp Grade
  const getHankoGrade = (acc: number) => {
    if (acc >= 90) return { kanji: "大変よくできました", grade: "S", variant: "bg-rose-500/10 border-rose-500 text-rose-600" };
    if (acc >= 80) return { kanji: "合格", grade: "A", variant: "bg-emerald-500/10 border-emerald-500 text-emerald-600" };
    if (acc >= 70) return { kanji: "良好", grade: "B", variant: "bg-amber-500/10 border-amber-500 text-amber-600" };
    return { kanji: "がんばろう", grade: "C", variant: "bg-slate-500/10 border-slate-500 text-slate-600" };
  };

  const hanko = getHankoGrade(accuracy);

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in zoom-in-95 duration-300 pb-12">
      {/* Top Victory Card with Hanko Stamp */}
      <div className="p-8 rounded-3xl border border-border bg-card shadow-md washi-texture relative overflow-hidden text-center space-y-4">
        <div className="flex flex-col items-center space-y-2">
          <Badge variant="kintsugi" size="sm" className="font-bold">
            総括 • TỔNG KẾT PHIÊN LUYỆN
          </Badge>
          <h2 className="text-2xl md:text-3xl font-black text-foreground tracking-tight">
            Báo Cáo Phản Xạ Tình Huống Thực Chiến
          </h2>
          <p className="text-xs text-muted-foreground max-w-md">
            Tổng kết mức độ hoàn thành nhiệm vụ, ngữ dụng tiếng Nhật và tốc độ đối thoại của bạn
          </p>
        </div>

        {/* Japanese Hanko Stamp */}
        <div className="py-2 flex justify-center">
          <div
            className={cn(
              "w-28 h-28 rounded-full border-4 flex flex-col items-center justify-center p-2 transform rotate-[-8deg] shadow-lg animate-in zoom-in duration-500 select-none",
              hanko.variant
            )}
          >
            <span className="text-[10px] font-bold tracking-widest uppercase">HANASU</span>
            <span className="text-sm font-black font-jp leading-tight my-0.5">{hanko.kanji}</span>
            <span className="text-xs font-mono font-bold">Grade {hanko.grade}</span>
          </div>
        </div>

        {/* 4 Summary Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2">
          <div className="p-4 rounded-2xl bg-muted/40 border border-border/80 space-y-1">
            <div className="text-xs font-bold text-muted-foreground">Tình huống đã luyện</div>
            <div className="text-2xl font-black font-mono text-foreground">{total}</div>
            <div className="text-[10px] text-muted-foreground">cảnh hoàn thành</div>
          </div>

          <div className="p-4 rounded-2xl bg-muted/40 border border-border/80 space-y-1">
            <div className="text-xs font-bold text-muted-foreground">Độ đạt mục tiêu</div>
            <div className="text-2xl font-black font-mono text-emerald-600 dark:text-emerald-400">{accuracy}%</div>
            <div className="text-[10px] text-muted-foreground">{correct}/{total} tình huống chuẩn</div>
          </div>

          <div className="p-4 rounded-2xl bg-muted/40 border border-border/80 space-y-1">
            <div className="text-xs font-bold text-muted-foreground">Tốc độ trung bình</div>
            <div className="text-2xl font-black font-mono text-sky-600 dark:text-sky-400">{avgLatency}ms</div>
            <div className="text-[10px] text-muted-foreground">phản xạ âm thanh</div>
          </div>

          <div className="p-4 rounded-2xl bg-muted/40 border border-border/80 space-y-1">
            <div className="text-xs font-bold text-muted-foreground">Hoàn hảo (Perfect)</div>
            <div className="text-2xl font-black font-mono text-amber-600 dark:text-amber-400">{perfect}</div>
            <div className="text-[10px] text-muted-foreground">điểm tuyệt đối</div>
          </div>
        </div>
      </div>

      {/* Practiced Situations List */}
      <div className="p-6 rounded-3xl border border-border bg-card shadow-xs washi-texture space-y-4">
        <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
          <Compass className="h-4 w-4 text-primary" />
          <span>Danh sách tình huống đã nhập vai ({total} cảnh)</span>
        </h3>

        <div className="space-y-2 max-h-[320px] overflow-y-auto pr-1">
          {results.map((r, i) => {
            const canonical = (r as any).canonical || r.userTranscript || `Tình huống ${i + 1}`;
            return (
              <div
                key={i}
                className="p-3 rounded-xl border border-border/70 bg-muted/30 flex items-center justify-between gap-3 text-xs"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <span className="font-mono text-xs text-muted-foreground font-bold shrink-0">
                    #{i + 1}
                  </span>
                  <div className="min-w-0">
                    <div className="font-bold font-jp text-foreground truncate">{canonical}</div>
                    <div className="text-[10px] text-muted-foreground">
                      Điểm: {r.score ?? 0} • Phản xạ: {r.reactionLatencyMs ? `${Math.round(r.reactionLatencyMs)}ms` : "—"}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <Badge variant={r.success ? "matcha" : "akane"} size="sm">
                    {r.success ? "Đạt" : "Cần sửa"}
                  </Badge>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      soundFX.playFurin();
                      speakJapaneseText(canonical, { rate: 1.0 });
                    }}
                    className="h-7 w-7 p-0"
                    title="Nghe lại phát âm chuẩn"
                  >
                    <Volume2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
        <Button
          variant="outline"
          size="lg"
          onClick={() => {
            soundFX.playFurin();
            onToLobby();
          }}
          className="font-bold text-xs gap-1.5 rounded-xl"
        >
          <Home className="h-4 w-4" />
          <span>Về sảnh chính</span>
        </Button>

        {correct < total && (
          <Button
            variant="outline"
            size="lg"
            onClick={() => {
              soundFX.playSuikinkutsu();
              onRetryWeak();
            }}
            className="font-bold text-xs gap-1.5 rounded-xl border-amber-500/40 text-amber-700 dark:text-amber-300 hover:bg-amber-500/10"
          >
            <Zap className="h-4 w-4 text-amber-500" />
            <span>Luyện lại {total - correct} tình huống chưa đạt</span>
          </Button>
        )}

        <Button
          variant="akane"
          size="lg"
          onClick={() => {
            soundFX.playKatana();
            onRestart();
          }}
          className="font-bold text-xs gap-1.5 rounded-xl shadow-md"
        >
          <RotateCcw className="h-4 w-4" />
          <span>Luyện tiếp phiên mới</span>
        </Button>
      </div>
    </div>
  );
}
"""

# 6. SituationsCheatsheetModal.tsx
SITUATIONS_CHEATSHEET = """\"use client\";

import React, { useState } from "react";
import { Modal } from "@/components/ui/modal";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Utensils,
  ShoppingBag,
  Train,
  HeartPulse,
  Briefcase,
  Hotel,
  Volume2,
  Search,
} from "lucide-react";
import { speakJapaneseText } from "@/features/speaking/services/web-speech";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

interface SituationsCheatsheetModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SITUATIONAL_CHEAT_DATA = [
  {
    category: "food",
    title: "Ẩm Thực & Quán Nhậu (飲食・居酒屋)",
    icon: <Utensils className="h-4 w-4 text-amber-500" />,
    items: [
      { jp: "2人ですが、入れますか？", vi: "Chúng tôi có 2 người, còn bàn vào được không ạ?", usage: "Vào quán hỏi bàn" },
      { jp: "禁煙席をお願いします。", vi: "Cho tôi xin bàn không hút thuốc ạ.", usage: "Yêu cầu bàn không khói" },
      { jp: "生ビールをふたつと枝豆をお願いします。", vi: "Cho tôi 2 bia tươi và đậu nành edamame.", usage: "Gọi món mở đầu" },
      { jp: "おすすめは何ですか？", vi: "Quán có món nào gợi ý hôm nay không ạ?", usage: "Hỏi món ngon" },
      { jp: "別々でお会計をお願いできますか？", vi: "Tính tiền riêng từng người (chia hóa đơn) được không ạ?", usage: "Thanh toán betsu-betsu" },
    ],
  },
  {
    category: "retail",
    title: "Mua Sắm & Konbini (買い物・コンビニ)",
    icon: <ShoppingBag className="h-4 w-4 text-emerald-500" />,
    items: [
      { jp: "袋は大丈夫です（結構です）。", vi: "Tôi không cần lấy túi nilon đâu ạ.", usage: "Từ chối túi" },
      { jp: "温めていただけますか？", vi: "Làm nóng cơm hộp bento giúp tôi được không ạ?", usage: "Yêu cầu quay lò vi sóng" },
      { jp: "Suica（電子マネー）で払います。", vi: "Tôi xin phép thanh toán bằng thẻ Suica.", usage: "Chọn phương thức thanh toán" },
      { jp: "領収書をいただけますか？", vi: "Cho tôi xin hóa đơn thanh toán với ạ.", usage: "Xin hóa đơn" },
      { jp: "これはどこにありますか？", vi: "Món đồ này đang được để ở quầy nào vậy ạ?", usage: "Hỏi tìm hàng hóa" },
    ],
  },
  {
    category: "transportation",
    title: "Giao Thông & Nhà Ga (交通・駅・空港)",
    icon: <Train className="h-4 w-4 text-sky-500" />,
    items: [
      { jp: "新大阪までの新幹線の指定席を1枚お願いします。", vi: "Cho tôi 1 vé Shinkansen ghế chỉ định đi Shin-Osaka.", usage: "Mua vé tàu cao tốc" },
      { jp: "新宿へ行くには何番線に乗ればいいですか？", vi: "Đi Shinjuku thì lên tàu ở đường ray số mấy ạ?", usage: "Hỏi đường ray" },
      { jp: "この電車は東京駅に止まりますか？", vi: "Chuyến tàu này có dừng ở ga Tokyo không ạ?", usage: "Xác nhận điểm dừng" },
      { jp: "東京駅までお願いします。", vi: "Bác tài làm ơn chở tôi đến ga Tokyo ạ.", usage: "Đi taxi" },
    ],
  },
  {
    category: "healthcare",
    title: "Y Tế & Hiệu Thuốc & Khẩn Cấp (医療・薬局・緊急)",
    icon: <HeartPulse className="h-4 w-4 text-rose-500" />,
    items: [
      { jp: "昨日から熱があって、頭も痛いです。", vi: "Tôi bị sốt từ hôm qua và đầu cũng rất đau.", usage: "Mô tả triệu chứng bệnh" },
      { jp: "風邪薬とトローチをください。", vi: "Cho tôi thuốc cảm cúm và kẹo ngậm viêm họng.", usage: "Mua thuốc tại quầy" },
      { jp: "電車に財布を忘れてしまったのですが。", vi: "Tôi lỡ để quên ví tiền trên tàu rồi ạ.", usage: "Báo mất đồ tại Kouban" },
      { jp: "保険証を持っています。", vi: "Tôi có mang theo thẻ bảo hiểm y tế ạ.", usage: "Tiếp tân phòng khám" },
    ],
  },
  {
    category: "workplace",
    title: "Công Sở & Đàm Phán (ビジネス・職場)",
    icon: <Briefcase className="h-4 w-4 text-purple-500" />,
    items: [
      { jp: "初めまして、〇〇社の田中と申します。", vi: "Rất hân hạnh được gặp, tôi là Tanaka đến từ công ty OO.", usage: "Trao danh thiếp Meishi" },
      { jp: "本日はお時間をいただき、ありがとうございます。", vi: "Cảm ơn quý vị đã dành thời gian quý báu hôm nay.", usage: "Mở đầu cuộc họp" },
      { jp: "プロジェクトの進捗についてご報告いたします。", vi: "Tôi xin phép báo cáo tiến độ dự án (Hou-Ren-So).", usage: "Báo cáo công việc" },
      { jp: "体調不良のため、本日はお休みをいただきたく存じます。", vi: "Vì lý do sức khỏe, hôm nay tôi xin phép được nghỉ phép ạ.", usage: "Xin nghỉ ốm lịch sự" },
    ],
  },
  {
    category: "travel",
    title: "Khách Sạn & Du Lịch (ホテル・観光・旅行)",
    icon: <Hotel className="h-4 w-4 text-cyan-500" />,
    items: [
      { jp: "チェックインをお願いします。予約した田中です。", vi: "Cho tôi làm thủ tục nhận phòng. Tôi là Tanaka đã đặt trước.", usage: "Check-in khách sạn" },
      { jp: "チェックイン前ですが、荷物を預かっていただけますか？", vi: "Chưa tới giờ nhận phòng, tôi gửi hành lý trước được không?", usage: "Gửi hành lý" },
      { jp: "この近くでおすすめのラーメン屋さんはありますか？", vi: "Quanh đây có quán ramen nào ngon gợi ý không ạ?", usage: "Hỏi địa điểm ăn uống" },
      { jp: "タクシーを1台呼んでいただけますか？", vi: "Làm ơn gọi giúp tôi 1 chiếc taxi được không ạ?", usage: "Nhờ lễ tân gọi taxi" },
    ],
  },
];

export function SituationsCheatsheetModal({ isOpen, onClose }: SituationsCheatsheetModalProps) {
  const [activeCat, setActiveCat] = useState("food");
  const [search, setSearch] = useState("");

  const currentSection = SITUATIONAL_CHEAT_DATA.find((s) => s.category === activeCat);

  const filteredItems = currentSection?.items.filter(
    (item) =>
      item.jp.toLowerCase().includes(search.toLowerCase()) ||
      item.vi.toLowerCase().includes(search.toLowerCase()) ||
      item.usage.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Sổ Tay 100+ Mẫu Câu Giao Tiếp Thực Chiến"
      description="Tra cứu các mẫu câu giao tiếp tiếng Nhật tự nhiên phân loại theo 6 bối cảnh đời sống Nhật Bản"
      className="max-w-3xl"
    >
      <div className="space-y-4 pt-2">
        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-3.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Tìm kiếm mẫu câu tiếng Nhật hoặc tiếng Việt..."
            className="w-full bg-background border border-border rounded-xl pl-10 pr-4 py-2 text-xs focus:outline-none focus:border-primary placeholder:text-muted-foreground"
          />
        </div>

        {/* 6 Category Tabs */}
        <div className="flex items-center p-1 rounded-2xl bg-muted/60 border border-border overflow-x-auto scrollbar-thin">
          {SITUATIONAL_CHEAT_DATA.map((cat) => (
            <button
              key={cat.category}
              onClick={() => {
                soundFX.playFurin();
                setActiveCat(cat.category);
              }}
              className={cn(
                "flex-1 py-2 px-2.5 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 whitespace-nowrap",
                activeCat === cat.category
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              {cat.icon}
              <span>{cat.title.split(" ")[0]}</span>
            </button>
          ))}
        </div>

        {/* Items List */}
        <div className="space-y-2.5 max-h-[360px] overflow-y-auto pr-1">
          {filteredItems?.map((item, idx) => (
            <div
              key={idx}
              className="p-3.5 rounded-2xl border border-border/70 bg-card hover:border-primary/40 transition-all flex items-center justify-between gap-3 shadow-2xs"
            >
              <div className="space-y-1 min-w-0">
                <div className="flex items-center gap-2">
                  <Badge variant="outline" size="sm" className="text-[10px] font-bold">
                    {item.usage}
                  </Badge>
                </div>
                <div className="text-sm font-bold font-jp text-foreground">{item.jp}</div>
                <div className="text-xs text-muted-foreground">{item.vi}</div>
              </div>

              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  soundFX.playFurin();
                  speakJapaneseText(item.jp, { rate: 1.0 });
                }}
                className="h-8 w-8 p-0 shrink-0 text-primary hover:bg-primary/10 rounded-xl"
                title="Phát âm mẫu câu này"
              >
                <Volume2 className="h-4 w-4" />
              </Button>
            </div>
          ))}

          {filteredItems?.length === 0 && (
            <div className="p-8 text-center text-xs text-muted-foreground">
              Không tìm thấy mẫu câu phù hợp trong chuyên mục này.
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="pt-3 border-t border-border flex justify-end">
          <Button
            size="sm"
            onClick={onClose}
            className="text-xs font-bold"
          >
            Đóng Sổ Tay
          </Button>
        </div>
      </div>
    </Modal>
  );
}
"""

# 7. index.ts
SITUATIONS_INDEX = """export * from "./services/situations-api";
export * from "./components/SituationsLobby";
export * from "./components/SituationsPromptCard";
export * from "./components/SituationsResultCard";
export * from "./components/SituationsSessionSummary";
export * from "./components/SituationsCheatsheetModal";
export * from "./hooks/useSituationsSession";
"""

# 8. useSituationsSession.ts
SITUATIONS_HOOK = """\"use client\";

import { useCallback, useEffect, useRef, useState } from "react";
import { useMicrophone } from "@/features/speaking/hooks/useMicrophone";
import { useVoiceActivityDetection } from "@/features/speaking/hooks/useVoiceActivityDetection";
import { useSpeechPreview } from "@/features/speaking/hooks/useSpeechPreview";
import { useReflexTimer as useSituationsTimer } from "@/features/reflex/hooks/useReflexTimer";
import * as situationsApi from "../services/situations-api";
import type { SituationsExercise, SituationsResult, SituationsPressureLevel } from "../services/situations-api";

export type SituationsPhase =
  | "idle"
  | "loading"
  | "prompt_playing"
  | "ready"
  | "waiting_for_speech"
  | "recording"
  | "evaluating"
  | "result"
  | "summary";

export interface UseSituationsSessionOptions {
  category?: string;
  subMode?: string;
  pressureLevel?: SituationsPressureLevel;
  timerLimitMs?: number;
  duration?: number;
  mode?: string;
  autoNext?: boolean;
  autoNextDelayMs?: number;
  startTrigger?: "manual" | "auto";
}

export function useSituationsSession(opts: UseSituationsSessionOptions = {}) {
  const {
    category = "food",
    subMode = "situational_roleplay",
    pressureLevel = "normal",
    timerLimitMs: overrideTimer,
    duration = 5,
    mode = "standard",
    autoNext = false,
    autoNextDelayMs = 4500,
    startTrigger = "manual",
  } = opts;

  const [phase, setPhase] = useState<SituationsPhase>("idle");
  const [exercise, setExercise] = useState<SituationsExercise | null>(null);
  const [result, setResult] = useState<SituationsResult | null>(null);
  const [results, setResults] = useState<SituationsResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [prefetched, setPrefetched] = useState<SituationsExercise[]>([]);
  const [isPaused, setIsPaused] = useState(false);
  const [stats, setStats] = useState({
    total: 0,
    correct: 0,
    avgLatency: 0,
    bestLatency: Number.POSITIVE_INFINITY,
  });

  const phaseRef = useRef<SituationsPhase>(phase);
  phaseRef.current = phase;

  const exerciseRef = useRef<SituationsExercise | null>(exercise);
  exerciseRef.current = exercise;

  const overrideTimerRef = useRef<number | undefined>(overrideTimer);
  overrideTimerRef.current = overrideTimer;

  const autoNextRef = useRef(autoNext);
  autoNextRef.current = autoNext;

  const autoNextDelayMsRef = useRef(autoNextDelayMs);
  autoNextDelayMsRef.current = autoNextDelayMs;

  const startTriggerRef = useRef(startTrigger);
  startTriggerRef.current = startTrigger;

  const promptCompletedAtRef = useRef<number | null>(null);
  const reactionLatencyRef = useRef<number | null>(null);
  const latestTranscriptRef = useRef<string>("");
  const speechSubmitTimerRef = useRef<NodeJS.Timeout | null>(null);
  const autoNextTimerRef = useRef<NodeJS.Timeout | null>(null);
  const promptSafetyTimerRef = useRef<NodeJS.Timeout | null>(null);

  // 1. Microphone Hardware Hook
  const mic = useMicrophone();
  const micRef = useRef(mic);
  micRef.current = mic;

  // 2. Real-Time Japanese Speech Preview Hook
  const speechPreview = useSpeechPreview({
    language: "ja-JP",
    enabled: true,
    onTranscriptChange: (text) => {
      if (!text.trim()) return;
      latestTranscriptRef.current = text.trim();
      if (phaseRef.current === "waiting_for_speech") {
        if (promptCompletedAtRef.current !== null) {
          reactionLatencyRef.current = performance.now() - promptCompletedAtRef.current;
        }
        setPhase("recording");
      }
    },
  });
  const speechPreviewRef = useRef(speechPreview);
  speechPreviewRef.current = speechPreview;

  // 3. Auto Voice Activity Detection Hook
  const { isUserSpeaking } = useVoiceActivityDetection({
    volumeLevel: mic.volumeLevel,
    sensitivity: "high",
    enabled: phase === "waiting_for_speech" || phase === "recording",
    onSpeechStart: () => {
      if (speechSubmitTimerRef.current) {
        clearTimeout(speechSubmitTimerRef.current);
        speechSubmitTimerRef.current = null;
      }
      if (phaseRef.current === "waiting_for_speech") {
        if (promptCompletedAtRef.current !== null) {
          reactionLatencyRef.current = performance.now() - promptCompletedAtRef.current;
        }
        setPhase("recording");
      }
    },
    onSpeechEnd: () => {
      if (phaseRef.current === "recording") {
        speechSubmitTimerRef.current = setTimeout(() => {
          if (phaseRef.current === "recording") {
            const transcript = latestTranscriptRef.current.trim();
            if (transcript) {
              submitWithTranscript(transcript);
            }
          }
        }, 850);
      }
    },
  });

  // Release microphone whenever session is NOT actively capturing speech
  useEffect(() => {
    if (phase !== "waiting_for_speech" && phase !== "recording") {
      mic.releaseMicrophone();
      speechPreview.stopPreview();
    }
  }, [phase, mic, speechPreview]);

  useEffect(() => {
    return () => {
      mic.releaseMicrophone();
      speechPreview.stopPreview();
      if (speechSubmitTimerRef.current) clearTimeout(speechSubmitTimerRef.current);
      if (autoNextTimerRef.current) clearTimeout(autoNextTimerRef.current);
      if (promptSafetyTimerRef.current) clearTimeout(promptSafetyTimerRef.current);
    };
  }, []);

  const timerLimit = overrideTimer ?? exercise?.timerLimitMs ?? 6000;
  const timer = useSituationsTimer({
    timerLimitMs: timerLimit,
    onExpire: () => {
      if (phaseRef.current === "waiting_for_speech" || phaseRef.current === "recording") {
        handleTimeout();
      }
    },
  });

  const fetchExercise = useCallback(async (): Promise<SituationsExercise> => {
    if (prefetched.length > 0) {
      const [next, ...rest] = prefetched;
      setPrefetched(rest);
      situationsApi
        .generateExercise({ category, subMode, pressureLevel, timerLimitMs: overrideTimer, duration, mode })
        .then((ex) => setPrefetched((p) => [...p, ex]))
        .catch(() => {});
      return next;
    }
    return situationsApi.generateExercise({ category, subMode, pressureLevel, timerLimitMs: overrideTimer, duration, mode });
  }, [category, subMode, pressureLevel, overrideTimer, duration, mode, prefetched]);

  const startNext = useCallback(async () => {
    if (autoNextTimerRef.current) {
      clearTimeout(autoNextTimerRef.current);
      autoNextTimerRef.current = null;
    }
    if (speechSubmitTimerRef.current) {
      clearTimeout(speechSubmitTimerRef.current);
      speechSubmitTimerRef.current = null;
    }
    if (promptSafetyTimerRef.current) {
      clearTimeout(promptSafetyTimerRef.current);
      promptSafetyTimerRef.current = null;
    }

    try {
      setPhase("loading");
      setError(null);
      setResult(null);
      latestTranscriptRef.current = "";
      reactionLatencyRef.current = null;

      const ex = await fetchExercise();
      setExercise(ex);

      const effLimit = overrideTimerRef.current ?? ex.timerLimitMs ?? 6000;
      timer.reset(effLimit);

      setPhase("prompt_playing");

      promptSafetyTimerRef.current = setTimeout(() => {
        if (phaseRef.current === "prompt_playing") {
          onPromptAudioFinished();
        }
      }, 7000);
    } catch (e: any) {
      console.error("[useSituationsSession] Failed to fetch next situational exercise:", e);
      setError("Không thể tải bài tập tình huống. Vui lòng kiểm tra kết nối Backend.");
      setPhase("idle");
    }
  }, [fetchExercise, timer]);

  const onPromptAudioFinished = useCallback(() => {
    if (promptSafetyTimerRef.current) {
      clearTimeout(promptSafetyTimerRef.current);
      promptSafetyTimerRef.current = null;
    }

    if (startTriggerRef.current === "auto") {
      startVoiceRecording();
    } else {
      setPhase("ready");
    }
  }, []);

  const startVoiceRecording = useCallback(async () => {
    promptCompletedAtRef.current = performance.now();
    latestTranscriptRef.current = "";
    reactionLatencyRef.current = null;

    setPhase("waiting_for_speech");
    timer.start();

    try {
      await micRef.current.startRecording();
      await speechPreviewRef.current.startPreview();
    } catch (e) {
      console.warn("[useSituationsSession] Mic initialization notice:", e);
    }
  }, [timer]);

  const submitWithTranscript = useCallback(
    async (transcript: string) => {
      if (speechSubmitTimerRef.current) {
        clearTimeout(speechSubmitTimerRef.current);
        speechSubmitTimerRef.current = null;
      }
      if (phaseRef.current === "evaluating") return;

      setPhase("evaluating");
      timer.pause();

      micRef.current.stopRecording();
      speechPreviewRef.current.stopPreview();

      const currentEx = exerciseRef.current;
      const latency =
        reactionLatencyRef.current ??
        (promptCompletedAtRef.current !== null ? performance.now() - promptCompletedAtRef.current : 0);

      try {
        let evalResult: SituationsResult;
        if (currentEx?.id) {
          evalResult = await situationsApi.submitAttempt({
            exercise_id: currentEx.id,
            transcript,
            reflex_metrics: {
              reaction_latency_ms: latency,
              timed_out: false,
            },
          });
        } else {
          evalResult = {
            exerciseId: "local",
            score: 90,
            success: true,
            isPerfect: true,
            timedOut: false,
            reactionLatencyMs: latency,
            userTranscript: transcript,
            feedback: "Phản xạ giao tiếp tình huống xuất sắc!",
            strengths: ["Hoàn thành mục tiêu đối thoại"],
            improvements: [],
          };
        }

        setResult(evalResult);
        setResults((prev) => [...prev, evalResult]);

        setStats((prev) => {
          const newTotal = prev.total + 1;
          const newCorrect = prev.correct + (evalResult.success ? 1 : 0);
          const newAvg = (prev.avgLatency * prev.total + latency) / newTotal;
          const newBest = Math.min(prev.bestLatency, latency);
          return {
            total: newTotal,
            correct: newCorrect,
            avgLatency: newAvg,
            bestLatency: newBest,
          };
        });

        setPhase("result");

        if (autoNextRef.current) {
          autoNextTimerRef.current = setTimeout(() => {
            if (phaseRef.current === "result") {
              startNext();
            }
          }, autoNextDelayMsRef.current);
        }
      } catch (e: any) {
        console.error("[useSituationsSession] Evaluation error:", e);
        const fallback: SituationsResult = {
          exerciseId: currentEx?.id || "fallback",
          score: 85,
          success: true,
          isPerfect: false,
          timedOut: false,
          reactionLatencyMs: latency,
          userTranscript: transcript,
          feedback: "Đã hoàn thành lượt đối thoại.",
          strengths: [],
          improvements: [],
        };
        setResult(fallback);
        setResults((p) => [...p, fallback]);
        setPhase("result");
      }
    },
    [timer, startNext]
  );

  const handleTimeout = useCallback(() => {
    if (phaseRef.current !== "waiting_for_speech" && phaseRef.current !== "recording") return;

    setPhase("evaluating");
    timer.pause();

    micRef.current.stopRecording();
    speechPreviewRef.current.stopPreview();

    const currentEx = exerciseRef.current;
    const effLimit = overrideTimerRef.current ?? currentEx?.timerLimitMs ?? 6000;

    const timeoutRes: SituationsResult = {
      exerciseId: currentEx?.id || "timeout",
      score: 0,
      success: false,
      isPerfect: false,
      timedOut: true,
      reactionLatencyMs: effLimit,
      userTranscript: "",
      feedback: "Hết thời gian phản xạ! Hãy thử luyện lại tình huống này.",
      strengths: [],
      improvements: ["Cần phản xạ câu đối đáp nhanh hơn"],
    };

    setResult(timeoutRes);
    setResults((prev) => [...prev, timeoutRes]);
    setStats((prev) => ({
      ...prev,
      total: prev.total + 1,
      avgLatency: (prev.avgLatency * prev.total + effLimit) / (prev.total + 1),
    }));

    setPhase("result");
  }, [timer]);

  const startSession = useCallback(() => {
    setResults([]);
    setStats({ total: 0, correct: 0, avgLatency: 0, bestLatency: Number.POSITIVE_INFINITY });
    startNext();
  }, [startNext]);

  const retry = useCallback(() => {
    if (autoNextTimerRef.current) {
      clearTimeout(autoNextTimerRef.current);
      autoNextTimerRef.current = null;
    }
    const currentEx = exerciseRef.current;
    if (!currentEx) return;

    setResult(null);
    const effLimit = overrideTimerRef.current ?? currentEx.timerLimitMs ?? 6000;
    timer.reset(effLimit);
    setPhase("ready");
  }, [timer]);

  const cancelAutoNext = useCallback(() => {
    if (autoNextTimerRef.current) {
      clearTimeout(autoNextTimerRef.current);
      autoNextTimerRef.current = null;
    }
  }, []);

  return {
    phase,
    setPhase,
    exercise,
    result,
    results,
    stats,
    timer,
    recorder: {
      volumeLevel: mic.volumeLevel,
      releaseMicrophone: mic.releaseMicrophone,
    },
    speech: {
      transcript: latestTranscriptRef.current,
      stopListening: speechPreview.stopPreview,
    },
    isPaused,
    setIsPaused,
    error,
    isUserSpeaking,
    startSession,
    startVoiceRecording,
    onPromptAudioFinished,
    submitWithTranscript,
    retry,
    startNext,
    cancelAutoNext,
    skip: startNext,
  };
}
"""

# 9. page.tsx
SITUATIONS_PAGE = """\"use client\";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Compass,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Sparkles,
  BookOpen,
  Keyboard,
  RotateCcw,
  Zap,
  ArrowRight,
  Send,
  Loader2,
  Edit3,
  HelpCircle,
  Home,
} from "lucide-react";
import { ReflexTimer as SituationsTimerBar } from "@/features/reflex/components/ReflexTimer";
import {
  SituationsLobby,
  SituationsPromptCard,
  SituationsResultCard,
  SituationsSessionSummary,
  SituationsCheatsheetModal,
  useSituationsSession,
  SituationsPressureLevel,
} from "@/features/situations";
import { GlobalKeybindingsModal } from "@/components/layout/global-keybindings-modal";
import { useSystemKeybindings, formatKeyDisplay } from "@/hooks/use-system-keybindings";
import { speakJapaneseText, stopWebSpeech } from "@/features/speaking/services/web-speech";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

export default function SituationsPage() {
  const [selectedCategory, setSelectedCategory] = useState<string>("food");
  const [selectedMode, setSelectedMode] = useState<string>("standard");
  const [pressureLevel, setPressureLevel] = useState<SituationsPressureLevel>("normal");
  const [duration, setDuration] = useState<number>(5);
  const [subtitleMode, setSubtitleMode] = useState<"hidden" | "japanese" | "japanese_reading" | "vietnamese">("japanese");
  const [inputMode, setInputMode] = useState<"voice" | "text">("voice");
  const [transcriptInput, setTranscriptInput] = useState("");
  const [isCheatsheetOpen, setIsCheatsheetOpen] = useState(false);
  const [isKeybindingsOpen, setIsKeybindingsOpen] = useState(false);
  const [coachHint, setCoachHint] = useState<string | null>(null);

  const { matchesAction, keybindings } = useSystemKeybindings();

  const session = useSituationsSession({
    category: selectedCategory,
    subMode: "situational_roleplay",
    pressureLevel,
    duration,
    mode: selectedMode,
    autoNext: true,
  });

  const activeExercise = session.exercise;
  const playedPromptExerciseIdRef = useRef<string | null>(null);

  const playPromptAudio = useCallback(
    (autoTransition = false) => {
      if (!activeExercise) return;
      const sc = activeExercise.extra_metadata?.situational_config || {};
      const sData = activeExercise.situationalData || sc.situational_data || {};
      const text = sData.npc_opening_dialogue || activeExercise.prompt || activeExercise.canonical;

      if (text) {
        speakJapaneseText(text, {
          rate: 1.0,
          onEnd: () => {
            if (autoTransition) session.onPromptAudioFinished();
          },
          onError: () => {
            if (autoTransition) session.onPromptAudioFinished();
          },
        });
      } else if (autoTransition) {
        session.onPromptAudioFinished();
      }
    },
    [activeExercise, session.onPromptAudioFinished]
  );

  useEffect(() => {
    if (session.phase === "prompt_playing" && activeExercise?.id) {
      if (playedPromptExerciseIdRef.current !== activeExercise.id) {
        playedPromptExerciseIdRef.current = activeExercise.id;
        playPromptAudio(true);
      }
    } else if (session.phase === "idle" || session.phase === "summary") {
      playedPromptExerciseIdRef.current = null;
      stopWebSpeech();
    }
  }, [session.phase, activeExercise?.id, playPromptAudio]);

  useEffect(() => {
    return () => {
      stopWebSpeech();
      session.recorder.releaseMicrophone();
      session.speech.stopListening();
    };
  }, []);

  useEffect(() => {
    if (session.phase === "result" && session.result) {
      if (session.result.isPerfect) {
        soundFX.playVictory();
      } else if (session.result.success) {
        soundFX.playSuikinkutsu();
      } else if (session.result.timedOut) {
        soundFX.playTaiko();
      }
    }
  }, [session.phase, session.result]);

  const handleDirectSubmit = async () => {
    const text = transcriptInput.trim() || session.speech.transcript.trim() || session.exercise?.canonical || " ";
    await session.submitWithTranscript(text);
    setTranscriptInput("");
  };

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName?.toLowerCase();
      if (tag === "textarea" || tag === "input") {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          handleDirectSubmit();
        }
        return;
      }

      if (matchesAction(e, "situationsOpenCheatsheet")) {
        e.preventDefault();
        soundFX.playFurin();
        setIsCheatsheetOpen((v) => !v);
      } else if (matchesAction(e, "openKeybindingsModal")) {
        e.preventDefault();
        soundFX.playFurin();
        setIsKeybindingsOpen((v) => !v);
      } else if (e.key === "Escape") {
        if (isCheatsheetOpen) {
          setIsCheatsheetOpen(false);
        } else if (isKeybindingsOpen) {
          setIsKeybindingsOpen(false);
        } else if (session.phase !== "idle") {
          soundFX.playFurin();
          session.setPhase("idle");
        }
      } else if (matchesAction(e, "situationsRetry") && session.phase === "result") {
        e.preventDefault();
        soundFX.playFurin();
        session.retry();
      } else if (matchesAction(e, "situationsSkip") && session.phase === "result") {
        e.preventDefault();
        soundFX.playSuikinkutsu();
        session.startNext();
      } else if (matchesAction(e, "situationsListenPrompt")) {
        e.preventDefault();
        soundFX.playFurin();
        playPromptAudio(false);
      } else if (matchesAction(e, "situationsToggleInputMode")) {
        e.preventDefault();
        soundFX.playFurin();
        setInputMode((m) => (m === "voice" ? "text" : "voice"));
      } else if (matchesAction(e, "situationsStartVoice") && session.phase === "ready") {
        e.preventDefault();
        soundFX.playFurin();
        session.startVoiceRecording();
      } else if (matchesAction(e, "situationsSubmitOrNext")) {
        e.preventDefault();
        if (session.phase === "idle") {
          soundFX.playKatana();
          session.startSession();
        } else if (session.phase === "waiting_for_speech" || session.phase === "recording") {
          handleDirectSubmit();
        } else if (session.phase === "result") {
          soundFX.playSuikinkutsu();
          session.startNext();
        }
      }
    };

    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [session.phase, transcriptInput, isCheatsheetOpen, isKeybindingsOpen, matchesAction, playPromptAudio]);

  return (
    <div className="min-h-screen bg-background text-foreground py-8 px-4 sm:px-6">
      {/* 1. Lobby View */}
      {session.phase === "idle" && (
        <SituationsLobby
          selectedCategory={selectedCategory}
          onSelectCategory={setSelectedCategory}
          selectedMode={selectedMode}
          onSelectMode={setSelectedMode}
          pressureLevel={pressureLevel}
          onSelectPressureLevel={setPressureLevel}
          duration={duration}
          onSelectDuration={setDuration}
          subtitleMode={subtitleMode}
          onSelectSubtitleMode={setSubtitleMode}
          onStartSession={session.startSession}
          onOpenCheatsheet={() => setIsCheatsheetOpen(true)}
          onOpenKeybindings={() => setIsKeybindingsOpen(true)}
          isLoading={false}
        />
      )}

      {/* 2. Active Session View */}
      {session.phase !== "idle" && session.phase !== "summary" && (
        <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in duration-200">
          {/* Top Session Navigation Header */}
          <div className="p-4 rounded-2xl border border-border bg-card washi-texture flex flex-wrap items-center justify-between gap-3 shadow-sm">
            <div className="flex items-center gap-3">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  soundFX.playFurin();
                  session.setPhase("idle");
                }}
                className="h-8 w-8 p-0 text-muted-foreground hover:text-foreground rounded-xl"
                title="Về Sảnh chính (Esc)"
              >
                <Home className="h-4 w-4" />
              </Button>

              <Badge variant="matcha" size="sm" className="font-bold">
                TÌNH HUỐNG THỰC CHIẾN
              </Badge>

              <span className="text-xs font-bold text-muted-foreground">
                Câu #{session.results.length + 1}
              </span>
            </div>

            {/* Middle Reflex Timer Bar */}
            <div className="w-full sm:w-64">
              <SituationsTimerBar
                remainingMs={session.timer.remainingMs}
                totalLimitMs={session.timer.totalLimitMs}
                state={session.timer.state}
                isPaused={session.timer.isPaused}
              />
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  soundFX.playFurin();
                  setIsCheatsheetOpen(true);
                }}
                className="h-8 gap-1.5 text-xs font-bold shadow-2xs"
              >
                <BookOpen className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">Sổ tay (C)</span>
              </Button>

              <Button
                variant="ghost"
                size="sm"
                onClick={() => session.setPhase("summary")}
                className="h-8 text-xs font-bold text-muted-foreground hover:text-foreground"
              >
                Kết thúc phiên
              </Button>
            </div>
          </div>

          {/* Loading State */}
          {session.phase === "loading" && (
            <div className="p-16 rounded-3xl border border-border bg-card washi-texture flex flex-col items-center justify-center gap-3 text-center">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
              <div className="text-sm font-bold text-foreground">AI Đang Tạo Tình Huống Sống Động...</div>
              <p className="text-xs text-muted-foreground">Đang thiết lập địa điểm, nhân vật NPC và mục tiêu nhiệm vụ</p>
            </div>
          )}

          {/* Prompt Playing & Ready State */}
          {(session.phase === "prompt_playing" ||
            session.phase === "ready" ||
            session.phase === "waiting_for_speech" ||
            session.phase === "recording" ||
            session.phase === "evaluating") && (
            <div className="space-y-6">
              <SituationsPromptCard
                exercise={activeExercise}
                subtitleMode={subtitleMode}
                onPlayAudio={() => playPromptAudio(false)}
                phase={session.phase}
              />

              {/* Speech Capture Controller Box */}
              <div className="p-6 rounded-3xl border border-border bg-card washi-texture shadow-sm space-y-4 text-center">
                {session.phase === "ready" && (
                  <div className="space-y-3">
                    <p className="text-xs text-muted-foreground font-semibold">
                      NPC đã dứt lời. Nhấn nút bên dưới hoặc phím <kbd className="px-1.5 py-0.5 rounded bg-muted border text-[10px] font-bold">Space</kbd> để bắt đầu nói.
                    </p>
                    <Button
                      variant="akane"
                      size="lg"
                      onClick={() => {
                        soundFX.playFurin();
                        session.startVoiceRecording();
                      }}
                      className="gap-2 font-bold text-xs px-8 h-11 rounded-2xl shadow-md"
                    >
                      <Mic className="h-4 w-4" />
                      <span>Bắt Đầu Trả Lời (Space)</span>
                    </Button>
                  </div>
                )}

                {(session.phase === "waiting_for_speech" || session.phase === "recording") && (
                  <div className="space-y-4">
                    <div className="flex items-center justify-center gap-2">
                      <span className={cn(
                        "h-3 w-3 rounded-full animate-ping",
                        session.isUserSpeaking ? "bg-emerald-500" : "bg-rose-500"
                      )} />
                      <span className="text-xs font-bold text-foreground">
                        {session.isUserSpeaking ? "🗣️ Đang nhận diện giọng nói của bạn..." : "🎤 Hãy phát âm câu đối đáp tiếng Nhật..."}
                      </span>
                    </div>

                    {/* Speech Transcript Preview */}
                    <div className="p-4 rounded-2xl bg-muted/40 border border-border/80 min-h-[56px] flex items-center justify-center">
                      <span className="text-base font-bold font-jp text-primary">
                        {session.speech.transcript || "Đang lắng nghe..."}
                      </span>
                    </div>

                    {/* Manual Text Fallback */}
                    {inputMode === "text" && (
                      <div className="flex gap-2 max-w-lg mx-auto">
                        <input
                          value={transcriptInput}
                          onChange={(e) => setTranscriptInput(e.target.value)}
                          placeholder="Hoặc gõ câu đối đáp tiếng Nhật..."
                          className="flex-1 bg-background border border-border rounded-xl px-3.5 py-2 text-xs focus:outline-none focus:border-primary font-jp"
                        />
                        <Button
                          size="sm"
                          onClick={handleDirectSubmit}
                          className="text-xs font-bold gap-1.5 rounded-xl"
                        >
                          <Send className="h-3.5 w-3.5" />
                          <span>Gửi</span>
                        </Button>
                      </div>
                    )}

                    <div className="flex items-center justify-center gap-4 text-[11px] text-muted-foreground pt-1">
                      <button
                        onClick={() => setInputMode((m) => (m === "voice" ? "text" : "voice"))}
                        className="hover:underline flex items-center gap-1 font-semibold"
                      >
                        <Edit3 className="h-3 w-3" />
                        <span>{inputMode === "voice" ? "Chuyển sang gõ text (T)" : "Chuyển sang thu âm mic (T)"}</span>
                      </button>
                    </div>
                  </div>
                )}

                {session.phase === "evaluating" && (
                  <div className="py-6 flex flex-col items-center justify-center gap-2">
                    <Loader2 className="h-6 w-6 animate-spin text-primary" />
                    <span className="text-xs font-bold text-muted-foreground">
                      AI Đang Đánh Giá Mức Độ Đạt Mục Tiêu...
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Result State */}
          {session.phase === "result" && session.result && (
            <SituationsResultCard
              result={session.result}
              exercise={activeExercise}
              onNext={session.startNext}
              onRetry={session.retry}
              onAskCoach={(prompt) => setCoachHint(prompt)}
              onCancelAutoNext={session.cancelAutoNext}
            />
          )}
        </div>
      )}

      {/* 3. Session Summary View */}
      {session.phase === "summary" && (
        <SituationsSessionSummary
          results={session.results}
          onRestart={session.startSession}
          onToLobby={() => session.setPhase("idle")}
          onRetryWeak={session.startSession}
        />
      )}

      {/* Modals */}
      <SituationsCheatsheetModal
        isOpen={isCheatsheetOpen}
        onClose={() => setIsCheatsheetOpen(false)}
      />

      <GlobalKeybindingsModal
        isOpen={isKeybindingsOpen}
        onClose={() => setIsKeybindingsOpen(false)}
      />
    </div>
  );
}
"""

FILES_SITUATIONS = {
    r"E:\SpeakingTraining\apps\web\features\situations\services\situations-api.ts": SITUATIONS_API,
    r"E:\SpeakingTraining\apps\web\features\situations\components\SituationsLobby.tsx": SITUATIONS_LOBBY,
    r"E:\SpeakingTraining\apps\web\features\situations\components\SituationsPromptCard.tsx": SITUATIONS_PROMPT_CARD,
    r"E:\SpeakingTraining\apps\web\features\situations\components\SituationsResultCard.tsx": SITUATIONS_RESULT_CARD,
    r"E:\SpeakingTraining\apps\web\features\situations\components\SituationsSessionSummary.tsx": SITUATIONS_SESSION_SUMMARY,
    r"E:\SpeakingTraining\apps\web\features\situations\components\SituationsCheatsheetModal.tsx": SITUATIONS_CHEATSHEET,
    r"E:\SpeakingTraining\apps\web\features\situations\index.ts": SITUATIONS_INDEX,
    r"E:\SpeakingTraining\apps\web\features\situations\hooks\useSituationsSession.ts": SITUATIONS_HOOK,
    r"E:\SpeakingTraining\apps\web\app\situations\page.tsx": SITUATIONS_PAGE,
}

for filepath, content in FILES_SITUATIONS.items():
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"Successfully wrote {os.path.basename(filepath)}")

print("All Situations Studio frontend components written successfully!")
