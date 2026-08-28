"use client";

import React from "react";
import { Lock, CheckCircle2, Award, User, Mic, FileText, Sparkles } from "lucide-react";
import { UnlockableDTO } from "../types/game";

interface UnlockCardProps {
  unlockable: UnlockableDTO;
  onEquipTitle?: (title: string) => void;
  isEquipping?: boolean;
}

export const UnlockCard: React.FC<UnlockCardProps> = ({
  unlockable,
  onEquipTitle,
  isEquipping,
}) => {
  const getTypeIcon = (type: string) => {
    switch (type) {
      case "persona":
        return User;
      case "voice_profile":
        return Mic;
      case "scenario":
        return FileText;
      default:
        return Award;
    }
  };

  const IconComponent = getTypeIcon(unlockable.unlock_type);

  return (
    <div
      className={`relative p-5 rounded-2xl border transition-all ${
        unlockable.is_unlocked
          ? "bg-card/90 border-border/80 shadow-md hover:border-slate-600"
          : "bg-background/60 border-border/60 opacity-60"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3.5">
          <div
            className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 ${
              unlockable.is_unlocked
                ? "bg-gradient-to-br from-rose-500/20 to-indigo-500/20 border border-rose-500/30 text-rose-300"
                : "bg-muted border border-border text-muted-foreground"
            }`}
          >
            {unlockable.is_unlocked ? (
              <IconComponent className="w-5 h-5" />
            ) : (
              <Lock className="w-5 h-5" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="text-sm font-bold text-foreground font-jp tracking-tight">
                {unlockable.title}
              </h4>
              <span className="px-2 py-0.5 rounded-full text-[9px] font-bold bg-muted text-muted-foreground border border-border uppercase tracking-wider">
                {unlockable.unlock_type}
              </span>
            </div>
            <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
              {unlockable.description}
            </p>
          </div>
        </div>

        {/* Level Req or Unlocked Badge */}
        {unlockable.is_unlocked ? (
          <div className="shrink-0 flex items-center gap-1 text-emerald-400 text-xs font-bold font-jp">
            <CheckCircle2 className="w-4 h-4" />
            <span>Unlocked</span>
          </div>
        ) : (
          <span className="shrink-0 text-xs font-mono font-semibold text-muted-foreground">
            Lv. {unlockable.level_required}
          </span>
        )}
      </div>

      {/* Equip Action for Titles */}
      {unlockable.is_unlocked && unlockable.unlock_type === "title" && onEquipTitle && (
        <div className="mt-4 pt-3 border-t border-border/80 flex justify-end">
          <button
            onClick={() => onEquipTitle(unlockable.title)}
            disabled={isEquipping}
            className="px-3.5 py-1.5 rounded-xl bg-muted hover:bg-slate-700 text-foreground text-xs font-bold flex items-center gap-1.5 transition-all"
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            <span>Equip Title (称号を装備)</span>
          </button>
        </div>
      )}
    </div>
  );
};
