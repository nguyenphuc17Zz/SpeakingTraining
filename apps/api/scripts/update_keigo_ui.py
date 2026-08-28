import os

LOBBY_CONTENT = """\"use client\";

import React from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Crown,
  Play,
  Settings2,
  Keyboard,
  Shuffle,
  Sparkles,
  BookOpen,
  Users,
  Repeat,
  ShieldAlert,
  Compass,
  CheckCircle2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { PressureLevel } from "../services/keigo-api";

export interface KeigoSubModeConfig {
  id: string;
  label: string;
  subLabel: string;
  ja: string;
  icon: any;
  desc: string;
  exampleSource: string;
  exampleTarget: string;
  badgeVariant: "sakura" | "kintsugi" | "matcha" | "fuji" | "jlpt" | "torii" | "akane";
  iconColor: string;
}

export const KEIGO_SUB_MODES: KeigoSubModeConfig[] = [
  {
    id: "mixed",
    label: "総合特訓",
    subLabel: "Mixed Adaptive",
    ja: "総合",
    icon: Shuffle,
    desc: "AI tự động đảo bài 7 chuyên đề theo điểm yếu của bạn",
    exampleSource: "Tình huống hỗn hợp",
    exampleTarget: "Phản xạ toàn diện",
    badgeVariant: "kintsugi",
    iconColor: "text-amber-500 bg-amber-500/10 border-amber-500/20",
  },
  {
    id: "keigo_sonkeigo",
    label: "尊敬語",
    subLabel: "Sonkeigo ↑",
    ja: "尊敬",
    icon: Crown,
    desc: "Nâng cao hành động và trạng thái của khách hàng, đối tác, cấp trên",
    exampleSource: "食べる (Ăn)",
    exampleTarget: "召し上がる",
    badgeVariant: "sakura",
    iconColor: "text-rose-500 bg-rose-500/10 border-rose-500/20",
  },
  {
    id: "keigo_kenjougo",
    label: "謙譲語",
    subLabel: "Kenjougo ↓",
    ja: "謙譲",
    icon: Users,
    desc: "Hạ thấp hành động của bản thân / nhóm mình khi nói với người ngoài",
    exampleSource: "言う (Nói)",
    exampleTarget: "申す / 申し上げる",
    badgeVariant: "matcha",
    iconColor: "text-emerald-500 bg-emerald-500/10 border-emerald-500/20",
  },
  {
    id: "keigo_teineigo",
    label: "丁寧語・美化語",
    subLabel: "Teineigo",
    ja: "丁寧",
    icon: Sparkles,
    desc: "Quy chuẩn desu/masu, gozaimasu và thêm tiền tố mỹ từ お/ご",
    exampleSource: "水 / 会社",
    exampleTarget: "お水 / 貴社・御社",
    badgeVariant: "fuji",
    iconColor: "text-indigo-500 bg-indigo-500/10 border-indigo-500/20",
  },
  {
    id: "keigo_transformation",
    label: "言葉遣い変換",
    subLabel: "Register Shift",
    ja: "変換",
    icon: Repeat,
    desc: "Chuyển đổi tức thì giữa Thân mật (Tameguchi) ⇄ Kính ngữ thương mại",
    exampleSource: "明日、社長に会うよ",
    exampleTarget: "明日、社長にお会いします",
    badgeVariant: "kintsugi",
    iconColor: "text-amber-500 bg-amber-500/10 border-amber-500/20",
  },
  {
    id: "keigo_context",
    label: "ウチ・ソト特訓",
    subLabel: "Uchi / Soto",
    ja: "内外",
    icon: Compass,
    desc: "Thử thách chọn đúng hướng Kính ngữ theo quan hệ Trong - Ngoài",
    exampleSource: "Nói về sếp mình với khách",
    exampleTarget: "社長の田中が申しました",
    badgeVariant: "torii",
    iconColor: "text-sky-500 bg-sky-500/10 border-sky-500/20",
  },
  {
    id: "keigo_doctor",
    label: "敬語診断",
    subLabel: "Keigo Doctor",
    ja: "診断",
    icon: ShieldAlert,
    desc: "Phát hiện và sửa lỗi Nhị trùng kính ngữ (Double Keigo) & lộn hướng",
    exampleSource: "おっしゃられる ❌",
    exampleTarget: "おっしゃる ✅",
    badgeVariant: "akane",
    iconColor: "text-rose-600 bg-rose-600/10 border-rose-600/20",
  },
  {
    id: "keigo_naturalness",
    label: "自然度判定",
    subLabel: "Naturalness",
    ja: "自然",
    icon: CheckCircle2,
    desc: "Đo độ tự nhiên: Phân biệt câu chuẩn Nhật vs câu ngượng gạo",
    exampleSource: "ご苦労様です (Sai ngữ cảnh)",
    exampleTarget: "お疲れ様でございます ✅",
    badgeVariant: "jlpt",
    iconColor: "text-teal-500 bg-teal-500/10 border-teal-500/20",
  },
];

export const PRESSURE_LEVELS = [
  { id: "relaxed", label: "Dễ", icon: "🐢", ms: 6000, desc: "6.0s" },
  { id: "normal", label: "Tiêu chuẩn", icon: "🚶", ms: 5000, desc: "5.0s" },
  { id: "fast", label: "Nhanh", icon: "🏃", ms: 4000, desc: "4.0s" },
  { id: "reflex", label: "Phản xạ", icon: "⚡", ms: 3000, desc: "3.0s" },
  { id: "extreme", label: "Cực hạn", icon: "🔥", ms: 2000, desc: "2.0s" },
] as const;

export const DURATIONS = [3, 5, 10, 20] as const;

interface Props {
  subMode: string;
  setSubMode: (m: string) => void;
  pressure: PressureLevel;
  setPressure: (p: PressureLevel) => void;
  subtitleMode: "hidden" | "japanese" | "japanese_reading" | "vietnamese";
  setSubtitleMode: (m: "hidden" | "japanese" | "japanese_reading" | "vietnamese") => void;
  duration: 3 | 5 | 10 | 20;
  setDuration: (d: 3 | 5 | 10 | 20) => void;
  autoNext: boolean;
  setAutoNext: (v: boolean | ((prev: boolean) => boolean)) => void;
  startTrigger: "manual" | "auto";
  setStartTrigger: (t: "manual" | "auto") => void;
  onStartSession: () => void;
  onOpenCheatsheet: () => void;
  onOpenHelp: () => void;
  error?: string | null;
}

export function KeigoLobby({
  subMode,
  setSubMode,
  pressure,
  setPressure,
  subtitleMode,
  setSubtitleMode,
  duration,
  setDuration,
  autoNext,
  setAutoNext,
  onStartSession,
  onOpenCheatsheet,
  onOpenHelp,
  error,
}: Props) {
  const selectedMode = KEIGO_SUB_MODES.find((m) => m.id === subMode) || KEIGO_SUB_MODES[0];
  const selectedPressure = PRESSURE_LEVELS.find((p) => p.id === pressure) || PRESSURE_LEVELS[1];

  return (
    <div className="space-y-6 animate-in fade-in duration-300 max-w-5xl mx-auto">
      {/* 1. Hero Banner */}
      <div className="relative overflow-hidden rounded-[28px] border border-border/80 bg-card p-6 md:p-8 washi-texture shadow-sm">
        <div className="absolute -top-12 -right-12 h-48 w-48 rounded-full bg-enso-gradient opacity-30 blur-2xl pointer-events-none" />
        <div className="relative flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2.5">
              <span className="h-10 w-10 rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary shadow-xs">
                <Crown className="h-5 w-5" />
              </span>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-2xl md:text-3xl font-black tracking-tight text-foreground font-jp">
                    敬語スタジオ <span className="text-lg font-bold font-sans text-primary">Keigo Studio</span>
                  </h1>
                  <Badge variant="kintsugi" size="sm">Mode 2</Badge>
                </div>
                <p className="text-xs md:text-sm text-muted-foreground mt-0.5">
                  Luyện phản xạ Kính ngữ (敬語) & Văn phong công sở Nhật Bản dưới áp lực thời gian
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={onOpenCheatsheet}
              className="gap-1.5 text-xs font-bold border-amber-500/30 text-amber-700 dark:text-amber-300 hover:bg-amber-500/10"
            >
              <BookOpen className="h-4 w-4" />
              <span>Sổ tay Kính ngữ</span>
            </Button>
            <Button variant="ghost" size="sm" onClick={onOpenHelp} className="gap-1.5 text-xs font-bold">
              <Keyboard className="h-4 w-4" />
              <span>Phím tắt (?)</span>
            </Button>
          </div>
        </div>
      </div>

      {/* 2. Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Submode Selection (8 modes) */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Badge variant="sakura">Chuyên Đề Luyện Tập</Badge>
              <span className="text-xs text-muted-foreground">Chọn 1 chuyên đề hoặc Tổng hợp</span>
            </div>
            <span className="text-[11px] text-muted-foreground font-mono">8 Sub-modes</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {KEIGO_SUB_MODES.map((m) => {
              const isActive = subMode === m.id;
              const isMixed = m.id === "mixed";
              const IconComp = m.icon;

              return (
                <button
                  key={m.id}
                  onClick={() => setSubMode(m.id)}
                  className={cn(
                    "text-left rounded-2xl border p-4 transition-all flex flex-col justify-between space-y-2.5 washi-texture cursor-pointer relative group",
                    isActive
                      ? "border-primary bg-primary/8 shadow-md ring-1 ring-primary/30"
                      : "border-border/80 hover:border-primary/40 bg-card hover:shadow-xs",
                    isMixed && "sm:col-span-2 bg-gradient-to-r from-amber-500/10 via-primary/5 to-transparent border-amber-500/30"
                  )}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2.5">
                      <span className={cn("h-8 w-8 rounded-xl border flex items-center justify-center shrink-0", m.iconColor)}>
                        <IconComp className="h-4 w-4" />
                      </span>
                      <div>
                        <span className="text-sm font-black text-foreground font-jp">{m.label}</span>
                        <span className="text-[11px] text-muted-foreground ml-1.5 font-sans">({m.subLabel})</span>
                      </div>
                    </div>
                    <Badge variant={m.badgeVariant} size="sm">{m.ja}</Badge>
                  </div>

                  <p className="text-xs text-muted-foreground leading-relaxed">{m.desc}</p>

                  <div className="pt-2 border-t border-border/50 flex items-center justify-between text-[11px] text-muted-foreground font-jp">
                    <span className="truncate max-w-[45%]">{m.exampleSource}</span>
                    <span className="text-primary font-bold">➔</span>
                    <span className="font-bold text-foreground truncate max-w-[45%] text-right">{m.exampleTarget}</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right Column: Settings & CTA */}
        <div className="space-y-4">
          <Card className="p-5 space-y-5 border-border/90 bg-card shadow-sm washi-texture">
            <div className="flex items-center gap-2 text-sm font-bold text-foreground border-b border-border/70 pb-3">
              <Settings2 className="h-4 w-4 text-primary" />
              <span>Cấu Hình Phiên Luyện Tập</span>
            </div>

            {/* Pressure Selector */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs font-bold">
                <span className="text-muted-foreground">Áp Lực Thời Gian:</span>
                <span className="text-primary font-mono">{selectedPressure.ms / 1000}s / câu</span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5">
                {PRESSURE_LEVELS.map((p) => (
                  <button
                    key={p.id}
                    onClick={() => setPressure(p.id as any)}
                    className={cn(
                      "px-2 py-1.5 rounded-xl text-xs font-bold border transition-all text-center flex flex-col items-center gap-0.5",
                      pressure === p.id
                        ? "bg-primary text-primary-foreground border-primary shadow-xs"
                        : "bg-muted/40 border-border/80 hover:bg-muted text-foreground"
                    )}
                  >
                    <span>{p.icon} {p.label}</span>
                    <span className="text-[10px] opacity-80 font-mono">{p.desc}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Duration Selector */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs font-bold">
                <span className="text-muted-foreground">Thời Lượng Phiên:</span>
                <span className="text-primary font-mono">{duration} phút</span>
              </div>
              <div className="grid grid-cols-4 gap-1.5">
                {DURATIONS.map((d) => (
                  <button
                    key={d}
                    onClick={() => setDuration(d)}
                    className={cn(
                      "py-1.5 rounded-xl text-xs font-bold border transition-all text-center",
                      duration === d
                        ? "bg-primary text-primary-foreground border-primary shadow-xs"
                        : "bg-muted/40 border-border/80 hover:bg-muted text-foreground"
                    )}
                  >
                    {d} min
                  </button>
                ))}
              </div>
            </div>

            {/* Subtitle Mode */}
            <div className="space-y-2">
              <span className="text-xs font-bold text-muted-foreground">Hiển Thị Đề Bài:</span>
              <div className="grid grid-cols-2 gap-1.5 text-xs">
                {(
                  [
                    { id: "japanese", label: "Chữ Hán (Kanji)" },
                    { id: "japanese_reading", label: "Kanji + Cách đọc" },
                    { id: "vietnamese", label: "Dịch tiếng Việt" },
                    { id: "hidden", label: "Audio-Only 🎧" },
                  ] as const
                ).map((m) => (
                  <button
                    key={m.id}
                    onClick={() => setSubtitleMode(m.id)}
                    className={cn(
                      "p-2 rounded-xl text-[11px] font-bold border transition-all text-center",
                      subtitleMode === m.id
                        ? "bg-primary text-primary-foreground border-primary shadow-xs"
                        : "bg-muted/40 border-border/80 hover:bg-muted text-foreground"
                    )}
                  >
                    {m.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Auto Next Toggle */}
            <div className="pt-2 border-t border-border/70 flex items-center justify-between text-xs">
              <span className="font-bold text-muted-foreground">Tự Động Chuyển Câu:</span>
              <button
                onClick={() => setAutoNext((v) => !v)}
                className={cn(
                  "px-3 py-1 rounded-full text-xs font-bold border transition-all",
                  autoNext
                    ? "bg-emerald-600 text-white border-emerald-600 shadow-2xs"
                    : "bg-muted border-border text-muted-foreground"
                )}
              >
                {autoNext ? "BẬT (Auto)" : "TẮT (Thủ công)"}
              </button>
            </div>

            {/* Big CTA Button */}
            <Button
              variant="akane"
              size="lg"
              className="w-full font-bold gap-2 text-sm shadow-md h-12"
              onClick={onStartSession}
            >
              <Play className="h-4 w-4 fill-current" />
              <span>Bắt Đầu {duration} Phút • {selectedMode.ja}</span>
            </Button>

            {error && (
              <div className="text-xs text-red-600 border border-red-200 bg-red-50 dark:bg-red-950/20 rounded-xl p-2.5">
                {error}
              </div>
            )}
          </Card>

          {/* Quick Cheatsheet Promotion Card */}
          <Card
            onClick={onOpenCheatsheet}
            className="p-4 bg-amber-500/5 hover:bg-amber-500/10 border-amber-500/20 transition-all cursor-pointer space-y-1.5 group"
          >
            <div className="flex items-center justify-between">
              <div className="text-xs font-bold text-amber-700 dark:text-amber-300 flex items-center gap-1.5">
                <BookOpen className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400" />
                <span>Cẩm Nang Kính Ngữ Công Sở</span>
              </div>
              <span className="text-[11px] text-amber-600 font-bold group-hover:translate-x-0.5 transition-transform">
                Mở ➔
              </span>
            </div>
            <p className="text-[11px] text-foreground/80 leading-relaxed">
              Bảng 25+ động từ bất quy tắc, ma trận quan hệ Trong/Ngoài (Uchi/Soto) và quy tắc tránh Nhị trùng kính ngữ.
            </p>
          </Card>
        </div>
      </div>
    </div>
  );
}
"""

PROMPT_CARD_CONTENT = """\"use client\";

import React, { useState, useEffect } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Crown,
  Volume2,
  Sparkles,
  ArrowRight,
  Headphones,
  Building,
} from "lucide-react";
import type { KeigoExercise } from "../services/keigo-api";
import { translateJaToVi } from "@/features/reflex/services/google-translate";
import { cn } from "@/lib/utils";

interface Props {
  exercise: KeigoExercise | null;
  subtitleMode?: "hidden" | "japanese" | "japanese_reading" | "vietnamese";
  onPlayAudio?: () => void;
  phase: string;
}

export function KeigoPromptCard({
  exercise,
  subtitleMode = "japanese",
  onPlayAudio,
  phase,
}: Props) {
  const [liveTranslation, setLiveTranslation] = useState<string>("");

  const rc = exercise?.extra_metadata?.keigo_config || {};
  const prompt = rc.prompt || exercise?.prompt || exercise?.scenario || exercise?.title || "";
  const isPlaying = phase === "prompt_playing";

  const socialCtx = exercise?.socialContext || rc.social_context || {};
  const speakerRole = socialCtx.speaker_role || "SELF";
  const listenerRole = socialCtx.listener_role || "CUSTOMER";
  const referentRole = socialCtx.referent_role || socialCtx.target_subject;
  const speakerGroup = socialCtx.speaker_group || "UCHI";
  const listenerGroup = socialCtx.listener_group || "SOTO";
  const relationship = socialCtx.relationship || "BUSINESS";

  const staticTranslation =
    rc.translation ||
    rc.vietnamese ||
    exercise?.extra_metadata?.vietnamese_translation ||
    exercise?.extra_metadata?.translation ||
    null;

  useEffect(() => {
    if (subtitleMode === "vietnamese" && exercise && prompt) {
      translateJaToVi(prompt).then((res) => {
        if (res) setLiveTranslation(res);
      });
    } else {
      setLiveTranslation("");
    }
  }, [subtitleMode, exercise, prompt]);

  const displayTranslation = liveTranslation || staticTranslation;

  if (!exercise) {
    return (
      <div className="p-8 text-center rounded-3xl border border-dashed border-border bg-card/60 washi-texture flex flex-col items-center justify-center space-y-2">
        <div className="h-8 w-8 rounded-full border-2 border-primary/20 border-t-primary animate-spin" />
        <p className="text-xs font-bold text-muted-foreground">Đang chuẩn bị đề bài...</p>
      </div>
    );
  }

  const subModeMap: Record<
    string,
    { label: string; ja: string; color: "sakura" | "kintsugi" | "matcha" | "fuji" | "jlpt" | "torii" | "akane" }
  > = {
    keigo_sonkeigo: { label: "Tôn Kính Ngữ", ja: "尊敬語 ↑", color: "sakura" },
    keigo_kenjougo: { label: "Khiêm Nhường Ngữ", ja: "謙譲語 ↓", color: "matcha" },
    keigo_teineigo: { label: "Lịch Sự & Mỹ Từ", ja: "丁寧語 ↔", color: "fuji" },
    keigo_transformation: { label: "Chuyển Đổi Văn Phong", ja: "言葉遣い変換 ⇄", color: "kintsugi" },
    keigo_context: { label: "Trong / Ngoài", ja: "ウチ・ソト ⚔️", color: "torii" },
    keigo_doctor: { label: "Bắt Lỗi Kính Ngữ", ja: "敬語診断 🩺", color: "akane" },
    keigo_naturalness: { label: "Độ Tự Nhiên", ja: "自然度判定 🍃", color: "jlpt" },
  };

  const modeInfo =
    subModeMap[exercise.subMode || exercise.exercise_type] || {
      label: "Luyện Kính Ngữ",
      ja: "敬語",
      color: "kintsugi",
    };

  return (
    <div className="relative overflow-hidden rounded-3xl border border-border/90 bg-card shadow-sm washi-texture transition-all duration-300">
      {/* Top Header Strip */}
      <div className="bg-muted/40 border-b border-border/70 px-5 py-2.5 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Badge variant={modeInfo.color} size="sm" className="font-bold">
            {modeInfo.ja} • {modeInfo.label}
          </Badge>
          {relationship && (
            <span className="text-[11px] font-bold text-muted-foreground hidden sm:inline-flex items-center gap-1">
              <Building className="h-3 w-3" />
              <span>{relationship}</span>
            </span>
          )}
        </div>

        <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground">
          <span className="px-2 py-0.5 rounded-md bg-background border text-[10px] uppercase font-bold tracking-wider">
            {exercise.difficulty || "Normal"}
          </span>
          <span>•</span>
          <span className="text-primary font-mono font-bold">
            {(exercise.timerLimitMs || 5000) / 1000}s
          </span>
        </div>
      </div>

      {/* Main Prompt Content Area */}
      <div className="p-5 md:p-6 space-y-4">
        {/* Visual Uchi - Soto Relationship Diagram */}
        <div className="p-3.5 rounded-2xl bg-muted/40 border border-border/70 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Ngữ cảnh:</span>
            <div className="flex items-center gap-1.5 font-bold">
              <span className="px-2 py-0.5 rounded-lg bg-rose-500/10 text-rose-600 border border-rose-500/20 text-[11px]">
                {speakerRole} [{speakerGroup}]
              </span>
              <ArrowRight className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="px-2 py-0.5 rounded-lg bg-emerald-500/10 text-emerald-600 border border-emerald-500/20 text-[11px]">
                {listenerRole} [{listenerGroup}]
              </span>
            </div>
          </div>

          {referentRole && (
            <div className="flex items-center gap-1.5 text-muted-foreground text-[11px]">
              <span>Chủ thể hành động:</span>
              <span className="font-bold text-foreground px-2 py-0.5 rounded-md bg-background border">
                {referentRole}
              </span>
            </div>
          )}
        </div>

        {/* Prompt Question Display */}
        {subtitleMode === "hidden" ? (
          /* Audio-Only Mode */
          <div className="p-6 rounded-2xl bg-muted/30 border border-dashed text-center text-xs text-muted-foreground italic flex flex-col items-center justify-center space-y-3 max-w-md mx-auto">
            <div className="flex items-center gap-2 font-bold text-primary text-sm not-italic">
              <Headphones className="h-5 w-5 animate-pulse" />
              <span>🎧 Chế độ Audio-Only: Hãy lắng nghe câu tình huống qua loa</span>
            </div>
            <p className="not-italic text-foreground text-xs">
              Mục tiêu: <span className="font-bold text-primary">{exercise.instructions || "Hãy nói câu Kính ngữ phù hợp"}</span>
            </p>
          </div>
        ) : (
          /* Visible Mode */
          <div className="text-center space-y-3 py-2">
            <div className="text-xs font-bold text-muted-foreground uppercase tracking-wider flex items-center justify-center gap-1.5">
              <span>Câu tình huống / Câu gốc (Prompt)</span>
              {isPlaying && <span className="inline-flex h-2 w-2 rounded-full bg-primary animate-ping" />}
            </div>

            <div className="text-2xl sm:text-3xl md:text-4xl font-black font-jp tracking-tight text-foreground px-2 leading-tight">
              {prompt}
            </div>

            {displayTranslation && (
              <p className="text-xs sm:text-sm font-medium text-muted-foreground max-w-lg mx-auto leading-relaxed">
                🇻🇳 {displayTranslation}
              </p>
            )}
          </div>
        )}

        {/* Footnote */}
        <div className="pt-2 border-t border-border/70 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-1.5 text-muted-foreground">
            <Sparkles className="h-3.5 w-3.5 text-amber-500 shrink-0" />
            <span>{exercise.instructions || exercise.objective || "Hãy nói câu Kính ngữ phù hợp"}</span>
          </div>

          {onPlayAudio && (
            <Button
              size="sm"
              variant="outline"
              onClick={onPlayAudio}
              className="gap-1.5 text-xs font-bold shrink-0 ml-auto"
            >
              <Volume2 className={cn("h-3.5 w-3.5 text-primary", isPlaying && "animate-bounce")} />
              <span>{isPlaying ? "Đang phát..." : "Nghe lại đề (L)"}</span>
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
"""

RESULT_CARD_CONTENT = """\"use client\";

import React, { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  CheckCircle2,
  XCircle,
  Clock,
  Zap,
  Trophy,
  RotateCcw,
  ArrowRight,
  Volume2,
  Play,
  Pause,
  Mic,
  Crown,
  AlertTriangle,
  MessageSquare,
} from "lucide-react";
import type { KeigoResult, KeigoExercise } from "../services/keigo-api";
import { speakJapaneseText, stopWebSpeech } from "@/features/speaking/services/web-speech";
import { cn } from "@/lib/utils";

interface Props {
  result: KeigoResult | null;
  exercise?: KeigoExercise | null;
  onNext?: () => void;
  onRetry?: () => void;
  onAskCoach?: (prompt: string) => void;
  onCancelAutoNext?: () => void;
}

export function KeigoResultCard({
  result,
  exercise,
  onNext,
  onRetry,
  onAskCoach,
  onCancelAutoNext,
}: Props) {
  const [isUserAudioPlaying, setIsUserAudioPlaying] = useState(false);
  const [userAudioCurrentTime, setUserAudioCurrentTime] = useState(0);
  const [userAudioDuration, setUserAudioDuration] = useState(0);
  const [isTTSPlaying, setIsTTSPlaying] = useState(false);

  const userAudioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    setIsUserAudioPlaying(false);
    setUserAudioCurrentTime(0);
    setUserAudioDuration(0);
  }, [result]);

  if (!result) return null;

  const isPerfect = result.isPerfect;
  const isTimeout = result.timedOut;
  const isCorrect = result.success;
  const latency = result.reactionLatencyMs;
  const timerLimit = result.timerLimitMs || 5000;
  const latencyRatio = latency != null ? Math.min(1, latency / timerLimit) : 1;

  const canonical =
    result.canonicalAnswer ||
    exercise?.canonical ||
    (exercise?.target_patterns && exercise.target_patterns.length > 0 ? exercise.target_patterns[0] : "") ||
    "";

  useEffect(() => {
    if (!canonical) return;
    setIsTTSPlaying(true);
    const timer = setTimeout(() => {
      speakJapaneseText(canonical, {
        rate: 0.95,
        onEnd: () => setIsTTSPlaying(false),
        onError: () => setIsTTSPlaying(false),
      });
    }, 200);

    return () => clearTimeout(timer);
  }, [result.exerciseId, canonical]);

  const variants =
    result.acceptableVariants ||
    exercise?.acceptableVariants ||
    (exercise?.extra_metadata?.keigo_config?.acceptable_variants as string[]) ||
    [];

  const togglePlayUserAudio = () => {
    onCancelAutoNext?.();
    if (!userAudioRef.current || !result.userAudioUrl) return;

    if (isUserAudioPlaying) {
      userAudioRef.current.pause();
      setIsUserAudioPlaying(false);
    } else {
      stopWebSpeech();
      setIsTTSPlaying(false);
      userAudioRef.current
        .play()
        .then(() => setIsUserAudioPlaying(true))
        .catch(() => setIsUserAudioPlaying(false));
    }
  };

  const handlePlayModelTTS = () => {
    onCancelAutoNext?.();
    if (!canonical) return;

    if (isUserAudioPlaying && userAudioRef.current) {
      userAudioRef.current.pause();
      setIsUserAudioPlaying(false);
    }

    if (isTTSPlaying) {
      stopWebSpeech();
      setIsTTSPlaying(false);
      return;
    }

    setIsTTSPlaying(true);
    speakJapaneseText(canonical, {
      rate: 0.95,
      onEnd: () => setIsTTSPlaying(false),
      onError: () => setIsTTSPlaying(false),
    });
  };

  const formatAudioTime = (seconds: number) => {
    const s = Math.floor(seconds % 60);
    const m = Math.floor(seconds / 60);
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  const statusConfig = isTimeout
    ? {
        label: "HẾT GIỜ (TIME'S UP)",
        icon: <Clock className="h-4 w-4" />,
        badgeClass: "bg-muted text-muted-foreground border-border",
        borderClass: "border-border/80 bg-muted/20",
        scoreColor: "text-muted-foreground",
      }
    : isPerfect
    ? {
        label: "HOÀN HẢO (PERFECT KEIGO)",
        icon: <Trophy className="h-4 w-4 text-amber-300" />,
        badgeClass: "bg-amber-500 text-sumi-950 font-black border-amber-400 shadow-md shadow-amber-500/20",
        borderClass: "border-amber-500/40 bg-amber-500/8 dark:bg-amber-950/20",
        scoreColor: "text-amber-600 dark:text-amber-400",
      }
    : isCorrect
    ? {
        label: "CHÍNH XÁC (CORRECT)",
        icon: <CheckCircle2 className="h-4 w-4" />,
        badgeClass: "bg-emerald-600 text-white font-bold border-emerald-500",
        borderClass: "border-emerald-500/30 bg-emerald-500/8 dark:bg-emerald-950/20",
        scoreColor: "text-emerald-600 dark:text-emerald-400",
      }
    : {
        label: "CẦN CỐ GẮNG (TRY AGAIN)",
        icon: <XCircle className="h-4 w-4" />,
        badgeClass: "bg-rose-600 text-white font-bold border-rose-500",
        borderClass: "border-rose-500/30 bg-rose-500/8 dark:bg-rose-950/20",
        scoreColor: "text-rose-600 dark:text-rose-400",
      };

  return (
    <div
      className={cn(
        "rounded-3xl border p-5 md:p-6 space-y-4 shadow-lg transition-all animate-in fade-in zoom-in-95 duration-200 washi-texture",
        statusConfig.borderClass
      )}
    >
      {result.userAudioUrl && (
        <audio
          ref={userAudioRef}
          src={result.userAudioUrl}
          onLoadedMetadata={() => {
            if (userAudioRef.current) setUserAudioDuration(userAudioRef.current.duration || 0);
          }}
          onTimeUpdate={() => {
            if (userAudioRef.current) setUserAudioCurrentTime(userAudioRef.current.currentTime || 0);
          }}
          onEnded={() => {
            setIsUserAudioPlaying(false);
            setUserAudioCurrentTime(0);
          }}
          onError={() => setIsUserAudioPlaying(false)}
        />
      )}

      {/* 1. Status & Latency Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <span
          className={cn(
            "inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-bold border shadow-2xs",
            statusConfig.badgeClass
          )}
        >
          {statusConfig.icon}
          <span>{statusConfig.label}</span>
        </span>

        {latency != null && (
          <div className="flex items-center gap-2 text-xs font-mono font-bold text-foreground">
            <Zap className="h-3.5 w-3.5 text-amber-500" />
            <span>Phản xạ: {Math.round(latency)}ms</span>
            <span className="text-muted-foreground font-normal">/ {timerLimit / 1000}s</span>
          </div>
        )}
      </div>

      {/* Latency Speed Bar */}
      {latency != null && (
        <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden border border-border/50">
          <div
            className={cn(
              "h-full rounded-full transition-all duration-500",
              latencyRatio < 0.5
                ? "bg-emerald-500"
                : latencyRatio < 0.75
                ? "bg-amber-500"
                : "bg-rose-500"
            )}
            style={{ width: `${latencyRatio * 100}%` }}
          />
        </div>
      )}

      {/* 2. Feedback Banner */}
      <div className="flex items-start gap-4 p-3.5 rounded-2xl bg-card border border-border/80 shadow-xs">
        <div className="flex flex-col items-center justify-center p-3 rounded-xl bg-muted/60 border border-border shrink-0 min-w-[68px]">
          <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Điểm</span>
          <span className={cn("text-2xl font-black font-mono", statusConfig.scoreColor)}>
            {result.score.toFixed(0)}
          </span>
        </div>

        <div className="flex-1 min-w-0 space-y-1">
          <p className="text-sm font-bold text-foreground leading-snug">{result.feedback}</p>
          {result.doubleKeigo && (
            <div className="flex items-center gap-1 text-xs text-amber-600 dark:text-amber-400 font-semibold">
              <AlertTriangle className="h-3.5 w-3.5" />
              <span>Cảnh báo: Phát hiện dấu hiệu lặp kính ngữ (Double Keigo)</span>
            </div>
          )}
        </div>
      </div>

      {/* 3. DUAL CORE COMPARISON */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
        {/* CARD A: Your Voice */}
        <div className="p-4 rounded-2xl bg-card border border-border/80 shadow-xs space-y-3 flex flex-col justify-between">
          <div className="space-y-1.5">
            <div className="flex items-center justify-between gap-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                <Mic className="h-3.5 w-3.5 text-primary" />
                <span>Bạn đã nói (Your Voice)</span>
              </span>
              {result.transcript && (
                <span className="text-[10px] px-2 py-0.5 rounded-md bg-muted text-muted-foreground font-mono">
                  ja-JP
                </span>
              )}
            </div>

            <div className="text-base font-black font-jp text-foreground min-h-[1.75rem] flex items-center">
              {result.transcript ? (
                <span>“{result.transcript}”</span>
              ) : (
                <span className="text-xs text-muted-foreground italic font-sans font-normal">
                  {isTimeout ? "Không nhận diện được giọng nói (Hết giờ)" : "Không có âm thanh thu âm"}
                </span>
              )}
            </div>
          </div>

          {result.userAudioUrl ? (
            <div className="pt-2 border-t border-border/60 flex items-center gap-2.5">
              <Button
                size="sm"
                variant={isUserAudioPlaying ? "sakura" : "outline"}
                onClick={togglePlayUserAudio}
                className="h-8 w-8 rounded-full p-0 shrink-0 shadow-2xs"
                title="Nghe lại giọng của bạn"
              >
                {isUserAudioPlaying ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5 ml-0.5" />}
              </Button>
              <div className="flex-1 min-w-0 space-y-1">
                <div className="flex items-center justify-between text-[10px] font-mono text-muted-foreground">
                  <span>{formatAudioTime(userAudioCurrentTime)}</span>
                  <span>{formatAudioTime(userAudioDuration || 0)}</span>
                </div>
                <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary transition-all duration-100"
                    style={{
                      width: `${userAudioDuration ? (userAudioCurrentTime / userAudioDuration) * 100 : 0}%`,
                    }}
                  />
                </div>
              </div>
            </div>
          ) : (
            <div className="pt-2 border-t border-border/60 text-[10px] text-muted-foreground italic">
              Không có bản ghi âm
            </div>
          )}
        </div>

        {/* CARD B: Model Answer */}
        <div className="p-4 rounded-2xl bg-card border border-border/80 shadow-xs space-y-3 flex flex-col justify-between">
          <div className="space-y-1.5">
            <div className="flex items-center justify-between gap-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-primary flex items-center gap-1.5">
                <Crown className="h-3.5 w-3.5 text-amber-500" />
                <span>Đáp án Kính ngữ chuẩn</span>
              </span>
              <Badge variant="matcha" size="sm" className="text-[10px]">Chuẩn công sở</Badge>
            </div>

            <div className="text-base font-black font-jp text-primary min-h-[1.75rem] flex items-center">
              {canonical ? (
                <span>“{canonical}”</span>
              ) : (
                <span className="text-xs text-muted-foreground italic font-sans font-normal">
                  Chưa có đáp án mẫu
                </span>
              )}
            </div>
          </div>

          <div className="pt-2 border-t border-border/60 flex items-center justify-between gap-2">
            <Button
              size="sm"
              variant={isTTSPlaying ? "akane" : "outline"}
              onClick={handlePlayModelTTS}
              className="gap-1.5 text-xs font-bold shrink-0"
            >
              <Volume2 className={cn("h-3.5 w-3.5", isTTSPlaying && "animate-bounce")} />
              <span>{isTTSPlaying ? "Đang phát..." : "Nghe mẫu (TTS)"}</span>
            </Button>

            {variants.length > 1 && (
              <div className="text-[10px] text-muted-foreground truncate font-jp" title={variants.join(" / ")}>
                +{variants.length - 1} cách nói khác
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 4. Bottom Action Controls */}
      <div className="pt-2 flex flex-wrap items-center gap-2">
        {onNext && (
          <Button size="sm" variant="akane" onClick={onNext} className="flex-1 gap-1.5 font-bold min-w-[130px]">
            <span>Câu tiếp theo (Enter)</span>
            <ArrowRight className="h-4 w-4" />
          </Button>
        )}

        {onRetry && (
          <Button size="sm" variant="outline" onClick={onRetry} className="gap-1.5 font-bold">
            <RotateCcw className="h-3.5 w-3.5" />
            <span>Thử lại (R)</span>
          </Button>
        )}

        {onAskCoach && canonical && (
          <Button
            size="sm"
            variant="ghost"
            onClick={() =>
              onAskCoach(`Giải thích ngắn gọn sắc thái và cách dùng kính ngữ trong câu: "${canonical}"`)
            }
            className="gap-1.5 text-xs text-primary font-bold ml-auto"
          >
            <MessageSquare className="h-3.5 w-3.5" />
            <span>Hỏi Sensei</span>
          </Button>
        )}
      </div>
    </div>
  );
}
"""

SESSION_SUMMARY_CONTENT = """\"use client\";

import React, { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  RotateCcw,
  Sparkles,
  Volume2,
  Crown,
} from "lucide-react";
import type { KeigoResult } from "../services/keigo-api";
import { speakJapaneseText, stopWebSpeech } from "@/features/speaking/services/web-speech";
import { cn } from "@/lib/utils";

interface Props {
  results: KeigoResult[];
  onRestart?: () => void;
  onToLobby?: () => void;
  onRetryWeak?: (weakResults: KeigoResult[]) => void;
}

export function KeigoSessionSummary({ results, onRestart, onToLobby, onRetryWeak }: Props) {
  const [playingTTSId, setPlayingTTSId] = useState<string | null>(null);

  if (!results.length) return null;

  const total = results.length;
  const correct = results.filter((r) => r.success).length;
  const perfect = results.filter((r) => r.isPerfect).length;
  const acc = total ? Math.round((correct / total) * 100) : 0;
  const latencies = results
    .map((r) => r.reactionLatencyMs)
    .filter((v): v is number => v != null)
    .sort((a, b) => a - b);
  const avg = latencies.length ? Math.round(latencies.reduce((a, b) => a + b, 0) / latencies.length) : null;
  const best = latencies.length ? Math.round(Math.min(...latencies)) : null;
  const incorrectResults = results.filter((r) => !r.success);

  const grade =
    acc >= 90 && (avg == null || avg < 2500)
      ? { text: "S", stamp: "大変よくできました", color: "text-amber-500 border-amber-500 bg-amber-500/10" }
      : acc >= 75
      ? { text: "A", stamp: "合格", color: "text-emerald-600 border-emerald-600 bg-emerald-500/10" }
      : acc >= 50
      ? { text: "B", stamp: "良好", color: "text-sky-600 border-sky-600 bg-sky-500/10" }
      : { text: "C", stamp: "がんばろう", color: "text-rose-600 border-rose-600 bg-rose-500/10" };

  const handlePlayTTS = (text: string, id: string) => {
    if (playingTTSId === id) {
      stopWebSpeech();
      setPlayingTTSId(null);
      return;
    }
    setPlayingTTSId(id);
    speakJapaneseText(text, {
      rate: 0.95,
      onEnd: () => setPlayingTTSId(null),
      onError: () => setPlayingTTSId(null),
    });
  };

  return (
    <div className="p-6 md:p-8 rounded-3xl border border-border bg-card washi-texture shadow-lg space-y-6 animate-in fade-in zoom-in-95 duration-300 max-w-4xl mx-auto">
      {/* Top Banner with Japanese Hanko Stamp */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-border/80">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Badge variant="kintsugi" size="sm">
              <Crown className="h-3 w-3 mr-1" />
              Tổng Kết Phiên Luyện
            </Badge>
          </div>
          <h3 className="text-xl md:text-2xl font-black text-foreground">
            Báo Cáo Phản Xạ Kính Ngữ Công Sở
          </h3>
          <p className="text-xs text-muted-foreground">
            Đã hoàn thành toàn bộ {total} câu luyện tập phản xạ Kính ngữ & Uchi/Soto
          </p>
        </div>

        {/* Hanko Stamp */}
        <div
          className={cn(
            "hanko-badge shrink-0 self-start sm:self-center px-4 py-2 rounded-2xl border-2 rotate-[-4deg] text-center shadow-sm select-none",
            grade.color
          )}
        >
          <div className="text-[10px] font-extrabold tracking-widest uppercase">HANKO STAMP</div>
          <div className="text-sm font-black font-jp">{grade.stamp}</div>
        </div>
      </div>

      {/* 4 Performance Metric Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 text-center">
        <div className="p-4 rounded-2xl bg-card border border-border/80 shadow-xs space-y-1">
          <div className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
            Số câu luyện
          </div>
          <div className="text-2xl md:text-3xl font-black font-mono text-foreground">{total}</div>
          <div className="text-[10px] text-muted-foreground">câu hoàn thành</div>
        </div>

        <div className="p-4 rounded-2xl bg-emerald-500/8 border border-emerald-500/20 shadow-xs space-y-1">
          <div className="text-[10px] font-bold uppercase tracking-wider text-emerald-700 dark:text-emerald-300">
            Độ chính xác
          </div>
          <div className="text-2xl md:text-3xl font-black font-mono text-emerald-600 dark:text-emerald-400">
            {acc}%
          </div>
          <div className="text-[10px] text-muted-foreground">{correct}/{total} câu chuẩn</div>
        </div>

        <div className="p-4 rounded-2xl bg-amber-500/8 border border-amber-500/20 shadow-xs space-y-1">
          <div className="text-[10px] font-bold uppercase tracking-wider text-amber-700 dark:text-amber-300">
            Tốc độ trung bình
          </div>
          <div className="text-2xl md:text-3xl font-black font-mono text-amber-600 dark:text-amber-400">
            {avg ? `${avg}ms` : "—"}
          </div>
          <div className="text-[10px] text-muted-foreground font-mono">
            Nhanh nhất: {best ? `${best}ms` : "—"}
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-fuji-500/8 border border-fuji-500/20 shadow-xs space-y-1">
          <div className="text-[10px] font-bold uppercase tracking-wider text-fuji-600 dark:text-fuji-400">
            Kính ngữ Hoàn hảo
          </div>
          <div className="text-2xl md:text-3xl font-black font-mono text-fuji-600 dark:text-fuji-400">
            {perfect}
          </div>
          <div className="text-[10px] text-muted-foreground">điểm tuyệt đối</div>
        </div>
      </div>

      {/* Review Exercises List */}
      <div className="space-y-3 pt-2">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-bold text-foreground flex items-center gap-1.5">
            <Sparkles className="h-4 w-4 text-primary" />
            <span>Danh sách câu đã luyện trong phiên</span>
          </h4>
          <span className="text-xs text-muted-foreground font-mono">{results.length} câu</span>
        </div>

        <div className="max-h-[320px] overflow-y-auto space-y-2 pr-1">
          {results.map((r, index) => {
            const isCorrectItem = r.success;
            return (
              <div
                key={`${r.exerciseId}-${index}`}
                className={cn(
                  "p-3.5 rounded-2xl border transition-all flex items-start justify-between gap-3 text-xs",
                  isCorrectItem
                    ? "bg-emerald-500/5 border-emerald-500/20"
                    : "bg-rose-500/5 border-rose-500/20"
                )}
              >
                <div className="space-y-1 flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-muted-foreground">#{index + 1}</span>
                    <Badge variant={isCorrectItem ? "matcha" : "sakura"} size="sm">
                      {isCorrectItem ? "Đúng" : "Cần sửa"}
                    </Badge>
                    {r.reactionLatencyMs && (
                      <span className="text-[10px] font-mono text-muted-foreground">
                        {Math.round(r.reactionLatencyMs)}ms
                      </span>
                    )}
                  </div>

                  <div className="font-jp text-sm font-bold text-foreground">
                    Đáp án: “{r.canonicalAnswer || r.transcript || "—"}”
                  </div>

                  {r.transcript && r.transcript !== r.canonicalAnswer && (
                    <div className="text-[11px] text-muted-foreground">
                      Bạn đã nói: <span className="font-jp italic">“{r.transcript}”</span>
                    </div>
                  )}
                </div>

                {r.canonicalAnswer && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handlePlayTTS(r.canonicalAnswer!, `${r.exerciseId}-${index}`)}
                    className="h-8 w-8 rounded-full p-0 shrink-0 text-primary"
                    title="Nghe mẫu phát âm"
                  >
                    <Volume2 className={cn("h-4 w-4", playingTTSId === `${r.exerciseId}-${index}` && "animate-bounce")} />
                  </Button>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Bottom Actions */}
      <div className="pt-4 border-t border-border/80 flex flex-wrap items-center gap-3">
        {onRestart && (
          <Button variant="akane" size="lg" onClick={onRestart} className="flex-1 gap-2 font-bold min-w-[160px]">
            <RotateCcw className="h-4 w-4" />
            <span>Luyện tiếp phiên mới</span>
          </Button>
        )}

        {incorrectResults.length > 0 && onRetryWeak && (
          <Button
            variant="outline"
            size="lg"
            onClick={() => onRetryWeak(incorrectResults)}
            className="gap-2 font-bold border-rose-500/30 text-rose-600 hover:bg-rose-500/10"
          >
            <RotateCcw className="h-4 w-4" />
            <span>Luyện lại {incorrectResults.length} câu sai</span>
          </Button>
        )}

        {onToLobby && (
          <Button variant="ghost" size="lg" onClick={onToLobby} className="font-bold">
            Về sảnh chính
          </Button>
        )}
      </div>
    </div>
  );
}
"""

CHEATSHEET_CONTENT = """\"use client\";

import React, { useState } from "react";
import { Modal } from "@/components/ui/modal";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Crown,
  Search,
  CheckCircle2,
  AlertTriangle,
  ShieldAlert,
  Users,
  Building,
} from "lucide-react";

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

const KEIGO_VERB_TABLE = [
  { plain: "する (Làm)", sonkeigo: "なさる", kenjougo: "いたす", teineigo: "します", example: "ご検討なさる / 準備いたします" },
  { plain: "言う (Nói)", sonkeigo: "おっしゃる", kenjougo: "申す / 申し上げる", teineigo: "言います", example: "社長がおっしゃる / 田中と申します" },
  { plain: "行く (Đi)", sonkeigo: "いらっしゃる", kenjougo: "参る / 伺う", teineigo: "行きます", example: "どちらにいらっしゃいますか / 明日伺います" },
  { plain: "来る (Đến)", sonkeigo: "いらっしゃる / お見えになる", kenjougo: "参る", teineigo: "来ます", example: "お客様がお見えになりました" },
  { plain: "いる (Ở/Có)", sonkeigo: "いらっしゃる", kenjougo: "おる", teineigo: "います", example: "部長はいらっしゃいますか / 席におります" },
  { plain: "食べる・飲む (Ăn/Uống)", sonkeigo: "召し上がる", kenjougo: "いただく", teineigo: "食べます", example: "どうぞ召し上がってください / いただきます" },
  { plain: "見る (Xem/Nhìn)", sonkeigo: "ご覧になる", kenjougo: "拝見する", teineigo: "見ます", example: "資料をご覧になりましたか / 拝見しました" },
  { plain: "知っている (Biết)", sonkeigo: "ご存知だ", kenjougo: "存じている / 存じる", teineigo: "知っています", example: "ご存知ですか / 存じております" },
  { plain: "聞く (Nghe/Hỏi)", sonkeigo: "お聞きになる", kenjougo: "伺う / 拝聴する", teineigo: "聞きます", example: "お話を伺いました" },
  { plain: "会う (Gặp)", sonkeigo: "お会いになる", kenjougo: "お目にかかる", teineigo: "会います", example: "初めてお目にかかります" },
  { plain: "もらう (Nhận)", sonkeigo: "—", kenjougo: "いただく / 頂戴する", teineigo: "もらいます", example: "名刺を頂戴いたします" },
  { plain: "あげる (Tặng)", sonkeigo: "—", kenjougo: "差し上げる", teineigo: "あげます", example: "資料を差し上げます" },
  { plain: "くれる (Cho mình)", sonkeigo: "くださる", kenjougo: "—", teineigo: "くれます", example: "教えてくださり感謝いたします" },
  { plain: "伝える (Nhắn lại)", sonkeigo: "お伝えになる", kenjougo: "申し伝える", teineigo: "伝えます", example: "担当の者に申し伝えます" },
  { plain: "思う (Nghĩ)", sonkeigo: "お思いになる", kenjougo: "存じます", teineigo: "思います", example: "結構だと存じます" },
];

export function KeigoCheatsheetModal({ isOpen, onClose }: Props) {
  const [activeTab, setActiveTab] = useState<"verbs" | "uchi_soto" | "double_keigo">("verbs");
  const [searchQuery, setSearchQuery] = useState("");

  const filteredVerbs = KEIGO_VERB_TABLE.filter(
    (v) =>
      v.plain.toLowerCase().includes(searchQuery.toLowerCase()) ||
      v.sonkeigo.toLowerCase().includes(searchQuery.toLowerCase()) ||
      v.kenjougo.toLowerCase().includes(searchQuery.toLowerCase()) ||
      v.example.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="📖 Sổ Tay Kính Ngữ Công Sở (Pocket Reference)" className="max-w-4xl">
      <div className="space-y-4 text-sm">
        {/* Navigation Tabs */}
        <div className="flex gap-2 border-b border-border/80 pb-2">
          <Button
            size="sm"
            variant={activeTab === "verbs" ? "akane" : "ghost"}
            onClick={() => setActiveTab("verbs")}
            className="gap-1.5 font-bold"
          >
            <Crown className="h-4 w-4" /> Bảng Động Từ Bất Quy Tắc
          </Button>
          <Button
            size="sm"
            variant={activeTab === "uchi_soto" ? "akane" : "ghost"}
            onClick={() => setActiveTab("uchi_soto")}
            className="gap-1.5 font-bold"
          >
            <Users className="h-4 w-4" /> Quy Tắc Trong/Ngoài (Uchi - Soto)
          </Button>
          <Button
            size="sm"
            variant={activeTab === "double_keigo" ? "akane" : "ghost"}
            onClick={() => setActiveTab("double_keigo")}
            className="gap-1.5 font-bold"
          >
            <ShieldAlert className="h-4 w-4" /> Bẫy Nhị Trùng Kính Ngữ
          </Button>
        </div>

        {/* Tab 1: Verbs Table */}
        {activeTab === "verbs" && (
          <div className="space-y-3">
            <div className="relative">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Tìm kiếm: 食べる, 召し上がる, 申す, ăn, nói, gặp..."
                className="w-full rounded-xl border bg-background pl-9 pr-4 py-2 text-xs focus:border-primary focus:ring-1 focus:ring-primary/20"
              />
            </div>

            <div className="max-h-[380px] overflow-y-auto rounded-2xl border border-border/80 bg-card">
              <table className="w-full text-left text-xs border-collapse font-jp">
                <thead className="sticky top-0 bg-muted/90 backdrop-blur-xs border-b border-border text-[11px] font-bold text-muted-foreground">
                  <tr>
                    <th className="p-2.5 font-sans">Động từ gốc (Ý nghĩa)</th>
                    <th className="p-2.5 text-rose-600 dark:text-rose-400 font-sans">Tôn Kính (尊敬語) ↑</th>
                    <th className="p-2.5 text-emerald-600 dark:text-emerald-400 font-sans">Khiêm Nhường (謙譲語) ↓</th>
                    <th className="p-2.5 text-muted-foreground hidden md:table-cell font-sans">Ví dụ ứng dụng</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/60">
                  {filteredVerbs.map((v, idx) => (
                    <tr key={idx} className="hover:bg-muted/30 transition-colors">
                      <td className="p-2.5 font-bold text-foreground font-sans">{v.plain}</td>
                      <td className="p-2.5 font-extrabold text-rose-600 dark:text-rose-400">{v.sonkeigo}</td>
                      <td className="p-2.5 font-extrabold text-emerald-600 dark:text-emerald-400">{v.kenjougo}</td>
                      <td className="p-2.5 text-muted-foreground text-[11px] hidden md:table-cell">{v.example}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="p-3 rounded-xl bg-muted/40 border text-xs text-muted-foreground space-y-1">
              <p className="font-bold text-foreground">💡 Quy tắc biến đổi động từ thường (không bất quy tắc):</p>
              <p>• <strong>Tôn Kính Ngữ:</strong> お＋V_stem＋になる (Ví dụ: お読みになる, お待ちになる)</p>
              <p>• <strong>Khiêm Nhường Ngữ:</strong> お＋V_stem＋する / いたす (Ví dụ: お持ちする, お手伝いいたします)</p>
            </div>
          </div>
        )}

        {/* Tab 2: Uchi / Soto Principle */}
        {activeTab === "uchi_soto" && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="p-4 rounded-2xl bg-rose-500/8 border border-rose-500/20 space-y-2">
                <div className="flex items-center gap-2">
                  <Badge variant="sakura" size="sm">Uchi (身内)</Badge>
                  <span className="font-bold text-xs text-rose-700 dark:text-rose-300">Bản thân & Người công ty mình</span>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Bản thân, đồng nghiệp, và khi nói chuyện với đối tác ngoài thì <strong>Giám đốc/Trưởng phòng công ty mình</strong> cũng được tính là người trong nhà (Uchi).
                </p>
                <div className="p-2.5 rounded-xl bg-background/80 border text-xs space-y-1">
                  <span className="font-bold text-primary">Hành động của Uchi ➔ Dùng Khiêm Nhường Ngữ (謙譲語 ↓)</span>
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-emerald-500/8 border border-emerald-500/20 space-y-2">
                <div className="flex items-center gap-2">
                  <Badge variant="matcha" size="sm">Soto (他者)</Badge>
                  <span className="font-bold text-xs text-emerald-700 dark:text-emerald-300">Khách hàng & Đối tác ngoài</span>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Khách hàng, đối tác, người gọi điện từ công ty khác đến đều là người ngoài (Soto).
                </p>
                <div className="p-2.5 rounded-xl bg-background/80 border text-xs space-y-1">
                  <span className="font-bold text-rose-600 dark:text-rose-400">Hành động của Soto ➔ Dùng Tôn Kính Ngữ (尊敬語 ↑)</span>
                </div>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-amber-500/8 border border-amber-500/20 space-y-3">
              <div className="font-bold text-xs text-amber-800 dark:text-amber-300 flex items-center gap-2">
                <Building className="h-4 w-4" /> Tình huống kinh điển: Nói về Giám đốc mình với khách hàng ngoài
              </div>
              <div className="space-y-2 text-xs">
                <div className="flex items-start gap-2 text-rose-600 dark:text-rose-400">
                  <span className="font-bold">❌ Sai lầm:</span>
                  <span>「田中社長はおっしゃいました」(Tôn xưng sếp mình trước mặt khách ngoài)</span>
                </div>
                <div className="flex items-start gap-2 text-emerald-600 dark:text-emerald-400 font-bold">
                  <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
                  <span>「社長の田中が申しました」(Bỏ chức danh và dùng khiêm nhường ngữ 申す)</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 3: Double Keigo Pitfalls */}
        {activeTab === "double_keigo" && (
          <div className="space-y-3">
            <div className="p-4 rounded-2xl bg-card border border-border/80 space-y-2">
              <h4 className="font-bold text-sm text-foreground flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-amber-500" /> Nhị trùng kính ngữ (二重敬語) là gì?
              </h4>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Là lỗi dùng 2 lần kính ngữ trên cùng một động từ, khiến câu nói trở nên rườm rà, quá đà và thiếu chuyên nghiệp.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
              <div className="p-3.5 rounded-2xl border border-rose-500/30 bg-rose-500/5 space-y-2">
                <div className="font-bold text-rose-600">❌ Các lỗi Nhị trùng kính ngữ phổ biến:</div>
                <ul className="space-y-1.5 text-muted-foreground list-disc pl-4 font-jp">
                  <li><span className="line-through text-foreground">おっしゃられる</span> (おっしゃる ＋ られる ❌)</li>
                  <li><span className="line-through text-foreground">ご覧になられる</span> (ご覧になる ＋ られる ❌)</li>
                  <li><span className="line-through text-foreground">お召し上がりになられる</span> ❌</li>
                </ul>
              </div>

              <div className="p-3.5 rounded-2xl border border-emerald-500/30 bg-emerald-500/5 space-y-2">
                <div className="font-bold text-emerald-600">✅ Cách nói chuẩn mực:</div>
                <ul className="space-y-1.5 text-foreground list-disc pl-4 font-jp font-bold">
                  <li>おっしゃる / 言われる</li>
                  <li>ご覧になる / 見られる</li>
                  <li>召し上がる</li>
                </ul>
              </div>
            </div>
          </div>
        )}

        <div className="pt-2 flex justify-end">
          <Button size="sm" variant="outline" onClick={onClose}>Đóng (Esc)</Button>
        </div>
      </div>
    </Modal>
  );
}
"""

PAGE_CONTENT = """\"use client\";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import {
  Crown,
  Mic,
  Clock,
  Play,
  RotateCcw,
  Sparkles,
  BookOpen,
  Edit3,
} from "lucide-react";
import { useKeigoSession } from "@/features/keigo/hooks/useKeigoSession";
import { ReflexTimer as KeigoTimer } from "@/features/reflex/components/ReflexTimer";
import { KeigoPromptCard } from "@/features/keigo/components/KeigoPromptCard";
import { KeigoResultCard } from "@/features/keigo/components/KeigoResultCard";
import { KeigoSessionSummary } from "@/features/keigo/components/KeigoSessionSummary";
import { KeigoCheatsheetModal } from "@/features/keigo/components/KeigoCheatsheetModal";
import { KeigoLobby, KEIGO_SUB_MODES, PRESSURE_LEVELS } from "@/features/keigo/components/KeigoLobby";
import { CoachPanel } from "@/features/coach";
import { usePathname } from "next/navigation";
import { useCoachCore } from "@/features/coach/hooks/useCoachCore";
import { CoachInsightCard } from "@/features/coach/components/CoachInsightCard";
import { useCoachProactive } from "@/features/coach/hooks/useCoachProactive";
import { useSystemKeybindings, formatKeyDisplay } from "@/hooks/use-system-keybindings";
import { speakJapaneseText, stopWebSpeech } from "@/features/speaking/services/web-speech";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

export default function KeigoPage() {
  const [subMode, setSubMode] = useState("mixed");
  const [pressure, setPressure] = useState<"relaxed" | "normal" | "fast" | "reflex" | "extreme">("normal");
  const [subtitleMode, setSubtitleMode] = useState<"hidden" | "japanese" | "japanese_reading" | "vietnamese">("japanese");
  const [startTrigger, setStartTrigger] = useState<"manual" | "auto">("manual");
  const [transcriptInput, setTranscriptInput] = useState("");
  const [showTextInput, setShowTextInput] = useState(false);
  const [showSummary, setShowSummary] = useState(false);
  const [showCheatsheet, setShowCheatsheet] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const [duration, setDuration] = useState<3 | 5 | 10 | 20>(5);
  const [sessionRemainingSec, setSessionRemainingSec] = useState(duration * 60);
  const [autoNext, setAutoNext] = useState(false);

  const sessionEndTimestampRef = useRef<number | null>(null);
  const sessionPausedRemainingMsRef = useRef<number>(duration * 60 * 1000);

  const { matchesAction, keybindings } = useSystemKeybindings();

  const session = useKeigoSession({
    subMode,
    pressureLevel: pressure as any,
    autoNext,
    startTrigger,
  });

  useEffect(() => {
    if (session.phase === "idle" || session.phase === "summary" || showSummary) {
      setSessionRemainingSec(duration * 60);
      sessionEndTimestampRef.current = null;
      sessionPausedRemainingMsRef.current = duration * 60 * 1000;
    }
  }, [duration, session.phase, showSummary]);

  useEffect(() => {
    const isSessionActive = session.phase !== "idle" && session.phase !== "summary" && !showSummary;
    if (!isSessionActive) return;

    if (session.isPaused) {
      if (sessionEndTimestampRef.current !== null) {
        const remaining = Math.max(0, sessionEndTimestampRef.current - Date.now());
        sessionPausedRemainingMsRef.current = remaining;
        sessionEndTimestampRef.current = null;
      }
      return;
    }

    if (sessionEndTimestampRef.current === null) {
      sessionEndTimestampRef.current = Date.now() + sessionPausedRemainingMsRef.current;
    }

    const interval = setInterval(() => {
      if (sessionEndTimestampRef.current === null) return;
      const remainingMs = sessionEndTimestampRef.current - Date.now();
      const remainingSec = Math.max(0, Math.ceil(remainingMs / 1000));
      setSessionRemainingSec(remainingSec);

      if (remainingSec <= 0) {
        clearInterval(interval);
        sessionEndTimestampRef.current = null;
        setShowSummary(true);
        session.setPhase("summary" as any);
        soundFX.playVictory();
      }
    }, 500);

    return () => clearInterval(interval);
  }, [session.phase, session.isPaused, showSummary, session.setPhase]);

  const timerMs = PRESSURE_LEVELS.find((p) => p.id === pressure)?.ms ?? 5000;
  const activeExercise = session.exercise;
  const pathname = usePathname();
  const { insights, dismiss } = useCoachProactive();
  const [coachOpen, setCoachOpen] = useState(false);
  const coach = useCoachCore();

  const handleCoachSelect = (prompt: string) => {
    setCoachOpen(true);
    setTimeout(() => coach.ask(prompt, { route: pathname || "/keigo", exerciseId: (activeExercise as any)?.id }), 300);
  };

  const playedPromptExerciseIdRef = useRef<string | null>(null);

  const playPromptAudio = useCallback(
    (autoTransition = false) => {
      if (!activeExercise) return;
      const rc = activeExercise.extra_metadata?.keigo_config || {};
      const text = rc.prompt || activeExercise.prompt || activeExercise.scenario || activeExercise.title;
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
    const text = transcriptInput.trim() || session.speech.transcript.trim();
    if (!text) return;
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

      if (matchesAction(e, "drillToggleHelp")) {
        e.preventDefault();
        setShowHelp((v) => !v);
      } else if (matchesAction(e, "drillRetry") && session.phase === "result") {
        e.preventDefault();
        soundFX.playSuikinkutsu();
        session.retry();
      } else if (matchesAction(e, "drillSkip") && session.phase === "result") {
        e.preventDefault();
        soundFX.playSuikinkutsu();
        session.startNext();
      } else if (e.key.toLowerCase() === "l" && session.phase !== "idle") {
        e.preventDefault();
        playPromptAudio(false);
      } else if (e.key === "Escape") {
        if (showCheatsheet) {
          setShowCheatsheet(false);
        } else if (showHelp) {
          setShowHelp(false);
        } else if (session.phase !== "idle") {
          session.setPhase("idle" as any);
          setShowSummary(false);
          stopWebSpeech();
        }
      } else if (matchesAction(e, "drillSubmitOrNext")) {
        e.preventDefault();
        if (session.phase === "ready") {
          session.startVoiceRecording();
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
  }, [session.phase, transcriptInput, session.speech.transcript, showCheatsheet, showHelp, matchesAction, playPromptAudio]);

  const formatSessionTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  if (showSummary || session.phase === "summary") {
    return (
      <div className="py-6 animate-in fade-in duration-300">
        <KeigoSessionSummary
          results={session.results}
          onRestart={() => {
            setShowSummary(false);
            soundFX.playSuikinkutsu();
            session.startSession();
          }}
          onToLobby={() => {
            setShowSummary(false);
            session.setPhase("idle" as any);
          }}
          onRetryWeak={() => {
            setShowSummary(false);
            soundFX.playSuikinkutsu();
            session.startSession();
          }}
        />
      </div>
    );
  }

  if (session.phase === "idle") {
    return (
      <div className="py-2">
        <KeigoLobby
          subMode={subMode}
          setSubMode={setSubMode}
          pressure={pressure}
          setPressure={setPressure}
          subtitleMode={subtitleMode}
          setSubtitleMode={setSubtitleMode}
          duration={duration}
          setDuration={setDuration}
          autoNext={autoNext}
          setAutoNext={setAutoNext}
          startTrigger={startTrigger}
          setStartTrigger={setStartTrigger}
          onStartSession={() => {
            soundFX.playKatana();
            session.startSession();
          }}
          onOpenCheatsheet={() => setShowCheatsheet(true)}
          onOpenHelp={() => setShowHelp(true)}
          error={session.error}
        />

        <KeigoCheatsheetModal isOpen={showCheatsheet} onClose={() => setShowCheatsheet(false)} />

        <Modal isOpen={showHelp} onClose={() => setShowHelp(false)} title="Bảng Phím Tắt Thao Tác">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
            <div className="rounded-xl border bg-muted/40 p-3 space-y-1">
              <div className="font-bold font-mono text-primary">{formatKeyDisplay(keybindings.drillSubmitOrNext)}</div>
              <div className="text-muted-foreground">Nộp bài / Chuyển câu tiếp theo (Submit / Next)</div>
            </div>
            <div className="rounded-xl border bg-muted/40 p-3 space-y-1">
              <div className="font-bold font-mono text-primary">
                {formatKeyDisplay(keybindings.drillRetry)} / {formatKeyDisplay(keybindings.drillSkip)}
              </div>
              <div className="text-muted-foreground">Thử lại câu này / Bỏ qua (Retry / Skip)</div>
            </div>
            <div className="rounded-xl border bg-muted/40 p-3 space-y-1">
              <div className="font-bold font-mono text-primary">L</div>
              <div className="text-muted-foreground">Nghe lại giọng đọc đề bài (Listen TTS)</div>
            </div>
            <div className="rounded-xl border bg-muted/40 p-3 space-y-1">
              <div className="font-bold font-mono text-primary">Esc</div>
              <div className="text-muted-foreground">Tạm dừng & Thoát về Sảnh chính (Exit)</div>
            </div>
          </div>
        </Modal>
      </div>
    );
  }

  const isEvaluating = session.phase === "evaluating" || session.phase === "loading";
  const isRecordingOrWaiting = session.phase === "waiting_for_speech" || session.phase === "recording";
  const currentSubModeInfo = KEIGO_SUB_MODES.find((m) => m.id === subMode) || KEIGO_SUB_MODES[0];

  return (
    <div className="max-w-5xl mx-auto space-y-4 animate-in fade-in duration-300 pb-8">
      {/* Session Top Status Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 rounded-2xl bg-card border border-border/80 washi-texture shadow-xs">
        <div className="flex items-center gap-2">
          <Badge variant={currentSubModeInfo.badgeVariant} size="sm" className="font-bold">
            {currentSubModeInfo.ja} • {currentSubModeInfo.label}
          </Badge>
          <div className="hidden sm:flex items-center gap-2 text-xs font-semibold text-muted-foreground">
            <span>•</span>
            <span>Đúng: <strong className="text-emerald-600 dark:text-emerald-400">{session.stats.correct}</strong>/{session.stats.total}</span>
            <span>•</span>
            <span>TB: <strong className="text-foreground">{session.stats.avgLatency ? Math.round(session.stats.avgLatency) : "—"}ms</strong></span>
          </div>
        </div>

        <div className="flex items-center gap-3 ml-auto">
          <div
            className={cn(
              "flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-bold border shadow-2xs",
              sessionRemainingSec <= 30
                ? "bg-rose-500/10 text-rose-600 border-rose-500/30 animate-pulse"
                : "bg-muted/60 text-foreground border-border"
            )}
          >
            <Clock className="h-3.5 w-3.5 text-primary" />
            <span>{formatSessionTime(sessionRemainingSec)}</span>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowCheatsheet(true)}
            className="h-8 gap-1 text-xs font-bold border-amber-500/30 text-amber-700 dark:text-amber-300 hover:bg-amber-500/10"
            title="Mở Sổ tay Kính ngữ"
          >
            <BookOpen className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Sổ tay</span>
          </Button>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              stopWebSpeech();
              session.setPhase("idle" as any);
              setShowSummary(false);
            }}
            className="h-8 text-xs font-bold text-muted-foreground hover:text-foreground"
          >
            Thoát (Esc)
          </Button>
        </div>
      </div>

      {/* Main Workout Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 items-start">
        {/* Left 2 Columns: Prompt & Result Arena */}
        <div className="lg:col-span-2 space-y-4">
          <KeigoPromptCard
            exercise={activeExercise}
            subtitleMode={subtitleMode}
            onPlayAudio={() => playPromptAudio(false)}
            phase={session.phase}
          />

          {isEvaluating && (
            <div className="p-5 rounded-3xl border border-primary/20 bg-primary/5 text-center space-y-2 animate-pulse washi-texture">
              <div className="flex items-center justify-center gap-2 font-bold text-sm text-primary">
                <Sparkles className="h-4 w-4 animate-spin" />
                <span>✨ Đang phân tích phản xạ & chuẩn mực Kính ngữ...</span>
              </div>
              <p className="text-xs text-muted-foreground">
                Kiểm tra hướng Tôn kính / Khiêm nhường, Uchi-Soto & Nhị trùng kính ngữ
              </p>
            </div>
          )}

          {session.phase === "result" && session.result && (
            <KeigoResultCard
              result={session.result}
              exercise={activeExercise}
              onNext={() => {
                soundFX.playSuikinkutsu();
                session.startNext();
              }}
              onRetry={() => {
                soundFX.playSuikinkutsu();
                session.retry();
              }}
              onAskCoach={handleCoachSelect}
              onCancelAutoNext={session.cancelAutoNext}
            />
          )}

          {session.phase === "ready" && (
            <div className="p-6 rounded-3xl border-2 border-primary/30 bg-card washi-texture text-center space-y-3 shadow-md">
              <div className="h-10 w-10 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center text-primary mx-auto">
                <Play className="h-5 w-5 fill-current ml-0.5" />
              </div>
              <div className="space-y-1">
                <h4 className="font-bold text-base text-foreground">Bạn đã sẵn sàng trả lời?</h4>
                <p className="text-xs text-muted-foreground">
                  Bấm nút bên dưới hoặc phím <kbd className="px-1.5 py-0.5 rounded bg-muted border text-[11px] font-mono font-bold">Space</kbd> để kích hoạt microphone và bắt đầu nói
                </p>
              </div>
              <Button
                variant="akane"
                size="lg"
                onClick={() => session.startVoiceRecording()}
                className="font-bold gap-2 text-sm shadow-md"
              >
                <Mic className="h-4 w-4" />
                <span>🎙️ Bắt Đầu Trả Lời</span>
              </Button>
            </div>
          )}
        </div>

        {/* Right 1 Column: Timer & Speech Controls */}
        <div className="space-y-4">
          <KeigoTimer
            remainingMs={session.timer.remainingMs}
            timerLimitMs={session.timer.isActive ? timerMs : activeExercise?.timerLimitMs ?? timerMs}
            progress={session.timer.progress}
            state={session.timer.state}
            isActive={session.timer.isActive}
          />

          <div className="p-4 rounded-3xl border border-border/80 bg-card shadow-xs washi-texture space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-foreground flex items-center gap-1.5">
                <Mic className="h-3.5 w-3.5 text-primary" />
                <span>Giọng Nói & Nhập Liệu</span>
              </span>
              <button
                onClick={() => setShowTextInput((v) => !v)}
                className="text-[11px] font-bold text-primary hover:underline flex items-center gap-1"
              >
                <Edit3 className="h-3 w-3" />
                <span>{showTextInput ? "Dùng Mic" : "Gõ phím"}</span>
              </button>
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-[11px] text-muted-foreground">
                <span>Âm lượng mic:</span>
                <span className="font-bold font-mono">
                  {session.isUserSpeaking ? "Đang nói..." : `${Math.round(session.recorder.volumeLevel * 100)}%`}
                </span>
              </div>
              <div className="h-2 w-full bg-muted rounded-full overflow-hidden border border-border/60">
                <div
                  className={cn(
                    "h-full transition-all duration-75",
                    session.isUserSpeaking ? "bg-emerald-500" : "bg-primary"
                  )}
                  style={{ width: `${Math.min(100, Math.round(session.recorder.volumeLevel * 100))}%` }}
                />
              </div>
            </div>

            <div className="p-3 rounded-2xl bg-muted/40 border border-border/60 min-h-[58px] flex flex-col justify-center space-y-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                Nhận diện trực tiếp (ja-JP):
              </span>
              <div className="text-xs font-bold font-jp text-foreground">
                {session.speech.transcript ? (
                  <span>“{session.speech.transcript}”</span>
                ) : isRecordingOrWaiting ? (
                  <span className="text-muted-foreground italic font-sans font-normal animate-pulse">
                    Đang lắng nghe giọng nói tiếng Nhật của bạn...
                  </span>
                ) : (
                  <span className="text-muted-foreground italic font-sans font-normal">Chờ kích hoạt mic</span>
                )}
              </div>
            </div>

            {showTextInput && (
              <div className="space-y-2 pt-1">
                <textarea
                  value={transcriptInput}
                  onChange={(e) => setTranscriptInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleDirectSubmit();
                    }
                  }}
                  placeholder="Nhập câu kính ngữ của bạn (VD: ご覧になります / 拝見いたします)..."
                  className="w-full rounded-xl border bg-background p-2.5 text-xs font-jp min-h-[64px] focus:border-primary focus:ring-1 focus:ring-primary/20"
                />
              </div>
            )}

            <div className="pt-1 flex gap-2">
              <Button
                size="sm"
                variant="akane"
                className="flex-1 font-bold text-xs"
                onClick={handleDirectSubmit}
                disabled={isEvaluating}
              >
                Gửi câu trả lời (Enter)
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="font-bold text-xs"
                onClick={() => session.skip()}
                disabled={isEvaluating}
              >
                Bỏ qua
              </Button>
            </div>
          </div>

          {insights.length > 0 && (
            <CoachInsightCard
              insight={insights[0]}
              onDismiss={() => dismiss(insights[0].id)}
              onAction={(ins) => handleCoachSelect(ins.recommended_action || ins.description)}
            />
          )}
        </div>
      </div>

      <KeigoCheatsheetModal isOpen={showCheatsheet} onClose={() => setShowCheatsheet(false)} />

      <Modal isOpen={showHelp} onClose={() => setShowHelp(false)} title="Bảng Phím Tắt Thao Tác">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
          <div className="rounded-xl border bg-muted/40 p-3 space-y-1">
            <div className="font-bold font-mono text-primary">{formatKeyDisplay(keybindings.drillSubmitOrNext)}</div>
            <div className="text-muted-foreground">Nộp bài / Chuyển câu tiếp theo (Submit / Next)</div>
          </div>
          <div className="rounded-xl border bg-muted/40 p-3 space-y-1">
            <div className="font-bold font-mono text-primary">
              {formatKeyDisplay(keybindings.drillRetry)} / {formatKeyDisplay(keybindings.drillSkip)}
            </div>
            <div className="text-muted-foreground">Thử lại câu này / Bỏ qua (Retry / Skip)</div>
          </div>
          <div className="rounded-xl border bg-muted/40 p-3 space-y-1">
            <div className="font-bold font-mono text-primary">L</div>
            <div className="text-muted-foreground">Nghe lại giọng đọc đề bài (Listen TTS)</div>
          </div>
          <div className="rounded-xl border bg-muted/40 p-3 space-y-1">
            <div className="font-bold font-mono text-primary">Esc</div>
            <div className="text-muted-foreground">Tạm dừng & Thoát về Sảnh chính (Exit)</div>
          </div>
        </div>
      </Modal>

      <CoachPanel open={coachOpen} onClose={() => setCoachOpen(false)} />
    </div>
  );
}
"""

FILES = {
    r"E:\SpeakingTraining\apps\web\features\keigo\components\KeigoLobby.tsx": LOBBY_CONTENT,
    r"E:\SpeakingTraining\apps\web\features\keigo\components\KeigoPromptCard.tsx": PROMPT_CARD_CONTENT,
    r"E:\SpeakingTraining\apps\web\features\keigo\components\KeigoResultCard.tsx": RESULT_CARD_CONTENT,
    r"E:\SpeakingTraining\apps\web\features\keigo\components\KeigoSessionSummary.tsx": SESSION_SUMMARY_CONTENT,
    r"E:\SpeakingTraining\apps\web\features\keigo\components\KeigoCheatsheetModal.tsx": CHEATSHEET_CONTENT,
    r"E:\SpeakingTraining\apps\web\app\keigo\page.tsx": PAGE_CONTENT,
}

for filepath, content in FILES.items():
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"Successfully wrote {os.path.basename(filepath)}")

print("All 6 files reverted to Vietnamese UI while keeping submode titles in Japanese!")
