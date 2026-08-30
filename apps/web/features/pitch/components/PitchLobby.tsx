"use client";

import React from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Music,
  Shuffle,
  Volume2,
  Clock,
  Zap,
  BookOpen,
  Keyboard,
  CheckCircle2,
  Sparkles,
  HelpCircle,
} from "lucide-react";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

export interface PitchSubModeItem {
  id: string;
  label: string;
  ja: string;
  badgeVariant: "sakura" | "matcha" | "fuji" | "kintsugi" | "torii" | "akane" | "jlpt";
  desc: string;
  example: string;
}

export const PITCH_SUB_MODES: PitchSubModeItem[] = [
  {
    id: "mixed",
    label: "Luyện Tổng Hợp Thích Ứng",
    ja: "総合特訓 (Mixed Adaptive)",
    badgeVariant: "kintsugi",
    desc: "Hệ thống AI tự động phân tích điểm yếu và đảo ngẫu nhiên 5 dạng bài",
    example: "雨 vs 飴, 拍長, 無声化, 音調曲線, 聞き分け",
  },
  {
    id: "pitch_minimal_pair",
    label: "Cặp Từ Tối Thiểu (Minimal Pairs)",
    ja: "最小対比 (Minimal Pairs)",
    badgeVariant: "sakura",
    desc: "Phân biệt cặp từ đồng âm cùng cách đọc Hiragana nhưng khác cao độ Tokyo",
    example: "雨 [1] (Mưa) vs 飴 [0] (Kẹo) • 箸 [1] vs 橋 [2]",
  },
  {
    id: "mora_length",
    label: "Độ Dài Phách (Mora Timing)",
    ja: "拍の長さ (Mora Length)",
    badgeVariant: "matcha",
    desc: "Luyện nhịp phách trường âm, âm ngắt, âm đôi đều đặn chuẩn nhịp người bản xứ",
    example: "おじさん (4 mora) vs おじいさん (5 mora) • 来て vs 切って",
  },
  {
    id: "vowel_devoicing",
    label: "Vô Thanh Hóa Nguyên Âm",
    ja: "母音無声化 (Vowel Devoicing)",
    badgeVariant: "fuji",
    desc: "Luyện phản xạ nuốt thanh nguyên âm i/u khi đứng giữa phụ âm vô thanh k,s,t,h,p",
    example: "です (âm su vô thanh) • ました (âm shi vô thanh) • 好き",
  },
  {
    id: "pitch_contour",
    label: "Đường Cao Độ Tokyo (Pitch Contour)",
    ja: "音調アクセント (Pitch Contour)",
    badgeVariant: "torii",
    desc: "Luyện 4 mô hình cao độ chuẩn: 平板 [0], 頭高 [1], 中高 [2], 尾高 [3]",
    example: "日本語 (L-H-H-H) • ありがとう (L-H-L-L) • 寿司 (H-L)",
  },
  {
    id: "pitch_recognition",
    label: "Luyện Tai Nghe Phân Biệt",
    ja: "聞き分けクイズ (Pitch Recognition)",
    badgeVariant: "akane",
    desc: "Nghe phát âm từ vựng và phản xạ chọn nhanh nghĩa chuẩn tương ứng",
    example: "Nghe phát âm 'はし' ➔ Chọn Đũa [1] hay Cầu [2]",
  },
];

export const PITCH_PRESSURE_LEVELS = [
  { id: "relaxed", label: "🐢 Dễ (6.0s)", ms: 6000, desc: "Thoải mái luyện nghe và uốn giọng" },
  { id: "normal", label: "🚶 Tiêu chuẩn (5.0s)", ms: 5000, desc: "Áp lực tự nhiên như giao tiếp hàng ngày" },
  { id: "fast", label: "🏃 Nhanh (4.0s)", ms: 4000, desc: "Tăng tốc độ phản xạ cao độ" },
  { id: "reflex", label: "⚡ Phản xạ (3.0s)", ms: 3000, desc: "Phát âm ngay khi nghe xong" },
  { id: "extreme", label: "🔥 Cực hạn (2.0s)", ms: 2000, desc: "Thử thách phản xạ âm vị đỉnh cao" },
];

export const PITCH_DURATIONS = [
  { min: 0, label: "∞ Vô hạn", desc: "Không giới hạn thời gian" },
  { min: 3, label: "3 phút", desc: "Khởi động nhanh" },
  { min: 5, label: "5 phút", desc: "Tiêu chuẩn mỗi ngày" },
  { min: 10, label: "10 phút", desc: "Luyện chuyên sâu" },
  { min: 20, label: "20 phút", desc: "Thử thách bền bỉ" },
];

interface PitchLobbyProps {
  subMode: string;
  setSubMode: (v: string) => void;
  pressure: string;
  setPressure: (v: any) => void;
  subtitleMode: "hidden" | "japanese" | "japanese_reading" | "vietnamese";
  setSubtitleMode: (v: any) => void;
  duration: 0 | 3 | 5 | 10 | 20;
  setDuration: (v: 0 | 3 | 5 | 10 | 20) => void;
  autoNext: boolean;
  setAutoNext: (v: boolean) => void;
  onStartSession: () => void;
  onOpenCheatsheet: () => void;
  onOpenHelp: () => void;
  error?: string | null;
}

export function PitchLobby({
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
}: PitchLobbyProps) {
  const currentSubMode = PITCH_SUB_MODES.find((m) => m.id === subMode) || PITCH_SUB_MODES[0];

  return (
    <div className="space-y-6 max-w-5xl mx-auto animate-in fade-in duration-300 pb-10">
      {/* Hero Zen Banner */}
      <div className="relative overflow-hidden rounded-3xl border border-border bg-card p-6 md:p-8 washi-texture shadow-sm">
        <div className="absolute -top-12 -right-12 h-44 w-44 rounded-full bg-primary/10 blur-2xl pointer-events-none" />
        <div className="relative flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="h-12 w-12 rounded-2xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-600 dark:text-sky-400 shrink-0 shadow-2xs">
              <Music className="h-6 w-6" />
            </div>
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-black tracking-tight text-foreground">
                  Phòng Luyện Cao Độ & Phách
                </h1>
                <Badge variant="fuji" size="sm" className="font-mono font-bold">Mode 3</Badge>
              </div>
              <p className="text-sm text-muted-foreground max-w-2xl leading-relaxed">
                Rèn luyện cao độ chuẩn Tokyo (Pitch Accent), nhịp phách Mora đều đặn và hiện tượng vô thanh hóa nguyên âm không lẫn tạp âm.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 self-start md:self-auto shrink-0">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                soundFX.playFurin();
                onOpenCheatsheet();
              }}
              className="gap-1.5 text-xs font-bold border-sky-500/30 text-sky-700 dark:text-sky-300 hover:bg-sky-500/10 shadow-2xs"
            >
              <BookOpen className="h-3.5 w-3.5" />
              <span>Sổ tay Cao độ</span>
            </Button>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                soundFX.playFurin();
                onOpenHelp();
              }}
              className="gap-1.5 text-xs font-bold text-muted-foreground hover:text-foreground"
            >
              <HelpCircle className="h-3.5 w-3.5" />
              <span>Phím tắt (?)</span>
            </Button>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-2xl border border-destructive/40 bg-destructive/10 text-destructive text-xs font-semibold animate-in shake">
          {error}
        </div>
      )}

      {/* 2-Column Grid: Submode Selection & Session Config */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Left 2 Cols: 6 Submodes */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-primary" />
              <h2 className="text-sm font-bold text-foreground">Chuyên Đề Luyện Tập (6 Chế Độ)</h2>
            </div>
            <span className="text-xs text-muted-foreground font-semibold">Chọn 1 chuyên đề</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {PITCH_SUB_MODES.map((m) => {
              const isSelected = subMode === m.id;
              const isMixed = m.id === "mixed";
              return (
                <button
                  key={m.id}
                  type="button"
                  onClick={() => {
                    soundFX.playFurin();
                    setSubMode(m.id);
                  }}
                  className={cn(
                    "text-left p-4 rounded-2xl border transition-all duration-200 relative group flex flex-col justify-between bg-card shadow-2xs hover:border-primary/40",
                    isMixed ? "sm:col-span-2 bg-gradient-to-r from-card to-primary/5 border-primary/30" : "",
                    isSelected
                      ? "border-primary ring-2 ring-primary/20 bg-primary/5 shadow-sm"
                      : "hover:bg-muted/40"
                  )}
                >
                  <div className="space-y-1.5 w-full">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm font-bold text-foreground flex items-center gap-1.5">
                        {isMixed && <Shuffle className="h-3.5 w-3.5 text-primary" />}
                        {m.ja}
                      </span>
                      <Badge variant={m.badgeVariant} size="sm">
                        {m.label.split(" ")[0]}
                      </Badge>
                    </div>

                    <p className="text-xs text-muted-foreground leading-snug">
                      {m.desc}
                    </p>
                  </div>

                  <div className="mt-3 pt-2.5 border-t border-border/60 flex items-center justify-between text-[11px] text-muted-foreground font-jp">
                    <span className="truncate max-w-[280px]">Ví dụ: {m.example}</span>
                    {isSelected && (
                      <CheckCircle2 className="h-4 w-4 text-primary shrink-0 ml-2" />
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right 1 Col: Session Configuration */}
        <div className="space-y-5 p-5 rounded-3xl border border-border/80 bg-card shadow-xs washi-texture">
          <div className="space-y-1">
            <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
              <Volume2 className="h-4 w-4 text-primary" />
              <span>Cấu Hình Phiên Luyện Tập</span>
            </h3>
            <p className="text-xs text-muted-foreground">Tùy chỉnh áp lực thời gian và chế độ hiển thị</p>
          </div>

          {/* Time Pressure Selector */}
          <div className="space-y-2">
            <label className="text-xs font-bold text-foreground">Áp Lực Thời Gian:</label>
            <div className="grid grid-cols-1 gap-1.5">
              {PITCH_PRESSURE_LEVELS.map((p) => {
                const isActive = pressure === p.id;
                return (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => {
                      soundFX.playFurin();
                      setPressure(p.id as any);
                    }}
                    className={cn(
                      "w-full text-left p-2.5 rounded-xl border text-xs transition-all flex items-center justify-between",
                      isActive
                        ? "border-primary bg-primary/10 font-bold text-primary shadow-2xs"
                        : "border-border/70 hover:bg-muted/50 text-foreground"
                    )}
                  >
                    <span>{p.label}</span>
                    <span className="text-[10px] text-muted-foreground font-normal">{p.desc}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Session Duration Selector */}
          <div className="space-y-2">
            <label className="text-xs font-bold text-foreground">Thời Lượng Phiên:</label>
            <div className="grid grid-cols-4 gap-1.5">
              {PITCH_DURATIONS.map((d) => (
                <button
                  key={d.min}
                  type="button"
                  onClick={() => {
                    soundFX.playFurin();
                    setDuration(d.min as any);
                  }}
                  className={cn(
                    "py-2 rounded-xl border text-xs font-bold transition-all text-center",
                    duration === d.min
                      ? "border-primary bg-primary text-primary-foreground shadow-2xs"
                      : "border-border/70 bg-muted/40 hover:bg-muted text-foreground"
                  )}
                >
                  {d.min}p
                </button>
              ))}
            </div>
          </div>

          {/* Subtitle / Display Option */}
          <div className="space-y-2">
            <label className="text-xs font-bold text-foreground">Hiển Thị Đề Bài:</label>
            <div className="grid grid-cols-2 gap-1.5 text-xs">
              {[
                { id: "japanese", label: "Chữ Hán (Kanji)" },
                { id: "japanese_reading", label: "Kanji + Cách đọc" },
                { id: "vietnamese", label: "Dịch tiếng Việt" },
                { id: "hidden", label: "Audio-Only 🎧" },
              ].map((opt) => (
                <button
                  key={opt.id}
                  type="button"
                  onClick={() => {
                    soundFX.playFurin();
                    setSubtitleMode(opt.id as any);
                  }}
                  className={cn(
                    "p-2 rounded-xl border font-medium text-center transition-all text-[11px]",
                    subtitleMode === opt.id
                      ? "border-primary bg-primary/10 text-primary font-bold shadow-2xs"
                      : "border-border/70 hover:bg-muted/40 text-foreground"
                  )}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Auto Next Toggle */}
          <div className="pt-2 border-t border-border flex items-center justify-between">
            <div className="space-y-0.5">
              <div className="text-xs font-bold text-foreground">Tự Động Chuyển Câu</div>
              <div className="text-[10px] text-muted-foreground">Tự sang câu mới sau khi chấm xong</div>
            </div>
            <button
              type="button"
              onClick={() => setAutoNext(!autoNext)}
              className={cn(
                "px-3 py-1.5 rounded-full text-xs font-bold transition-all border",
                autoNext
                  ? "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border-emerald-500/40"
                  : "bg-muted text-muted-foreground border-border"
              )}
            >
              {autoNext ? "BẬT (Auto)" : "TẮT (Thủ công)"}
            </button>
          </div>

          {/* Big Start Button */}
          <div className="pt-2">
            <Button
              variant="akane"
              size="lg"
              onClick={() => {
                soundFX.playKatana();
                onStartSession();
              }}
              className="w-full font-bold gap-2 text-sm shadow-md py-6 rounded-2xl"
            >
              <Zap className="h-4 w-4" />
              <span>Bắt Đầu {duration} Phút • {currentSubMode.ja.split(" ")[0]}</span>
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
