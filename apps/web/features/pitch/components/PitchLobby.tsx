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
  { id: "infinite", label: "♾️ Vô hạn (∞)", ms: 0, desc: "Không giới hạn thời gian phát âm" },
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
  const [isAdvancedOpen, setIsAdvancedOpen] = React.useState(false);
  const currentSubMode = PITCH_SUB_MODES.find((m) => m.id === subMode) || PITCH_SUB_MODES[0];

  return (
    <div className="space-y-4 max-w-5xl mx-auto animate-in fade-in duration-300 pb-8">
      {/* Hero Zen Banner */}
      <div className="relative overflow-hidden rounded-2xl border border-border bg-card p-4 sm:p-5 washi-texture shadow-2xs">
        <div className="absolute -top-12 -right-12 h-40 w-40 rounded-full bg-primary/10 blur-2xl pointer-events-none" />
        <div className="relative flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-600 dark:text-sky-400 shrink-0 shadow-2xs">
              <Music className="h-4 w-4" />
            </div>
            <div className="space-y-0.5">
              <div className="flex items-center gap-2">
                <h1 className="text-xl sm:text-2xl font-black tracking-tight text-foreground">
                  Phòng Luyện Cao Độ & Phách
                </h1>
                <Badge variant="fuji" size="sm" className="font-mono font-bold text-[10px]">Mode 3</Badge>
              </div>
              <p className="text-[11px] text-muted-foreground">
                Rèn luyện cao độ Tokyo (Pitch Accent), nhịp phách Mora và vô thanh hóa
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                soundFX.playFurin();
                onOpenCheatsheet();
              }}
              className="gap-1 text-xs font-bold border-sky-500/30 text-sky-700 dark:text-sky-300 hover:bg-sky-500/10 h-8 px-2.5 rounded-xl"
            >
              <BookOpen className="h-3.5 w-3.5" />
              <span>Sổ tay</span>
            </Button>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                soundFX.playFurin();
                onOpenHelp();
              }}
              className="gap-1 text-xs font-bold text-muted-foreground hover:text-foreground h-8 px-2 rounded-xl"
            >
              <HelpCircle className="h-3.5 w-3.5" />
              <span>Phím (?)</span>
            </Button>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded-xl border border-destructive/40 bg-destructive/10 text-destructive text-xs font-semibold animate-in shake">
          {error}
        </div>
      )}

      {/* 2-Column Grid: Submode Selection & Session Config */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 items-start">
        {/* Left 2 Cols: 6 Submodes */}
        <div className="lg:col-span-2 space-y-2.5">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-bold text-foreground flex items-center gap-1.5">
              <span>1. Chọn Chuyên Đề Âm Điệu:</span>
            </h2>
            <span className="text-[10px] text-muted-foreground font-semibold">6 Chế Độ Luyện Tập</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
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
                    "text-left p-3 rounded-2xl border transition-all duration-150 relative group flex flex-col justify-between bg-card shadow-2xs hover:border-primary/40",
                    isMixed ? "sm:col-span-2 bg-gradient-to-r from-card to-primary/5 border-primary/30" : "",
                    isSelected
                      ? "border-primary ring-1 ring-primary/30 bg-primary/5 shadow-2xs"
                      : "hover:bg-muted/40"
                  )}
                >
                  <div className="space-y-1 w-full">
                    <div className="flex items-center justify-between gap-1.5">
                      <span className="text-xs font-bold text-foreground flex items-center gap-1">
                        {isMixed && <Shuffle className="h-3 w-3 text-primary" />}
                        {m.ja}
                      </span>
                      <Badge variant={m.badgeVariant} size="sm" className="text-[9px] px-1.5 py-0">
                        {m.label.split(" ")[0]}
                      </Badge>
                    </div>

                    <p className="text-[11px] text-muted-foreground leading-snug line-clamp-1">
                      {m.desc}
                    </p>
                  </div>

                  <div className="mt-2 pt-1 border-t border-border/40 flex items-center justify-between text-[10px] text-muted-foreground font-jp">
                    <span className="truncate max-w-[220px]">Ví dụ: {m.example}</span>
                    {isSelected && (
                      <CheckCircle2 className="h-3.5 w-3.5 text-primary shrink-0 ml-1" />
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right 1 Col: Session Configuration */}
        <div className="space-y-3 p-3.5 rounded-2xl border border-border/80 bg-card shadow-2xs washi-texture">
          {/* Time Pressure Selector */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs font-bold">
              <span className="text-muted-foreground">Áp Lực Thời Gian:</span>
              <span className="text-primary font-mono text-[11px]">
                {PITCH_PRESSURE_LEVELS.find((p) => p.id === pressure)?.label || "Tiêu chuẩn"}
              </span>
            </div>
            <div className="flex items-center gap-1 p-0.5 rounded-xl bg-muted/50 border border-border">
              {[
                { id: "infinite", label: "∞ Vô hạn" },
                { id: "normal", label: "5s Chuẩn" },
                { id: "reflex", label: "3s Phản xạ" },
                { id: "extreme", label: "2s Cực hạn" },
              ].map((p) => (
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
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          {/* Session Duration Selector */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs font-bold">
              <span className="text-muted-foreground">Thời Lượng Phiên:</span>
              <span className="text-primary font-mono text-[11px]">{duration === 0 ? "∞ Vô hạn" : `${duration} phút`}</span>
            </div>
            <div className="flex items-center gap-1 p-0.5 rounded-xl bg-muted/50 border border-border">
              {PITCH_DURATIONS.map((d) => (
                <button
                  key={d.min}
                  type="button"
                  onClick={() => {
                    soundFX.playFurin();
                    setDuration(d.min as any);
                  }}
                  className={cn(
                    "flex-1 py-1 rounded-lg text-[10px] font-bold transition-all text-center",
                    duration === d.min
                      ? "bg-card text-foreground border border-border shadow-2xs"
                      : "text-muted-foreground hover:text-foreground"
                  )}
                >
                  {d.min === 0 ? "∞" : `${d.min}m`}
                </button>
              ))}
            </div>
          </div>

          {/* Progressive Disclosure: Subtitles & Auto Next */}
          <div className="border border-border/80 rounded-xl bg-muted/20 overflow-hidden">
            <button
              type="button"
              onClick={() => setIsAdvancedOpen((v) => !v)}
              className="w-full px-2.5 py-1.5 flex items-center justify-between text-[11px] font-bold text-muted-foreground hover:text-foreground transition-colors"
            >
              <span>Phụ đề & Tự chuyển câu</span>
              <span className="text-[10px] text-primary">{isAdvancedOpen ? "▲" : "▼"}</span>
            </button>

            {isAdvancedOpen && (
              <div className="p-2.5 pt-1 space-y-2 border-t border-border/60 animate-in fade-in duration-150">
                <div className="grid grid-cols-2 gap-1 text-[10px]">
                  {[
                    { id: "japanese", label: "Kanji" },
                    { id: "japanese_reading", label: "Kanji + Kana" },
                    { id: "vietnamese", label: "Dịch Việt" },
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

                <div className="pt-1 flex items-center justify-between text-[11px]">
                  <span className="font-bold text-muted-foreground">Tự chuyển câu:</span>
                  <button
                    type="button"
                    onClick={() => setAutoNext(!autoNext)}
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

          {/* Big Start Button */}
          <Button
            variant="akane"
            size="lg"
            onClick={() => {
              soundFX.playKatana();
              onStartSession();
            }}
            className="w-full font-bold gap-2 text-xs shadow-md h-10 rounded-xl"
          >
            <Zap className="h-3.5 w-3.5" />
            <span>Bắt Đầu {duration === 0 ? "Vô Hạn" : `${duration}p`} • {currentSubMode.ja.split(" ")[0]}</span>
          </Button>
        </div>
      </div>
    </div>
  );
}
