"use client";

import React, { useState, useEffect } from "react";
import { gameApi } from "@/features/gamification/services/gameApi";
import { UnlockableDTO } from "@/features/gamification/types/game";
import { UnlockCard } from "@/features/gamification/components/UnlockCard";
import { Award, Sparkles, User, Mic, FileText, CheckCircle2 } from "lucide-react";

export default function UnlocksPage() {
  const [unlocks, setUnlocks] = useState<UnlockableDTO[]>([]);
  const [activeFilter, setActiveFilter] = useState<string>("all");
  const [loading, setLoading] = useState(true);
  const [equipping, setEquipping] = useState(false);

  const fetchUnlocks = async () => {
    try {
      setLoading(true);
      const data = await gameApi.getUnlocks();
      setUnlocks(data);
    } catch {
      //
    } finally {
      setLoading(false);
    }
  };

  const handleEquipTitle = async (title: string) => {
    try {
      setEquipping(true);
      await gameApi.equipTitle(title);
      alert(`Equipped title: ${title}`);
      await fetchUnlocks();
    } catch (err: any) {
      alert(err.message || "Failed to equip title.");
    } finally {
      setEquipping(false);
    }
  };

  useEffect(() => {
    fetchUnlocks();
  }, []);

  const filtered =
    activeFilter === "all"
      ? unlocks
      : unlocks.filter((u) => u.unlock_type === activeFilter);

  const unlockedCount = unlocks.filter((u) => u.is_unlocked).length;

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-black text-foreground tracking-tight font-jp">
              Progression Unlocks & Titles (解放報酬・称号)
            </h1>
            <span className="text-xl">🎁</span>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Unlock new conversation personas, voice profiles, scenario decks, and prestigious titles as you level up.
          </p>
        </div>

        <div className="flex items-center gap-3 p-3 rounded-2xl bg-card border border-border">
          <div className="w-10 h-10 rounded-xl bg-purple-500/10 text-purple-400 flex items-center justify-center">
            <Award className="w-5 h-5" />
          </div>
          <div>
            <span className="text-xs font-bold text-foreground">
              {unlockedCount} / {unlocks.length} Unlocked
            </span>
            <p className="text-[11px] text-muted-foreground">Reach higher RPG levels to unlock more</p>
          </div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center gap-2 p-1.5 rounded-2xl bg-card/80 border border-border">
        {[
          { key: "all", label: "All Rewards (全て)" },
          { key: "title", label: "Titles (称号)" },
          { key: "persona", label: "Personas (会話相手)" },
          { key: "voice_profile", label: "Voice Styles (音声)" },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveFilter(tab.key)}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              activeFilter === tab.key
                ? "bg-primary text-primary-foreground shadow-md shadow-primary/20"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Grid */}
      {loading ? (
        <div className="p-16 text-center text-xs text-muted-foreground">Loading unlocks...</div>
      ) : filtered.length === 0 ? (
        <div className="p-16 text-center text-xs text-muted-foreground">No items in this category.</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((item) => (
            <UnlockCard
              key={item.id}
              unlockable={item}
              onEquipTitle={handleEquipTitle}
              isEquipping={equipping}
            />
          ))}
        </div>
      )}
    </div>
  );
}
