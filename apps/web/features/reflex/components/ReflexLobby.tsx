"use client";

import React from "react";
import {
  Zap,
  Clock,
  Play,
  Shuffle,
  Keyboard,
  Check,
  ArrowRight,
  Sliders,
  MessageSquare,
  Repeat,
  Compass,
  BookText,
  Crown,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CoachInsightCard } from "@/features/coach/components/CoachInsightCard";
import { useCoachProactive } from "@/features/coach/hooks/useCoachProactive";
import { formatKeyDisplay } from "@/hooks/use-system-keybindings";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";
import { useReflexFilters } from "../hooks/useReflexFilters";

export const DEDICATED_MODES = [
  {
    id: "reflex_conjugation",
    title: "Conjugation Blitz",
    titleJa: "活用",
    icon: Zap,
    badgeVariant: "sakura" as const,
    iconColor: "text-rose-500 bg-rose-500/10 border-rose-500/20",
    accentColor: "text-rose-600 dark:text-rose-400",
    desc: "Chia thể động từ & tính từ phản xạ siêu tốc",
    source: "食べる",
    target: "食べさせる (Sai khiến)",
  },
  {
    id: "reflex_qna",
    title: "Speed Q&A",
    titleJa: "速答",
    icon: MessageSquare,
    badgeVariant: "matcha" as const,
    iconColor: "text-emerald-500 bg-emerald-500/10 border-emerald-500/20",
    accentColor: "text-emerald-600 dark:text-emerald-400",
    desc: "Hỏi - đáp tức thì câu hỏi thường ngày & công việc",
    source: "週末は何を？",
    target: "映画を見ました",
  },
  {
    id: "reflex_transformation",
    title: "Transformation",
    titleJa: "文型変換",
    icon: Repeat,
    badgeVariant: "fuji" as const,
    iconColor: "text-indigo-500 bg-indigo-500/10 border-indigo-500/20",
    accentColor: "text-indigo-600 dark:text-indigo-400",
    desc: "Đổi ngữ pháp: Lịch sự ↔ Thân mật, Phủ định, Quá khứ",
    source: "行きます",
    target: "行く (Thân mật)",
  },
  {
    id: "reflex_context",
    title: "Contextual Reaction",
    titleJa: "状況対応",
    icon: Compass,
    badgeVariant: "kintsugi" as const,
    iconColor: "text-amber-500 bg-amber-500/10 border-amber-500/20",
    accentColor: "text-amber-600 dark:text-amber-400",
    desc: "Phản xạ giao tiếp đúng vai vế và văn hóa ứng xử",
    source: "Đến muộn do trễ tàu",
    target: "大変申し訳ありません",
  },
  {
    id: "reflex_vocabulary",
    title: "Vocabulary Blitz",
    titleJa: "語彙",
    icon: BookText,
    badgeVariant: "fuji" as const,
    iconColor: "text-violet-500 bg-violet-500/10 border-violet-500/20",
    accentColor: "text-violet-600 dark:text-violet-400",
    desc: "Nhớ nghĩa từ vựng JLPT N5-N1 theo phản xạ siêu tốc",
    source: "諦める",
    target: "bỏ cuộc 🇯🇵→🇻🇳",
  },
  {
    id: "reflex_keigo_vocab",
    title: "Keigo Word Blitz",
    titleJa: "敬語単語",
    icon: Crown,
    badgeVariant: "kintsugi" as const,
    iconColor: "text-amber-500 bg-amber-500/10 border-amber-500/20",
    accentColor: "text-amber-600 dark:text-amber-400",
    desc: "Phản xạ nhanh Tôn kính ngữ, Khiêm nhường ngữ & Từ thương mại",
    source: "食べる",
    target: "召し上がる 👑",
  },
];

export const PRESSURE_LEVELS = [
  { id: "infinite", label: "Infinite", labelJa: "無制限", icon: "♾️", ms: 0, desc: "∞ • Không giới hạn thời gian phản xạ" },
  { id: "relaxed", label: "Relaxed", labelJa: "ゆっくり", icon: "🐢", ms: 6000, desc: "6.0s • Thong thả, tập trung độ chuẩn xác" },
  { id: "normal", label: "Normal", labelJa: "普通", icon: "🚶", ms: 4000, desc: "4.0s • Cân bằng, nhịp nói tự nhiên" },
  { id: "fast", label: "Fast", labelJa: "速め", icon: "🏃", ms: 3000, desc: "3.0s • Tăng tốc, phản xạ dứt khoát" },
  { id: "reflex", label: "Reflex", labelJa: "瞬発", icon: "⚡", ms: 2500, desc: "2.5s • Thực chiến, nhịp người bản xứ" },
  { id: "extreme", label: "Extreme", labelJa: "超速", icon: "🔥", ms: 1800, desc: "1.8s • Cực hạn, phản xạ chớp mắt" },
] as const;

export const DURATION_OPTIONS = [0, 3, 5, 10, 20] as const;

export interface ReflexLobbyProps {
  subMode: string;
  setSubMode: (mode: string) => void;
  pressure: "infinite" | "relaxed" | "normal" | "fast" | "reflex" | "extreme";
  setPressure: (p: "infinite" | "relaxed" | "normal" | "fast" | "reflex" | "extreme") => void;
  duration: 0 | 3 | 5 | 10 | 20;
  setDuration: (d: 0 | 3 | 5 | 10 | 20) => void;
  subtitleMode: "hidden" | "japanese" | "japanese_reading" | "vietnamese";
  setSubtitleMode: (m: "hidden" | "japanese" | "japanese_reading" | "vietnamese") => void;
  startTrigger: "manual" | "auto";
  setStartTrigger: (t: "manual" | "auto") => void;
  autoNext: boolean;
  setAutoNext: React.Dispatch<React.SetStateAction<boolean>>;
  isReflexAdvancedOpen: boolean;
  setIsReflexAdvancedOpen: React.Dispatch<React.SetStateAction<boolean>>;
  filters: ReturnType<typeof useReflexFilters>;
  keybindings: any;
  timerMs: number;
  onStartSession: () => void;
  onOpenHelp: () => void;
  onCoachSelect: (prompt: string) => void;
}

export function ReflexLobby({
  subMode,
  setSubMode,
  pressure,
  setPressure,
  duration,
  setDuration,
  subtitleMode,
  setSubtitleMode,
  startTrigger,
  setStartTrigger,
  autoNext,
  setAutoNext,
  isReflexAdvancedOpen,
  setIsReflexAdvancedOpen,
  filters,
  keybindings,
  timerMs,
  onStartSession,
  onOpenHelp,
  onCoachSelect,
}: ReflexLobbyProps) {
  const isMixedSelected = subMode === "mixed";
  const { insights, dismiss } = useCoachProactive();

  return (
    <div className="space-y-4 animate-in fade-in duration-300 max-w-5xl mx-auto pb-8">
      {/* Proactive Coach Insight Banner */}
      {insights.slice(0, 1).map((ins, idx) => (
        <CoachInsightCard
          key={idx}
          insight={ins}
          onDismiss={() => dismiss(ins.insight_type)}
          onAction={() => onCoachSelect(`Luyện ${ins.recommended_action || "reflex"} cho tui`)}
        />
      ))}

      {/* Hero Header */}
      <div className="relative overflow-hidden rounded-2xl border border-border bg-card p-4 sm:p-5 washi-texture shadow-2xs">
        <div className="absolute -top-12 -right-12 h-40 w-40 rounded-full bg-enso-gradient opacity-30 pointer-events-none" />
        <div className="relative flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <span className="h-9 w-9 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary shrink-0 shadow-2xs">
              <Zap className="h-5 w-5" />
            </span>
            <div className="space-y-0.5">
              <div className="flex items-center gap-2">
                <h1 className="text-xl sm:text-2xl font-black font-jp tracking-tight text-foreground">
                  瞬発力スピーキング
                </h1>
                <Badge variant="sakura" size="sm" className="font-bold text-[10px]">
                  Mode 3
                </Badge>
              </div>
              <p className="text-[11px] text-muted-foreground">
                Speed Reflex Speaking — Phản xạ câu nói tiếng Nhật dưới áp lực thời gian
              </p>
            </div>
          </div>

          <Button
            variant="outline"
            size="sm"
            className="gap-1 rounded-xl border-border h-8 px-2.5 text-xs font-bold shadow-2xs hover:border-primary/40 shrink-0"
            onClick={onOpenHelp}
          >
            <Keyboard className="h-3.5 w-3.5 text-primary" />
            <span>Phím tắt ({formatKeyDisplay(keybindings.drillToggleHelp)})</span>
          </Button>
        </div>
      </div>

      {/* 2-Column Cockpit Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 items-start">
        {/* Left 2 Cols: Mode Selection */}
        <div className="lg:col-span-2 space-y-2.5">
          <div className="flex items-center justify-between px-1">
            <h2 className="text-xs font-bold text-foreground flex items-center gap-1.5">
              <span>1. Chọn Dạng Bài Phản Xạ:</span>
            </h2>
            <span className="text-[10px] font-medium text-muted-foreground">6 Dạng bài thực chiến</span>
          </div>

          {/* TOP HERO CARD: Mixed Adaptive */}
          <button
            type="button"
            onClick={() => {
              soundFX.playFurin();
              setSubMode("mixed");
            }}
            className={cn(
              "w-full text-left rounded-2xl border p-3.5 transition-all duration-200 relative overflow-hidden group shadow-2xs washi-texture",
              isMixedSelected
                ? "border-primary bg-primary/10 ring-1 ring-primary/30 shadow-xs"
                : "border-border/80 bg-card hover:border-primary/40"
            )}
          >
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-2.5 min-w-0">
                <div className="h-8 w-8 rounded-xl bg-primary/15 border border-primary/25 flex items-center justify-center text-primary shrink-0 shadow-2xs">
                  <Shuffle className="h-4 w-4" />
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs font-bold text-foreground font-jp">
                      Mixed Adaptive (Tổng Hợp)
                    </span>
                    <Badge variant="kintsugi" size="sm" className="text-[9px] px-1.5 py-0">混合</Badge>
                  </div>
                  <p className="text-[10px] text-muted-foreground truncate">
                    Tự động phân tích điểm yếu & luân phiên 6 dạng bài để tối đa phản xạ
                  </p>
                </div>
              </div>

              <div
                className={cn(
                  "h-5 w-5 rounded-full border-2 flex items-center justify-center shrink-0 transition-all",
                  isMixedSelected ? "border-primary bg-primary text-primary-foreground shadow-xs" : "border-muted-foreground/30 bg-background"
                )}
              >
                {isMixedSelected && <Check className="h-3 w-3 stroke-[3]" />}
              </div>
            </div>
          </button>

          {/* 6 DEDICATED FOCUS MODES (2-Col Grid) */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {DEDICATED_MODES.map((m) => {
              const isSelected = subMode === m.id;
              const Icon = m.icon;

              return (
                <div
                  key={m.id}
                  onClick={() => {
                    soundFX.playFurin();
                    setSubMode(m.id);
                  }}
                  className={cn(
                    "text-left rounded-2xl border p-3 transition-all duration-150 relative overflow-hidden group shadow-2xs washi-texture flex flex-col justify-between space-y-2 cursor-pointer",
                    isSelected
                      ? "border-primary bg-primary/10 ring-1 ring-primary/30 shadow-xs"
                      : "border-border/80 bg-card hover:border-primary/40"
                  )}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2 min-w-0">
                      <div className={cn("h-7 w-7 rounded-lg border flex items-center justify-center shrink-0 text-xs", m.iconColor)}>
                        <Icon className="h-3.5 w-3.5" />
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-1">
                          <span className="text-xs font-bold text-foreground font-jp truncate">{m.title}</span>
                          <Badge variant={m.badgeVariant} size="sm" className="text-[9px] px-1 py-0 shrink-0">{m.titleJa}</Badge>
                        </div>
                        <p className="text-[10px] text-muted-foreground truncate">{m.desc}</p>
                      </div>
                    </div>

                    <div
                      className={cn(
                        "h-4 w-4 rounded-full border flex items-center justify-center shrink-0 transition-all mt-0.5",
                        isSelected ? "border-primary bg-primary text-primary-foreground" : "border-muted-foreground/30 bg-background"
                      )}
                    >
                      {isSelected && <Check className="h-2.5 w-2.5 stroke-[3]" />}
                    </div>
                  </div>

                  <div className="p-1.5 px-2.5 rounded-xl bg-muted/40 border border-border/60 text-[10px] flex items-center justify-between gap-1 font-medium">
                    <span className="text-foreground/80 font-mono truncate">{m.source}</span>
                    <ArrowRight className="h-3 w-3 text-muted-foreground shrink-0" />
                    <span className={cn("font-bold truncate", m.accentColor)}>{m.target}</span>
                  </div>

                  {/* Filter Action Pill */}
                  {m.id === "reflex_conjugation" && (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        soundFX.playFurin();
                        filters.setShowFormFilterModal(true);
                      }}
                      className="w-full py-1 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 text-[10px] font-bold text-rose-700 dark:text-rose-300 flex items-center justify-center gap-1 transition-colors"
                    >
                      <Sliders className="h-3 w-3 text-rose-500" />
                      <span>{filters.selectedForms.length === 0 ? "Tất cả 50 thể (Toàn diện)" : `${filters.selectedForms.length} thể đã lọc`}</span>
                    </button>
                  )}

                  {m.id === "reflex_qna" && (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        soundFX.playFurin();
                        filters.setShowQnaTopicFilterModal(true);
                      }}
                      className="w-full py-1 rounded-xl bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/20 text-[10px] font-bold text-emerald-700 dark:text-emerald-300 flex items-center justify-center gap-1 transition-colors"
                    >
                      <MessageSquare className="h-3 w-3 text-emerald-500" />
                      <span>{filters.customKeywords.trim() ? `"${filters.customKeywords.trim()}"` : filters.selectedQnaTopics.length === 0 ? "Ngẫu nhiên mọi chủ đề" : `${filters.selectedQnaTopics.length} chủ đề đã lọc`}</span>
                    </button>
                  )}

                  {m.id === "reflex_transformation" && (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        soundFX.playFurin();
                        filters.setShowTransformFilterModal(true);
                      }}
                      className="w-full py-1 rounded-xl bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/20 text-[10px] font-bold text-indigo-700 dark:text-indigo-300 flex items-center justify-center gap-1 transition-colors"
                    >
                      <Repeat className="h-3 w-3 text-indigo-500" />
                      <span>{filters.selectedTransformCategories.length === 0 ? "Ngẫu nhiên 75+ dạng ngữ pháp" : `${filters.selectedTransformCategories.length} nhóm đã lọc`}</span>
                    </button>
                  )}

                  {m.id === "reflex_context" && (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        soundFX.playFurin();
                        filters.setShowContextFilterModal(true);
                      }}
                      className="w-full py-1 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/20 text-[10px] font-bold text-amber-700 dark:text-amber-300 flex items-center justify-center gap-1 transition-colors"
                    >
                      <Compass className="h-3 w-3 text-amber-500" />
                      <span>{filters.selectedContextCategories.length === 0 ? "Ngẫu nhiên 60+ tình huống" : `${filters.selectedContextCategories.length} nhóm đã lọc`}</span>
                    </button>
                  )}

                  {m.id === "reflex_vocabulary" && (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        soundFX.playFurin();
                        filters.setShowVocabFilterModal(true);
                      }}
                      className="w-full py-1 rounded-xl bg-violet-500/10 hover:bg-violet-500/20 border border-violet-500/20 text-[10px] font-bold text-violet-700 dark:text-violet-300 flex items-center justify-center gap-1 transition-colors"
                    >
                      <BookText className="h-3 w-3 text-violet-500" />
                      <span>{filters.selectedVocabCategories.length === 0 ? "Ngẫu nhiên 500+ từ vựng" : `${filters.selectedVocabCategories.length} nhóm đã lọc`}</span>
                    </button>
                  )}

                  {m.id === "reflex_keigo_vocab" && (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        soundFX.playFurin();
                        filters.setShowKeigoFilterModal(true);
                      }}
                      className="w-full py-1 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/20 text-[10px] font-bold text-amber-700 dark:text-amber-300 flex items-center justify-center gap-1 transition-colors"
                    >
                      <Crown className="h-3 w-3 text-amber-500" />
                      <span>{filters.selectedKeigoCategories.length === 0 ? "Ngẫu nhiên 80+ cặp kính ngữ" : `${filters.selectedKeigoCategories.length} nhóm đã lọc`}</span>
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Right 1 Col: Session Configuration Cockpit */}
        <div className="space-y-3 p-3.5 rounded-2xl border border-border bg-card shadow-2xs washi-texture">
          {/* Pressure Selector */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs font-bold">
              <label className="text-muted-foreground flex items-center gap-1">
                <Clock className="h-3.5 w-3.5 text-primary" />
                <span>Áp Lực Thời Gian:</span>
              </label>
              <span className="text-primary font-mono text-[11px] font-bold">
                {timerMs > 0 ? `${timerMs / 1000}s / câu` : "∞ Vô hạn"}
              </span>
            </div>
            <div className="flex items-center gap-1 p-0.5 rounded-xl bg-muted/50 border border-border">
              {PRESSURE_LEVELS.map((p) => (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => {
                    soundFX.playFurin();
                    setPressure(p.id as any);
                  }}
                  className={cn(
                    "flex-1 py-1 rounded-lg text-[10px] font-bold transition-all text-center",
                    pressure === p.id
                      ? "bg-card text-foreground border border-border shadow-2xs"
                      : "text-muted-foreground hover:text-foreground"
                  )}
                  title={p.desc}
                >
                  {p.id === "infinite" ? "∞" : `${p.ms / 1000}s`}
                </button>
              ))}
            </div>
          </div>

          {/* Duration Selector */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs font-bold">
              <span className="text-muted-foreground">Thời Lượng Phiên:</span>
              <span className="text-primary font-mono text-[11px]">{duration === 0 ? "∞ Vô hạn" : `${duration} phút`}</span>
            </div>
            <div className="flex items-center gap-1 p-0.5 rounded-xl bg-muted/50 border border-border">
              {DURATION_OPTIONS.map((d) => (
                <button
                  key={d}
                  type="button"
                  onClick={() => setDuration(d)}
                  className={cn(
                    "flex-1 py-1 rounded-lg text-[10px] font-bold transition-all text-center",
                    duration === d
                      ? "bg-card text-foreground border border-border shadow-2xs"
                      : "text-muted-foreground hover:text-foreground"
                  )}
                >
                  {d === 0 ? "∞" : `${d}m`}
                </button>
              ))}
            </div>
          </div>

          {/* Progressive Disclosure: Subtitles, Start Trigger & Auto Next */}
          <div className="border border-border/80 rounded-xl bg-muted/20 overflow-hidden">
            <button
              type="button"
              onClick={() => setIsReflexAdvancedOpen((v) => !v)}
              className="w-full px-2.5 py-1.5 flex items-center justify-between text-[11px] font-bold text-muted-foreground hover:text-foreground transition-colors"
            >
              <span>Phụ đề & Chế độ xuất phát</span>
              <span className="text-[10px] text-primary">{isReflexAdvancedOpen ? "▲" : "▼"}</span>
            </button>

            {isReflexAdvancedOpen && (
              <div className="p-2.5 pt-1 space-y-2 border-t border-border/60 animate-in fade-in duration-150">
                {/* Subtitle Mode */}
                <div className="space-y-1">
                  <span className="text-[10px] font-bold text-muted-foreground">Hiển thị đề bài:</span>
                  <div className="grid grid-cols-3 gap-1 text-[10px]">
                    {[
                      { id: "japanese", label: "🇯🇵 Nhật" },
                      { id: "vietnamese", label: "🇻🇳 Dịch" },
                      { id: "hidden", label: "🎧 Ẩn" },
                    ].map((opt) => (
                      <button
                        key={opt.id}
                        type="button"
                        onClick={() => setSubtitleMode(opt.id as any)}
                        className={cn(
                          "py-1 rounded-lg font-bold border transition-all text-center",
                          subtitleMode === opt.id
                            ? "bg-primary text-primary-foreground border-primary"
                            : "bg-card border-border hover:bg-muted text-foreground"
                        )}
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Start Trigger Mode */}
                <div className="space-y-1 pt-1 border-t border-border/40">
                  <span className="text-[10px] font-bold text-muted-foreground">Chế độ xuất phát:</span>
                  <div className="grid grid-cols-2 gap-1 text-[10px]">
                    <button
                      type="button"
                      onClick={() => setStartTrigger("manual")}
                      className={cn(
                        "py-1 rounded-lg font-bold border transition-all text-center",
                        startTrigger === "manual" ? "bg-primary text-primary-foreground border-primary" : "bg-card border-border text-muted-foreground"
                      )}
                    >
                      🎯 Chủ động
                    </button>
                    <button
                      type="button"
                      onClick={() => setStartTrigger("auto")}
                      className={cn(
                        "py-1 rounded-lg font-bold border transition-all text-center",
                        startTrigger === "auto" ? "bg-amber-500 text-white border-amber-500" : "bg-card border-border text-muted-foreground"
                      )}
                    >
                      ⚡ Tự động
                    </button>
                  </div>
                </div>

                {/* Auto-Next */}
                <div className="pt-1 border-t border-border/40 flex items-center justify-between text-[11px]">
                  <span className="font-bold text-muted-foreground">Tự chuyển câu:</span>
                  <button
                    type="button"
                    onClick={() => setAutoNext((v) => !v)}
                    className={cn(
                      "px-2 py-0.5 rounded-full text-[10px] font-bold border transition-all",
                      autoNext ? "bg-emerald-600 text-white border-emerald-600" : "bg-muted border-border text-muted-foreground"
                    )}
                  >
                    {autoNext ? "BẬT" : "TẮT"}
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Big CTA Start Button */}
          <Button
            variant="akane"
            size="lg"
            className="w-full font-bold text-xs rounded-xl h-10 shadow-md hover:shadow-lg transition-all gap-2 cursor-pointer"
            onClick={() => {
              soundFX.playTaiko();
              onStartSession();
            }}
          >
            <Play className="h-3.5 w-3.5 fill-current" />
            <span>Bắt Đầu Phản Xạ ({duration === 0 ? "Vô Hạn" : `${duration}p`})</span>
          </Button>
        </div>
      </div>
    </div>
  );
}
