"use client";

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
    icon: <Sparkles className="h-4 w-4 text-amber-500" />,
    isSpecial: true,
  },
  {
    id: "food",
    jaTitle: "飲食・居酒屋",
    viTitle: "Ẩm Thực & Quán Nhậu",
    badge: "飲食",
    desc: "Đặt bàn, gọi món, yêu cầu đổi món do dị ứng, tách hóa đơn betsu-betsu",
    icon: <Utensils className="h-4 w-4 text-amber-500" />,
  },
  {
    id: "retail",
    jaTitle: "買い物・コンビニ",
    viTitle: "Mua Sắm & Konbini",
    badge: "店舗",
    desc: "Hâm nóng bento, từ chối túi nilon, rút tiền ATM, gửi bưu kiện",
    icon: <ShoppingBag className="h-4 w-4 text-emerald-500" />,
  },
  {
    id: "transportation",
    jaTitle: "交通・駅・空港",
    viTitle: "Giao Thông & Nhà Ga",
    badge: "交通",
    desc: "Mua vé Shinkansen ghế chỉ định, hỏi cửa chuyển tàu, nạp thẻ Suica",
    icon: <Train className="h-4 w-4 text-sky-500" />,
  },
  {
    id: "healthcare",
    jaTitle: "医療・薬局・緊急",
    viTitle: "Y Tế & Hiệu Thuốc & Khẩn Cấp",
    badge: "医療",
    desc: "Mô tả triệu chứng bệnh, mua thuốc tại Yakkyoku, báo rơi đồ tại Kouban",
    icon: <HeartPulse className="h-4 w-4 text-rose-500" />,
  },
  {
    id: "workplace",
    jaTitle: "ビジネス・職場",
    viTitle: "Công Sở & Đàm Phán",
    badge: "仕事",
    desc: "Tiếp đối tác, trao đổi danh thiếp Meishi, báo cáo tiến độ Hou-Ren-So",
    icon: <Briefcase className="h-4 w-4 text-purple-500" />,
  },
  {
    id: "travel",
    jaTitle: "ホテル・観光・旅行",
    viTitle: "Khách Sạn & Du Lịch",
    badge: "観光",
    desc: "Check-in khách sạn, gửi hành lý, hỏi gợi ý điểm tham quan, đặt tour",
    icon: <Hotel className="h-4 w-4 text-cyan-500" />,
  },
];

export const QUICK_SUGGESTION_TAGS = [
  { label: "🏠 Thuê nhà & Cọc tiền", prompt: "Thuê căn hộ 1DK tại Tokyo qua công ty bất động sản, hỏi tiền cọc Shikikin và Reikin" },
  { label: "💼 Phỏng vấn Baito quán ăn", prompt: "Phỏng vấn xin việc làm thêm tại quán mì Ramen, hỏi lịch làm Shifuto và mức lương" },
  { label: "🏛️ Đăng ký cư trú Shiyakusho", prompt: "Đến ủy ban Shiyakusho làm thủ tục chuyển địa chỉ cư trú Juuminhyou và bảo hiểm quốc dân" },
  { label: "💇 Tiệm cắt tóc Omotesando", prompt: "Cắt tóc tại salon Nhật, yêu cầu cắt ngắn hai bên và tỉa ngọn tự nhiên" },
  { label: "📦 Chợ đồ cũ Mercari", prompt: "Thương lượng giảm giá món đồ trên Mercari và hẹn phương thức nhận hàng" },
  { label: "🗑️ Phân loại rác Sodai Gomi", prompt: "Hỏi hàng xóm người Nhật cách phân loại rác cồng kềnh Sodai Gomi và lịch vứt rác" },
];

export const CHALLENGE_MODES = [
  { id: "standard", label: "標準 (Standard)", desc: "Hiện mục tiêu rõ ràng" },
  { id: "guided", label: "誘導付き (Guided)", desc: "Kèm mẫu câu gợi ý" },
  { id: "challenge", label: "挑戦 (Challenge)", desc: "Ẩn mục tiêu kế tiếp" },
  { id: "blind", label: "暗中模索 (Blind)", desc: "Ẩn toàn bộ mục tiêu" },
];

export const PRESSURE_OPTIONS: { id: SituationsPressureLevel; label: string; limit: string; desc: string }[] = [
  { id: "infinite", label: "∞ Vô hạn", limit: "∞", desc: "Không giới hạn thời gian" },
  { id: "relaxed", label: "6s Thư thái", limit: "6.0s", desc: "Dễ thở, suy nghĩ kỹ" },
  { id: "normal", label: "5s Chuẩn", limit: "5.0s", desc: "Tốc độ giao tiếp tự nhiên" },
  { id: "fast", label: "4s Nhanh", limit: "4.0s", desc: "Phản xạ nhanh nhạy" },
  { id: "reflex", label: "3s Cực hạn", limit: "3.0s", desc: "Áp lực thực chiến cao" },
];

export const DURATION_OPTIONS = [
  { mins: 0, label: "∞ Vô hạn" },
  { mins: 3, label: "3 phút" },
  { mins: 5, label: "5 phút" },
  { mins: 10, label: "10 phút" },
  { mins: 15, label: "15 phút" },
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
  const [isCustomOpen, setIsCustomOpen] = useState(Boolean(customTopic));
  const [isAdvancedOpen, setIsAdvancedOpen] = useState(false);

  const handleApplyCustomTopic = () => {
    if (localInput.trim()) {
      soundFX.playSuikinkutsu();
      onSelectCustomTopic(localInput.trim());
      onSelectCategory("custom");
    }
  };

  const handle1ClickRandom = () => {
    soundFX.playKatana();
    onSelectCustomTopic("");
    setLocalInput("");
    onSelectCategory("infinite");
    onStartSession();
  };

  const handlePickRandomSuggestion = () => {
    soundFX.playFurin();
    const item = QUICK_SUGGESTION_TAGS[Math.floor(Math.random() * QUICK_SUGGESTION_TAGS.length)];
    setLocalInput(item.prompt);
    onSelectCustomTopic(item.prompt);
    onSelectCategory("custom");
  };

  const selectedCatObj = SITUATIONAL_CATEGORIES.find((c) => c.id === selectedCategory);

  return (
    <div className="max-w-5xl mx-auto space-y-4 animate-in fade-in duration-300 pb-8">
      {/* Top Banner Haru Washi */}
      <div className="relative overflow-hidden rounded-2xl border border-border bg-card p-4 sm:p-5 washi-texture shadow-2xs space-y-3">
        <div className="absolute top-0 right-0 h-32 w-32 bg-emerald-500/10 rounded-full blur-2xl pointer-events-none" />

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 relative z-10">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Badge variant="matcha" size="sm" className="font-bold text-[10px]">
                MODE 4 • SITUATIONAL ROLEPLAY
              </Badge>
              <span className="text-[11px] text-muted-foreground font-semibold">
                AI Phản Xạ Nhập Vai Thực Chiến
              </span>
            </div>
            <h1 className="text-xl sm:text-2xl font-black text-foreground tracking-tight flex items-center gap-2">
              <span className="p-1.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 inline-flex">
                <Compass className="h-5 w-5" />
              </span>
              <span>Tình Huống Thực Chiến (場面英会話)</span>
            </h1>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <Button
              variant="akane"
              size="sm"
              onClick={handle1ClickRandom}
              disabled={isLoading}
              className="text-xs font-bold gap-1.5 shadow-md rounded-xl h-8 px-3.5"
            >
              <Dice5 className="h-3.5 w-3.5 animate-spin-slow" />
              <span>🎲 Ngẫu Nhiên 1-Chạm</span>
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                soundFX.playFurin();
                onOpenCheatsheet();
              }}
              className="text-xs font-bold gap-1 border-emerald-500/30 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-500/10 shadow-2xs rounded-xl h-8 px-2.5"
            >
              <BookOpen className="h-3 w-3" />
              <span>Sổ tay</span>
            </Button>
          </div>
        </div>
      </div>

      {/* Section 1: Category Cards Grid */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-bold text-foreground flex items-center gap-1.5">
            <Sliders className="h-3.5 w-3.5 text-primary" />
            <span>1. Chọn Bối Cảnh Luyện Tập:</span>
          </h2>

          <button
            type="button"
            onClick={() => setIsCustomOpen((v) => !v)}
            className="text-[11px] font-bold text-primary hover:underline flex items-center gap-1"
          >
            <Wand2 className="h-3 w-3" />
            <span>{isCustomOpen ? "Đóng tự chọn bối cảnh" : "✨ Nhập bối cảnh tự do / Gợi ý"}</span>
          </button>
        </div>

        {/* Custom Topic Drawer (Collapsible) */}
        {isCustomOpen && (
          <div className="p-3.5 rounded-2xl border border-primary/30 bg-card washi-texture shadow-xs space-y-2.5 animate-in fade-in duration-150">
            <div className="flex flex-col sm:flex-row gap-2">
              <input
                value={localInput}
                onChange={(e) => setLocalInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    handleApplyCustomTopic();
                  }
                }}
                placeholder="VD: Đi phỏng vấn xin việc baito, Thuê nhà trọ tại Shinjuku, Đổi hàng trên Mercari..."
                className="flex-1 bg-background border border-border rounded-xl px-3 py-2 text-xs focus:outline-none focus:border-primary placeholder:text-muted-foreground"
              />
              <div className="flex gap-1.5 shrink-0">
                <Button
                  variant="akane"
                  size="sm"
                  onClick={handleApplyCustomTopic}
                  disabled={!localInput.trim()}
                  className="text-xs font-bold gap-1 rounded-xl h-8 px-3"
                >
                  <Send className="h-3 w-3" />
                  <span>Áp Dụng</span>
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handlePickRandomSuggestion}
                  className="text-xs font-bold gap-1 rounded-xl h-8 px-2.5 border-border"
                >
                  <Dice5 className="h-3 w-3 text-primary" />
                  <span>Đổi Gợi Ý</span>
                </Button>
              </div>
            </div>

            {/* Quick Suggestion Tags Chips */}
            <div className="flex flex-wrap gap-1">
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
                    "px-2 py-0.5 rounded-lg border text-[10px] font-semibold transition-all",
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
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
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
                  "p-3 rounded-2xl border transition-all cursor-pointer bg-card washi-texture space-y-1 hover:shadow-xs",
                  cat.isSpecial && "border-amber-500/50 bg-amber-500/5",
                  isSelected
                    ? "border-primary ring-1 ring-primary/30 bg-primary/5 shadow-2xs"
                    : "border-border hover:border-primary/40"
                )}
              >
                <div className="flex items-center justify-between gap-1.5">
                  <div className="flex items-center gap-2 min-w-0">
                    <div className="p-1.5 rounded-lg bg-muted/60 border border-border/80 shrink-0">
                      {cat.icon}
                    </div>
                    <div className="min-w-0 truncate">
                      <div className="text-xs font-bold text-foreground font-jp truncate">{cat.jaTitle}</div>
                      <div className="text-[10px] text-muted-foreground font-medium truncate">{cat.viTitle}</div>
                    </div>
                  </div>
                  <Badge variant={isSelected ? "matcha" : cat.isSpecial ? "kintsugi" : "outline"} size="sm" className="font-mono text-[9px] px-1.5 py-0">
                    {cat.badge}
                  </Badge>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Section 2: Fast Cockpit Controls (Segmented Bar) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {/* Pressure Level Segmented Control */}
        <div className="p-3.5 rounded-2xl border border-border bg-card washi-texture space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-xs font-bold text-foreground flex items-center gap-1.5">
              <Zap className="h-3.5 w-3.5 text-amber-500" />
              <span>Áp Lực Thời Gian Phản Xạ</span>
            </label>
            <span className="text-[10px] font-mono font-bold text-primary">
              {PRESSURE_OPTIONS.find((p) => p.id === pressureLevel)?.limit || "5.0s"}
            </span>
          </div>

          <div className="flex items-center gap-1 p-1 rounded-xl bg-muted/50 border border-border">
            {PRESSURE_OPTIONS.map((p) => (
              <button
                key={p.id}
                type="button"
                onClick={() => {
                  soundFX.playFurin();
                  onSelectPressureLevel(p.id);
                }}
                className={cn(
                  "flex-1 py-1 text-center rounded-lg text-[11px] font-bold transition-all",
                  pressureLevel === p.id
                    ? "bg-card text-foreground border border-border shadow-2xs"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>

        {/* Duration Segmented Control */}
        <div className="p-3.5 rounded-2xl border border-border bg-card washi-texture space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-xs font-bold text-foreground flex items-center gap-1.5">
              <Clock className="h-3.5 w-3.5 text-sky-500" />
              <span>Thời Lượng Phiên Luyện</span>
            </label>
            <span className="text-[10px] font-bold text-primary">
              {duration === 0 ? "∞ Không giới hạn" : `${duration} phút`}
            </span>
          </div>

          <div className="flex items-center gap-1 p-1 rounded-xl bg-muted/50 border border-border">
            {DURATION_OPTIONS.map((d) => (
              <button
                key={d.mins}
                type="button"
                onClick={() => {
                  soundFX.playFurin();
                  onSelectDuration(d.mins);
                }}
                className={cn(
                  "flex-1 py-1 text-center rounded-lg text-[11px] font-bold transition-all",
                  duration === d.mins
                    ? "bg-card text-foreground border border-border shadow-2xs"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                {d.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Progressive Disclosure: Subtitles & Challenge Mode Accordion */}
      <div className="border border-border/80 rounded-2xl bg-muted/20 overflow-hidden">
        <button
          type="button"
          onClick={() => setIsAdvancedOpen((v) => !v)}
          className="w-full px-3.5 py-2 flex items-center justify-between text-[11px] font-bold text-muted-foreground hover:text-foreground hover:bg-muted/40 transition-colors"
        >
          <span className="flex items-center gap-1.5">
            <Shield className="h-3.5 w-3.5 text-emerald-500" />
            <span>Tùy chọn phụ đề & Chế độ thử thách mục tiêu</span>
          </span>
          <span className="text-[10px] font-semibold text-primary">
            {isAdvancedOpen ? "Thu gọn ▲" : "Mở rộng ▼"}
          </span>
        </button>

        {isAdvancedOpen && (
          <div className="p-3.5 pt-1 space-y-3 border-t border-border/60 animate-in fade-in duration-150 grid grid-cols-1 md:grid-cols-2 gap-3">
            {/* Subtitles */}
            <div className="space-y-1.5">
              <label className="text-[11px] font-bold text-muted-foreground">Phụ đề hiển thị:</label>
              <div className="grid grid-cols-2 gap-1.5">
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
                      "p-2 rounded-xl border text-left text-[11px] font-semibold transition-all",
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

            {/* Challenge Mode */}
            <div className="space-y-1.5">
              <label className="text-[11px] font-bold text-muted-foreground">Chế độ mục tiêu:</label>
              <div className="grid grid-cols-2 gap-1.5">
                {CHALLENGE_MODES.map((m) => (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() => {
                      soundFX.playFurin();
                      onSelectMode(m.id);
                    }}
                    className={cn(
                      "p-2 rounded-xl border text-left transition-all space-y-0.5",
                      selectedMode === m.id
                        ? "bg-primary/10 border-primary shadow-xs"
                        : "bg-muted/30 border-border hover:border-primary/40"
                    )}
                  >
                    <div className="text-[11px] font-bold text-foreground">{m.label}</div>
                    <div className="text-[9px] text-muted-foreground">{m.desc}</div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Start Button Bar */}
      <div className="p-3.5 sm:p-4 rounded-2xl border border-border bg-card washi-texture flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xs">
        <div className="space-y-0.5">
          <div className="text-[10px] font-bold text-muted-foreground uppercase">SẴN SÀNG NHẬP VAI:</div>
          <div className="text-xs font-bold text-foreground">
            Bối cảnh:{" "}
            <span className="text-primary font-jp font-bold">
              {customTopic ? `"${customTopic}"` : selectedCatObj?.jaTitle || "無限・AI Random"}
            </span>
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
          className="font-bold text-xs gap-2 rounded-xl shadow-md h-10 px-6 ml-auto"
        >
          <Play className="h-4 w-4 fill-current ml-0.5" />
          <span>Bắt Đầu Tình Huống (Enter)</span>
        </Button>
      </div>
    </div>
  );
}
