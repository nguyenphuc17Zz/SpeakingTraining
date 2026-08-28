"use client";

import React, { useState, useEffect } from "react";
import { Badge } from "@/components/ui/badge";
import { Volume2, Sparkles, ArrowRight, BookOpen, Headphones, HelpCircle } from "lucide-react";
import type { ReflexExercise } from "../services/reflex-api";
import { translateJaToVi } from "../services/google-translate";
import { cn } from "@/lib/utils";

interface Props {
  exercise: ReflexExercise | null;
  subtitleMode?: "hidden" | "japanese" | "japanese_reading" | "vietnamese";
  onPlayAudio?: () => void;
  phase: string;
}

export function formatJapaneseConjugationTarget(target: string): string {
  if (!target) return "";
  const t = target.trim().toLowerCase();

  const map: Record<string, string> = {
    "nai": "ない形 (Phủ định)",
    "negative": "ない形 (Phủ định)",
    "nai_form": "ない形 (Phủ định)",
    "te": "て形",
    "te_form": "て形",
    "ta": "た形 (Quá khứ)",
    "past": "た形 (Quá khứ)",
    "ta_form": "た形 (Quá khứ)",
    "causative": "使役形 (Sai khiến)",
    "shieki": "使役形 (Sai khiến)",
    "passive": "受身形 (Bị động)",
    "ukemi": "受身形 (Bị động)",
    "causative_passive": "使役受身形 (Bị động sai khiến)",
    "causative-passive": "使役受身形 (Bị động sai khiến)",
    "shieki_ukemi": "使役受身形 (Bị động sai khiến)",
    "potential": "可能形 (Khả năng)",
    "kanou": "可能形 (Khả năng)",
    "volitional": "意向形 (Ý chí / Rủ rê)",
    "ikou": "意向形 (Ý chí / Rủ rê)",
    "conditional": "仮定形 (ば形 - Điều kiện)",
    "ba": "仮定形 (ば形 - Điều kiện)",
    "tara": "〜たら形 (Điều kiện)",
    "tai": "〜たい形 (Mong muốn)",
    "imperative": "命令形 (Mệnh lệnh)",
    "meirei": "命令形 (Mệnh lệnh)",
    "prohibitive": "禁止形 (Cấm chỉ)",
    "kinshi": "禁止形 (Cấm chỉ)",
    "polite": "丁寧形 (ます形)",
    "masu": "丁寧形 (ます形)",
    "plain": "普通形 (辞書形)",
    "jisho": "普通形 (辞書形)",
    "dictionary": "普通形 (辞書形)",
  };

  if (map[t]) return map[t];
  return target;
}

export function ReflexPromptCard({ exercise, subtitleMode = "japanese", onPlayAudio, phase }: Props) {
  const [liveTranslation, setLiveTranslation] = useState<string>("");

  const rc = exercise?.extra_metadata?.reflex_config || {};
  const prompt = rc.prompt || exercise?.scenario || exercise?.title || "";
  const isConjugation = exercise?.exercise_type === "reflex_conjugation";
  const verb = rc.verb;
  const rawTarget = rc.conjugation_target || rc.form || "";
  const target = formatJapaneseConjugationTarget(rawTarget);
  const isPlaying = phase === "prompt_playing";

  const staticTranslation =
    rc.translation ||
    rc.vietnamese ||
    (exercise?.scenario && exercise.scenario !== prompt ? exercise.scenario : null) ||
    exercise?.extra_metadata?.vietnamese_translation ||
    exercise?.extra_metadata?.translation ||
    null;

  // Auto-translate using Google Translate Client Engine when in Vietnamese mode
  useEffect(() => {
    if (subtitleMode === "vietnamese" && exercise) {
      const textToTranslate = isConjugation ? (verb || prompt) : prompt;
      if (textToTranslate) {
        translateJaToVi(textToTranslate).then((res) => {
          if (res) setLiveTranslation(res);
        });
      }
    } else {
      setLiveTranslation("");
    }
  }, [subtitleMode, exercise, isConjugation, verb, prompt]);

  const displayTranslation = liveTranslation || staticTranslation;

  if (!exercise) {
    return (
      <div className="p-8 text-center rounded-3xl border border-dashed border-border bg-card/60 washi-texture flex flex-col items-center justify-center space-y-2">
        <div className="h-8 w-8 rounded-full border-2 border-primary/20 border-t-primary animate-spin" />
        <p className="text-xs font-bold text-muted-foreground">Đang chuẩn bị đề bài phản xạ...</p>
      </div>
    );
  }

  // Label formatting
  const subModeMap: Record<string, { label: string; ja: string; color: "sakura" | "kintsugi" | "matcha" | "fuji" | "jlpt" }> = {
    reflex_conjugation: { label: "Chia Thể Động Từ", ja: "活用", color: "sakura" },
    reflex_qna: { label: "Hỏi - Đáp Tức Thì", ja: "速答", color: "matcha" },
    reflex_transformation: { label: "Biến Đổi Câu", ja: "文型変換", color: "fuji" },
    reflex_context: { label: "Phản Ứng Tình Huống", ja: "状況対応", color: "kintsugi" },
    mixed: { label: "Mixed Adaptive", ja: "混合", color: "kintsugi" },
  };

  const modeInfo = subModeMap[exercise.exercise_type] || { label: "Reflex Blitz", ja: "瞬発", color: "jlpt" };

  return (
    <div className="relative overflow-hidden rounded-3xl border border-border/90 bg-card shadow-sm washi-texture transition-all duration-300">
      {/* Top Header Strip */}
      <div className="bg-muted/40 border-b border-border/70 px-5 py-2.5 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Badge variant={modeInfo.color} size="sm" className="font-bold">
            {modeInfo.ja} • {modeInfo.label}
          </Badge>
        </div>

        <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground">
          <span className="px-2 py-0.5 rounded-md bg-background border text-[10px] uppercase font-bold tracking-wider">
            {exercise.difficulty || "Normal"}
          </span>
          <span>•</span>
          <span className="text-primary font-mono font-bold">
            {(rc.timer_limit_ms || exercise.timerLimitMs || 3000) / 1000}s
          </span>
        </div>
      </div>

      {/* Main Prompt Content Area */}
      <div className="p-5 md:p-6 space-y-4">
        {isConjugation ? (
          subtitleMode === "hidden" ? (
            /* Audio-Only Mode for Conjugation */
            <div className="p-4 rounded-2xl bg-muted/40 border border-dashed text-center text-xs text-muted-foreground italic flex flex-col items-center justify-center space-y-2 max-w-md mx-auto">
              <div className="flex items-center gap-2 font-bold text-primary text-sm not-italic">
                <Headphones className="h-5 w-5 animate-pulse" />
                <span>Chế độ Audio-Only: Hãy lắng nghe động từ qua loa</span>
              </div>
              <p className="not-italic text-foreground">
                Chuyển sang: <span className="font-extrabold text-primary font-jp">{target || "Thể yêu cầu"}</span>
              </p>
            </div>
          ) : (
            /* Visible Japanese / Vietnamese Mode for Conjugation */
            <div className="text-center space-y-3">
              <span className="inline-block text-[11px] font-bold uppercase tracking-widest text-muted-foreground">
                Động từ gốc
              </span>
              <div className="text-3xl md:text-4xl font-black font-jp tracking-tight text-foreground">
                {verb || prompt}
              </div>

              {displayTranslation && subtitleMode === "vietnamese" && (
                <div className="text-xs md:text-sm font-bold text-primary animate-in fade-in duration-200">
                  (Nghĩa: {displayTranslation})
                </div>
              )}

              {target && (
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-2xl bg-primary/10 border border-primary/25 shadow-xs animate-in fade-in zoom-in duration-200">
                  <span className="text-xs font-bold text-muted-foreground">Chuyển sang:</span>
                  <span className="text-sm md:text-base font-black font-jp text-primary flex items-center gap-1.5">
                    <ArrowRight className="h-4 w-4" />
                    {target}
                  </span>
                </div>
              )}
            </div>
          )
        ) : (
          /* Q&A / Transformation / Context Modes */
          <div className="text-center space-y-2 max-w-xl mx-auto">
            {subtitleMode === "hidden" ? (
              <div className="p-4 rounded-2xl bg-muted/40 border border-dashed text-center text-xs text-muted-foreground italic flex flex-col items-center justify-center space-y-1.5">
                <div className="flex items-center gap-2 font-bold text-primary text-sm not-italic">
                  <Headphones className="h-4 w-4 animate-pulse" />
                  <span>Chế độ Audio-Only: Hãy lắng nghe câu hỏi và phản xạ</span>
                </div>
                <p>Nội dung đề bài được ẩn để rèn luyện phản xạ thính giác 100%</p>
              </div>
            ) : (
              <div className="text-xl md:text-2xl font-bold font-jp leading-relaxed text-foreground tracking-tight">
                {prompt}
              </div>
            )}

            {displayTranslation && subtitleMode === "vietnamese" && (
              <div className="text-xs md:text-sm text-foreground/90 font-medium pt-1.5 border-t border-border/60 bg-primary/5 p-2 rounded-xl mt-2 animate-in fade-in duration-200">
                🇻🇳 Dịch nghĩa: <span className="font-bold text-primary">{displayTranslation}</span>
              </div>
            )}

            {exercise.instructions && subtitleMode !== "hidden" && (
              <div className="text-xs text-muted-foreground/90 font-medium">
                🎯 {exercise.instructions}
              </div>
            )}
          </div>
        )}

        {/* Audio Prompt Player */}
        <div className="flex items-center justify-center gap-3 pt-1">
          <button
            type="button"
            onClick={onPlayAudio}
            className={cn(
              "inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all shadow-xs border",
              isPlaying
                ? "bg-primary text-primary-foreground border-primary animate-pulse ring-2 ring-primary/30"
                : "bg-muted/70 text-foreground border-border hover:bg-muted hover:border-primary/40"
            )}
            title="Nghe lại câu hỏi đề bài"
          >
            <Volume2 className={cn("h-3.5 w-3.5 text-primary", isPlaying && "text-white animate-bounce")} />
            <span>{isPlaying ? "Đang phát audio..." : "Nghe lại đề bài"}</span>
          </button>
        </div>
      </div>
    </div>
  );
}

