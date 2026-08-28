"use client";

import React from "react";
import { useSkillTree, SkillTree } from "@/features/gamification";
import { Zap, Sparkles, BookOpen, CheckCircle2 } from "lucide-react";

export default function SkillsPage() {
  const { skillTree, loading, error } = useSkillTree();

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-black text-foreground tracking-tight font-jp">
              Japanese Speaking Skill Tree (日本語スピーキング・スキルツリー)
            </h1>
            <span className="text-xl">🌳</span>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Visual mastery branches derived directly from your learning evidence. Master nodes to unlock advanced fluency.
          </p>
        </div>

        {/* Overview Stats Badge */}
        {skillTree && (
          <div className="flex items-center gap-3 p-3 rounded-2xl bg-card border border-border">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center">
              <Zap className="w-5 h-5" />
            </div>
            <div>
              <span className="text-xs font-bold text-foreground">
                {skillTree.mastered_count} / {skillTree.total_nodes} Mastered
              </span>
              <p className="text-[11px] font-mono text-rose-400 font-bold">
                {Math.round(skillTree.overall_mastery_average * 100)}% Average Mastery
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Main Interactive Skill Tree */}
      {loading ? (
        <div className="p-16 text-center text-xs text-muted-foreground">Loading skill tree...</div>
      ) : error || !skillTree ? (
        <div className="p-16 text-center text-xs text-rose-400">{error || "Failed to load skill tree."}</div>
      ) : (
        <SkillTree skillTree={skillTree} />
      )}
    </div>
  );
}
