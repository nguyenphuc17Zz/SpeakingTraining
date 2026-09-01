"use client";

import React, { useState } from "react";
import { RampScaffold, RampTaskSpec } from "@/services/ramp-api";
import {
  Eye,
  EyeOff,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Volume2,
  HelpCircle,
  Compass,
  Key,
  BookOpen,
} from "lucide-react";
import { UniversalFurigana } from "@/components/japanese/UniversalFurigana";
import { Badge } from "@/components/ui/badge";
import { speakJapaneseText, stopWebSpeech } from "@/features/speaking/services/web-speech";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

interface RampScaffoldPanelProps {
  task: RampTaskSpec;
  supportLevel: number;
  onRevealHint: () => void;
  hintRevealed: boolean;
}

const SUPPORT_LABEL: Record<number, string> = {
  0: "Độc lập (Tự thân phát ngôn)",
  1: "Chủ đề gợi mở",
  2: "Từ khóa dẫn dắt",
  3: "Câu hỏi gợi ý",
  4: "Câu mồi bắt đầu",
  5: "Cấu trúc khung ý",
  6: "Mẫu câu hoàn chỉnh",
  7: "Đầy đủ kèm bản dịch",
};

export function RampScaffoldPanel({
  task,
  supportLevel,
  onRevealHint,
  hintRevealed,
}: RampScaffoldPanelProps) {
  const [expanded, setExpanded] = useState(true);
  const scaffold = task.scaffold;
  const hasContent = supportLevel > 0;

  const handlePlayWord = (word: string) => {
    stopWebSpeech();
    soundFX.playFurin();
    speakJapaneseText(word);
  };

  if (!hasContent) {
    return (
      <div className="p-4 rounded-2xl border border-border/80 bg-card/60 washi-texture text-center space-y-1 shadow-2xs">
        <span className="text-xs font-bold text-primary flex items-center justify-center gap-1.5">
          🎯 Nấc Thang Độc Lập
        </span>
        <p className="text-[11px] text-muted-foreground">
          Giàn giáo đã rút hoàn toàn — Hãy tự tin phát ngôn tự do
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-border/80 bg-card washi-texture shadow-xs overflow-hidden transition-all">
      {/* Header */}
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="w-full p-3.5 flex items-center justify-between text-left hover:bg-muted/40 transition-colors border-b border-border/60"
      >
        <div className="flex items-center gap-2">
          <span className="h-6 w-6 rounded-md bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-600 dark:text-amber-400">
            <Sparkles className="h-3.5 w-3.5" />
          </span>
          <div>
            <span className="text-xs font-bold text-foreground block">
              Giàn Giáo AI Hỗ Trợ
            </span>
            <span className="text-[10px] text-muted-foreground">
              {SUPPORT_LABEL[supportLevel] || `Cấp độ ${supportLevel}/7`}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-1.5 text-muted-foreground">
          <Badge variant="outline" size="sm" className="text-[10px] font-mono font-bold">
            Lv.{supportLevel}
          </Badge>
          {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </div>
      </button>

      {/* Body */}
      {expanded && (
        <div className="p-3.5 space-y-3 animate-in fade-in duration-150">
          {/* Topic */}
          {supportLevel >= 1 && scaffold.topic && (
            <div className="flex items-center justify-between p-2 rounded-xl bg-muted/30 border border-border/60 text-xs">
              <span className="font-bold text-[11px] text-muted-foreground flex items-center gap-1.5">
                <Compass className="h-3.5 w-3.5 text-primary" /> Bối cảnh:
              </span>
              <span className="font-bold text-foreground font-jp text-right">
                {scaffold.topic}
              </span>
            </div>
          )}

          {/* Keywords (Interactive: Click to Listen) */}
          {supportLevel >= 2 && scaffold.keywords?.length > 0 && (
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-[11px]">
                <span className="font-bold text-muted-foreground flex items-center gap-1">
                  <Key className="h-3 w-3 text-amber-500" /> Từ khóa gợi ý (Bấm để nghe):
                </span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {scaffold.keywords.map((kw, i) => (
                  <button
                    key={i}
                    type="button"
                    onClick={() => handlePlayWord(kw)}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-muted/50 hover:bg-primary/10 border border-border/80 hover:border-primary/40 text-foreground text-xs font-jp transition-all group shadow-2xs"
                    title={`Nghe phát âm: ${kw}`}
                  >
                    <span>
                      <UniversalFurigana text={kw} />
                    </span>
                    <Volume2 className="h-3 w-3 text-muted-foreground group-hover:text-primary transition-colors shrink-0" />
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Guided Questions */}
          {supportLevel >= 3 && scaffold.guided_questions?.length > 0 && (
            <div className="p-2.5 rounded-xl bg-muted/30 border border-border/60 space-y-1.5 text-xs">
              <span className="font-bold text-[11px] text-muted-foreground flex items-center gap-1">
                <HelpCircle className="h-3 w-3 text-primary" /> Câu hỏi mồi ý tưởng:
              </span>
              <ul className="space-y-1 pl-1 font-jp text-[12px] text-foreground">
                {scaffold.guided_questions.map((q, i) => (
                  <li key={i} className="flex items-start gap-1.5 leading-relaxed">
                    <span className="text-primary font-bold shrink-0">•</span>
                    <span>
                      <UniversalFurigana text={q} />
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Sentence Starter */}
          {supportLevel >= 4 && scaffold.sentence_starter && (
            <div className="p-2.5 rounded-xl bg-primary/5 border border-primary/20 space-y-1 text-xs">
              <span className="font-bold text-[10px] text-primary uppercase tracking-wider block">
                Mồi câu bắt đầu:
              </span>
              <div className="font-jp font-bold text-foreground text-xs sm:text-sm">
                「<UniversalFurigana text={scaffold.sentence_starter} />」
              </div>
            </div>
          )}

          {/* Structure Outline */}
          {supportLevel >= 5 && scaffold.structure_outline?.length > 0 && (
            <div className="space-y-1 text-xs">
              <span className="font-bold text-[11px] text-muted-foreground block">
                Khung sườn triển khai:
              </span>
              <div className="space-y-1">
                {scaffold.structure_outline.map((step, i) => (
                  <div
                    key={i}
                    className="p-1.5 px-2.5 rounded-lg bg-muted/40 border border-border/60 text-[11px] flex items-center gap-2 text-foreground"
                  >
                    <span className="h-4 w-4 rounded-full bg-primary/20 text-primary font-bold flex items-center justify-center text-[9px] shrink-0">
                      {i + 1}
                    </span>
                    <span>{step}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Example Response (Gated Hint) */}
          {supportLevel >= 6 && scaffold.example_response && (
            <div className="p-2.5 rounded-xl bg-amber-500/5 border border-amber-500/20 space-y-1.5 text-xs">
              <div className="flex items-center justify-between text-[11px]">
                <span className="font-bold text-amber-700 dark:text-amber-300 flex items-center gap-1">
                  <BookOpen className="h-3 w-3 text-amber-500" /> Mẫu câu hoàn chỉnh
                </span>
                {!hintRevealed && (
                  <span className="text-[10px] text-muted-foreground">
                    (Phạt -30% điểm)
                  </span>
                )}
              </div>

              {hintRevealed ? (
                <div className="p-2 rounded-lg bg-card border border-border text-foreground font-jp text-xs leading-relaxed">
                  「<UniversalFurigana text={scaffold.example_response} />」
                </div>
              ) : (
                <button
                  type="button"
                  onClick={onRevealHint}
                  className="w-full py-2 px-3 rounded-lg border border-amber-500/30 bg-amber-500/10 hover:bg-amber-500/20 text-amber-800 dark:text-amber-200 font-bold text-xs flex items-center justify-center gap-1.5 transition-all shadow-2xs"
                >
                  <Eye className="h-3.5 w-3.5" />
                  <span>Xem mẫu câu tham chiếu</span>
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
