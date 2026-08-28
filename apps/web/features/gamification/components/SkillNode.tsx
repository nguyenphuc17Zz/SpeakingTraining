"use client";

import React from "react";
import { Lock, Zap, Shield, Smile, Feather, Link as LinkIcon, RefreshCw, Activity, TrendingUp, MessageSquare, Volume2, CheckCircle2 } from "lucide-react";
import { SkillNodeDTO } from "../types/game";

interface SkillNodeProps {
  node: SkillNodeDTO;
  onClick: (node: SkillNodeDTO) => void;
  isSelected?: boolean;
}

export const SkillNode: React.FC<SkillNodeProps> = ({ node, onClick, isSelected }) => {
  const getIcon = (iconName: string) => {
    switch (iconName) {
      case "zap":
        return Zap;
      case "message-square":
        return MessageSquare;
      case "volume-2":
        return Volume2;
      case "shield":
        return Shield;
      case "smile":
        return Smile;
      case "feather":
        return Feather;
      case "link":
        return LinkIcon;
      case "refresh-cw":
        return RefreshCw;
      case "activity":
        return Activity;
      case "trending-up":
        return TrendingUp;
      default:
        return Zap;
    }
  };

  const getStatusTheme = (status: string) => {
    switch (status) {
      case "mastered":
        return {
          bg: "bg-emerald-500/20 border-emerald-400 text-emerald-300 shadow-emerald-500/20",
          badge: "bg-emerald-500/30 text-emerald-200",
        };
      case "strong":
        return {
          bg: "bg-indigo-500/20 border-indigo-400 text-indigo-300 shadow-indigo-500/20",
          badge: "bg-indigo-500/30 text-indigo-200",
        };
      case "developing":
        return {
          bg: "bg-amber-500/20 border-amber-400 text-amber-300 shadow-amber-500/20",
          badge: "bg-amber-500/30 text-amber-200",
        };
      case "available":
        return {
          bg: "bg-muted/80 border-slate-600 text-foreground shadow-none",
          badge: "bg-slate-700 text-foreground",
        };
      default: // locked
        return {
          bg: "bg-card/60 border-border text-slate-600 shadow-none",
          badge: "bg-card text-slate-600",
        };
    }
  };

  const IconComponent = getIcon(node.icon);
  const theme = getStatusTheme(node.status);
  const percent = Math.round(node.current_mastery * 100);

  return (
    <button
      onClick={() => onClick(node)}
      className={`group relative flex flex-col items-center p-4 rounded-2xl border-2 transition-all duration-200 text-center w-full max-w-[200px] ${
        theme.bg
      } ${isSelected ? "ring-2 ring-primary ring-offset-2 ring-offset-slate-950 scale-105" : "hover:scale-102"} shadow-lg`}
    >
      {/* Icon Capsule */}
      <div className="w-12 h-12 rounded-2xl bg-card/90 border border-inherit flex items-center justify-center mb-2.5 shadow-inner">
        {node.status === "locked" ? (
          <Lock className="w-5 h-5 text-slate-600" />
        ) : (
          <IconComponent className="w-6 h-6" />
        )}
      </div>

      <h5 className="text-xs font-bold text-foreground font-jp leading-tight line-clamp-2">
        {node.name}
      </h5>

      {/* Mastery Badge */}
      <div className="mt-2 flex items-center gap-1">
        {node.status === "mastered" ? (
          <span className="flex items-center gap-1 text-[10px] font-bold text-emerald-400">
            <CheckCircle2 className="w-3 h-3" />
            <span>Mastered</span>
          </span>
        ) : (
          <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-bold ${theme.badge}`}>
            {node.status === "locked" ? "Locked" : `${percent}%`}
          </span>
        )}
      </div>
    </button>
  );
};
