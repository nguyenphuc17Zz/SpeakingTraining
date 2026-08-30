"use client";

import React from "react";
import { UniversalFurigana } from "@/components/japanese/UniversalFurigana";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Volume2, Music, Sparkles, Headphones, CheckCircle2, HelpCircle } from "lucide-react";
import { PitchExercise, PitchQuizOption } from "../services/pitch-api";
import { PitchAccentVisualizer } from "./PitchAccentVisualizer";
import { MoraMetronomeControl } from "./MoraMetronomeControl";
import { cn } from "@/lib/utils";

interface PitchPromptCardProps {
  exercise: PitchExercise | null;
  subtitleMode: "hidden" | "japanese" | "japanese_reading" | "vietnamese";
  onPlayAudio: () => void;
  phase: string;
  onSelectQuizChoice?: (choiceIndex: number) => void;
}

export function PitchPromptCard({
  exercise,
  subtitleMode,
  onPlayAudio,
  phase,
  onSelectQuizChoice,
}: PitchPromptCardProps) {
  if (!exercise) return null;

  const pc = exercise.extra_metadata?.pitch_config || {};
  const promptText = pc.prompt || exercise.prompt || exercise.scenario || exercise.title;
  const canonical = pc.canonical || exercise.canonical || promptText;
  const reading = pc.reading || exercise.reading || "";
  const translation = pc.translation || exercise.translation || exercise.scenario || "";
  const pairInfo = pc.pair_info;
  const moraInfo = pc.mora_info;
  const pattern = pc.pitch_pattern || exercise.pitchPattern || [];
  const moraBreakdown = pc.mora_breakdown || exercise.moraBreakdown || [];
  const downstepIndex = pc.downstep_index ?? exercise.downstepIndex ?? 0;
  const downstepNotation = pc.downstep_notation || exercise.downstepNotation || "";
  const quizOptions: PitchQuizOption[] = pc.quiz_options || exercise.quizOptions || [];
  const isRecognitionMode = exercise.subMode === "pitch_recognition" || exercise.exercise_type === "pitch_recognition";
  const isMoraMode = exercise.subMode === "mora_length" || exercise.exercise_type === "mora_length";

  const isAudioPlaying = phase === "prompt_playing";

  return (
    <div className="p-3.5 sm:p-4 md:p-5 rounded-2xl border border-border/80 bg-card shadow-xs washi-texture space-y-3 relative overflow-hidden">
      {/* Accent Background Glow */}
      <div className="absolute top-0 right-0 h-28 w-28 bg-sky-500/5 rounded-full blur-2xl pointer-events-none" />

      {/* Submode Objective Header */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/60 pb-2.5">
        <div className="flex items-center gap-2">
          <Badge variant="fuji" size="sm" className="font-bold text-[10px] py-0.5 px-2">
            {exercise.exercise_type.replace("pitch_", "").replace("_", " ").toUpperCase()}
          </Badge>
          <span className="text-[11px] text-muted-foreground font-semibold">
            {exercise.instructions || "Lắng nghe và phát âm đúng chuẩn cao độ Tokyo"}
          </span>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={onPlayAudio}
          disabled={isAudioPlaying}
          className="h-7 gap-1 text-[11px] font-bold border-sky-500/30 text-sky-700 dark:text-sky-300 hover:bg-sky-500/10 shadow-2xs px-2.5"
        >
          <Volume2 className={cn("h-3 w-3", isAudioPlaying && "animate-pulse text-sky-500")} />
          <span>{isAudioPlaying ? "Đang phát..." : "Nghe mẫu (L)"}</span>
        </Button>
      </div>

      {/* Mora Metronome Toolbar for Mora Length Mode */}
      {isMoraMode && (
        <MoraMetronomeControl
          defaultBpm={130}
          activeMoraCount={moraInfo?.long_mora?.length || 4}
        />
      )}

      {/* Minimal Pair Contrast View */}
      {pairInfo && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 p-4 rounded-2xl bg-muted/40 border border-border/70">
          <div
            className={cn(
              "p-3 rounded-xl border transition-all text-center space-y-1.5",
              canonical === pairInfo.word_a
                ? "bg-card border-primary shadow-xs ring-1 ring-primary/30"
                : "bg-card/60 border-border/80 opacity-75"
            )}
          >
            <div className="text-xs font-bold text-muted-foreground">TỪ A:</div>
            <div className="text-xl font-bold font-jp text-foreground">
              <UniversalFurigana text={pairInfo.word_a} fontSize="lg" />
            </div>
            <div className="text-xs font-semibold text-primary">{pairInfo.type_a}</div>
            <div className="text-[11px] text-muted-foreground">{pairInfo.meaning_a}</div>
          </div>

          <div
            className={cn(
              "p-3 rounded-xl border transition-all text-center space-y-1.5",
              canonical === pairInfo.word_b
                ? "bg-card border-primary shadow-xs ring-1 ring-primary/30"
                : "bg-card/60 border-border/80 opacity-75"
            )}
          >
            <div className="text-xs font-bold text-muted-foreground">TỪ B:</div>
            <div className="text-xl font-bold font-jp text-foreground">
              <UniversalFurigana text={pairInfo.word_b} fontSize="lg" />
            </div>
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
            <div className="text-lg font-bold font-jp text-foreground">
              <UniversalFurigana text={moraInfo.short_word} fontSize="lg" />
            </div>
            <div className="flex justify-center gap-1">
              {moraInfo.short_mora?.map((m: string, i: number) => (
                <span key={i} className="px-2 py-0.5 rounded bg-muted text-xs font-jp font-bold">{m}</span>
              ))}
            </div>
            <div className="text-[11px] text-muted-foreground">{moraInfo.short_meaning}</div>
          </div>

          <div className="p-3 rounded-xl bg-card border-primary border text-center space-y-1.5 shadow-xs">
            <div className="text-xs font-bold text-primary">Âm dài ({moraInfo.long_mora?.length} phách • {moraInfo.mora_type}):</div>
            <div className="text-lg font-bold font-jp text-foreground">
              <UniversalFurigana text={moraInfo.long_word} fontSize="lg" />
            </div>
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
      <div className="text-center py-2 space-y-2">
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
              <Headphones className="h-4 w-4 animate-bounce" />
              <span>🎧 Chế độ Audio-Only: Hãy lắng nghe và lặp lại với đúng cao độ</span>
            </div>
            <p className="text-xs text-muted-foreground">Bấm nút "Nghe mẫu (L)" để nghe lại nếu cần</p>
          </div>
        )}
      </div>

      {/* NHK Pitch Accent Visualizer (Overline Beam & Downstep Marker) */}
      <PitchAccentVisualizer
        reading={reading || canonical}
        moraBreakdown={moraBreakdown}
        pitchPattern={pattern}
        downstepIndex={downstepIndex}
        downstepNotation={downstepNotation}
      />

      {/* Rapid 1-Click Quiz Choice Buttons for pitch_recognition mode */}
      {isRecognitionMode && quizOptions.length > 0 && (
        <div className="space-y-2 pt-2 border-t border-border/70">
          <div className="text-xs font-bold text-muted-foreground text-center">
            👉 Nghe âm thanh & Chọn nghĩa đúng [Bấm phím 1 hoặc 2]:
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {quizOptions.map((opt, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => onSelectQuizChoice?.(idx)}
                className="p-4 rounded-2xl border border-border/80 bg-card hover:border-primary/50 hover:bg-primary/5 text-left transition-all space-y-1 shadow-xs group cursor-pointer"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold font-mono px-2 py-0.5 rounded-lg bg-primary/10 text-primary border border-primary/20">
                    Phím [{opt.key || idx + 1}]
                  </span>
                  <span className="text-[11px] font-mono text-muted-foreground">{opt.accent_type}</span>
                </div>
                <div className="text-lg font-black font-jp text-foreground group-hover:text-primary">
                  <UniversalFurigana text={opt.word} fontSize="normal" />
                </div>
                <div className="text-xs text-muted-foreground font-medium">
                  {opt.meaning}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
