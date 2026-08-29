"use client";

import { UniversalFurigana } from "@/components/japanese/UniversalFurigana";

import React from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Volume2, Music, Sparkles } from "lucide-react";
import { PitchExercise } from "../services/pitch-api";
import { cn } from "@/lib/utils";

interface PitchPromptCardProps {
  exercise: PitchExercise | null;
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
  const canonical = pc.canonical || exercise.canonical || promptText;
  const reading = pc.reading || exercise.reading || "";
  const translation = pc.translation || exercise.translation || exercise.scenario || "";
  const pairInfo = pc.pair_info;
  const moraInfo = pc.mora_info;
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
            <div className="text-xl md:text-2xl font-black font-jp text-foreground tracking-wide flex justify-center">
              <UniversalFurigana text={canonical} fontSize="xl" />
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
