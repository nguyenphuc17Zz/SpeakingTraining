"use client";

import React from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Zap,
  Crown,
  Volume2,
  Compass,
  ArrowRight,
  Shield,
} from "lucide-react";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";
import Link from "next/link";

interface FourPillarsRadarCardProps {
  pillars: Record<string, any> | undefined;
}

export function FourPillarsRadarCard({ pillars }: FourPillarsRadarCardProps) {
  if (!pillars) return null;

  const pillarItems = [
    {
      key: "reflex",
      title: "1. Phản Xạ Nhanh",
      jaTitle: "瞬発スピーキング",
      icon: <Zap className="h-4 w-4 text-amber-500" />,
      url: "/reflex",
      color: "amber",
      data: pillars.reflex || { count: 0, avg_score: 0 },
    },
    {
      key: "keigo",
      title: "2. Kính Ngữ Công Sở",
      jaTitle: "ビジネス敬語",
      icon: <Crown className="h-4 w-4 text-purple-500" />,
      url: "/keigo",
      color: "purple",
      data: pillars.keigo || { count: 0, avg_score: 0 },
    },
    {
      key: "pitch",
      title: "3. Cao Độ & Phách",
      jaTitle: "東京アクセント",
      icon: <Volume2 className="h-4 w-4 text-sky-500" />,
      url: "/pitch",
      color: "sky",
      data: pillars.pitch || { count: 0, avg_score: 0 },
    },
    {
      key: "situations",
      title: "4. Tình Huống Thực Chiến",
      jaTitle: "場面英会話",
      icon: <Compass className="h-4 w-4 text-emerald-500" />,
      url: "/situations",
      color: "emerald",
      data: pillars.situations || { count: 0, avg_score: 0 },
    },
  ];

  return (
    <div className="p-6 rounded-3xl border border-border bg-card washi-texture shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield className="h-5 w-5 text-primary" />
          <h3 className="text-sm font-bold text-foreground">
            Ma Trận 4 Trụ Cột Năng Lực Nói Tiếng Nhật (4-Pillar Mastery Matrix)
          </h3>
        </div>
        <Badge variant="outline" size="sm" className="text-xs font-semibold">
          4 STUDIO MODES
        </Badge>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
        {pillarItems.map((p) => {
          const score = Math.round(p.data.avg_score || 0);
          return (
            <div
              key={p.key}
              className="p-4 rounded-2xl border border-border/80 bg-card shadow-2xs space-y-3 hover:border-primary/40 transition-all group"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="p-2 rounded-xl bg-muted/50 border border-border/80">
                    {p.icon}
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-foreground group-hover:text-primary transition-colors">
                      {p.title}
                    </h4>
                    <span className="text-[10px] text-muted-foreground font-jp">{p.jaTitle}</span>
                  </div>
                </div>
              </div>

              {/* Progress Bar & Stats */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-muted-foreground font-semibold">
                    {p.data.count} bài đã luyện
                  </span>
                  <span className="font-bold font-mono text-primary">{score}%</span>
                </div>

                <div className="w-full h-2 rounded-full bg-muted/60 overflow-hidden">
                  <div
                    className={cn(
                      "h-full rounded-full transition-all duration-500",
                      score >= 80 ? "bg-emerald-500" : score >= 50 ? "bg-amber-500" : "bg-primary"
                    )}
                    style={{ width: `${score}%` }}
                  />
                </div>
              </div>

              <Link href={p.url}>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => soundFX.playFurin()}
                  className="w-full text-[11px] font-bold text-muted-foreground hover:text-foreground justify-between h-7 px-2 rounded-lg"
                >
                  <span>Vào phòng luyện</span>
                  <ArrowRight className="h-3 w-3" />
                </Button>
              </Link>
            </div>
          );
        })}
      </div>
    </div>
  );
}
