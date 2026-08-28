"use client";

import React, { useState } from "react";
import { useAchievements, AchievementCard } from "@/features/gamification";
import { Trophy, Award, Sparkles, CheckCircle2, Lock } from "lucide-react";

export default function AchievementsPage() {
  const { achievements, unlockedCount, totalCount, totalAchievementXP, loading } = useAchievements();
  const [filterRarity, setFilterRarity] = useState<string>("all");

  const filtered =
    filterRarity === "all"
      ? achievements
      : achievements.filter((a) => a.rarity.toLowerCase() === filterRarity);

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-black text-foreground tracking-tight font-jp">
              Trophies & Achievements (実績・称号)
            </h1>
            <span className="text-xl">🏆</span>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Milestones and masteries unlocked through genuine spoken Japanese practice.
          </p>
        </div>

        {/* Total Earned Badge */}
        <div className="flex items-center gap-3 p-3 rounded-2xl bg-card border border-border">
          <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center">
            <Trophy className="w-5 h-5" />
          </div>
          <div>
            <span className="text-xs font-bold text-foreground">
              {unlockedCount} / {totalCount} Unlocked
            </span>
            <p className="text-[11px] font-mono text-amber-400 font-bold">
              +{totalAchievementXP.toLocaleString()} XP Earned
            </p>
          </div>
        </div>
      </div>

      {/* Rarity Filter Tabs */}
      <div className="flex flex-wrap items-center gap-2 p-1.5 rounded-2xl bg-card/80 border border-border">
        {["all", "common", "rare", "epic", "legendary"].map((rarity) => (
          <button
            key={rarity}
            onClick={() => setFilterRarity(rarity)}
            className={`px-4 py-2 rounded-xl text-xs font-bold capitalize transition-all ${
              filterRarity === rarity
                ? "bg-primary text-primary-foreground shadow-md shadow-primary/20"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {rarity === "all" ? "All Trophies (全実績)" : rarity}
          </button>
        ))}
      </div>

      {/* Achievement Grid */}
      {loading ? (
        <div className="p-12 text-center text-xs text-muted-foreground">Loading trophies...</div>
      ) : filtered.length === 0 ? (
        <div className="p-12 text-center text-xs text-muted-foreground">No achievements in this category.</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((ach) => (
            <AchievementCard key={ach.id} achievement={ach} />
          ))}
        </div>
      )}
    </div>
  );
}
