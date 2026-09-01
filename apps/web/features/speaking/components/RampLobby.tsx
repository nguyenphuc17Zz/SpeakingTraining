"use client";

import React from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Sparkles,
  Play,
  Settings2,
  Keyboard,
  Shuffle,
  BookOpen,
  Zap,
  Target,
  Clock,
  Layers,
  CheckCircle2,
  Flame,
  Volume2,
  ArrowRight,
  ShieldCheck,
  Timer,
  Check,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { SakuraPetals } from "@/components/ui/sakura-petals";
import { soundFX } from "@/lib/sound-fx";
import { UniversalFurigana } from "@/components/japanese/UniversalFurigana";

export interface RampGoalConfig {
  id: string;
  label: string;
  subLabel: string;
  ja: string;
  stageBadge: string;
  stageRange: string;
  icon: any;
  desc: string;
  badgeVariant: "sakura" | "kintsugi" | "matcha" | "fuji" | "jlpt" | "torii" | "akane";
  iconColor: string;
  highlights: string[];
  examplePrompt: string;
  examplePromptVi: string;
  exampleTarget: string;
  exampleTargetVi: string;
  scaffoldDesc: string;
}

export const RAMP_GOALS: RampGoalConfig[] = [
  {
    id: "general",
    label: "Toàn diện",
    subLabel: "Adaptive",
    ja: "総合",
    stageBadge: "Stage 1-10",
    stageRange: "Stage 1 → 10 (Lộ trình phát ngôn 11 nấc thang)",
    icon: Shuffle,
    desc: "Tăng dần từ 1 câu ngắn → 60s độc lập theo phản xạ thích ứng AI",
    badgeVariant: "matcha",
    iconColor: "text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
    highlights: [
      "Thích ứng linh hoạt theo độ nhạy của bạn",
      "Chuyển hóa ngữ pháp N5→N1 sang phản xạ",
      "Đầy đủ 11 nấc thang từ nhại câu đến tự do",
    ],
    examplePrompt: "今日、何をしましたか？",
    examplePromptVi: "Hôm nay bạn đã làm những gì?",
    exampleTarget: "「友達とカフェへ行って、日本語を勉強しました。」",
    exampleTargetVi: "Tôi đã đi cà phê với bạn và học tiếng Nhật.",
    scaffoldDesc: "Giàn giáo thông minh 4 cấp (Âm mẫu ➔ Câu mồi ➔ Từ khóa ➔ Tự do)",
  },
  {
    id: "fluency",
    label: "Phản xạ nhanh",
    subLabel: "Fluency ⚡",
    ja: "瞬発",
    stageBadge: "Stage 1-3",
    stageRange: "Stage 1 → 3 (Echo, Thay thế & Hoàn thành chớp nhoáng)",
    icon: Zap,
    desc: "Bật câu tiếng Nhật dưới 2s, xóa bỏ ngập ngừng ngắt quãng",
    badgeVariant: "kintsugi",
    iconColor: "text-amber-600 dark:text-amber-400 bg-amber-500/10 border-amber-500/20",
    highlights: [
      "Bật câu tức thì dưới 2.0s không cần đắn đo",
      "Ép cơ hàm quen với cấu trúc câu chuẩn",
      "Đổi tân ngữ, tính từ tức thì theo từ mồi",
    ],
    examplePrompt: "「コーヒーを飲みます」 ➔ Thay tân ngữ: [お茶]",
    examplePromptVi: "Mẫu: Tôi uống cà phê ➔ Thay thế bằng: Trà",
    exampleTarget: "「お茶を飲みます！」 (Bật ngay trong 2s)",
    exampleTargetVi: "Tôi uống trà xanh!",
    scaffoldDesc: "Đếm ngược phản xạ tức thì, rút thời gian ngẫm để tạo phản xạ tự nhiên",
  },
  {
    id: "elaboration",
    label: "Mở rộng ý",
    subLabel: "Elaboration",
    ja: "拡張",
    stageBadge: "Stage 4-6",
    stageRange: "Stage 4 → 6 (Nối câu, Thêm lý do & Đưa ví dụ)",
    icon: Target,
    desc: "Rèn thói quen nói xong luôn thêm lý do (から) hoặc ví dụ",
    badgeVariant: "matcha",
    iconColor: "text-teal-600 dark:text-teal-400 bg-teal-500/10 border-teal-500/20",
    highlights: [
      "Xóa bỏ hoàn toàn thói quen nói câu cụt lủn",
      "Tự động nối tiếp bằng から, ので, 例えば",
      "Kéo dài độ dài câu nói lên 15-25 giây tự nhiên",
    ],
    examplePrompt: "Câu hạt giống:「日本料理が好きです」 (Tôi thích món Nhật)",
    examplePromptVi: "Yêu cầu: Thêm lý do tại sao và đưa ra ví dụ món bạn thích nhất",
    exampleTarget: "「日本料理が好きです。ヘルシーだからです。例えば寿司が一番好きです。」",
    exampleTargetVi: "Tôi thích món Nhật vì rất thanh lành. Ví dụ tôi thích nhất là món sushi.",
    scaffoldDesc: "Mồi liên từ nối câu, câu hỏi định hướng (Tại sao? Với ai? Cảm giác thế nào?)",
  },
  {
    id: "independence",
    label: "Tự lập",
    subLabel: "Blind",
    ja: "自立",
    stageBadge: "Stage 7-10",
    stageRange: "Stage 7 → 10 (Rút giàn giáo & Phát ngôn độc lập 30-60s)",
    icon: Flame,
    desc: "Rút toàn bộ giàn giáo để nói tự nhiên hoàn toàn không gợi ý",
    badgeVariant: "fuji",
    iconColor: "text-sky-600 dark:text-sky-400 bg-sky-500/10 border-sky-500/20",
    highlights: [
      "Chỉ nhìn 2-3 từ khóa hoặc hoàn toàn nghe chay",
      "Tự tổ chức ý và phát biểu 30-60s trôi chảy",
      "Thử thách đối đáp câu hỏi đào sâu từ AI Coach",
    ],
    examplePrompt: "Chủ đề:「週末の過ごし方」 • Từ khóa: 友達 / 旅行 / 楽しかった",
    examplePromptVi: "Chủ đề: Cuối tuần của bạn • Từ khóa: Bạn bè / Du lịch / Vui vẻ",
    exampleTarget: "「先週末は友達と京都へ旅行に行きました。古いお寺を見学して、とても楽しかったです...」",
    exampleTargetVi: "Tự do phát ngôn bài nói trọn vẹn 30-60s không cần văn bản gợi ý",
    scaffoldDesc: "Rút sạch câu mẫu, chỉ để lại từ khóa mồi ý tưởng để phát huy tự lập",
  },
];

export const RAMP_DURATIONS = [0, 5, 10, 15, 20, 30];

interface RampLobbyProps {
  selectedGoal: string;
  onGoalChange: (goal: string) => void;
  duration: number;
  onDurationChange: (dur: number) => void;
  subtitleMode: "hidden" | "japanese" | "vietnamese";
  onSubtitleModeChange: (mode: "hidden" | "japanese" | "vietnamese") => void;
  onStartSession: () => void;
  onOpenCheatsheet: () => void;
  onOpenKeybindings: () => void;
  isLoading?: boolean;
}

export function RampLobby({
  selectedGoal,
  onGoalChange,
  duration,
  onDurationChange,
  subtitleMode,
  onSubtitleModeChange,
  onStartSession,
  onOpenCheatsheet,
  onOpenKeybindings,
  isLoading = false,
}: RampLobbyProps) {
  const currentGoal = RAMP_GOALS.find((g) => g.id === selectedGoal) || RAMP_GOALS[0];
  const CurrentIcon = currentGoal.icon;

  const handleSelectGoal = (id: string) => {
    soundFX.playKatana();
    onGoalChange(id);
  };

  return (
    <div className="space-y-3.5 max-w-5xl mx-auto animate-in fade-in duration-300">
      {/* 1. Compact Hero Header Washi */}
      <div className="relative overflow-hidden rounded-2xl border border-border bg-card/95 seigaiha-pattern shadow-xs p-4 md:p-5 washi-texture">
        <SakuraPetals count={2} />
        <div className="absolute -top-10 -right-10 h-32 w-32 rounded-full bg-enso-gradient opacity-40 pointer-events-none" />

        <div className="relative flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="h-7 w-7 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center text-primary shrink-0">
                <Sparkles className="h-4 w-4" />
              </span>
              <h1 className="text-base md:text-lg font-extrabold tracking-tight text-foreground flex items-center gap-2">
                <span>Phục Hồi Phát Ngôn</span>
                <span className="text-xs font-normal text-muted-foreground font-jp">
                  アウトプット・リハビリ
                </span>
              </h1>
              <Badge variant="matcha" size="sm" className="font-bold text-[10px]">
                STAGE 0 → 10
              </Badge>
            </div>

            <p className="text-xs text-muted-foreground line-clamp-1">
              Rèn chuyển hóa ngữ pháp thụ động thành câu nói trọn vẹn và phản xạ 60 giây độc lập.
            </p>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <Button
              variant="outline"
              size="sm"
              onClick={onOpenCheatsheet}
              className="h-8 px-2.5 rounded-lg text-xs font-semibold border-border gap-1"
            >
              <BookOpen className="h-3.5 w-3.5 text-primary" />
              <span>Cẩm nang</span>
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={onOpenKeybindings}
              className="h-8 px-2 rounded-lg text-muted-foreground hover:text-foreground"
              title="Phím tắt"
            >
              <Keyboard className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* 2. Mục tiêu trọng tâm (Compact 4-Card Grid) */}
      <div className="space-y-2">
        <div className="flex items-center justify-between px-1">
          <div className="flex items-center gap-1.5 text-xs font-bold text-foreground">
            <Target className="h-3.5 w-3.5 text-primary" />
            <span>Chọn 1 Trong 4 Chuyên Đề Phục Hồi</span>
          </div>
          <span className="text-[11px] text-muted-foreground">Bấm chọn để xem giáo án chi tiết</span>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-2.5">
          {RAMP_GOALS.map((goal) => {
            const Icon = goal.icon;
            const isSelected = selectedGoal === goal.id;
            return (
              <div
                key={goal.id}
                onClick={() => handleSelectGoal(goal.id)}
                className={cn(
                  "p-3 rounded-xl border transition-all cursor-pointer flex flex-col justify-between gap-1.5 text-left washi-texture group relative",
                  isSelected
                    ? "bg-card border-primary shadow-sm ring-1 ring-primary/40"
                    : "bg-card/70 border-border/80 hover:border-primary/40 hover:bg-card"
                )}
              >
                <div className="flex items-center justify-between gap-1">
                  <div className="flex items-center gap-1.5 min-w-0">
                    <span className={cn("h-6 w-6 rounded-md border flex items-center justify-center shrink-0", goal.iconColor)}>
                      <Icon className="h-3.5 w-3.5" />
                    </span>
                    <span className="text-xs font-bold text-foreground truncate">
                      {goal.label}
                    </span>
                  </div>
                  <span className="text-[9px] px-1 py-0.2 rounded bg-muted/60 font-mono text-muted-foreground font-bold shrink-0">
                    {goal.stageBadge}
                  </span>
                </div>

                <p className="text-[11px] text-muted-foreground leading-tight line-clamp-2">
                  {goal.desc}
                </p>

                <div className="flex items-center justify-between pt-1 border-t border-border/40 text-[10px]">
                  <Badge variant={goal.badgeVariant} size="sm" className="text-[9px] font-bold px-1.5 py-0">
                    {goal.ja}
                  </Badge>
                  {isSelected ? (
                    <span className="flex items-center gap-1 font-extrabold text-primary">
                      <Check className="h-3 w-3" /> Đang chọn
                    </span>
                  ) : (
                    <span className="text-muted-foreground group-hover:text-primary transition-colors">
                      Chọn ➔
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 2.5. Spotlight Chi Tiết Chuyên Đề Đang Chọn (Hiện Ngay Khi Bấm) */}
      <div className="p-4 sm:p-4.5 rounded-2xl border border-primary/30 bg-card washi-texture shadow-xs space-y-3 relative overflow-hidden animate-in fade-in duration-200">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border/60 pb-2.5">
          <div className="flex items-center gap-2.5">
            <span className={cn("h-7 w-7 rounded-lg border flex items-center justify-center shrink-0", currentGoal.iconColor)}>
              <CurrentIcon className="h-4 w-4" />
            </span>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-extrabold text-foreground">
                  {currentGoal.label} ({currentGoal.subLabel})
                </span>
                <Badge variant={currentGoal.badgeVariant} size="sm" className="text-[10px] font-bold">
                  {currentGoal.ja}
                </Badge>
              </div>
              <span className="text-xs font-semibold text-primary block">
                {currentGoal.stageRange}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="primary"
              onClick={onStartSession}
              isLoading={isLoading}
              className="h-8 px-3 rounded-lg text-xs font-bold gap-1.5 shadow-xs"
            >
              <Play className="h-3.5 w-3.5 fill-current" />
              <span>Vào Luyện Chế Độ Này</span>
            </Button>
          </div>
        </div>

        {/* Điểm nhấn chuyên đề */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
          {currentGoal.highlights.map((point, idx) => (
            <div
              key={idx}
              className="p-2 rounded-xl bg-muted/40 border border-border/70 text-[11px] text-foreground flex items-start gap-1.5"
            >
              <CheckCircle2 className="h-3.5 w-3.5 text-primary shrink-0 mt-0.5" />
              <span className="leading-snug">{point}</span>
            </div>
          ))}
        </div>

        {/* Mẫu bài tập thực tế */}
        <div className="p-3 rounded-xl bg-muted/30 border border-border/80 space-y-1.5 text-xs">
          <div className="flex items-center justify-between text-[11px]">
            <span className="font-bold text-muted-foreground flex items-center gap-1">
              <BookOpen className="h-3 w-3 text-primary" /> Mẫu bài tập minh họa:
            </span>
            <span className="text-muted-foreground font-mono text-[10px]">
              {currentGoal.scaffoldDesc}
            </span>
          </div>

          <div className="space-y-1">
            <div className="font-jp font-bold text-foreground text-xs sm:text-sm">
              <UniversalFurigana text={currentGoal.examplePrompt} />
            </div>
            <div className="text-[11px] text-muted-foreground">
              {currentGoal.examplePromptVi}
            </div>
          </div>

          <div className="p-2 rounded-lg bg-primary/10 border border-primary/20 space-y-0.5">
            <div className="font-jp font-bold text-primary text-xs sm:text-sm">
              <UniversalFurigana text={currentGoal.exampleTarget} />
            </div>
            <div className="text-[11px] text-primary/80">
              {currentGoal.exampleTargetVi}
            </div>
          </div>
        </div>
      </div>

      {/* 3. Thời lượng & Phụ đề (Single Compact Strip) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
        {/* Thời lượng */}
        <div className="p-3 rounded-xl border border-border bg-card washi-texture space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold text-muted-foreground flex items-center gap-1.5">
              <Clock className="h-3.5 w-3.5 text-primary" /> Thời lượng phiên
            </span>
            <span className="text-[11px] font-bold text-foreground font-mono">
              {duration === 0 ? "Vô hạn (∞)" : `${duration} phút`}
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            {RAMP_DURATIONS.map((d) => (
              <Button
                key={d}
                type="button"
                variant={duration === d ? "primary" : "outline"}
                size="sm"
                onClick={() => onDurationChange(d)}
                className={cn(
                  "flex-1 h-7 rounded-lg text-xs font-bold transition-all px-0",
                  duration === d
                    ? "bg-primary text-primary-foreground shadow-xs"
                    : "border-border text-muted-foreground hover:text-foreground"
                )}
              >
                {d === 0 ? "∞ Vô hạn" : `${d}m`}
              </Button>
            ))}
          </div>
        </div>

        {/* Chế độ phụ đề (Bỏ option Furigana thừa vì đã có trên Header) */}
        <div className="p-3 rounded-xl border border-border bg-card washi-texture space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold text-muted-foreground flex items-center gap-1.5">
              <Volume2 className="h-3.5 w-3.5 text-sky-500" /> Hiển thị ngữ cảnh
            </span>
            <span className="text-[10px] text-muted-foreground">Furigana chỉnh ở Header</span>
          </div>
          <div className="flex items-center gap-1.5">
            {(
              [
                { id: "vietnamese", label: "Tiếng Nhật + Dịch" },
                { id: "japanese", label: "Chỉ Tiếng Nhật" },
                { id: "hidden", label: "Ẩn phụ đề (Hard)" },
              ] as const
            ).map((sub) => (
              <Button
                key={sub.id}
                type="button"
                variant={subtitleMode === sub.id ? "primary" : "outline"}
                size="sm"
                onClick={() => onSubtitleModeChange(sub.id)}
                className={cn(
                  "flex-1 h-7 rounded-lg text-xs font-bold transition-all px-1 truncate",
                  subtitleMode === sub.id
                    ? "bg-primary text-primary-foreground shadow-xs"
                    : "border-border text-muted-foreground hover:text-foreground"
                )}
              >
                {sub.label}
              </Button>
            ))}
          </div>
        </div>
      </div>

      {/* 4. Nút Khởi Động Phiên Lớn Cuối Trang */}
      <Button
        id="ramp-start-session-btn"
        size="lg"
        variant="primary"
        onClick={onStartSession}
        isLoading={isLoading}
        className="w-full py-5 rounded-xl bg-primary hover:bg-primary/90 text-primary-foreground font-extrabold text-sm shadow-sm transition-all flex items-center justify-center gap-2 group"
      >
        <Play className="h-4 w-4 fill-current transition-transform group-hover:scale-110" />
        <span>
          Bắt Đầu Luyện: {currentGoal.label} ({duration === 0 ? "Vô hạn" : `${duration} phút`})
        </span>
        <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
      </Button>
    </div>
  );
}
