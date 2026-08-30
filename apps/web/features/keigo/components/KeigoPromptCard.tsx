"use client";

import { UniversalFurigana } from "@/components/japanese/UniversalFurigana";

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
  Lightbulb,
  HelpCircle,
  Users,
  ShieldAlert,
} from "lucide-react";
import type { KeigoExercise } from "../services/keigo-api";
import { translateJaToVi } from "@/features/reflex/services/google-translate";
import { cn } from "@/lib/utils";

interface Props {
  exercise: KeigoExercise | null;
  subtitleMode?: "hidden" | "japanese" | "japanese_reading" | "vietnamese";
  onPlayAudio?: () => void;
  phase: string;
  hintLevel?: 0 | 1 | 2;
  onCycleHint?: () => void;
}

export function KeigoPromptCard({
  exercise,
  subtitleMode = "japanese",
  onPlayAudio,
  phase,
  hintLevel = 0,
  onCycleHint,
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

  const hints = exercise?.hints || rc.hints;
  const persona = exercise?.persona || rc.persona;

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
        <p className="text-xs font-bold text-muted-foreground">Đang chuẩn bị bài tập Kính ngữ...</p>
      </div>
    );
  }

  const subModeMap: Record<
    string,
    { label: string; ja: string; color: "sakura" | "kintsugi" | "matcha" | "fuji" | "jlpt" | "torii" | "akane" }
  > = {
    keigo_vocab_blitz: { label: "Phản Xạ Động Từ", ja: "瞬間反射 ⚡", color: "akane" },
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
    <div className="relative overflow-hidden rounded-2xl border border-border/90 bg-card shadow-xs washi-texture transition-all duration-300">
      {/* Top Header Strip */}
      <div className="bg-muted/40 border-b border-border/70 px-3.5 py-2 flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5">
          <Badge variant={modeInfo.color} size="sm" className="font-bold text-[10px] py-0.5 px-2">
            {modeInfo.ja} • {modeInfo.label}
          </Badge>
          {persona?.name && (
            <span className="text-[10px] font-bold text-muted-foreground hidden sm:inline-flex items-center gap-1 px-1.5 py-0.2 rounded-full bg-background border border-border/70">
              <span>{persona.avatar || "💼"}</span>
              <span>{persona.name}</span>
            </span>
          )}
        </div>

        <div className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground">
          {onCycleHint && (
            <Button
              size="sm"
              variant={hintLevel > 0 ? "akane" : "outline"}
              onClick={onCycleHint}
              className={cn(
                "h-6 px-2 text-[11px] font-bold gap-1 transition-all",
                hintLevel === 1 && "border-amber-500 text-amber-600 bg-amber-500/10",
                hintLevel === 2 && "border-rose-500 text-rose-600 bg-rose-500/10"
              )}
              title="Mở gợi ý nấc thang (Phím H)"
            >
              <Lightbulb className={cn("h-3 w-3", hintLevel > 0 ? "fill-current animate-pulse text-amber-500" : "text-muted-foreground")} />
              <span>Gợi ý {hintLevel > 0 ? `(C${hintLevel})` : "(H)"}</span>
            </Button>
          )}

          <span className="px-1.5 py-0.2 rounded bg-background border text-[9px] uppercase font-bold tracking-wider">
            {exercise.difficulty || "Normal"}
          </span>
          <span>•</span>
          <span className="text-primary font-mono font-bold text-[11px]">
            {(exercise.timerLimitMs !== undefined ? exercise.timerLimitMs : 5000) > 0
              ? `${(exercise.timerLimitMs ?? 5000) / 1000}s`
              : "∞"}
          </span>
        </div>
      </div>

      {/* Main Prompt Content Area */}
      <div className="p-3.5 sm:p-4 space-y-2.5">
        {/* Interactive 3-Party Uchi - Soto Relationship Diagram */}
        <div className="p-3.5 rounded-2xl bg-muted/40 border border-border/70 flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Ngữ cảnh:</span>
            <div className="flex items-center gap-1.5 font-bold">
              <span className="px-2.5 py-1 rounded-xl bg-rose-500/10 text-rose-600 border border-rose-500/20 text-[11px] flex items-center gap-1">
                <span>🧑‍💼</span>
                <span>{speakerRole} [{speakerGroup}]</span>
              </span>
              <ArrowRight className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="px-2.5 py-1 rounded-xl bg-emerald-500/10 text-emerald-600 border border-emerald-500/20 text-[11px] flex items-center gap-1">
                <span>{persona?.avatar || "💼"}</span>
                <span>{listenerRole} [{listenerGroup}]</span>
              </span>
            </div>
          </div>

          {referentRole && (
            <div className="flex items-center gap-1.5 text-muted-foreground text-[11px]">
              <span>Chủ thể hành động:</span>
              <span className="font-bold text-foreground px-2 py-0.5 rounded-md bg-background border border-primary/20">
                {referentRole} {referentRole === "MANAGER" || referentRole === "SELF" ? (speakerGroup === "UCHI" ? "(Uchi ➔ Khiêm nhường)" : "(Soto ➔ Tôn kính)") : ""}
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

            <div className="text-xl sm:text-2xl md:text-3xl font-black font-jp tracking-tight text-foreground px-2 flex justify-center">
              <UniversalFurigana text={prompt} fontSize="xl" />
            </div>

            {displayTranslation && (
              <p className="text-xs sm:text-sm font-medium text-muted-foreground max-w-lg mx-auto leading-relaxed">
                🇻🇳 {displayTranslation}
              </p>
            )}
          </div>
        )}

        {/* Multi-Tier Scaffolding Hint Area */}
        {hintLevel > 0 && hints && (
          <div className="rounded-2xl border border-amber-500/30 bg-amber-500/8 dark:bg-amber-950/20 p-4 space-y-2.5 animate-in fade-in slide-in-from-top-2 duration-200">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-amber-700 dark:text-amber-300 flex items-center gap-1.5">
                <Lightbulb className="h-4 w-4 text-amber-500 fill-current" />
                <span>💡 Gợi Ý Nấc Thang {hintLevel === 1 ? "(Cấp 1: Hướng & Động từ)" : "(Cấp 2: Khung câu)"}</span>
              </span>
              <span className="text-[10px] text-muted-foreground">Bấm H để đổi nấc gợi ý</span>
            </div>

            {hintLevel >= 1 && hints.tier1 && (
              <div className="p-2.5 rounded-xl bg-background/90 border border-amber-500/20 text-xs font-medium text-foreground">
                <span className="font-bold text-amber-600 dark:text-amber-400 mr-1.5">[Nấc 1]:</span>
                <span>{hints.tier1}</span>
              </div>
            )}

            {hintLevel >= 2 && hints.tier2 && (
              <div className="p-2.5 rounded-xl bg-background/90 border border-amber-500/30 text-xs font-bold text-foreground font-jp">
                <span className="font-bold text-rose-600 dark:text-rose-400 mr-1.5 font-sans">[Nấc 2]:</span>
                <UniversalFurigana text={hints.tier2} fontSize="normal" />
              </div>
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
