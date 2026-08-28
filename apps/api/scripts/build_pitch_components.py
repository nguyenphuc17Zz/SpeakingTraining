import os

# 1. pitch-api.ts
PITCH_API = """import { apiClient } from "@/lib/api/api-client";
import { ExerciseDTO, ExerciseResultDTO } from "@/features/learning";

export interface PitchMetrics {
  pitch_accuracy?: number;
  mora_score?: number;
  devoicing_score?: number;
  naturalness_score?: number;
  f0_contour?: number[];
  target_contour?: string[];
  mora_timings?: { mora: string; start_ms: number; end_ms: number; is_voiced: boolean }[];
  accent_detected?: string;
  accent_expected?: string;
  reaction_latency_ms?: number;
}

export interface PitchAttemptPayload {
  exercise_id: string;
  transcript?: string;
  audio_blob?: Blob;
  pitch_metrics?: PitchMetrics;
  reflex_metrics?: {
    reaction_latency_ms: number;
    timed_out: boolean;
  };
}

export const pitchApi = {
  async listPressureProfiles() {
    return apiClient.get<any>("/api/v1/pitch/pressure-profiles");
  },

  async generateExercise(subMode = "pitch_minimal_pair", pressureLevel = "normal", timerLimitMs?: number) {
    const params = new URLSearchParams({ sub_mode: subMode, pressure_level: pressureLevel });
    if (timerLimitMs) params.set("timer_limit_ms", timerLimitMs.toString());
    const res = await apiClient.post<ExerciseDTO>(`/api/v1/pitch/exercises/generate?${params.toString()}`);
    
    // Normalize metadata
    if (res && res.extra_metadata?.pitch_config) {
      const pc = res.extra_metadata.pitch_config;
      if (!res.canonicalAnswer && pc.canonical) res.canonicalAnswer = pc.canonical;
      if (!res.acceptableVariants && pc.accepted) res.acceptableVariants = pc.accepted;
      if (!res.prompt && pc.prompt) res.prompt = pc.prompt;
    }
    return res;
  },

  async submitAttempt(payload: PitchAttemptPayload) {
    return apiClient.post<ExerciseResultDTO>("/api/v1/pitch/attempts", payload);
  },

  async getProgress() {
    return apiClient.get<any>("/api/v1/pitch/progress");
  },
};
"""

# 2. PitchLobby.tsx
PITCH_LOBBY = """\"use client\";

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
  duration: 3 | 5 | 10 | 20;
  setDuration: (v: 3 | 5 | 10 | 20) => void;
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
"""

# 3. PitchPromptCard.tsx
PITCH_PROMPT_CARD = """\"use client\";

import React from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Volume2, Music, Sparkles, HelpCircle, ArrowRight } from "lucide-react";
import { ExerciseDTO } from "@/features/learning";
import { cn } from "@/lib/utils";

interface PitchPromptCardProps {
  exercise: ExerciseDTO | null;
  subtitleMode: "hidden" | "japanese" | "japanese_reading" | "vietnamese";
  onPlayAudio: () => void;
  phase: string;
}

export function PitchPromptCard({
  exercise,
  subtitleMode,
  onPlayAudio,
  phase,
}: PitchPromptCardProps) {
  if (!exercise) return null;

  const pc = exercise.extra_metadata?.pitch_config || {};
  const promptText = pc.prompt || exercise.prompt || exercise.scenario || exercise.title;
  const canonical = pc.canonical || exercise.canonicalAnswer || promptText;
  const reading = pc.reading || "";
  const translation = pc.translation || exercise.scenario || "";
  const pairInfo = pc.pair_info;
  const moraInfo = pc.mora_info;
  const devoicingInfo = pc.devoicing_info;
  const contourInfo = pc.contour_info;
  const pattern = pc.pitch_pattern || [];

  const isAudioPlaying = phase === "prompt_playing";

  return (
    <div className="p-6 rounded-3xl border border-border/80 bg-card shadow-sm washi-texture space-y-5 relative overflow-hidden">
      {/* Accent Background Glow */}
      <div className="absolute top-0 right-0 h-32 w-32 bg-sky-500/5 rounded-full blur-2xl pointer-events-none" />

      {/* Submode Objective Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/60 pb-3.5">
        <div className="flex items-center gap-2">
          <Badge variant="fuji" size="sm" className="font-bold">
            {exercise.exercise_type.replace("pitch_", "").replace("_", " ").toUpperCase()}
          </Badge>
          <span className="text-xs text-muted-foreground font-semibold">
            {exercise.instructions || "Lắng nghe và phát âm đúng chuẩn cao độ Tokyo"}
          </span>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={onPlayAudio}
          disabled={isAudioPlaying}
          className="h-8 gap-1.5 text-xs font-bold border-sky-500/30 text-sky-700 dark:text-sky-300 hover:bg-sky-500/10 shadow-2xs"
        >
          <Volume2 className={cn("h-3.5 w-3.5", isAudioPlaying && "animate-pulse text-sky-500")} />
          <span>{isAudioPlaying ? "Đang phát..." : "Nghe mẫu (L)"}</span>
        </Button>
      </div>

      {/* Minimal Pair Contrast View */}
      {pairInfo && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 p-4 rounded-2xl bg-muted/40 border border-border/70">
          <div className={cn(
            "p-3 rounded-xl border transition-all text-center space-y-1.5",
            canonical === pairInfo.word_a
              ? "bg-card border-primary shadow-xs ring-1 ring-primary/30"
              : "bg-card/60 border-border/80 opacity-75"
          )}>
            <div className="text-xs font-bold text-muted-foreground">TỪ A:</div>
            <div className="text-xl font-bold font-jp text-foreground">{pairInfo.word_a}</div>
            <div className="text-xs font-semibold text-primary">{pairInfo.type_a}</div>
            <div className="text-[11px] text-muted-foreground">{pairInfo.meaning_a}</div>
          </div>

          <div className={cn(
            "p-3 rounded-xl border transition-all text-center space-y-1.5",
            canonical === pairInfo.word_b
              ? "bg-card border-primary shadow-xs ring-1 ring-primary/30"
              : "bg-card/60 border-border/80 opacity-75"
          )}>
            <div className="text-xs font-bold text-muted-foreground">TỪ B:</div>
            <div className="text-xl font-bold font-jp text-foreground">{pairInfo.word_b}</div>
            <div className="text-xs font-semibold text-primary">{pairInfo.type_b}</div>
            <div className="text-[11px] text-muted-foreground">{pairInfo.meaning_b}</div>
          </div>
        </div>
      )}

      {/* Mora Length Comparison */}
      {moraInfo && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 p-4 rounded-2xl bg-muted/40 border border-border/70">
          <div className="p-3 rounded-xl bg-card border border-border/80 text-center space-y-1.5">
            <div className="text-xs font-bold text-muted-foreground">Âm ngắn ({moraInfo.short_mora?.length} phách):</div>
            <div className="text-lg font-bold font-jp text-foreground">{moraInfo.short_word}</div>
            <div className="flex justify-center gap-1">
              {moraInfo.short_mora?.map((m: string, i: number) => (
                <span key={i} className="px-2 py-0.5 rounded bg-muted text-xs font-jp font-bold">{m}</span>
              ))}
            </div>
            <div className="text-[11px] text-muted-foreground">{moraInfo.short_meaning}</div>
          </div>

          <div className="p-3 rounded-xl bg-card border-primary border text-center space-y-1.5 shadow-xs">
            <div className="text-xs font-bold text-primary">Âm dài ({moraInfo.long_mora?.length} phách • {moraInfo.mora_type}):</div>
            <div className="text-lg font-bold font-jp text-foreground">{moraInfo.long_word}</div>
            <div className="flex justify-center gap-1">
              {moraInfo.long_mora?.map((m: string, i: number) => (
                <span key={i} className="px-2 py-0.5 rounded bg-primary/10 border border-primary/20 text-xs font-jp font-bold text-primary">{m}</span>
              ))}
            </div>
            <div className="text-[11px] text-muted-foreground">{moraInfo.long_meaning}</div>
          </div>
        </div>
      )}

      {/* Main Target Prompt Sentence */}
      <div className="text-center py-4 space-y-2">
        {subtitleMode !== "hidden" ? (
          <>
            <div className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
              Từ Vựng / Câu Mục Tiêu:
            </div>
            <div className="text-2xl md:text-3xl font-black font-jp text-foreground tracking-wide leading-relaxed">
              {canonical}
            </div>

            {(subtitleMode === "japanese_reading" || subtitleMode === "vietnamese") && reading && (
              <div className="text-sm font-jp font-bold text-primary">
                「{reading}」
              </div>
            )}

            {(subtitleMode === "vietnamese" || translation) && (
              <div className="text-xs text-muted-foreground max-w-md mx-auto italic">
                {translation}
              </div>
            )}
          </>
        ) : (
          <div className="py-6 px-4 rounded-2xl bg-sky-500/5 border border-sky-500/20 text-center space-y-2">
            <div className="text-sm font-bold text-sky-600 dark:text-sky-400 flex items-center justify-center gap-2">
              <Volume2 className="h-4 w-4 animate-bounce" />
              <span>🎧 Chế độ Audio-Only: Hãy lắng nghe và lặp lại với đúng cao độ</span>
            </div>
            <p className="text-xs text-muted-foreground">Bấm nút "Nghe mẫu (L)" để nghe lại nếu cần</p>
          </div>
        )}
      </div>

      {/* Visual Pitch Accent Steps (High / Low Blocks) */}
      {pattern && pattern.length > 0 && (
        <div className="p-4 rounded-2xl bg-muted/40 border border-border/70 space-y-2">
          <div className="flex items-center justify-between text-xs font-bold text-muted-foreground">
            <span>Sơ đồ cao độ (Pitch Accent Pattern):</span>
            <span className="font-mono text-primary font-bold">{pattern.join(" - ")}</span>
          </div>

          <div className="flex items-end justify-center gap-2 pt-3 pb-1 h-20">
            {pattern.map((tone: string, idx: number) => {
              const isHigh = tone.toUpperCase() === "H";
              return (
                <div key={idx} className="flex flex-col items-center gap-1.5 flex-1 max-w-[56px]">
                  <span className={cn(
                    "text-[10px] font-bold font-mono",
                    isHigh ? "text-rose-500" : "text-sky-500"
                  )}>
                    {isHigh ? "CAO (H)" : "THẤP (L)"}
                  </span>
                  <div
                    className={cn(
                      "w-full rounded-xl border transition-all shadow-2xs flex items-center justify-center font-bold text-xs font-jp",
                      isHigh
                        ? "h-12 bg-rose-500/15 border-rose-500/40 text-rose-700 dark:text-rose-300 -translate-y-2"
                        : "h-7 bg-sky-500/15 border-sky-500/40 text-sky-700 dark:text-sky-300"
                    )}
                  >
                    {idx + 1}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
"""

# 4. PitchResultCard.tsx
PITCH_RESULT_CARD = """\"use client\";

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
  Music,
} from "lucide-react";
import { ExerciseDTO, ExerciseResultDTO } from "@/features/learning";
import { speakJapaneseText } from "@/features/speaking/services/web-speech";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

interface PitchResultCardProps {
  result: ExerciseResultDTO;
  exercise: ExerciseDTO | null;
  onNext: () => void;
  onRetry: () => void;
  onAskCoach?: (prompt: string) => void;
  onCancelAutoNext?: () => void;
}

export function PitchResultCard({
  result,
  exercise,
  onNext,
  onRetry,
  onAskCoach,
  onCancelAutoNext,
}: PitchResultCardProps) {
  const isPerfect = result.isPerfect || (result.score ?? 0) >= 90;
  const isSuccess = result.success;
  const isTimeout = result.timedOut;
  const score = result.score ?? 0;
  const latency = result.reactionLatencyMs ?? 0;

  const pc = exercise?.extra_metadata?.pitch_config || {};
  const canonical = pc.canonical || exercise?.canonicalAnswer || "";
  const metrics = (result as any).pitch_metrics || {};

  const pitchAccuracy = metrics.pitch_accuracy ?? score;
  const moraScore = metrics.mora_score ?? 90;
  const devoicingScore = metrics.devoicing_score ?? 88;
  const naturalnessScore = metrics.naturalness_score ?? 85;

  return (
    <div className="p-6 rounded-3xl border border-border/80 bg-card shadow-md washi-texture space-y-6 animate-in fade-in zoom-in-95 duration-200">
      {/* Result Status Banner */}
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
                ? "🏆 CAO ĐỘ HOÀN HẢO (PERFECT PITCH)"
                : isSuccess
                ? "✅ CHÍNH XÁC (CORRECT ACCENT)"
                : isTimeout
                ? "⏰ HẾT THỜI GIAN PHẢN XẠ"
                : "⚠️ CẦN ĐIỀU CHỈNH CAO ĐỘ"}
            </h3>
            <p className="text-xs opacity-85">
              {isPerfect
                ? "Đường cao độ F0 và độ đều phách đạt chuẩn giọng Tokyo bản xứ!"
                : isSuccess
                ? "Phát âm tốt, tiếp tục duy trì cao độ ổn định nhé."
                : isTimeout
                ? "Hãy bấm 'Thử lại (R)' để phản xạ nhanh hơn trong ngưỡng thời gian."
                : "Chú ý vị trí hạ giọng (downstep) hoặc độ dài phách trường âm."}
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

      {/* 4 Phonetic Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3 rounded-2xl bg-muted/40 border border-border/70 text-center space-y-1">
          <div className="text-[11px] font-bold text-muted-foreground">Độ Chuẩn Cao Độ</div>
          <div className="text-lg font-black font-mono text-sky-600 dark:text-sky-400">{pitchAccuracy}%</div>
          <div className="text-[10px] text-muted-foreground">Tokyo Semitone</div>
        </div>

        <div className="p-3 rounded-2xl bg-muted/40 border border-border/70 text-center space-y-1">
          <div className="text-[11px] font-bold text-muted-foreground">Độ Đều Phách</div>
          <div className="text-lg font-black font-mono text-emerald-600 dark:text-emerald-400">{moraScore}%</div>
          <div className="text-[10px] text-muted-foreground">Mora Timing</div>
        </div>

        <div className="p-3 rounded-2xl bg-muted/40 border border-border/70 text-center space-y-1">
          <div className="text-[11px] font-bold text-muted-foreground">Vô Thanh Hóa</div>
          <div className="text-lg font-black font-mono text-purple-600 dark:text-purple-400">{devoicingScore}%</div>
          <div className="text-[10px] text-muted-foreground">Devoicing i/u</div>
        </div>

        <div className="p-3 rounded-2xl bg-muted/40 border border-border/70 text-center space-y-1">
          <div className="text-[11px] font-bold text-muted-foreground">Độ Tự Nhiên</div>
          <div className="text-lg font-black font-mono text-amber-600 dark:text-amber-400">{naturalnessScore}%</div>
          <div className="text-[10px] text-muted-foreground">Acoustic Balance</div>
        </div>
      </div>

      {/* Dual Voice Comparison */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* User Voice */}
        <div className="p-4 rounded-2xl bg-muted/40 border border-border/70 space-y-2">
          <div className="flex items-center justify-between text-xs font-bold text-muted-foreground">
            <span>🗣️ Bạn đã phát âm (Your Voice):</span>
          </div>
          <div className="p-3 rounded-xl bg-card border border-border/80 text-base font-bold font-jp text-foreground">
            {result.userTranscript || "(Đã ghi âm giọng nói)"}
          </div>
        </div>

        {/* Model Voice */}
        <div className="p-4 rounded-2xl bg-sky-500/5 border border-sky-500/20 space-y-2">
          <div className="flex items-center justify-between text-xs font-bold text-sky-700 dark:text-sky-300">
            <span>👑 Phát âm chuẩn Tokyo (Model Pitch):</span>
            <button
              onClick={() => {
                soundFX.playFurin();
                speakJapaneseText(canonical, { rate: 1.0 });
              }}
              className="hover:underline flex items-center gap-1 font-bold text-primary text-[11px]"
            >
              <Volume2 className="h-3 w-3" />
              <span>Nghe lại</span>
            </button>
          </div>
          <div className="p-3 rounded-xl bg-card border border-sky-500/30 text-base font-bold font-jp text-foreground">
            {canonical}
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
                onAskCoach(`Hãy hướng dẫn cách phát âm chuẩn cao độ Tokyo cho từ "${canonical}".`);
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
          <span>Câu tiếp theo (Enter)</span>
          <ArrowRight className="h-3.5 w-3.5" />
        </Button>
      </div>
    </div>
  );
}
"""

# 5. PitchSessionSummary.tsx
PITCH_SESSION_SUMMARY = """\"use client\";

import React from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Trophy,
  RotateCcw,
  Zap,
  Home,
  CheckCircle2,
  Volume2,
  Clock,
  Music,
  Flame,
  Award,
} from "lucide-react";
import { ExerciseResultDTO } from "@/features/learning";
import { speakJapaneseText } from "@/features/speaking/services/web-speech";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

interface PitchSessionSummaryProps {
  results: ExerciseResultDTO[];
  onRestart: () => void;
  onToLobby: () => void;
  onRetryWeak: () => void;
}

export function PitchSessionSummary({
  results,
  onRestart,
  onToLobby,
  onRetryWeak,
}: PitchSessionSummaryProps) {
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
            Báo Cáo Phản Xạ Cao Độ & Phách
          </h2>
          <p className="text-xs text-muted-foreground max-w-md">
            Tổng kết chi tiết độ chuẩn âm vị, cao độ Tokyo và tốc độ phản xạ của bạn
          </p>
        </div>

        {/* Authentic Japanese Hanko Stamp */}
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
            <div className="text-xs font-bold text-muted-foreground">Số câu luyện</div>
            <div className="text-2xl font-black font-mono text-foreground">{total}</div>
            <div className="text-[10px] text-muted-foreground">câu hoàn thành</div>
          </div>

          <div className="p-4 rounded-2xl bg-muted/40 border border-border/80 space-y-1">
            <div className="text-xs font-bold text-muted-foreground">Độ chính xác</div>
            <div className="text-2xl font-black font-mono text-emerald-600 dark:text-emerald-400">{accuracy}%</div>
            <div className="text-[10px] text-muted-foreground">{correct}/{total} câu chuẩn</div>
          </div>

          <div className="p-4 rounded-2xl bg-muted/40 border border-border/80 space-y-1">
            <div className="text-xs font-bold text-muted-foreground">Tốc độ trung bình</div>
            <div className="text-2xl font-black font-mono text-sky-600 dark:text-sky-400">{avgLatency}ms</div>
            <div className="text-[10px] text-muted-foreground">phản xạ âm thanh</div>
          </div>

          <div className="p-4 rounded-2xl bg-muted/40 border border-border/80 space-y-1">
            <div className="text-xs font-bold text-muted-foreground">Cao Độ Hoàn Hảo</div>
            <div className="text-2xl font-black font-mono text-amber-600 dark:text-amber-400">{perfect}</div>
            <div className="text-[10px] text-muted-foreground">điểm tuyệt đối</div>
          </div>
        </div>
      </div>

      {/* Practiced Items List */}
      <div className="p-6 rounded-3xl border border-border bg-card shadow-xs washi-texture space-y-4">
        <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
          <Music className="h-4 w-4 text-primary" />
          <span>Danh sách câu đã luyện trong phiên ({total} câu)</span>
        </h3>

        <div className="space-y-2 max-h-[320px] overflow-y-auto pr-1">
          {results.map((r, i) => {
            const canonical = (r as any).canonicalAnswer || r.userTranscript || `Câu ${i + 1}`;
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
                    {r.success ? "Chuẩn" : "Cần sửa"}
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
            <span>Luyện lại {total - correct} câu chưa đạt</span>
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

# 6. PitchCheatsheetModal.tsx
PITCH_CHEATSHEET_MODAL = """\"use client\";

import React, { useState } from "react";
import { Modal } from "@/components/ui/modal";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Volume2, BookOpen, Music, Check } from "lucide-react";
import { speakJapaneseText } from "@/features/speaking/services/web-speech";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

interface PitchCheatsheetModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function PitchCheatsheetModal({ isOpen, onClose }: PitchCheatsheetModalProps) {
  const [activeTab, setActiveTab] = useState<"contours" | "minimal_pairs" | "mora" | "devoicing">("contours");

  const playTTS = (text: string) => {
    soundFX.playFurin();
    speakJapaneseText(text, { rate: 1.0 });
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Cẩm Nang Cao Độ & Phách Tiếng Nhật (Pitch & Mora Handbook)"
      description="Tra cứu nhanh 4 mô hình cao độ Tokyo, bảng cặp từ tối thiểu, quy tắc đếm phách và vô thanh hóa"
      className="max-w-3xl"
    >
      <div className="space-y-4 pt-2">
        {/* Navigation Tabs */}
        <div className="flex items-center p-1 rounded-2xl bg-muted/70 border border-border overflow-x-auto scrollbar-thin">
          {[
            { id: "contours", label: "📈 4 Mô Hình Cao Độ Tokyo" },
            { id: "minimal_pairs", label: "👥 Bảng Cặp Từ Tối Thiểu" },
            { id: "mora", label: "⏱️ Quy Tắc Đếm Phách (Mora)" },
            { id: "devoicing", label: "🔇 Vô Thanh Hóa (Devoicing)" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => {
                soundFX.playFurin();
                setActiveTab(tab.id as any);
              }}
              className={cn(
                "flex-1 py-2 px-3 rounded-xl text-xs font-bold transition-all whitespace-nowrap text-center",
                activeTab === tab.id
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab 1: 4 Tokyo Pitch Contours */}
        {activeTab === "contours" && (
          <div className="space-y-3 max-h-[380px] overflow-y-auto pr-1">
            {[
              {
                type: "平板型 (Heiban - Kiểu Bằng [0])",
                pattern: "L - H - H - H...",
                desc: "Âm thứ nhất THẤP, âm thứ hai và các âm tiếp theo CAO, khi đi kèm trợ từ (が, を) vẫn giữ CAO.",
                examples: [
                  { w: "日本語 (にほんご)", exp: "L-H-H-H" },
                  { w: "飴 (あめ)", exp: "L-H (Viên kẹo)" },
                  { w: "桜 (さくら)", exp: "L-H-H" },
                  { w: "友達 (ともだち)", exp: "L-H-H-H" },
                ],
              },
              {
                type: "頭高型 (Atamadaka - Kiểu Đầu Cao [1])",
                pattern: "H - L - L - L...",
                desc: "Âm đầu tiên CAO, hạ giọng ngay ở âm thứ hai và giữ THẤP cho đến hết từ và trợ từ.",
                examples: [
                  { w: "雨 (あめ)", exp: "H-L (Cơn mưa)" },
                  { w: "箸 (はし)", exp: "H-L (Đôi đũa)" },
                  { w: "寿司 (すし)", exp: "H-L" },
                  { w: "本 (ほん)", exp: "H-L" },
                ],
              },
              {
                type: "中高型 (Nakadaka - Kiểu Giữa Cao [2..N-1])",
                pattern: "L - H... - L - L...",
                desc: "Âm đầu THẤP, lên CAO ở giữa rồi HẠ giọng xuống THẤP trước khi kết thúc từ.",
                examples: [
                  { w: "ありがとう", exp: "L-H-L-L-L (Hạ ở âm thứ 2)" },
                  { w: "卵 (たまご)", exp: "L-H-L" },
                  { w: "飛行機 (ひこうき)", exp: "L-H-L-L" },
                ],
              },
              {
                type: "尾高型 (Odaka - Kiểu Đuôi Cao [N])",
                pattern: "L - H - H... (Hạ khi gặp trợ từ)",
                desc: "Âm đầu THẤP, các âm sau CAO đến hết từ; nhưng HẠ ngay xuống THẤP khi có trợ từ (が, を, に).",
                examples: [
                  { w: "橋 (はし)", exp: "L-H (Cây cầu) ➔ はしが (L-H-L)" },
                  { w: "花 (はな)", exp: "L-H (Bông hoa) ➔ はなが (L-H-L)" },
                  { w: "山 (やま)", exp: "L-H (Ngọn núi)" },
                ],
              },
            ].map((c, i) => (
              <div key={i} className="p-4 rounded-2xl border border-border/80 bg-card space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="font-bold text-xs text-foreground">{c.type}</h4>
                  <Badge variant="fuji" size="sm" className="font-mono">{c.pattern}</Badge>
                </div>
                <p className="text-xs text-muted-foreground">{c.desc}</p>
                <div className="flex flex-wrap gap-2 pt-1">
                  {c.examples.map((ex, j) => (
                    <button
                      key={j}
                      onClick={() => playTTS(ex.w)}
                      className="px-2.5 py-1 rounded-xl bg-muted/50 hover:bg-muted border text-xs font-jp flex items-center gap-1.5 transition-all"
                    >
                      <Volume2 className="h-3 w-3 text-primary" />
                      <span>{ex.w}</span>
                      <span className="text-[10px] text-muted-foreground font-sans">({ex.exp})</span>
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Tab 2: Minimal Pairs */}
        {activeTab === "minimal_pairs" && (
          <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1">
            {[
              { a: "雨 (あめ)", typeA: "頭高 [1] (Mưa)", b: "飴 (あめ)", typeB: "平板 [0] (Kẹo)" },
              { a: "箸 (はし)", typeA: "頭高 [1] (Đũa)", b: "橋 (はし)", typeB: "尾高 [2] (Cây cầu)" },
              { a: "酒 (さけ)", typeA: "平板 [0] (Rượu)", b: "鮭 (さけ)", typeB: "頭高 [1] (Cá hồi)" },
              { a: "柿 (かき)", typeA: "平板 [0] (Quả hồng)", b: "牡蠣 (かき)", typeB: "頭高 [1] (Con hàu)" },
              { a: "白 (しろ)", typeA: "頭高 [1] (Màu trắng)", b: "城 (しろ)", typeB: "平板 [0] (Lâu đài)" },
              { a: "雲 (くも)", typeA: "頭高 [1] (Đám mây)", b: "蜘蛛 (くも)", typeB: "平板 [0] (Con nhện)" },
              { a: "今 (いま)", typeA: "頭高 [1] (Bây giờ)", b: "居間 (いま)", typeB: "平板 [0] (Phòng khách)" },
              { a: "花 (はな)", typeA: "尾高 [2] (Bông hoa)", b: "鼻 (はな)", typeB: "平板 [0] (Cái mũi)" },
            ].map((p, i) => (
              <div key={i} className="p-3 rounded-xl border border-border/70 bg-card flex items-center justify-between gap-3 text-xs">
                <div className="flex items-center gap-2 flex-1">
                  <button onClick={() => playTTS(p.a)} className="font-bold font-jp text-primary hover:underline flex items-center gap-1">
                    <Volume2 className="h-3 w-3" />
                    <span>{p.a}</span>
                  </button>
                  <span className="text-muted-foreground text-[11px]">({p.typeA})</span>
                </div>
                <span className="text-muted-foreground font-bold">vs</span>
                <div className="flex items-center gap-2 flex-1 justify-end">
                  <button onClick={() => playTTS(p.b)} className="font-bold font-jp text-primary hover:underline flex items-center gap-1">
                    <Volume2 className="h-3 w-3" />
                    <span>{p.b}</span>
                  </button>
                  <span className="text-muted-foreground text-[11px]">({p.typeB})</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Tab 3: Mora Timing */}
        {activeTab === "mora" && (
          <div className="space-y-3 max-h-[380px] overflow-y-auto pr-1 text-xs">
            <div className="p-4 rounded-2xl bg-card border border-border/80 space-y-2">
              <h4 className="font-bold text-foreground">1. Trường Âm (長音 - Long Vowels): Tính là 1 phách riêng</h4>
              <p className="text-muted-foreground">おばさん (4 mora - Cô/Dì) ↔ おばあさん (5 mora - Bà cụ)</p>
              <p className="text-muted-foreground">ビル (2 mora - Tòa nhà) ↔ ビール (3 mora - Đồ uống Bia)</p>
            </div>
            <div className="p-4 rounded-2xl bg-card border border-border/80 space-y-2">
              <h4 className="font-bold text-foreground">2. Âm Ngắt (促音 - Small Tsu っ): Tính là 1 phách im lặng</h4>
              <p className="text-muted-foreground">きて (2 mora - Hãy đến) ↔ きって (3 mora - Con tem)</p>
              <p className="text-muted-foreground">さか (2 mora - Con dốc) ↔ さっか (3 mora - Nhà văn)</p>
            </div>
            <div className="p-4 rounded-2xl bg-card border border-border/80 space-y-2">
              <h4 className="font-bold text-foreground">3. Âm Mũi (撥音 - Âm ん): Tính là 1 phách riêng</h4>
              <p className="text-muted-foreground">ほん (2 mora - Quyển sách) • にほん (3 mora - Nước Nhật)</p>
            </div>
            <div className="p-4 rounded-2xl bg-card border border-border/80 space-y-2">
              <h4 className="font-bold text-foreground">4. Âm Ghép (拗音 - Âm nhỏ ゃ, ゅ, ょ): Tính chung 1 phách</h4>
              <p className="text-muted-foreground">きゃく (2 mora: [きゃ] + [く] - Khách hàng) • きょう (2 mora: [きょ] + [う] - Hôm nay)</p>
            </div>
          </div>
        )}

        {/* Tab 4: Vowel Devoicing */}
        {activeTab === "devoicing" && (
          <div className="space-y-3 max-h-[380px] overflow-y-auto pr-1 text-xs">
            <div className="p-4 rounded-2xl bg-card border border-border/80 space-y-2">
              <h4 className="font-bold text-foreground">Quy tắc Vô thanh hóa (母音無声化):</h4>
              <p className="text-muted-foreground leading-relaxed">
                Nguyên âm <strong>[ i ]</strong> và <strong>[ u ]</strong> không rung dây thanh (chỉ phát ra luồng hơi gió nhẹ) khi:
              </p>
              <ul className="list-disc pl-5 space-y-1 text-muted-foreground">
                <li>Đứng giữa 2 phụ âm vô thanh: <strong>k, s, t, h, p</strong> (VD: すき [suki] ➔ âm [su] vô thanh; つき [tsuki] ➔ âm [tsu] vô thanh).</li>
                <li>Đứng ở cuối câu sau phụ âm vô thanh: <strong>~です [desu]</strong>, <strong>~ました [mashita]</strong>.</li>
              </ul>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {[
                { w: "ありがとうございます", d: "す ở cuối câu vô thanh" },
                { w: "好きです (すきです)", d: "す vô thanh trước phụ âm k" },
                { w: "聞きます (ききます)", d: "き đầu tiên vô thanh" },
                { w: "二つ (ふたつ)", d: "ふ vô thanh trước phụ âm t" },
              ].map((item, i) => (
                <div key={i} className="p-3 rounded-xl border border-border/70 bg-card flex items-center justify-between">
                  <div>
                    <div className="font-bold font-jp text-foreground">{item.w}</div>
                    <div className="text-[11px] text-muted-foreground">{item.d}</div>
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => playTTS(item.w)} className="h-7 w-7 p-0">
                    <Volume2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Modal Footer */}
        <div className="pt-3 border-t border-border flex justify-end">
          <Button size="sm" onClick={onClose} className="text-xs font-bold gap-1.5">
            <Check className="h-3.5 w-3.5" />
            <span>Đã hiểu</span>
          </Button>
        </div>
      </div>
    </Modal>
  );
}
"""

# 7. index.ts
PITCH_INDEX = """export * from "./components/PitchLobby";
export * from "./components/PitchPromptCard";
export * from "./components/PitchResultCard";
export * from "./components/PitchSessionSummary";
export * from "./components/PitchCheatsheetModal";
export * from "./hooks/usePitchSession";
export * from "./services/pitch-api";
"""

# 8. usePitchSession.ts
PITCH_HOOK = """\"use client\";

import { useState, useRef, useCallback, useEffect } from "react";
import { pitchApi } from "../services/pitch-api";
import { ExerciseDTO, ExerciseResultDTO } from "@/features/learning";
import { useReflexTimer } from "@/features/reflex/hooks/useReflexTimer";
import { useMicrophone } from "@/features/speaking/hooks/useMicrophone";
import { useSpeechRecognition } from "@/features/speaking/hooks/useSpeechRecognition";

export type PitchPhase =
  | "idle"
  | "loading"
  | "prompt_playing"
  | "ready"
  | "waiting_for_speech"
  | "recording"
  | "evaluating"
  | "result"
  | "summary";

interface UsePitchSessionOptions {
  subMode?: string;
  pressureLevel?: "relaxed" | "normal" | "fast" | "reflex" | "extreme";
  autoNext?: boolean;
  startTrigger?: "manual" | "auto";
}

export function usePitchSession({
  subMode = "pitch_minimal_pair",
  pressureLevel = "normal",
  autoNext = true,
  startTrigger = "manual",
}: UsePitchSessionOptions = {}) {
  const [phase, setPhase] = useState<PitchPhase>("idle");
  const [exercise, setExercise] = useState<ExerciseDTO | null>(null);
  const [result, setResult] = useState<ExerciseResultDTO | null>(null);
  const [results, setResults] = useState<ExerciseResultDTO[]>([]);
  const [isPaused, setIsPaused] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [stats, setStats] = useState({
    total: 0,
    correct: 0,
    perfectCount: 0,
    avgLatency: 0,
  });

  const recorder = useMicrophone({ sampleRate: 16000 });
  const speech = useSpeechRecognition({
    language: "ja-JP",
    continuous: false,
    interimResults: true,
  });

  const promptStartTimeRef = useRef<number>(0);
  const autoNextTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const timer = useReflexTimer({
    onExpire: () => {
      handleTimeout();
    },
  });

  const handleTimeout = useCallback(async () => {
    if (phase !== "waiting_for_speech" && phase !== "recording") return;
    setPhase("evaluating");
    recorder.stopRecording();
    speech.stopListening();

    const latency = timer.timerLimitMs;
    const timeoutResult: ExerciseResultDTO = {
      exerciseId: exercise?.id || "",
      score: 0,
      success: false,
      isPerfect: false,
      timedOut: true,
      reactionLatencyMs: latency,
      userTranscript: "",
      feedback: "Hết thời gian phản xạ! Hãy thử luyện lại câu này.",
      strengths: [],
      improvements: ["Cần phản xạ nhanh hơn trong ngưỡng thời gian"],
      drillScores: {},
    };

    setResult(timeoutResult);
    setResults((prev) => [...prev, timeoutResult]);
    setStats((prev) => ({
      ...prev,
      total: prev.total + 1,
      avgLatency: (prev.avgLatency * prev.total + latency) / (prev.total + 1),
    }));
    setPhase("result");
  }, [phase, exercise?.id, timer.timerLimitMs, recorder, speech]);

  const loadNextExercise = useCallback(async () => {
    try {
      setPhase("loading");
      setError(null);
      const ex = await pitchApi.generateExercise(subMode, pressureLevel);
      setExercise(ex);
      setResult(null);

      const pc = ex.extra_metadata?.pitch_config || {};
      const timerMs = pc.timer_limit_ms || 5000;
      timer.reset(timerMs);

      setPhase("prompt_playing");
    } catch (e: any) {
      console.error("[usePitchSession] Failed to load pitch exercise:", e);
      setError("Không thể tải bài tập cao độ. Vui lòng kiểm tra kết nối Backend.");
      setPhase("idle");
    }
  }, [subMode, pressureLevel, timer]);

  const onPromptAudioFinished = useCallback(() => {
    if (startTrigger === "auto") {
      startVoiceRecording();
    } else {
      setPhase("ready");
    }
  }, [startTrigger]);

  const startVoiceRecording = useCallback(async () => {
    setPhase("recording");
    promptStartTimeRef.current = Date.now();
    timer.start();
    await recorder.startRecording();
    speech.startListening();
  }, [timer, recorder, speech]);

  const submitWithTranscript = useCallback(
    async (text: string) => {
      if (!exercise) return;
      setPhase("evaluating");
      timer.pause();
      const latency = Date.now() - promptStartTimeRef.current;

      recorder.stopRecording();
      speech.stopListening();

      try {
        const payload = {
          exercise_id: exercise.id,
          transcript: text,
          reflex_metrics: {
            reaction_latency_ms: latency,
            timed_out: false,
          },
        };

        const res = await pitchApi.submitAttempt(payload);
        setResult(res);
        setResults((prev) => [...prev, res]);

        setStats((prev) => ({
          total: prev.total + 1,
          correct: prev.correct + (res.success ? 1 : 0),
          perfectCount: prev.perfectCount + (res.isPerfect ? 1 : 0),
          avgLatency: (prev.avgLatency * prev.total + latency) / (prev.total + 1),
        }));

        setPhase("result");

        if (autoNext) {
          autoNextTimeoutRef.current = setTimeout(() => {
            loadNextExercise();
          }, 3500);
        }
      } catch (e: any) {
        console.error("[usePitchSession] Failed to submit attempt:", e);
        // Fallback local evaluation
        const canonical = exercise.canonicalAnswer || exercise.extra_metadata?.pitch_config?.canonical || "";
        const isMatch = text.toLowerCase().includes(canonical.toLowerCase());
        const localRes: ExerciseResultDTO = {
          exerciseId: exercise.id,
          score: isMatch ? 95 : 60,
          success: isMatch,
          isPerfect: isMatch,
          timedOut: false,
          reactionLatencyMs: latency,
          userTranscript: text,
          feedback: isMatch ? "Phát âm chuẩn xác!" : "Cần lưu ý cao độ",
          strengths: [],
          improvements: [],
          drillScores: {},
        };
        setResult(localRes);
        setResults((prev) => [...prev, localRes]);
        setPhase("result");
      }
    },
    [exercise, timer, recorder, speech, autoNext, loadNextExercise]
  );

  const startSession = useCallback(() => {
    setResults([]);
    setStats({ total: 0, correct: 0, perfectCount: 0, avgLatency: 0 });
    loadNextExercise();
  }, [loadNextExercise]);

  const retry = useCallback(() => {
    if (autoNextTimeoutRef.current) clearTimeout(autoNextTimeoutRef.current);
    if (!exercise) return;
    setResult(null);
    const pc = exercise.extra_metadata?.pitch_config || {};
    const timerMs = pc.timer_limit_ms || 5000;
    timer.reset(timerMs);
    setPhase("ready");
  }, [exercise, timer]);

  const startNext = useCallback(() => {
    if (autoNextTimeoutRef.current) clearTimeout(autoNextTimeoutRef.current);
    loadNextExercise();
  }, [loadNextExercise]);

  const cancelAutoNext = useCallback(() => {
    if (autoNextTimeoutRef.current) {
      clearTimeout(autoNextTimeoutRef.current);
      autoNextTimeoutRef.current = null;
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
    recorder,
    speech,
    isPaused,
    setIsPaused,
    error,
    isUserSpeaking: recorder.isRecording && recorder.volumeLevel > 0.08,
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
PITCH_PAGE = """\"use client\";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Music,
  Mic,
  Clock,
  Play,
  RotateCcw,
  Sparkles,
  BookOpen,
  Edit3,
} from "lucide-react";
import { usePitchSession } from "@/features/pitch/hooks/usePitchSession";
import { ReflexTimer as PitchTimer } from "@/features/reflex/components/ReflexTimer";
import { PitchPromptCard } from "@/features/pitch/components/PitchPromptCard";
import { PitchResultCard } from "@/features/pitch/components/PitchResultCard";
import { PitchSessionSummary } from "@/features/pitch/components/PitchSessionSummary";
import { PitchCheatsheetModal } from "@/features/pitch/components/PitchCheatsheetModal";
import { PitchLobby, PITCH_SUB_MODES, PITCH_PRESSURE_LEVELS } from "@/features/pitch/components/PitchLobby";
import { GlobalKeybindingsModal } from "@/components/layout/global-keybindings-modal";
import { CoachPanel } from "@/features/coach";
import { usePathname } from "next/navigation";
import { useCoachCore } from "@/features/coach/hooks/useCoachCore";
import { CoachInsightCard } from "@/features/coach/components/CoachInsightCard";
import { useCoachProactive } from "@/features/coach/hooks/useCoachProactive";
import { useSystemKeybindings, formatKeyDisplay } from "@/hooks/use-system-keybindings";
import { speakJapaneseText, stopWebSpeech } from "@/features/speaking/services/web-speech";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

export default function PitchPage() {
  const [subMode, setSubMode] = useState("mixed");
  const [pressure, setPressure] = useState<"relaxed" | "normal" | "fast" | "reflex" | "extreme">("normal");
  const [subtitleMode, setSubtitleMode] = useState<"hidden" | "japanese" | "japanese_reading" | "vietnamese">("japanese");
  const [startTrigger, setStartTrigger] = useState<"manual" | "auto">("manual");
  const [transcriptInput, setTranscriptInput] = useState("");
  const [showTextInput, setShowTextInput] = useState(false);
  const [showSummary, setShowSummary] = useState(false);
  const [showCheatsheet, setShowCheatsheet] = useState(false);
  const [showKeybindingsModal, setShowKeybindingsModal] = useState(false);
  const [duration, setDuration] = useState<3 | 5 | 10 | 20>(5);
  const [sessionRemainingSec, setSessionRemainingSec] = useState(duration * 60);
  const [autoNext, setAutoNext] = useState(false);

  const sessionEndTimestampRef = useRef<number | null>(null);
  const sessionPausedRemainingMsRef = useRef<number>(duration * 60 * 1000);

  const { matchesAction, keybindings } = useSystemKeybindings();

  const session = usePitchSession({
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

  const timerMs = PITCH_PRESSURE_LEVELS.find((p) => p.id === pressure)?.ms ?? 5000;
  const activeExercise = session.exercise;
  const pathname = usePathname();
  const { insights, dismiss } = useCoachProactive();
  const [coachOpen, setCoachOpen] = useState(false);
  const coach = useCoachCore();

  const handleCoachSelect = (prompt: string) => {
    setCoachOpen(true);
    setTimeout(() => coach.ask(prompt, { route: pathname || "/pitch", exerciseId: (activeExercise as any)?.id }), 300);
  };

  const playedPromptExerciseIdRef = useRef<string | null>(null);

  const playPromptAudio = useCallback(
    (autoTransition = false) => {
      if (!activeExercise) return;
      const pc = activeExercise.extra_metadata?.pitch_config || {};
      const text = pc.canonical || pc.prompt || activeExercise.canonicalAnswer || activeExercise.prompt;
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
    const text = transcriptInput.trim() || session.speech.transcript.trim() || session.exercise?.canonicalAnswer || " ";
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

      if (matchesAction(e, "openKeybindingsModal") || matchesAction(e, "drillToggleHelp")) {
        e.preventDefault();
        setShowKeybindingsModal((v) => !v);
      } else if (matchesAction(e, "pitchOpenCheatsheet")) {
        e.preventDefault();
        setShowCheatsheet((v) => !v);
      } else if (matchesAction(e, "pitchToggleInputMode")) {
        e.preventDefault();
        setShowTextInput((v) => !v);
      } else if (matchesAction(e, "pitchRetry") && session.phase === "result") {
        e.preventDefault();
        soundFX.playSuikinkutsu();
        session.retry();
      } else if (matchesAction(e, "pitchSkip") && session.phase === "result") {
        e.preventDefault();
        soundFX.playSuikinkutsu();
        session.startNext();
      } else if (matchesAction(e, "pitchListenPrompt") && session.phase !== "idle") {
        e.preventDefault();
        playPromptAudio(false);
      } else if (e.key === "Escape") {
        if (showCheatsheet) {
          setShowCheatsheet(false);
        } else if (showKeybindingsModal) {
          setShowKeybindingsModal(false);
        } else if (session.phase !== "idle") {
          session.setPhase("idle" as any);
          setShowSummary(false);
          stopWebSpeech();
        }
      } else if (matchesAction(e, "pitchSubmitOrNext") || matchesAction(e, "drillSubmitOrNext")) {
        e.preventDefault();
        if (session.phase === "ready") {
          session.startVoiceRecording();
        } else if (session.phase === "waiting_for_speech" || session.phase === "recording") {
          handleDirectSubmit();
        } else if (session.phase === "result") {
          soundFX.playSuikinkutsu();
          session.startNext();
        }
      } else if (matchesAction(e, "pitchStartVoice")) {
        if (session.phase === "ready") {
          e.preventDefault();
          session.startVoiceRecording();
        }
      }
    };

    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [session.phase, transcriptInput, session.speech.transcript, showCheatsheet, showKeybindingsModal, matchesAction, playPromptAudio]);

  const formatSessionTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  if (showSummary || session.phase === "summary") {
    return (
      <div className="py-6 animate-in fade-in duration-300">
        <PitchSessionSummary
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
        <PitchLobby
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
          onStartSession={() => {
            soundFX.playKatana();
            session.startSession();
          }}
          onOpenCheatsheet={() => setShowCheatsheet(true)}
          onOpenHelp={() => setShowKeybindingsModal(true)}
          error={session.error}
        />

        <PitchCheatsheetModal isOpen={showCheatsheet} onClose={() => setShowCheatsheet(false)} />
        <GlobalKeybindingsModal isOpen={showKeybindingsModal} onClose={() => setShowKeybindingsModal(false)} />
      </div>
    );
  }

  const isEvaluating = session.phase === "evaluating" || session.phase === "loading";
  const isRecordingOrWaiting = session.phase === "waiting_for_speech" || session.phase === "recording";
  const currentSubModeInfo = PITCH_SUB_MODES.find((m) => m.id === subMode) || PITCH_SUB_MODES[0];

  return (
    <div className="max-w-5xl mx-auto space-y-4 animate-in fade-in duration-300 pb-8">
      {/* Session Top Status Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 rounded-2xl bg-card border border-border/80 washi-texture shadow-xs">
        <div className="flex items-center gap-2">
          <Badge variant={currentSubModeInfo.badgeVariant} size="sm" className="font-bold">
            {currentSubModeInfo.ja}
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
            className="h-8 gap-1 text-xs font-bold border-sky-500/30 text-sky-700 dark:text-sky-300 hover:bg-sky-500/10"
            title="Mở Sổ tay Cao độ & Phách"
          >
            <BookOpen className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Sổ tay ({formatKeyDisplay(keybindings.pitchOpenCheatsheet)})</span>
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
          <PitchPromptCard
            exercise={activeExercise}
            subtitleMode={subtitleMode}
            onPlayAudio={() => playPromptAudio(false)}
            phase={session.phase}
          />

          {isEvaluating && (
            <div className="p-5 rounded-3xl border border-primary/20 bg-primary/5 text-center space-y-2 animate-pulse washi-texture">
              <div className="flex items-center justify-center gap-2 font-bold text-sm text-primary">
                <Sparkles className="h-4 w-4 animate-spin" />
                <span>✨ Đang phân tích đường cao độ F0, Mora & Vô thanh hóa...</span>
              </div>
              <p className="text-xs text-muted-foreground">
                So sánh contour semitone tương đối và độ đồng đều nhịp phách
              </p>
            </div>
          )}

          {session.phase === "result" && session.result && (
            <PitchResultCard
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
                <h4 className="font-bold text-base text-foreground">Bạn đã sẵn sàng phát âm?</h4>
                <p className="text-xs text-muted-foreground">
                  Bấm nút bên dưới hoặc phím <kbd className="px-1.5 py-0.5 rounded bg-muted border text-[11px] font-mono font-bold">{formatKeyDisplay(keybindings.pitchStartVoice)}</kbd> để kích hoạt microphone
                </p>
              </div>
              <Button
                variant="akane"
                size="lg"
                onClick={() => session.startVoiceRecording()}
                className="font-bold gap-2 text-sm shadow-md"
              >
                <Mic className="h-4 w-4" />
                <span>🎙️ Bắt Đầu Phát Âm</span>
              </Button>
            </div>
          )}
        </div>

        {/* Right 1 Column: Timer & Speech Controls */}
        <div className="space-y-4">
          <PitchTimer
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
                title={`Đổi chế độ nhập (${formatKeyDisplay(keybindings.pitchToggleInputMode)})`}
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
                Nhận diện âm thanh (ja-JP):
              </span>
              <div className="text-xs font-bold font-jp text-foreground">
                {session.speech.transcript ? (
                  <span>“{session.speech.transcript}”</span>
                ) : isRecordingOrWaiting ? (
                  <span className="text-muted-foreground italic font-sans font-normal animate-pulse">
                    Đang lắng nghe âm thanh tiếng Nhật...
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
                  placeholder="Nhập từ vựng phát âm của bạn (VD: 雨 / 飴 / おじいさん)..."
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
                Gửi ({formatKeyDisplay(keybindings.pitchSubmitOrNext)})
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="font-bold text-xs"
                onClick={() => session.skip()}
                disabled={isEvaluating}
              >
                Bỏ qua ({formatKeyDisplay(keybindings.pitchSkip)})
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

      <PitchCheatsheetModal isOpen={showCheatsheet} onClose={() => setShowCheatsheet(false)} />
      <GlobalKeybindingsModal isOpen={showKeybindingsModal} onClose={() => setShowKeybindingsModal(false)} />

      <CoachPanel open={coachOpen} onClose={() => setCoachOpen(false)} />
    </div>
  );
}
"""

FILES_PITCH = {
    r"E:\SpeakingTraining\apps\web\features\pitch\services\pitch-api.ts": PITCH_API,
    r"E:\SpeakingTraining\apps\web\features\pitch\components\PitchLobby.tsx": PITCH_LOBBY,
    r"E:\SpeakingTraining\apps\web\features\pitch\components\PitchPromptCard.tsx": PITCH_PROMPT_CARD,
    r"E:\SpeakingTraining\apps\web\features\pitch\components\PitchResultCard.tsx": PITCH_RESULT_CARD,
    r"E:\SpeakingTraining\apps\web\features\pitch\components\PitchSessionSummary.tsx": PITCH_SESSION_SUMMARY,
    r"E:\SpeakingTraining\apps\web\features\pitch\components\PitchCheatsheetModal.tsx": PITCH_CHEATSHEET_MODAL,
    r"E:\SpeakingTraining\apps\web\features\pitch\index.ts": PITCH_INDEX,
    r"E:\SpeakingTraining\apps\web\features\pitch\hooks\usePitchSession.ts": PITCH_HOOK,
    r"E:\SpeakingTraining\apps\web\app\pitch\page.tsx": PITCH_PAGE,
}

for filepath, content in FILES_PITCH.items():
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"Successfully wrote {os.path.basename(filepath)}")

print("All 9 Pitch Lab frontend components created successfully!")
