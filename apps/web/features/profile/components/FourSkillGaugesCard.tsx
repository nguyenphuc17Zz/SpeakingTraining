"use client";

import React from "react";
import { Badge } from "@/components/ui/badge";
import {
  Waves,
  Ruler,
  Volume2,
  BookOpen,
  Shield,
} from "lucide-react";
import { LearnerProfile } from "@/types/profile";
import { cn } from "@/lib/utils";

interface FourSkillGaugesCardProps {
  profile: LearnerProfile | null;
}

export function FourSkillGaugesCard({ profile }: FourSkillGaugesCardProps) {
  if (!profile) return null;

  const levelToScore = (lvl: string) => {
    switch (lvl) {
      case "advanced": return 92;
      case "upper_intermediate": return 82;
      case "intermediate": return 72;
      case "elementary": return 58;
      default: return 45;
    }
  };

  const skills = [
    {
      title: "1. Độ Trôi Chảy & Tốc Độ",
      jaTitle: "流暢さ・瞬発力",
      score: levelToScore(profile.fluency_level),
      icon: <Waves className="h-4 w-4 text-sky-500" />,
      desc: "Thời gian suy nghĩ và độ liên tục khi phát ngôn",
      color: "sky",
    },
    {
      title: "2. Độ Chuẩn Ngữ Pháp",
      jaTitle: "文法正確性",
      score: levelToScore(profile.grammar_level),
      icon: <Ruler className="h-4 w-4 text-emerald-500" />,
      desc: "Chia thể động từ, trợ từ và cấu trúc câu phức",
      color: "emerald",
    },
    {
      title: "3. Ngữ Âm & Cao Độ Tokyo",
      jaTitle: "発音・ピッチ",
      score: levelToScore(profile.naturalness_level),
      icon: <Volume2 className="h-4 w-4 text-purple-500" />,
      desc: "Cao độ từ vựng, phách Mora và ngữ điệu câu",
      color: "purple",
    },
    {
      title: "4. Vốn Từ & Biểu Đạt",
      jaTitle: "語彙力・表現",
      score: levelToScore(profile.vocabulary_level),
      icon: <BookOpen className="h-4 w-4 text-amber-500" />,
      desc: "Độ phong phú từ vựng và Kính ngữ theo ngữ cảnh",
      color: "amber",
    },
  ];

  return (
    <div className="p-6 rounded-3xl border border-border bg-card washi-texture shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield className="h-5 w-5 text-primary" />
          <h3 className="text-sm font-bold text-foreground">
            Bảng Đánh Giá 4 Trục Kỹ Năng Cốt Lõi (Core Skill Competencies)
          </h3>
        </div>
        <Badge variant="outline" size="sm" className="text-xs font-semibold">
          EVALUATED
        </Badge>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {skills.map((s, idx) => (
          <div
            key={idx}
            className="p-4 rounded-2xl border border-border/80 bg-card shadow-2xs space-y-3"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-xl bg-muted/50 border border-border/80">
                  {s.icon}
                </div>
                <div>
                  <h4 className="text-xs font-bold text-foreground">{s.title}</h4>
                  <span className="text-[10px] text-muted-foreground font-jp">{s.jaTitle}</span>
                </div>
              </div>
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-muted-foreground font-semibold">{s.desc}</span>
                <span className="font-bold font-mono text-primary">{s.score}%</span>
              </div>

              <div className="w-full h-2 rounded-full bg-muted/60 overflow-hidden">
                <div
                  className={cn(
                    "h-full rounded-full transition-all duration-500",
                    s.score >= 80 ? "bg-emerald-500" : s.score >= 65 ? "bg-primary" : "bg-amber-500"
                  )}
                  style={{ width: `${s.score}%` }}
                />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
