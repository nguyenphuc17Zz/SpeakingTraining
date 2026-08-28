"use client";

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
