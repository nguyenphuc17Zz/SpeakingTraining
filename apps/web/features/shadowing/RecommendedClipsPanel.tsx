"use client";

import React from "react";
import { Sparkles, Play, Target, Award, Clock, ArrowRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { CandidateCategory, ShadowingCandidate } from "@/types/shadowing";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

interface RecommendedClipsPanelProps {
  candidates: ShadowingCandidate[];
  onSelectCandidate: (candidate: ShadowingCandidate) => void;
}

export function RecommendedClipsPanel({
  candidates,
  onSelectCandidate,
}: RecommendedClipsPanelProps) {
  if (!candidates || candidates.length === 0) {
    return null;
  }

  const getCategoryLabel = (cat: CandidateCategory) => {
    switch (cat) {
      case "BEST_FOR_PRONUNCIATION":
        return { label: "Luyện phát âm", color: "bg-primary/20 text-primary border-primary/40" };
      case "BEST_FOR_WORKPLACE":
        return { label: "Kính ngữ & Công sở", color: "bg-amber-500/20 text-amber-300 border-amber-500/40" };
      case "BEST_FOR_NATURALNESS":
        return { label: "Khẩu ngữ tự nhiên", color: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40" };
      case "BEST_FOR_SPEED":
        return { label: "Thử thách tốc độ", color: "bg-aizome-500/20 text-aizome-300 border-aizome-500/40" };
      case "BEST_FOR_BEGINNER":
        return { label: "Dễ bắt nhịp", color: "bg-sky-500/20 text-sky-300 border-sky-500/40" };
      case "BEST_FOR_CHALLENGE":
        return { label: "Thử thách nâng cao", color: "bg-kintsugi-500/20 text-kintsugi-300 border-kintsugi-500/40" };
      default:
        return { label: "Gợi ý luyện", color: "bg-muted text-foreground border-border" };
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs < 10 ? "0" : ""}${secs}`;
  };

  return (
    <div className="p-4 sm:p-5 rounded-2xl bg-card/95 border border-border/90 washi-texture backdrop-blur-xl shadow-sumi-md space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-lg bg-primary/15 text-primary border border-primary/20">
            <Sparkles className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm sm:text-base font-bold text-foreground font-sans tracking-wide">
              Đoạn Luyện Gợi Ý Cá Nhân Hóa
            </h3>
          </div>
        </div>
        <span className="text-xs px-2.5 py-1 rounded-full bg-muted/80 text-muted-foreground font-semibold">
          {candidates.length} đoạn khuyên luyện
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {candidates.map((cand, idx) => {
          const primaryCat = cand.categories[0] || "BEST_FOR_NATURALNESS";
          const catMeta = getCategoryLabel(primaryCat);

          return (
            <div
              key={cand.segment_id || idx}
              onClick={() => {
                soundFX.playFurin();
                onSelectCandidate(cand);
              }}
              className="group p-4 rounded-2xl bg-background/90 border border-border/80 hover:border-primary/50 hover:bg-card/95 transition-all cursor-pointer flex flex-col justify-between space-y-3 shadow-sm hover:shadow-md"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <span className={cn("text-xs px-2.5 py-0.5 rounded-full border font-semibold", catMeta.color)}>
                    {catMeta.label}
                  </span>
                  <span className="text-xs font-mono text-muted-foreground flex items-center gap-1 font-semibold">
                    <Clock className="h-3 w-3" />
                    {formatTime(cand.start_time)} - {formatTime(cand.end_time)}
                  </span>
                </div>

                <p className="text-sm sm:text-base font-bold text-foreground font-jp line-clamp-2 leading-relaxed group-hover:text-primary transition">
                  {cand.text}
                </p>
              </div>

              <div className="pt-2 border-t border-border/60 flex items-center justify-between gap-2">
                <p className="text-xs text-muted-foreground line-clamp-1 flex-1 font-medium">
                  💡 {cand.reason}
                </p>
                <span className="text-xs text-primary font-bold group-hover:translate-x-0.5 transition flex items-center gap-1 shrink-0">
                  <span>Luyện ngay</span>
                  <Play className="h-3 w-3 fill-current" />
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
