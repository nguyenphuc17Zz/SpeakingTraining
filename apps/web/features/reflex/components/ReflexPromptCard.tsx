"use client";

import { UniversalFurigana } from "@/components/japanese/UniversalFurigana";

import React, { useState, useEffect } from "react";
import { Badge } from "@/components/ui/badge";
import { Volume2, Sparkles, ArrowRight, BookOpen, Headphones, HelpCircle, Crown } from "lucide-react";
import type { ReflexExercise } from "../services/reflex-api";
import { translateJaToVi } from "../services/google-translate";
import { cn } from "@/lib/utils";

interface Props {
  exercise: ReflexExercise | null;
  subtitleMode?: "hidden" | "japanese" | "japanese_reading" | "vietnamese";
  onPlayAudio?: () => void;
  phase: string;
}

export interface ConjugationTargetDetail {
  shortName: string;
  formJa: string;
  meaning: string;
  suffixHint: string;
  fullLabel: string;
}

export const CONJUGATION_FORM_DETAILS: Record<string, ConjugationTargetDetail> = {
  nai: {
    shortName: "Thể Phủ định (〜ない)",
    formJa: "ない形",
    meaning: "Không làm / Chưa làm",
    suffixHint: "〜ない",
    fullLabel: "Thể Phủ định [〜ない] (Không làm...)",
  },
  negative: {
    shortName: "Thể Phủ định (〜ない)",
    formJa: "ない形",
    meaning: "Không làm / Chưa làm",
    suffixHint: "〜ない",
    fullLabel: "Thể Phủ định [〜ない] (Không làm...)",
  },
  nai_form: {
    shortName: "Thể Phủ định (〜ない)",
    formJa: "ない形",
    meaning: "Không làm / Chưa làm",
    suffixHint: "〜ない",
    fullLabel: "Thể Phủ định [〜ない] (Không làm...)",
  },
  te: {
    shortName: "Thể TE (〜て / 〜で)",
    formJa: "て形",
    meaning: "Nối câu, đang làm, yêu cầu nhẹ",
    suffixHint: "〜て / 〜で",
    fullLabel: "Thể TE [〜て / 〜で] (Nối câu / Đang làm...)",
  },
  te_form: {
    shortName: "Thể TE (〜て / 〜で)",
    formJa: "て形",
    meaning: "Nối câu, đang làm, yêu cầu nhẹ",
    suffixHint: "〜て / 〜で",
    fullLabel: "Thể TE [〜て / 〜で] (Nối câu / Đang làm...)",
  },
  ta: {
    shortName: "Thể Quá khứ (〜た / 〜だ)",
    formJa: "た形",
    meaning: "Đã làm",
    suffixHint: "〜た / 〜だ",
    fullLabel: "Thể Quá khứ [〜た / 〜だ] (Đã làm...)",
  },
  past: {
    shortName: "Thể Quá khứ (〜た / 〜だ)",
    formJa: "た形",
    meaning: "Đã làm",
    suffixHint: "〜た / 〜だ",
    fullLabel: "Thể Quá khứ [〜た / 〜だ] (Đã làm...)",
  },
  ta_form: {
    shortName: "Thể Quá khứ (〜た / 〜だ)",
    formJa: "た形",
    meaning: "Đã làm",
    suffixHint: "〜た / 〜だ",
    fullLabel: "Thể Quá khứ [〜た / 〜だ] (Đã làm...)",
  },
  potential: {
    shortName: "Thể Khả năng (〜れる / 〜える)",
    formJa: "可能形",
    meaning: "Có thể làm...",
    suffixHint: "〜れる / 〜える",
    fullLabel: "Thể Khả năng [〜れる / 〜える] (Có thể làm...)",
  },
  kanou: {
    shortName: "Thể Khả năng (〜れる / 〜える)",
    formJa: "可能形",
    meaning: "Có thể làm...",
    suffixHint: "〜れる / 〜える",
    fullLabel: "Thể Khả năng [〜れる / 〜える] (Có thể làm...)",
  },
  passive: {
    shortName: "Thể Bị động (〜られる / 〜れる)",
    formJa: "受身形",
    meaning: "Bị / Được làm...",
    suffixHint: "〜られる / 〜れる",
    fullLabel: "Thể Bị động [〜られる / 〜れる] (Bị / Được làm...)",
  },
  ukemi: {
    shortName: "Thể Bị động (〜られる / 〜れる)",
    formJa: "受身形",
    meaning: "Bị / Được làm...",
    suffixHint: "〜られる / 〜れる",
    fullLabel: "Thể Bị động [〜られる / 〜れる] (Bị / Được làm...)",
  },
  causative: {
    shortName: "Thể Sai khiến (〜させる / 〜せる)",
    formJa: "使役形",
    meaning: "Bắt / Cho phép làm...",
    suffixHint: "〜させる / 〜せる",
    fullLabel: "Thể Sai khiến [〜させる / 〜せる] (Bắt / Cho phép làm...)",
  },
  shieki: {
    shortName: "Thể Sai khiến (〜させる / 〜せる)",
    formJa: "使役形",
    meaning: "Bắt / Cho phép làm...",
    suffixHint: "〜させる / 〜せる",
    fullLabel: "Thể Sai khiến [〜させる / 〜せる] (Bắt / Cho phép làm...)",
  },
  causative_passive: {
    shortName: "Thể Bị động Sai khiến (〜させられる)",
    formJa: "使役受身形",
    meaning: "Bị bắt phải làm...",
    suffixHint: "〜させられる / 〜される",
    fullLabel: "Thể Bị động Sai khiến [〜させられる] (Bị bắt phải làm...)",
  },
  "causative-passive": {
    shortName: "Thể Bị động Sai khiến (〜させられる)",
    formJa: "使役受身形",
    meaning: "Bị bắt phải làm...",
    suffixHint: "〜させられる / 〜される",
    fullLabel: "Thể Bị động Sai khiến [〜させられる] (Bị bắt phải làm...)",
  },
  shieki_ukemi: {
    shortName: "Thể Bị động Sai khiến (〜させられる)",
    formJa: "使役受身形",
    meaning: "Bị bắt phải làm...",
    suffixHint: "〜させられる / 〜される",
    fullLabel: "Thể Bị động Sai khiến [〜させられる] (Bị bắt phải làm...)",
  },
  volitional: {
    shortName: "Thể Ý chí / Rủ rê (〜よう / 〜おう)",
    formJa: "意向形",
    meaning: "Hãy cùng làm / Dự định làm...",
    suffixHint: "〜よう / 〜おう",
    fullLabel: "Thể Ý chí / Rủ rê [〜よう / 〜おう] (Hãy cùng làm...)",
  },
  ikou: {
    shortName: "Thể Ý chí / Rủ rê (〜よう / 〜おう)",
    formJa: "意向形",
    meaning: "Hãy cùng làm / Dự định làm...",
    suffixHint: "〜よう / 〜おう",
    fullLabel: "Thể Ý chí / Rủ rê [〜よう / 〜おう] (Hãy cùng làm...)",
  },
  ba: {
    shortName: "Thể Điều kiện (〜ば)",
    formJa: "ば形",
    meaning: "Nếu làm...",
    suffixHint: "〜えば / 〜れば",
    fullLabel: "Thể Điều kiện BA [〜ば] (Nếu làm...)",
  },
  conditional: {
    shortName: "Thể Điều kiện (〜ば)",
    formJa: "ば形",
    meaning: "Nếu làm...",
    suffixHint: "〜えば / 〜れば",
    fullLabel: "Thể Điều kiện BA [〜ば] (Nếu làm...)",
  },
  tara: {
    shortName: "Thể Điều kiện (〜たら)",
    formJa: "たら形",
    meaning: "Nếu / Sau khi làm...",
    suffixHint: "〜たら / 〜だら",
    fullLabel: "Thể Điều kiện TARA [〜たら] (Nếu / Sau khi làm...)",
  },
  tai: {
    shortName: "Thể Mong muốn (〜たい)",
    formJa: "たい形",
    meaning: "Muốn làm...",
    suffixHint: "〜たい",
    fullLabel: "Thể Mong muốn [〜たい] (Muốn làm...)",
  },
  imperative: {
    shortName: "Thể Mệnh lệnh (〜ろ / 〜え)",
    formJa: "命令形",
    meaning: "Hãy làm! / Ra lệnh",
    suffixHint: "〜ろ / 〜え",
    fullLabel: "Thể Mệnh lệnh [〜ろ / 〜え] (Hãy làm!)",
  },
  meirei: {
    shortName: "Thể Mệnh lệnh (〜ろ / 〜え)",
    formJa: "命令形",
    meaning: "Hãy làm! / Ra lệnh",
    suffixHint: "〜ろ / 〜え",
    fullLabel: "Thể Mệnh lệnh [〜ろ / 〜え] (Hãy làm!)",
  },
  prohibitive: {
    shortName: "Thể Cấm chỉ (〜な)",
    formJa: "禁止形",
    meaning: "Cấm làm!",
    suffixHint: "〜な",
    fullLabel: "Thể Cấm chỉ [〜な] (Cấm làm!)",
  },
  kinshi: {
    shortName: "Thể Cấm chỉ (〜な)",
    formJa: "禁止形",
    meaning: "Cấm làm!",
    suffixHint: "〜な",
    fullLabel: "Thể Cấm chỉ [〜な] (Cấm làm!)",
  },
  polite: {
    shortName: "Thể Lịch sự (〜ます)",
    formJa: "ます形",
    meaning: "Lịch sự",
    suffixHint: "〜ます",
    fullLabel: "Thể Lịch sự [〜ます]",
  },
  masu: {
    shortName: "Thể Lịch sự (〜ます)",
    formJa: "ます形",
    meaning: "Lịch sự",
    suffixHint: "〜ます",
    fullLabel: "Thể Lịch sự [〜ます]",
  },
  plain: {
    shortName: "Thể Từ điển (Nguyên mẫu)",
    formJa: "辞書形",
    meaning: "Nguyên mẫu",
    suffixHint: "〜る / 〜う",
    fullLabel: "Thể Từ điển [辞書形] (Nguyên mẫu)",
  },
  dictionary: {
    shortName: "Thể Từ điển (Nguyên mẫu)",
    formJa: "辞書形",
    meaning: "Nguyên mẫu",
    suffixHint: "〜る / 〜う",
    fullLabel: "Thể Từ điển [辞書形] (Nguyên mẫu)",
  },
  jisho: {
    shortName: "Thể Từ điển (Nguyên mẫu)",
    formJa: "辞書形",
    meaning: "Nguyên mẫu",
    suffixHint: "〜る / 〜う",
    fullLabel: "Thể Từ điển [辞書形] (Nguyên mẫu)",
  },
};

export function getConjugationTargetDetail(target: string): ConjugationTargetDetail | null {
  if (!target) return null;
  const t = target.trim().toLowerCase();
  return CONJUGATION_FORM_DETAILS[t] || null;
}

export function formatJapaneseConjugationTarget(target: string): string {
  if (!target) return "";
  const detail = getConjugationTargetDetail(target);
  if (detail) return detail.fullLabel;
  return target;
}

export function ReflexPromptCard({ exercise, subtitleMode = "japanese", onPlayAudio, phase }: Props) {
  const [liveTranslation, setLiveTranslation] = useState<string>("");

  const rc = exercise?.extra_metadata?.reflex_config || {};
  const prompt = rc.prompt || exercise?.scenario || exercise?.title || "";
  const isConjugation = exercise?.exercise_type === "reflex_conjugation";
  const isVocabulary = exercise?.exercise_type === "reflex_vocabulary";
  const isKeigoVocab = exercise?.exercise_type === "reflex_keigo_vocab";
  const verb = rc.verb;
  const rawTarget = rc.conjugation_target || rc.form || "";
  const target = formatJapaneseConjugationTarget(rawTarget);
  const targetDetail = getConjugationTargetDetail(rawTarget);
  const isPlaying = phase === "prompt_playing";

  // Keigo-specific data
  const keigoTargetType = rc.target_type || "sonkeigo";
  const keigoTargetLabel = rc.target_label_vi || "Kính ngữ";
  const keigoMeaning = rc.prompt_translation || rc.word_meaning_vi || "";
  const keigoReading = rc.prompt_reading || rc.word_reading || "";

  // Vocabulary-specific data
  const vocabDirection: "ja_to_vi" | "vi_to_ja" = rc.direction || "ja_to_vi";
  const vocabWord = rc.prompt || "";
  const vocabReading = rc.word_reading || rc.prompt_reading || "";
  const vocabMeaning = rc.word_meaning_vi || rc.prompt_translation || "";
  const vocabWordType: string = rc.word_type || "noun";
  const vocabJlpt: string = rc.jlpt_level || "";

  const wordTypeLabel: Record<string, string> = {
    noun: "名 Danh từ",
    verb: "動 Động từ",
    adj_i: "形(い) Tính từ い",
    adj_na: "形(な) Tính từ な",
    adverb: "副 Trạng từ",
  };

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
    reflex_vocabulary: { label: "Từ Vựng Phản Xạ", ja: "語彙", color: "fuji" },
    reflex_keigo_vocab: { label: "Kính Ngữ Từ Vựng", ja: "敬語単語", color: "kintsugi" },
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
          {rc.jlpt_level && (
            <Badge variant="jlpt" size="sm" className="font-extrabold text-[10px]">
              {rc.jlpt_level}
            </Badge>
          )}
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
        {isKeigoVocab ? (
          /* ====== KEIGO WORD BLITZ MODE ====== */
          <div className="text-center space-y-4">
            {/* Keigo target badge */}
            <div className="flex items-center justify-center gap-2 flex-wrap">
              <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-black border shadow-2xs ${
                keigoTargetType === "sonkeigo"
                  ? "bg-amber-500/15 border-amber-500/30 text-amber-600 dark:text-amber-400"
                  : keigoTargetType === "kenjougo"
                  ? "bg-indigo-500/15 border-indigo-500/30 text-indigo-600 dark:text-indigo-400"
                  : "bg-emerald-500/15 border-emerald-500/30 text-emerald-600 dark:text-emerald-400"
              }`}>
                <Crown className="h-3.5 w-3.5" />
                <span>{keigoTargetLabel}</span>
              </span>
              {rc.jlpt_level && (
                <Badge variant="jlpt" size="sm" className="font-extrabold text-[10px]">
                  JLPT {rc.jlpt_level}
                </Badge>
              )}
            </div>

            {subtitleMode === "hidden" ? (
              <div className="p-4 rounded-2xl bg-muted/40 border border-dashed text-center text-xs text-muted-foreground italic flex flex-col items-center justify-center space-y-2">
                <div className="flex items-center gap-2 font-bold text-amber-500 text-sm not-italic">
                  <Headphones className="h-5 w-5 animate-pulse" />
                  <span>Audio-Only: Hãy lắng nghe từ gốc và nói dạng kính ngữ</span>
                </div>
              </div>
            ) : (
              <div className="space-y-2">
                <span className="inline-block text-[11px] font-bold uppercase tracking-widest text-muted-foreground">
                  Từ gốc thông thường
                </span>
                <div className="text-3xl md:text-4xl font-black font-jp tracking-tight text-foreground flex justify-center">
                  <UniversalFurigana text={prompt} fontSize="xl" />
                </div>
                {keigoReading && keigoReading !== prompt && (
                  <div className="text-sm font-bold text-muted-foreground font-jp">
                    ({keigoReading})
                  </div>
                )}
                {keigoMeaning && (
                  <div className="text-xs font-semibold text-muted-foreground">
                    Nghĩa: <span className="font-bold text-foreground">{keigoMeaning}</span>
                  </div>
                )}
                <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-2xl border shadow-xs animate-in fade-in zoom-in duration-200 ${
                  keigoTargetType === "sonkeigo"
                    ? "bg-amber-500/10 border-amber-500/25 text-amber-600 dark:text-amber-400"
                    : keigoTargetType === "kenjougo"
                    ? "bg-indigo-500/10 border-indigo-500/25 text-indigo-600 dark:text-indigo-400"
                    : "bg-emerald-500/10 border-emerald-500/25 text-emerald-600 dark:text-emerald-400"
                }`}>
                  <ArrowRight className="h-4 w-4 animate-pulse" />
                  <span className="text-sm font-black">Nói dạng: {keigoTargetLabel}</span>
                </div>
              </div>
            )}
          </div>
        ) : isVocabulary ? (
          /* ====== VOCABULARY BLITZ MODE ====== */
          <div className="text-center space-y-4">
            {/* Direction badge */}
            <div className="flex items-center justify-center gap-2">
              <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-xs font-black border ${
                vocabDirection === "ja_to_vi"
                  ? "bg-violet-500/10 border-violet-500/25 text-violet-600 dark:text-violet-400"
                  : "bg-emerald-500/10 border-emerald-500/25 text-emerald-600 dark:text-emerald-400"
              }`}>
                {vocabDirection === "ja_to_vi" ? "🇯🇵 → 🇻🇳 Nói nghĩa tiếng Việt" : "🇻🇳 → 🇯🇵 Nói từ tiếng Nhật"}
              </span>
              {vocabJlpt && (
                <Badge variant="jlpt" size="sm" className="font-extrabold text-[10px]">
                  {vocabJlpt}
                </Badge>
              )}
              {vocabWordType && (
                <span className="px-2 py-0.5 rounded-lg bg-background border text-[10px] font-bold text-muted-foreground">
                  {wordTypeLabel[vocabWordType] || vocabWordType}
                </span>
              )}
            </div>

            {subtitleMode === "hidden" ? (
              <div className="p-4 rounded-2xl bg-muted/40 border border-dashed text-center text-xs text-muted-foreground italic flex flex-col items-center justify-center space-y-2">
                <div className="flex items-center gap-2 font-bold text-primary text-sm not-italic">
                  <Headphones className="h-5 w-5 animate-pulse" />
                  <span>Audio-Only: Hãy lắng nghe và phản xạ</span>
                </div>
              </div>
            ) : vocabDirection === "ja_to_vi" ? (
              /* ja→vi: show big Japanese word */
              <div className="space-y-2">
                <span className="inline-block text-[11px] font-bold uppercase tracking-widest text-muted-foreground">
                  Từ tiếng Nhật
                </span>
                <div className="text-3xl md:text-4xl font-black font-jp tracking-tight text-foreground flex justify-center">
                  <UniversalFurigana text={vocabWord} fontSize="xl" />
                </div>
                {vocabReading && vocabReading !== vocabWord && (
                  <div className="text-sm font-bold text-muted-foreground font-jp">
                    ({vocabReading})
                  </div>
                )}
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-2xl bg-violet-500/10 border border-violet-500/25 shadow-xs animate-in fade-in zoom-in duration-200">
                  <ArrowRight className="h-4 w-4 text-violet-500 animate-pulse" />
                  <span className="text-sm font-black text-violet-600 dark:text-violet-400">Nghĩa tiếng Việt là gì?</span>
                </div>
              </div>
            ) : (
              /* vi→ja: show big Vietnamese meaning */
              <div className="space-y-2">
                <span className="inline-block text-[11px] font-bold uppercase tracking-widest text-muted-foreground">
                  Nghĩa tiếng Việt
                </span>
                <div className="text-2xl md:text-3xl font-black tracking-tight text-foreground">
                  {vocabWord}
                </div>
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-2xl bg-emerald-500/10 border border-emerald-500/25 shadow-xs animate-in fade-in zoom-in duration-200">
                  <ArrowRight className="h-4 w-4 text-emerald-500 animate-pulse" />
                  <span className="text-sm font-black text-emerald-600 dark:text-emerald-400">Từ tiếng Nhật là gì?</span>
                </div>
              </div>
            )}
          </div>
        ) : isConjugation ? (
          subtitleMode === "hidden" ? (
            /* Audio-Only Mode for Conjugation */
            <div className="p-4 rounded-2xl bg-muted/40 border border-dashed text-center text-xs text-muted-foreground italic flex flex-col items-center justify-center space-y-2 max-w-md mx-auto">
              <div className="flex items-center gap-2 font-bold text-primary text-sm not-italic">
                <Headphones className="h-5 w-5 animate-pulse" />
                <span>Chế độ Audio-Only: Hãy lắng nghe động từ qua loa</span>
              </div>
              <div className="not-italic text-foreground flex items-center justify-center gap-2 flex-wrap">
                <span className="text-xs font-bold text-muted-foreground">Yêu cầu chia:</span>
                <span className="font-extrabold text-primary text-sm font-jp bg-primary/10 px-3 py-1 rounded-xl border border-primary/20">
                  {targetDetail ? `${targetDetail.formJa} — ${targetDetail.shortName}` : target || "Thể yêu cầu"}
                </span>
              </div>
            </div>
          ) : (
            /* Visible Japanese / Vietnamese Mode for Conjugation */
            <div className="text-center space-y-3.5">
              <span className="inline-block text-[11px] font-bold uppercase tracking-widest text-muted-foreground">
                Động từ gốc
              </span>
              <div className="text-2xl md:text-3xl font-black font-jp tracking-tight text-foreground flex justify-center">
                <UniversalFurigana text={verb || prompt} fontSize="xl" />
              </div>

              {displayTranslation && subtitleMode === "vietnamese" && (
                <div className="text-xs md:text-sm font-bold text-primary animate-in fade-in duration-200">
                  (Nghĩa: {displayTranslation})
                </div>
              )}

              {targetDetail ? (
                <div className="inline-flex flex-col items-center gap-1.5 p-3 px-5 rounded-2xl bg-primary/10 border border-primary/25 shadow-xs animate-in fade-in zoom-in duration-200 max-w-lg mx-auto">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Yêu cầu chia sang:</span>
                    <Badge variant="sakura" size="sm" className="font-extrabold font-jp text-xs">
                      {targetDetail.formJa}
                    </Badge>
                  </div>
                  <div className="text-sm md:text-base font-black text-primary flex items-center justify-center gap-2 flex-wrap">
                    <ArrowRight className="h-4 w-4 text-primary shrink-0 animate-pulse" />
                    <span>{targetDetail.shortName}</span>
                    <span className="text-xs font-semibold text-muted-foreground bg-card/90 px-2.5 py-0.5 rounded-lg border border-border/70">
                      {targetDetail.meaning}
                    </span>
                  </div>
                </div>
              ) : target ? (
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-2xl bg-primary/10 border border-primary/25 shadow-xs animate-in fade-in zoom-in duration-200">
                  <span className="text-xs font-bold text-muted-foreground">Chuyển sang:</span>
                  <span className="text-sm md:text-base font-black font-jp text-primary flex items-center gap-1.5">
                    <ArrowRight className="h-4 w-4" />
                    {target}
                  </span>
                </div>
              ) : null}
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
              <div className="text-lg md:text-xl font-bold font-jp leading-relaxed text-foreground tracking-tight flex justify-center">
                <UniversalFurigana text={prompt} fontSize="lg" />
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
