"use client";

import React, { useState } from "react";
import { UniversalFurigana } from "@/components/japanese/UniversalFurigana";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Volume2,
  MapPin,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  Sparkles,
  Zap,
  Lightbulb,
  ChevronRight,
  MessageSquare,
  Flame,
} from "lucide-react";
import { SituationsExercise, SituationsHints, SituationsKeyword } from "../services/situations-api";
import { speakJapaneseText } from "@/features/speaking/services/web-speech";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

interface SituationsPromptCardProps {
  exercise: SituationsExercise | null;
  subtitleMode: "hidden" | "japanese" | "japanese_reading" | "vietnamese";
  onPlayAudio: () => void;
  phase: string;
  hintTier?: number;
  onSetHintTier?: (tier: number) => void;
}

export function SituationsPromptCard({
  exercise,
  subtitleMode,
  onPlayAudio,
  phase,
  hintTier: externalHintTier,
  onSetHintTier,
}: SituationsPromptCardProps) {
  const [internalHintTier, setInternalHintTier] = useState<number>(0);
  const hintTier = externalHintTier !== undefined ? externalHintTier : internalHintTier;

  const setHintTier = (tier: number) => {
    if (onSetHintTier) {
      onSetHintTier(tier);
    } else {
      setInternalHintTier(tier);
    }
  };

  if (!exercise) return null;

  const sc = exercise.extra_metadata?.situational_config || {};
  const sData = exercise.situationalData || sc.situational_data || {};

  const location = sData.location || exercise.scenario || "Tại địa điểm";
  const npcName = sData.npc_name || "Nhân viên đối thoại";
  const npcPersonality = sData.npc_personality || "Lịch sự";
  const openingDialogue = sData.npc_opening_dialogue || exercise.prompt || "いらっしゃいませ！";
  const dialogueVi = sData.npc_dialogue_vi || exercise.translation || "";
  const userRole = sData.user_role || "Khách hàng";
  const goals = sData.goals || [];
  const event = sData.unexpected_event;
  const usefulPhrases: string[] = sData.useful_phrases || [];
  const vocabHints = sData.vocabulary_hints;
  const hints: SituationsHints | undefined = sData.hints || sc.hints || exercise.hints;
  const quickStarters: string[] = sData.quick_starters || sc.quick_starters || exercise.quickStarters || [
    "すみません、...",
    "〜をお願いできますか？",
    "確認したいのですが...",
  ];

  const isAudioPlaying = phase === "prompt_playing";

  const handleCycleHint = () => {
    soundFX.playFurin();
    setHintTier((hintTier + 1) % 4);
  };

  return (
    <div className="p-3.5 sm:p-4 md:p-5 rounded-2xl border border-border/80 bg-card shadow-xs washi-texture space-y-3 relative overflow-hidden">
      {/* Background Accent Glow */}
      <div className="absolute top-0 right-0 h-28 w-28 bg-emerald-500/5 rounded-full blur-2xl pointer-events-none" />

      {/* Header Scene Info */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/60 pb-2.5">
        <div className="flex items-center gap-2">
          <Badge variant="fuji" size="sm" className="font-bold flex items-center gap-1 text-[11px] py-0.5 px-2">
            <MapPin className="h-3 w-3" />
            <span>{location}</span>
          </Badge>
          <span className="text-[11px] text-muted-foreground font-semibold">
            Vai trò: <span className="text-foreground font-bold">{userRole}</span>
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          {/* Emergency Scaffolding Hint Toggle Button */}
          <Button
            variant={hintTier > 0 ? "sakura" : "outline"}
            size="sm"
            onClick={handleCycleHint}
            className="h-7 gap-1 text-[11px] font-bold shadow-2xs px-2.5"
            title="Gợi ý cứu nguy 3 cấp độ (Phím H)"
          >
            <Lightbulb className={cn("h-3 w-3", hintTier > 0 && "text-amber-500 fill-amber-500")} />
            <span>{hintTier === 0 ? "Gợi ý (H)" : `Gợi ý T${hintTier}/3`}</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={onPlayAudio}
            disabled={isAudioPlaying}
            className="h-7 gap-1 text-[11px] font-bold border-emerald-500/30 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-500/10 shadow-2xs px-2.5"
          >
            <Volume2 className={cn("h-3 w-3", isAudioPlaying && "animate-pulse text-emerald-500")} />
            <span>{isAudioPlaying ? "NPC nói..." : "Nghe (L)"}</span>
          </Button>
        </div>
      </div>

      {/* NPC Dialogue Arena Box */}
      <div className="p-3 sm:p-4 rounded-xl bg-muted/40 border border-border/80 space-y-1.5 relative">
        <div className="flex items-center justify-between text-[11px] font-bold text-muted-foreground">
          <div className="flex items-center gap-1.5">
            <span className="h-5 w-5 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center text-primary text-[9px] font-bold">
              NPC
            </span>
            <span className="text-foreground font-jp">{npcName}</span>
            <span className="text-[10px] text-muted-foreground">({npcPersonality})</span>
          </div>
          <span className="text-[10px] text-primary font-bold">Lời thoại mở đầu:</span>
        </div>

        {subtitleMode !== "hidden" ? (
          <div className="space-y-0.5 pt-0.5">
            <div className="text-base sm:text-lg font-black font-jp text-foreground tracking-wide flex justify-center text-center">
              <UniversalFurigana text={openingDialogue} fontSize="normal" />
            </div>
            {(subtitleMode === "vietnamese" || dialogueVi) && (
              <div className="text-[11px] text-muted-foreground italic text-center">
                {dialogueVi}
              </div>
            )}
          </div>
        ) : (
          <div className="py-2.5 text-center text-xs font-semibold text-muted-foreground">
            🎧 Chế độ Audio-Only: Hãy lắng nghe lời thoại của NPC và phản xạ câu trả lời thích hợp
          </div>
        )}
      </div>

      {/* Quick Response Starters (1-Chạm lấy đà phản xạ) */}
      {quickStarters && quickStarters.length > 0 && (
        <div className="p-2.5 rounded-xl bg-emerald-500/5 border border-emerald-500/20 space-y-1">
          <div className="flex items-center justify-between text-[10px] font-bold text-emerald-800 dark:text-emerald-300">
            <span className="flex items-center gap-1">
              <Flame className="h-3 w-3 text-emerald-600 dark:text-emerald-400" />
              <span>Gợi ý câu mồi (Quick Starters):</span>
            </span>
            <span className="opacity-75">1-chạm nghe</span>
          </div>

          <div className="flex flex-wrap gap-1.5">
            {quickStarters.map((starter: string, i: number) => (
              <button
                key={i}
                type="button"
                onClick={() => {
                  soundFX.playFurin();
                  speakJapaneseText(starter.replace("...", "").replace("〜", ""), { rate: 1.0 });
                }}
                className="px-2 py-0.5 rounded-lg bg-card hover:bg-emerald-500/10 active:scale-95 transition-all border border-emerald-500/30 text-emerald-900 dark:text-emerald-200 font-jp font-bold text-[11px] flex items-center gap-1 shadow-2xs cursor-pointer group"
              >
                <MessageSquare className="h-2.5 w-2.5 text-emerald-600 group-hover:text-emerald-500" />
                <span>
                  <UniversalFurigana text={starter} fontSize="sm" />
                </span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Emergency Scaffolding Hints Panel (Multi-Tier) */}
      {hintTier > 0 && hints && (
        <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 space-y-2 animate-in fade-in zoom-in-95 duration-150">
          <div className="flex items-center justify-between text-[11px] font-bold text-amber-900 dark:text-amber-200">
            <span className="flex items-center gap-1">
              <Lightbulb className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400 fill-amber-500" />
              <span>Gợi Ý Cứu Nguy (Tầng {hintTier}/3) [Phím H]</span>
            </span>
            <button
              type="button"
              onClick={handleCycleHint}
              className="text-[10px] hover:underline flex items-center gap-0.5 text-primary font-bold"
            >
              <span>{hintTier < 3 ? `Tầng ${hintTier + 1}` : "Đóng"}</span>
              <ChevronRight className="h-2.5 w-2.5" />
            </button>
          </div>

          {/* Tier 1: Keywords */}
          {hintTier >= 1 && hints.tier1_keywords && hints.tier1_keywords.length > 0 && (
            <div className="space-y-1">
              <div className="text-[10px] font-bold text-muted-foreground uppercase">
                🔑 Tầng 1 — Từ khóa:
              </div>
              <div className="flex flex-wrap gap-1.5">
                {hints.tier1_keywords.map((kw: SituationsKeyword, i: number) => (
                  <span
                    key={i}
                    className="px-2 py-0.5 rounded bg-card border border-amber-500/30 text-[11px] font-jp font-bold flex items-center gap-1 shadow-2xs"
                  >
                    <span className="text-foreground">
                      <UniversalFurigana text={kw.word} fontSize="sm" />
                    </span>
                    <span className="text-[10px] text-muted-foreground font-sans font-normal">
                      ({kw.meaning})
                    </span>
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Tier 2: Sentence Frame */}
          {hintTier >= 2 && hints.tier2_frame && (
            <div className="space-y-0.5 pt-1 border-t border-amber-500/20">
              <div className="text-[10px] font-bold text-muted-foreground uppercase">
                🧩 Tầng 2 — Khung câu mồi:
              </div>
              <div className="p-1.5 rounded-lg bg-card border border-amber-500/30 text-[11px] font-jp font-bold text-foreground">
                <UniversalFurigana text={hints.tier2_frame} fontSize="sm" />
              </div>
            </div>
          )}

          {/* Tier 3: Full Native Model Response with TTS */}
          {hintTier >= 3 && hints.tier3_model && (
            <div className="space-y-0.5 pt-1 border-t border-amber-500/20">
              <div className="flex items-center justify-between text-[10px] font-bold text-muted-foreground uppercase">
                <span>👑 Tầng 3 — Mẫu chuẩn:</span>
                <button
                  type="button"
                  onClick={() => {
                    soundFX.playFurin();
                    speakJapaneseText(hints.tier3_model!, { rate: 0.95 });
                  }}
                  className="text-primary hover:underline flex items-center gap-0.5 text-[10px]"
                >
                  <Volume2 className="h-2.5 w-2.5" />
                  <span>Nghe</span>
                </button>
              </div>
              <div className="p-2 rounded-lg bg-card border border-amber-500/40 text-xs font-jp font-black text-primary">
                <UniversalFurigana text={hints.tier3_model} fontSize="sm" />
              </div>
            </div>
          )}
        </div>
      )}

      {/* Live Goals Checklist */}
      {goals.length > 0 && (
        <div className="p-2.5 sm:p-3 rounded-xl bg-card border border-border/80 space-y-1.5 shadow-2xs">
          <div className="flex items-center justify-between text-[11px] font-bold text-muted-foreground">
            <span>🎯 Mục tiêu ({goals.length}):</span>
          </div>

          <div className="space-y-1">
            {goals.map((g: any, idx: number) => (
              <div
                key={g.id || idx}
                className="p-1.5 sm:p-2 rounded-lg border border-border/60 bg-muted/20 flex items-start gap-2 text-[11px]"
              >
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500 shrink-0 mt-0.5" />
                <span className="font-semibold text-foreground leading-tight">
                  <UniversalFurigana text={g.task || g.description} fontSize="sm" />
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Unexpected Event Twist */}
      {event && event !== "Tình huống diễn ra bình thường" && (
        <div className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-start gap-2 text-[11px]">
          <AlertTriangle className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            <div className="font-bold text-amber-900 dark:text-amber-100">Sự cố phát sinh (Twist):</div>
            <div className="text-muted-foreground leading-snug">{event}</div>
          </div>
        </div>
      )}
    </div>
  );
}
