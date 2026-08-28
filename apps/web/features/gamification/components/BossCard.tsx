"use client";

import React from "react";
import { Swords, Trophy, Lock, CheckCircle2, Flame, Sparkles, Shield, ArrowRight } from "lucide-react";
import { BossDTO } from "../types/game";

interface BossCardProps {
  boss: BossDTO;
  onStart: (boss: BossDTO) => void;
  isStarting?: boolean;
}

export const BossCard: React.FC<BossCardProps> = ({ boss, onStart, isStarting }) => {
  const getDifficultyConfig = (diff: string) => {
    switch (diff.toLowerCase()) {
      case "extreme":
        return {
          tag: "bg-red-500/20 text-red-300 border-red-500/40",
          border: "border-red-500/40",
          glow: "shadow-red-500/10",
        };
      case "hard":
        return {
          tag: "bg-amber-500/20 text-amber-300 border-amber-500/40",
          border: "border-amber-500/40",
          glow: "shadow-amber-500/10",
        };
      default:
        return {
          tag: "bg-indigo-500/20 text-indigo-300 border-indigo-500/40",
          border: "border-indigo-500/40",
          glow: "shadow-indigo-500/10",
        };
    }
  };

  const config = getDifficultyConfig(boss.difficulty);

  return (
    <div
      className={`relative overflow-hidden p-6 rounded-3xl border bg-gradient-to-br from-slate-900/90 via-slate-900/95 to-slate-950 ${
        config.border
      } shadow-xl ${config.glow} backdrop-blur-md flex flex-col justify-between space-y-5`}
    >
      {/* Top Header */}
      <div>
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border uppercase tracking-wider ${config.tag}`}>
              {boss.difficulty}
            </span>
            <span className="text-xs font-semibold text-muted-foreground">
              Req. Lv. {boss.required_level}
            </span>
          </div>

          {/* Cleared Stamp or Reward */}
          {boss.cleared ? (
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-xl bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-xs font-bold font-jp">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>CLEARED (撃破済)</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-xl bg-amber-500/20 border border-amber-500/40 text-amber-300 text-xs font-mono font-bold">
              <Trophy className="w-3.5 h-3.5 text-amber-400" />
              <span>+{boss.xp_reward} XP</span>
            </div>
          )}
        </div>

        <div className="mt-3">
          <h3 className="text-lg font-black text-foreground font-jp tracking-tight">
            {boss.name}
          </h3>
          <p className="text-xs font-medium text-primary mt-0.5">
            {boss.subtitle}
          </p>
          <p className="text-xs text-muted-foreground mt-2 leading-relaxed">
            {boss.description}
          </p>
        </div>
      </div>

      {/* Objectives List */}
      {boss.objectives.length > 0 && (
        <div className="p-3.5 rounded-2xl bg-background/60 border border-border/80 space-y-1.5">
          <span className="text-[11px] font-bold text-foreground uppercase tracking-wider">
            Clear Objectives (合格基準):
          </span>
          <ul className="space-y-1">
            {boss.objectives.map((obj, idx) => (
              <li key={idx} className="flex items-center gap-2 text-xs text-muted-foreground">
                <span className="w-1.5 h-1.5 rounded-full bg-primary shrink-0" />
                <span>{obj}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Action Footer */}
      <div className="pt-2 flex items-center justify-between gap-4 border-t border-border/60">
        <div className="text-xs text-muted-foreground">
          {boss.personal_best_score !== null && boss.personal_best_score !== undefined ? (
            <span className="font-mono font-semibold">
              Personal Best: <strong className="text-foreground">{boss.personal_best_score}</strong> pts
            </span>
          ) : (
            <span>No attempts yet</span>
          )}
        </div>

        {boss.is_unlocked ? (
          <button
            onClick={() => onStart(boss)}
            disabled={isStarting}
            className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-primary via-primary/90 to-aizome-600 hover:opacity-90 text-primary-foreground text-xs font-bold flex items-center gap-2 shadow-md shadow-primary/20 transition-all disabled:opacity-50"
          >
            <Swords className="w-4 h-4" />
            <span>{boss.cleared ? "Retry Battle (再挑戦)" : "Start Battle (挑戦する)"}</span>
          </button>
        ) : (
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground font-semibold">
            <Lock className="w-4 h-4" />
            <span>Locked (Lv. {boss.required_level} Required)</span>
          </div>
        )}
      </div>
    </div>
  );
};
