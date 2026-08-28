"use client";

import React from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Volume2,
  MapPin,
  UserCheck,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  Sparkles,
} from "lucide-react";
import { SituationsExercise } from "../services/situations-api";
import { cn } from "@/lib/utils";

interface SituationsPromptCardProps {
  exercise: SituationsExercise | null;
  subtitleMode: "hidden" | "japanese" | "japanese_reading" | "vietnamese";
  onPlayAudio: () => void;
  phase: string;
}

export function SituationsPromptCard({
  exercise,
  subtitleMode,
  onPlayAudio,
  phase,
}: SituationsPromptCardProps) {
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
  const usefulPhrases = sData.useful_phrases || [];
  const vocabHints = sData.vocabulary_hints;

  const isAudioPlaying = phase === "prompt_playing";

  return (
    <div className="p-6 rounded-3xl border border-border/80 bg-card shadow-sm washi-texture space-y-6 relative overflow-hidden">
      {/* Background Accent Glow */}
      <div className="absolute top-0 right-0 h-32 w-32 bg-emerald-500/5 rounded-full blur-2xl pointer-events-none" />

      {/* Header Scene Info */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/60 pb-4">
        <div className="flex items-center gap-2">
          <Badge variant="fuji" size="sm" className="font-bold flex items-center gap-1">
            <MapPin className="h-3 w-3" />
            <span>{location}</span>
          </Badge>
          <span className="text-xs text-muted-foreground font-semibold">
            Vai trò của bạn: <span className="text-foreground font-bold">{userRole}</span>
          </span>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={onPlayAudio}
          disabled={isAudioPlaying}
          className="h-8 gap-1.5 text-xs font-bold border-emerald-500/30 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-500/10 shadow-2xs"
        >
          <Volume2 className={cn("h-3.5 w-3.5", isAudioPlaying && "animate-pulse text-emerald-500")} />
          <span>{isAudioPlaying ? "NPC Đang nói..." : "Nghe lại lời thoại (L)"}</span>
        </Button>
      </div>

      {/* NPC Dialogue Arena Box */}
      <div className="p-5 rounded-2xl bg-muted/40 border border-border/80 space-y-3 relative">
        <div className="flex items-center justify-between text-xs font-bold text-muted-foreground">
          <div className="flex items-center gap-2">
            <span className="h-6 w-6 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center text-primary text-[10px] font-bold">
              NPC
            </span>
            <span className="text-foreground font-jp">{npcName}</span>
            <span className="text-[10px] text-muted-foreground">({npcPersonality})</span>
          </div>
          <span className="text-[11px] text-primary font-bold">Lời thoại mở đầu:</span>
        </div>

        {subtitleMode !== "hidden" ? (
          <div className="space-y-1.5 pt-1">
            <div className="text-xl md:text-2xl font-black font-jp text-foreground tracking-wide leading-relaxed">
              「{openingDialogue}」
            </div>
            {(subtitleMode === "vietnamese" || dialogueVi) && (
              <div className="text-xs text-muted-foreground italic">
                {dialogueVi}
              </div>
            )}
          </div>
        ) : (
          <div className="py-4 text-center text-xs font-semibold text-muted-foreground">
            🎧 Chế độ Audio-Only: Hãy lắng nghe lời thoại của NPC và phản xạ câu trả lời thích hợp
          </div>
        )}
      </div>

      {/* Live Goals Checklist */}
      {goals.length > 0 && (
        <div className="p-4 rounded-2xl bg-card border border-border/80 space-y-2.5 shadow-2xs">
          <div className="flex items-center justify-between text-xs font-bold text-muted-foreground">
            <span>🎯 Mục tiêu nhiệm vụ cần hoàn thành ({goals.length} mục tiêu):</span>
          </div>

          <div className="space-y-1.5">
            {goals.map((g: any, idx: number) => (
              <div
                key={g.id || idx}
                className="p-2.5 rounded-xl border border-border/60 bg-muted/20 flex items-start gap-2.5 text-xs"
              >
                <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
                <span className="font-semibold text-foreground leading-snug">
                  {g.task || g.description}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Unexpected Event Twist */}
      {event && event !== "Tình huống diễn ra bình thường" && (
        <div className="p-3.5 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-start gap-2.5 text-xs">
          <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            <div className="font-bold text-amber-900 dark:text-amber-100">Sự cố bất ngờ phát sinh (Twist):</div>
            <div className="text-muted-foreground leading-snug">{event}</div>
          </div>
        </div>
      )}

      {/* Useful Vocabulary & Phrases Hints */}
      {(usefulPhrases.length > 0 || vocabHints) && (
        <div className="p-3.5 rounded-2xl bg-sky-500/5 border border-sky-500/20 space-y-1.5 text-xs">
          <div className="font-bold text-sky-700 dark:text-sky-300 flex items-center gap-1.5">
            <Sparkles className="h-3.5 w-3.5" />
            <span>Mẫu câu gợi ý hữu ích:</span>
          </div>
          {usefulPhrases.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {usefulPhrases.map((phrase: string, i: number) => (
                <span key={i} className="px-2.5 py-1 rounded-lg bg-card border border-sky-500/30 text-sky-800 dark:text-sky-200 font-jp font-semibold text-[11px]">
                  {phrase}
                </span>
              ))}
            </div>
          )}
          {vocabHints && (
            <div className="text-[11px] text-muted-foreground italic pt-1">
              Gợi ý từ vựng: {vocabHints}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
