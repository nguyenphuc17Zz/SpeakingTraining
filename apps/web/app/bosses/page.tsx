"use client";

import React, { useState } from "react";
import { useBosses, BossCard } from "@/features/gamification";
import { DynamicBossGeneratorModal } from "@/features/gamification/components/DynamicBossGeneratorModal";
import { DojoBossArenaModal } from "@/features/gamification/components/DojoBossArenaModal";
import { Swords, Trophy, ShieldAlert, Sparkles, Flame, CheckCircle2, Zap, Dices, Plus } from "lucide-react";
import { BossDTO } from "@/features/gamification";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

export default function BossesPage() {
  const { bosses, loading, error, refetch } = useBosses();
  const [selectedDifficulty, setSelectedDifficulty] = useState<"all" | "normal" | "hard" | "extreme">("all");
  const [isGeneratorOpen, setIsGeneratorOpen] = useState(false);
  const [activeArenaBoss, setActiveArenaBoss] = useState<BossDTO | null>(null);

  const clearedCount = bosses.filter((b) => b.cleared).length;

  const filteredBosses = bosses.filter((b) => {
    if (selectedDifficulty === "all") return true;
    return b.difficulty === selectedDifficulty;
  });

  const handleStartArena = (boss: BossDTO) => {
    soundFX.playKatana();
    setActiveArenaBoss(boss);
  };

  const handleVictory = (boss: any, xp: number) => {
    console.log("Boss Victory:", boss.name, "+XP:", xp);
    if (refetch) refetch();
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300 max-w-6xl mx-auto pb-16">
      {/* 1. Header Hero Banner */}
      <div className="p-6 md:p-8 rounded-3xl border border-primary/30 bg-card washi-texture shadow-sm space-y-4 relative overflow-hidden ring-1 ring-primary/20">
        <div className="absolute top-0 right-0 h-56 w-56 bg-primary/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Badge variant="kintsugi" size="sm" className="font-bold">
                DOJO BOSS ARENA ⚔️
              </Badge>
              <Badge variant="matcha" size="sm" className="font-bold">
                100% DYNAMIC AI
              </Badge>
            </div>
            <h1 className="text-2xl md:text-3xl font-black text-foreground tracking-tight flex items-center gap-2">
              <span>Đấu Trường Boss & Thử Thách Cực Hạn</span>
              <span className="text-base font-jp font-normal text-muted-foreground">(強敵試練)</span>
            </h1>
            <p className="text-xs sm:text-sm text-muted-foreground max-w-xl leading-relaxed">
              Các kịch bản đối thoại đối kháng áp lực cao do Gemini AI sinh mới: Phỏng vấn công sở, giải trình khủng hoảng và tranh biện kịch tính.
            </p>
          </div>

          {/* Action Buttons: Generator & Stats */}
          <div className="flex items-center gap-2.5 shrink-0 flex-wrap">
            <Button
              variant="primary"
              size="md"
              onClick={() => {
                soundFX.playKatana();
                setIsGeneratorOpen(true);
              }}
              className="text-xs font-bold gap-1.5 rounded-xl shadow-md"
            >
              <Plus className="h-4 w-4" />
              <span>Tạo Boss AI Mới</span>
            </Button>
          </div>
        </div>

        {/* Clear Stats Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-3 border-t border-border/60 relative z-10">
          <div className="p-3 rounded-2xl bg-card border border-border/80 shadow-2xs">
            <span className="text-[10px] text-muted-foreground font-semibold uppercase">ĐÃ KHUẤT PHỤC</span>
            <div className="text-lg font-black text-foreground font-mono">
              {clearedCount} / {bosses.length} <span className="text-xs font-normal text-muted-foreground">Boss</span>
            </div>
          </div>

          <div className="p-3 rounded-2xl bg-card border border-border/80 shadow-2xs">
            <span className="text-[10px] text-muted-foreground font-semibold uppercase">QUY TẮC ĐẤU TRƯỜNG</span>
            <div className="text-xs font-bold text-foreground">
              3 Hiệp Rút Máu Boss HP
            </div>
          </div>

          <div className="p-3 rounded-2xl bg-card border border-border/80 shadow-2xs col-span-2 sm:col-span-1">
            <span className="text-[10px] text-muted-foreground font-semibold uppercase">PHẦN THƯỞNG</span>
            <div className="text-xs font-bold text-amber-500 font-mono">
              +500 ~ 1500 EXP & Danh Hiệu
            </div>
          </div>
        </div>
      </div>

      {/* 2. Difficulty Filter Tabs */}
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-1.5">
          {(["all", "normal", "hard", "extreme"] as const).map((diff) => (
            <button
              key={diff}
              type="button"
              onClick={() => {
                soundFX.playFurin();
                setSelectedDifficulty(diff);
              }}
              className={cn(
                "px-3.5 py-1.5 rounded-xl text-xs font-bold border transition-all capitalize",
                selectedDifficulty === diff
                  ? "bg-primary text-primary-foreground border-primary shadow-xs"
                  : "bg-card border-border text-muted-foreground hover:text-foreground"
              )}
            >
              {diff === "all" ? "Tất cả" : diff === "normal" ? "Thường (Normal)" : diff === "hard" ? "Khó (Hard)" : "Cực Hạn (Extreme)"}
            </button>
          ))}
        </div>
      </div>

      {/* 3. Boss Grid */}
      {loading ? (
        <div className="p-16 text-center text-xs text-muted-foreground animate-pulse">
          Đang chuẩn bị đấu trường Boss từ hệ thống...
        </div>
      ) : filteredBosses.length === 0 ? (
        <div className="p-16 text-center text-xs text-muted-foreground border rounded-3xl">
          Chưa có Boss nào thuộc phân loại này. Hãy bấm "Tạo Boss AI Mới"!
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredBosses.map((boss) => (
            <div
              key={boss.id}
              className="p-6 rounded-3xl border border-border/80 bg-card washi-texture shadow-xs hover:border-primary/40 hover:shadow-md transition-all flex flex-col justify-between space-y-4 relative overflow-hidden group"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Badge
                    variant={boss.difficulty === "extreme" ? "sakura" : boss.difficulty === "hard" ? "kintsugi" : "matcha"}
                    size="sm"
                    className="font-bold text-[10px] uppercase"
                  >
                    {boss.difficulty}
                  </Badge>
                  <span className="text-[10px] font-mono text-muted-foreground">Req Lv. {boss.required_level}</span>
                </div>

                <div className="space-y-1">
                  <h3 className="text-base font-black text-foreground font-jp group-hover:text-primary transition-colors">
                    {boss.name}
                  </h3>
                  <p className="text-xs text-muted-foreground leading-snug line-clamp-2">
                    {boss.subtitle || boss.description}
                  </p>
                </div>

                {/* Objectives */}
                <div className="space-y-1 pt-1">
                  {boss.objectives?.slice(0, 2).map((obj: string, idx: number) => (
                    <div key={idx} className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
                      <span className="text-primary">•</span>
                      <span className="line-clamp-1">{obj}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Action Button */}
              <div className="pt-3 border-t border-border/60">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleStartArena(boss)}
                  className="w-full text-xs font-bold rounded-xl justify-between hover:bg-primary hover:text-primary-foreground hover:border-primary transition-all shadow-2xs"
                >
                  <span>Vào Đấu Trường Arena</span>
                  <Swords className="h-3.5 w-3.5" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Dynamic Boss Generator Modal */}
      <DynamicBossGeneratorModal
        isOpen={isGeneratorOpen}
        onClose={() => setIsGeneratorOpen(false)}
        onBossCreated={(newBoss) => {
          if (refetch) refetch();
          setActiveArenaBoss(newBoss);
        }}
      />

      {/* Dojo Boss Arena Interactive Modal */}
      <DojoBossArenaModal
        boss={activeArenaBoss}
        isOpen={!!activeArenaBoss}
        onClose={() => setActiveArenaBoss(null)}
        onVictory={handleVictory}
      />
    </div>
  );
}
