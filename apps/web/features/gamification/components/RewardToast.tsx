"use client";

import React, { useEffect } from "react";
import { Sparkles, Trophy, CheckCircle2, Swords, X } from "lucide-react";
import { RewardNotificationDTO } from "../types/game";

interface RewardToastProps {
  notification: RewardNotificationDTO | null;
  onDismiss: (id: string) => void;
}

export const RewardToast: React.FC<RewardToastProps> = ({ notification, onDismiss }) => {
  useEffect(() => {
    if (notification) {
      const timer = setTimeout(() => {
        onDismiss(notification.id);
      }, 6000);
      return () => clearTimeout(timer);
    }
  }, [notification, onDismiss]);

  if (!notification) return null;

  const getTypeStyle = (type: string) => {
    switch (type) {
      case "level_up":
        return {
          border: "border-amber-400/80 shadow-amber-500/30",
          bg: "from-amber-900/90 via-slate-900/95 to-purple-950/90",
          icon: Sparkles,
          iconColor: "text-amber-300",
        };
      case "achievement_unlocked":
        return {
          border: "border-purple-500/80 shadow-purple-500/30",
          bg: "from-purple-900/90 via-slate-900/95 to-slate-950",
          icon: Trophy,
          iconColor: "text-purple-300",
        };
      case "boss_cleared":
        return {
          border: "border-rose-500/80 shadow-rose-500/30",
          bg: "from-rose-900/90 via-slate-900/95 to-indigo-950",
          icon: Swords,
          iconColor: "text-rose-300",
        };
      default:
        return {
          border: "border-emerald-500/80 shadow-emerald-500/30",
          bg: "from-emerald-900/90 via-slate-900/95 to-slate-950",
          icon: CheckCircle2,
          iconColor: "text-emerald-300",
        };
    }
  };

  const style = getTypeStyle(notification.notification_type);
  const IconComponent = style.icon;

  return (
    <div className="fixed top-6 right-6 z-50 max-w-md w-full animate-in slide-in-from-top-4 fade-in duration-300">
      <div
        className={`relative p-5 rounded-3xl border-2 bg-gradient-to-br ${style.bg} ${style.border} shadow-2xl backdrop-blur-xl flex items-start gap-4`}
      >
        <div className="w-12 h-12 rounded-2xl bg-white/10 flex items-center justify-center shrink-0 shadow-inner">
          <IconComponent className={`w-7 h-7 ${style.iconColor} animate-pulse`} />
        </div>

        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-black text-foreground font-jp tracking-tight flex items-center gap-2">
            <span>{notification.title}</span>
          </h4>
          <p className="text-xs text-foreground mt-1 leading-relaxed">
            {notification.message}
          </p>

          {notification.xp_amount && (
            <div className="mt-2 inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-white/10 text-amber-300 font-mono font-bold text-xs">
              <Sparkles className="w-3 h-3" />
              <span>+{notification.xp_amount} XP</span>
            </div>
          )}
        </div>

        <button
          onClick={() => onDismiss(notification.id)}
          className="text-muted-foreground hover:text-white p-1 rounded-lg hover:bg-white/10 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
