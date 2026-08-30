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
  { mins: 0, label: "∞ Vô hạn • Tự do (Không giới hạn)" },
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
              Tự do gõ bất kỳ bối cảnh nào bạn muốn hoặc để AI sáng tạo ngẫu nhiên vô hạn từ mọi khía cạnh đời sống, văn hóa, công sở và pháp lý tại Nhật Bản.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5 shrink-0 self-start md:self-auto">
            <Button
              variant="akane"
              size="sm"
              onClick={handle1ClickRandom}
              disabled={isLoading}
              className="text-xs font-bold gap-1.5 shadow-md rounded-xl h-9 px-4"
            >
              <Dice5 className="h-4 w-4 animate-spin-slow" />
              <span>🎲 Ngẫu Nhiên 1 Chạm</span>
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                soundFX.playFurin();
                onOpenCheatsheet();
              }}
              className="text-xs font-bold gap-1.5 border-emerald-500/30 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-500/10 shadow-2xs rounded-xl h-9"
            >
              <BookOpen className="h-3.5 w-3.5" />
              <span>Sổ tay (C)</span>
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                soundFX.playFurin();
                onOpenKeybindings();
              }}
              className="text-xs font-bold gap-1.5 shadow-2xs rounded-xl h-9"
            >
              <Keyboard className="h-3.5 w-3.5" />
              <span>Phím tắt (?)</span>
            </Button>
          </div>
        </div>
      </div>

      {/* Custom Topic Builder Section */}
      <div className="p-6 rounded-3xl border border-primary/30 bg-card washi-texture shadow-sm space-y-4 relative overflow-hidden ring-1 ring-primary/20">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Wand2 className="h-5 w-5 text-primary" />
            <h2 className="text-sm font-bold text-foreground">
              ✨ Tùy Chọn Bối Cảnh / Tình Huống Tự Do Hoặc Ngẫu Nhiên
            </h2>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handle1ClickRandom}
              className="h-7 text-xs font-bold border-amber-500/40 text-amber-700 dark:text-amber-300 hover:bg-amber-500/10 gap-1 rounded-lg"
            >
              <Dice5 className="h-3.5 w-3.5 text-amber-500" />
              <span>🎲 Tạo ngẫu nhiên (Không nhập gì)</span>
            </Button>
            <Badge variant="kintsugi" size="sm" className="font-bold">
              INFINITE AI
            </Badge>
          </div>
        </div>

        <p className="text-xs text-muted-foreground">
          Bạn có thể <strong>gõ bất kỳ bối cảnh nào</strong> (VD: <em>Đi phỏng vấn baito, Thuê nhà ở Tokyo...</em>) hoặc bấm <strong>"🎲 Tạo ngẫu nhiên"</strong> để AI tự chọn 1 tình huống bất ngờ chưa từng gặp:
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
              placeholder="VD: Đi phỏng vấn xin việc baito, Thuê nhà trọ tại Shinjuku, Đổi hàng trên Mercari, Đi cắt tóc... (hoặc để trống để AI tự tạo ngẫu nhiên)"
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

          <Button
            variant="outline"
            size="sm"
            onClick={handlePickRandomSuggestion}
            className="text-xs font-bold gap-1.5 rounded-2xl px-4 h-11 shrink-0 border-border"
            title="Đổi một gợi ý ngẫu nhiên vào ô nhập"
          >
            <Dice5 className="h-3.5 w-3.5 text-primary" />
            <span>Đổi Gợi Ý</span>
          </Button>
        </div>

        {/* Quick Suggestion Tags */}
        <div className="space-y-1.5 pt-1">
          <div className="text-[11px] font-bold text-muted-foreground">
            Hoặc bấm 1 chạm vào các bối cảnh đời sống Nhật phổ biến bên dưới:
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

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="lg"
            onClick={handle1ClickRandom}
            disabled={isLoading}
            className="font-bold text-xs gap-2 px-5 h-12 rounded-2xl border-amber-500/40 text-amber-700 dark:text-amber-300 hover:bg-amber-500/10 shrink-0"
          >
            <Dice5 className="h-4 w-4 text-amber-500" />
            <span>🎲 Ngẫu Nhiên (Không Cần Chọn)</span>
          </Button>

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
    </div>
  );
}
