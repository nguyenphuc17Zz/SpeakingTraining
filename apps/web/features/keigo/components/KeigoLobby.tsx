"use client";

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
