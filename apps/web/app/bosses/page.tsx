"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useBosses, BossCard } from "@/features/gamification";
import { Swords, Trophy, ShieldAlert, Sparkles, Flame, CheckCircle2, Zap } from "lucide-react";
import { BossDTO } from "@/features/gamification";
import { AtmosphericWeatherEngine } from "@/components/ui/atmospheric-weather-engine";

export default function BossesPage() {
  const router = useRouter();
  const { bosses, loading, error, startBoss } = useBosses();
  const [startingBossId, setStartingBossId] = useState<string | null>(null);

  const handleStartBoss = async (boss: BossDTO) => {
    try {
      setStartingBossId(boss.id);
      const battle = await startBoss(boss.id);
      // Navigate to interactive exercise / speaking session with the boss exercise
      router.push(`/learning?exercise_id=${battle.exercise_id}`);
    } catch (err: any) {
      alert(err.message || "Failed to start boss battle.");
      setStartingBossId(null);
    }
  };

  const clearedCount = bosses.filter((b) => b.cleared).length;

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-black text-foreground tracking-tight font-jp">
              Boss Battles & High-Stakes Arenas (強敵試練)
            </h1>
            <span className="text-xl">⚔️</span>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Challenging simulated Japanese conversational trials: Job interviews, negotiation, and live debates.
          </p>
        </div>

        {/* Clear Stats */}
        <div className="flex items-center gap-3 p-3 rounded-2xl bg-card border border-border">
          <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center">
            <Swords className="w-5 h-5" />
          </div>
          <div>
            <span className="text-xs font-bold text-foreground">
              {clearedCount} / {bosses.length} Bosses Defeated
            </span>
            <p className="text-[11px] text-muted-foreground">
              Score ≥ Pass Threshold to win exclusive titles & massive XP
            </p>
          </div>
        </div>
      </div>

      {/* Info Banner */}
      <div className="p-4 rounded-2xl bg-gradient-to-r from-rose-950/40 via-slate-900/60 to-indigo-950/40 border border-rose-500/20 flex items-center gap-3">
        <Sparkles className="w-5 h-5 text-rose-400 shrink-0" />
        <p className="text-xs text-foreground">
          Boss battles evaluate communication success, keigo naturalness, response speed, and pronunciation under pressure.
          Failure never breaks your daily streak — you can train and retry anytime!
        </p>
      </div>

      {/* Boss Grid */}
      {loading ? (
        <div className="p-16 text-center text-xs text-muted-foreground">Loading boss challenges...</div>
      ) : bosses.length === 0 ? (
        <div className="p-16 text-center text-xs text-muted-foreground">No boss challenges available.</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {bosses.map((boss) => (
            <BossCard
              key={boss.id}
              boss={boss}
              onStart={handleStartBoss}
              isStarting={startingBossId === boss.id}
            />
          ))}
        </div>
      )}

      {/* Atmospheric Thunder & Rain during Boss trials */}
      <AtmosphericWeatherEngine mode="thunder" />
    </div>
  );
}
