"use client";

import React, { useState } from "react";
import { useQuests, QuestCard } from "@/features/gamification";
import { Target, Calendar, Sparkles, Trophy, CheckCircle2 } from "lucide-react";

export default function QuestsPage() {
  const { dailyQuests, weeklyQuests, loading, error, refetch } = useQuests();
  const [activeTab, setActiveTab] = useState<"daily" | "weekly">("daily");

  const displayedQuests = activeTab === "daily" ? dailyQuests : weeklyQuests;
  const completedCount = displayedQuests.filter((q) => q.is_completed).length;

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-black text-foreground tracking-tight font-jp">
              Quests & Missions (クエスト・試練)
            </h1>
            <span className="text-xl">🎯</span>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Personalized daily and weekly challenges generated from your active learning priorities.
          </p>
        </div>

        {/* Tab Toggle */}
        <div className="flex items-center gap-1.5 p-1 rounded-2xl bg-card border border-border">
          <button
            onClick={() => setActiveTab("daily")}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              activeTab === "daily"
                ? "bg-primary text-primary-foreground shadow-md shadow-primary/20"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Today's Daily ({dailyQuests.length})
          </button>
          <button
            onClick={() => setActiveTab("weekly")}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              activeTab === "weekly"
                ? "bg-primary text-primary-foreground shadow-md shadow-primary/20"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Weekly Challenges ({weeklyQuests.length})
          </button>
        </div>
      </div>

      {/* Overview Stat Strip */}
      <div className="p-4 rounded-2xl bg-card/60 border border-border flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <div>
            <span className="text-xs font-bold text-foreground">
              Completed {completedCount} of {displayedQuests.length}{" "}
              {activeTab === "daily" ? "Today" : "This Week"}
            </span>
            <p className="text-[11px] text-muted-foreground">
              Quests automatically advance as you practice speaking in the app.
            </p>
          </div>
        </div>
      </div>

      {/* Quests List */}
      {loading ? (
        <div className="p-12 text-center text-xs text-muted-foreground">Loading quests...</div>
      ) : displayedQuests.length === 0 ? (
        <div className="p-12 text-center text-xs text-muted-foreground">No quests found for this tab.</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {displayedQuests.map((quest) => (
            <QuestCard key={quest.id} quest={quest} />
          ))}
        </div>
      )}
    </div>
  );
}
