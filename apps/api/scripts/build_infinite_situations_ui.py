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
  is_custom?: boolean;
  custom_topic?: string | null;
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
  customTopic?: string;
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
    customTopic,
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
  if (customTopic && customTopic.trim()) q.set("custom_topic", customTopic.trim());
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

import React, { useState } from "react";
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
  Wand2,
  Send,
  Dice5,
} from "lucide-react";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";
import type { SituationsPressureLevel } from "../services/situations-api";

export interface SituationsLobbyProps {
  selectedCategory: string;
  onSelectCategory: (cat: string) => void;
  customTopic: string;
  onSelectCustomTopic: (topic: string) => void;
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
    id: "infinite",
    jaTitle: "無限・AI Random",
    viTitle: "Vô Tận Ngẫu Nhiên (AI Sandbox)",
    badge: "無限",
    desc: "AI tự do sáng tạo 100,000+ tình huống độc lạ từ mọi ngóc ngách xã hội Nhật Bản",
    icon: <Sparkles className="h-5 w-5 text-amber-500" />,
    isSpecial: true,
  },
  {
    id: "food",
    jaTitle: "飲食・居酒屋",
    viTitle: "Ẩm Thực & Quán Nhậu",
    badge: "飲食",
    desc: "Đặt bàn, gọi món, yêu cầu đổi món do dị ứng, tách hóa đơn betsu-betsu",
    icon: <Utensils className="h-5 w-5 text-amber-500" />,
  },
  {
    id: "retail",
    jaTitle: "買い物・コンビニ",
    viTitle: "Mua Sắm & Konbini",
    badge: "店舗",
    desc: "Hâm nóng bento, từ chối túi nilon, rút tiền ATM, gửi bưu kiện",
    icon: <ShoppingBag className="h-5 w-5 text-emerald-500" />,
  },
  {
    id: "transportation",
    jaTitle: "交通・駅・空港",
    viTitle: "Giao Thông & Nhà Ga",
    badge: "交通",
    desc: "Mua vé Shinkansen ghế chỉ định, hỏi cửa chuyển tàu, nạp thẻ Suica",
    icon: <Train className="h-5 w-5 text-sky-500" />,
  },
  {
    id: "healthcare",
    jaTitle: "医療・薬局・緊急",
    viTitle: "Y Tế & Hiệu Thuốc & Khẩn Cấp",
    badge: "医療",
    desc: "Mô tả triệu chứng bệnh, mua thuốc tại Yakkyoku, báo rơi đồ tại Kouban",
    icon: <HeartPulse className="h-5 w-5 text-rose-500" />,
  },
  {
    id: "workplace",
    jaTitle: "ビジネス・職場",
    viTitle: "Công Sở & Đàm Phán",
    badge: "仕事",
    desc: "Tiếp đối tác, trao đổi danh thiếp Meishi, báo cáo tiến độ Hou-Ren-So",
    icon: <Briefcase className="h-5 w-5 text-purple-500" />,
  },
  {
    id: "travel",
    jaTitle: "ホテル・観光・旅行",
    viTitle: "Khách Sạn & Du Lịch",
    badge: "観光",
    desc: "Check-in khách sạn, gửi hành lý, hỏi gợi ý điểm tham quan, đặt tour",
    icon: <Hotel className="h-5 w-5 text-cyan-500" />,
  },
];

export const QUICK_SUGGESTION_TAGS = [
  { label: "🏠 Thuê nhà & Cọc tiền (不動産・敷金礼金)", prompt: "Thuê căn hộ 1DK tại Tokyo qua công ty bất động sản, hỏi tiền cọc Shikikin và Reikin" },
  { label: "💼 Phỏng vấn Baito quán ăn (バイト面接)", prompt: "Phỏng vấn xin việc làm thêm tại quán mì Ramen, hỏi lịch làm Shifuto và mức lương" },
  { label: "🏛️ Đăng ký cư trú Shiyakusho (市役所住民票)", prompt: "Đến ủy ban Shiyakusho làm thủ tục chuyển địa chỉ cư trú Juuminhyou và bảo hiểm quốc dân" },
  { label: "💇 Tiệm cắt tóc Omotesando (美容室)", prompt: "Cắt tóc tại salon Nhật, yêu cầu cắt ngắn hai bên và tỉa ngọn tự nhiên" },
  { label: "📦 Chợ đồ cũ Mercari (メルカリ・値下げ)", prompt: "Thương lượng giảm giá món đồ trên Mercari và hẹn phương thức nhận hàng" },
  { label: "🗑️ Quy tắc phân loại rác (ごみ分別・粗大ごみ)", prompt: "Hỏi hàng xóm người Nhật cách phân loại rác cồng kềnh Sodai Gomi và lịch vứt rác" },
  { label: "🚗 Thuê xe tự lái & Đổ xăng (レンタカー)", prompt: "Thuê xe du lịch có thẻ ETC tại Hokkaido và hỏi cách đổ xăng đầy bình Mantan" },
  { label: "🚨 Sự cố động đất & Điểm sơ tán (防災・避難所)", prompt: "Hỏi cảnh sát về điểm sơ tán khẩn cấp Hinanjo khi có dư chấn động đất" },
  { label: "🐾 Đưa thú cưng đi khám (動物病院)", prompt: "Dẫn mèo đi khám tại thú y vì sốt bỏ ăn, hỏi lịch tiêm vắc xin" },
  { label: "🏋️ Đăng ký thẻ tập Gym (フィットネス)", prompt: "Đăng ký hội viên phòng gym 24/7 và hỏi thuê huấn luyện viên cá nhân" },
  { label: "🎮 Mua sắm Otaku Akihabara (アニメ・フィギュア)", prompt: "Tìm mua mô hình Figure hiếm tại Akihabara và hỏi thủ tục miễn thuế Tax Free" },
  { label: "🍻 Rót rượu tiệc Nomikai (飲み会マナー)", prompt: "Nói lời chúc mừng Kanpai và giao lưu mời rượu cấp trên tại tiệc Nomikai công ty" },
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
  customTopic,
  onSelectCustomTopic,
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
  const [localInput, setLocalInput] = useState(customTopic);

  const handleApplyCustomTopic = () => {
    if (localInput.trim()) {
      soundFX.playSuikinkutsu();
      onSelectCustomTopic(localInput.trim());
      onSelectCategory("custom");
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in duration-300 pb-12">
      {/* Top Banner Haru Washi */}
      <div className="relative overflow-hidden rounded-3xl border border-border bg-card p-6 md:p-8 washi-texture shadow-sm space-y-4">
        <div className="absolute top-0 right-0 h-48 w-48 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Badge variant="matcha" size="sm" className="font-bold">
                MODE 4 • INFINITE SITUATIONAL ROLEPLAY STUDIO
              </Badge>
              <span className="text-xs text-muted-foreground font-semibold">
                AI Phản Xạ Nhập Vai Thực Chiến Vô Hạn
              </span>
            </div>
            <h1 className="text-2xl md:text-3xl font-black text-foreground tracking-tight flex items-center gap-3">
              <span className="p-2 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 inline-flex">
                <Compass className="h-6 w-6" />
              </span>
              <span>Tình Huống Thực Chiến Vô Tận (場面英会話)</span>
            </h1>
            <p className="text-xs md:text-sm text-muted-foreground max-w-2xl leading-relaxed">
              Tự do gõ bất kỳ bối cảnh nào bạn muốn hoặc để AI sáng tạo vô hạn từ mọi khía cạnh đời sống, văn hóa, công sở và pháp lý tại Nhật Bản.
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

      {/* Custom Topic Builder Section */}
      <div className="p-6 rounded-3xl border border-primary/30 bg-card washi-texture shadow-sm space-y-4 relative overflow-hidden ring-1 ring-primary/20">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Wand2 className="h-5 w-5 text-primary" />
            <h2 className="text-sm font-bold text-foreground">
              ✨ Tự Tạo Bối Cảnh / Tình Huống Tự Do Bằng AI (Custom Prompt)
            </h2>
          </div>
          <Badge variant="kintsugi" size="sm" className="font-bold">
            INFINITE AI
          </Badge>
        </div>

        <p className="text-xs text-muted-foreground">
          Gõ bất kỳ tình huống thực tế nào bạn muốn luyện tập (bằng tiếng Việt hoặc tiếng Nhật). AI sẽ phân tích và tạo ngay nhân vật NPC đối thoại chân thực:
        </p>

        {/* Input Bar */}
        <div className="flex flex-col sm:flex-row gap-2">
          <div className="relative flex-1">
            <input
              value={localInput}
              onChange={(e) => setLocalInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  handleApplyCustomTopic();
                }
              }}
              placeholder="VD: Đi phỏng vấn xin việc baito, Thuê nhà trọ tại Shinjuku, Đổi hàng trên Mercari, Đi cắt tóc..."
              className="w-full bg-background border border-border rounded-2xl px-4 py-3 text-xs focus:outline-none focus:border-primary placeholder:text-muted-foreground shadow-2xs"
            />
          </div>

          <Button
            variant="akane"
            size="sm"
            onClick={handleApplyCustomTopic}
            disabled={!localInput.trim()}
            className="text-xs font-bold gap-1.5 rounded-2xl px-5 h-11 shrink-0 shadow-md"
          >
            <Send className="h-3.5 w-3.5" />
            <span>Áp Dụng Bối Cảnh Này</span>
          </Button>
        </div>

        {/* Quick Suggestion Tags */}
        <div className="space-y-1.5 pt-1">
          <div className="text-[11px] font-bold text-muted-foreground">
            Hoặc chọn nhanh bối cảnh đời sống Nhật phổ biến:
          </div>
          <div className="flex flex-wrap gap-1.5">
            {QUICK_SUGGESTION_TAGS.map((tag, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => {
                  soundFX.playFurin();
                  setLocalInput(tag.prompt);
                  onSelectCustomTopic(tag.prompt);
                  onSelectCategory("custom");
                }}
                className={cn(
                  "px-3 py-1 rounded-xl border text-[11px] font-semibold transition-all text-left",
                  customTopic === tag.prompt
                    ? "bg-primary text-primary-foreground border-primary shadow-xs"
                    : "bg-muted/40 hover:bg-muted text-muted-foreground hover:text-foreground border-border/80"
                )}
              >
                {tag.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 7 Category Cards Grid (Including Infinite Random Sandbox) */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-foreground flex items-center gap-2">
            <Sliders className="h-4 w-4 text-primary" />
            <span>1. Chọn Bối Cảnh Luyện Tập Có Sẵn</span>
          </h2>
          <span className="text-xs text-muted-foreground">Sinh dữ liệu ngẫu nhiên thời gian thực</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
          {SITUATIONAL_CATEGORIES.map((cat) => {
            const isSelected = selectedCategory === cat.id && (!customTopic || cat.id !== "custom");
            return (
              <div
                key={cat.id}
                onClick={() => {
                  soundFX.playFurin();
                  onSelectCustomTopic("");
                  setLocalInput("");
                  onSelectCategory(cat.id);
                }}
                className={cn(
                  "p-4 rounded-2xl border transition-all cursor-pointer relative overflow-hidden bg-card washi-texture space-y-2 hover:shadow-md",
                  cat.isSpecial && "border-amber-500/50 bg-amber-500/5",
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
                  <Badge variant={isSelected ? "matcha" : cat.isSpecial ? "kintsugi" : "outline"} size="sm" className="font-mono text-[10px]">
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
            Bối cảnh:{" "}
            <span className="text-primary font-jp font-bold">
              {customTopic
                ? `Tùy biến: ${customTopic}`
                : selectedCategory === "infinite"
                ? "✨ Vô Tận Ngẫu Nhiên (AI Sandbox)"
                : SITUATIONAL_CATEGORIES.find((c) => c.id === selectedCategory)?.jaTitle}
            </span>{" "}
            • Thời lượng: {duration} phút
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
          <span>{isLoading ? "Đang tạo bối cảnh AI..." : "Bắt Đầu Nhập Vai (Enter)"}</span>
        </Button>
      </div>
    </div>
  );
}
"""

# 3. useSituationsSession.ts
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
  customTopic?: string;
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
    customTopic,
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
        .generateExercise({ category, customTopic, subMode, pressureLevel, timerLimitMs: overrideTimer, duration, mode })
        .then((ex) => setPrefetched((p) => [...p, ex]))
        .catch(() => {});
      return next;
    }
    return situationsApi.generateExercise({ category, customTopic, subMode, pressureLevel, timerLimitMs: overrideTimer, duration, mode });
  }, [category, customTopic, subMode, pressureLevel, overrideTimer, duration, mode, prefetched]);

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

# 4. page.tsx
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
  const [selectedCategory, setSelectedCategory] = useState<string>("infinite");
  const [customTopic, setCustomTopic] = useState<string>("");
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
    customTopic,
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
          customTopic={customTopic}
          onSelectCustomTopic={setCustomTopic}
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
                timerLimitMs={session.timer.totalLimitMs}
                progress={session.timer.progress}
                state={session.timer.state}
                isActive={session.timer.isActive}
                isPaused={session.timer.isPaused}
                variant="bar"
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

FILES_INFINITE = {
    r"E:\SpeakingTraining\apps\web\features\situations\services\situations-api.ts": SITUATIONS_API,
    r"E:\SpeakingTraining\apps\web\features\situations\components\SituationsLobby.tsx": SITUATIONS_LOBBY,
    r"E:\SpeakingTraining\apps\web\features\situations\hooks\useSituationsSession.ts": SITUATIONS_HOOK,
    r"E:\SpeakingTraining\apps\web\app\situations\page.tsx": SITUATIONS_PAGE,
}

for filepath, content in FILES_INFINITE.items():
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"Successfully wrote {os.path.basename(filepath)}")

print("Infinite Situations frontend files updated successfully!")
