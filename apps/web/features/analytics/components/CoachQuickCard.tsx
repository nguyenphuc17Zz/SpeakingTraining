"use client";

import React from "react";
import { CoachQuickCardDTO } from "../types/analytics";
import { Sparkles, ArrowRight, Zap, Target, AlertTriangle } from "lucide-react";

interface CoachQuickCardProps {
  card: CoachQuickCardDTO;
  onClick: (card: CoachQuickCardDTO) => void;
}

export const CoachQuickCard: React.FC<CoachQuickCardProps> = ({ card, onClick }) => {
  const getIcon = (type: string) => {
    switch (type) {
      case "progress":
        return { icon: Sparkles, color: "text-emerald-400" };
      case "weakness":
        return { icon: AlertTriangle, color: "text-amber-400" };
      default:
        return { icon: Zap, color: "text-rose-400" };
    }
  };

  const { icon: Icon, color } = getIcon(card.card_type);

  return (
    <button
      onClick={() => onClick(card)}
      className="p-4 rounded-2xl bg-card/80 hover:bg-card border border-border hover:border-border text-left transition-all shadow-md group flex flex-col justify-between space-y-3"
    >
      <div className="flex items-center gap-2">
        <Icon className={`w-4 h-4 ${color}`} />
        <h4 className="text-xs font-bold text-foreground font-jp group-hover:text-rose-400 transition-colors">
          {card.title}
        </h4>
      </div>

      <p className="text-xs text-foreground font-medium line-clamp-2 leading-relaxed">
        {card.summary}
      </p>

      <div className="flex items-center gap-1 text-[11px] font-bold text-rose-400">
        <span>{card.action_cta || "Ask Coach"}</span>
        <ArrowRight className="w-3 h-3 group-hover:translate-x-1 transition-transform" />
      </div>
    </button>
  );
};
