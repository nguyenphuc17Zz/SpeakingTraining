"use client";

import React from "react";
import Link from "next/link";
import { Sparkles, Activity, ArrowRight, Mic, TrendingUp, BarChart2 } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useAnalyticsDashboard } from "@/features/analytics/hooks/useAnalyticsDashboard";
import { cn } from "@/lib/utils";

interface SkillItem {
  key: string;
  name: string;
  jaName: string;
  score: number;
  color: string;
  sampleSize: number;
}

export function SkillRadarCard({ className }: { className?: string }) {
  const { dashboard, loading } = useAnalyticsDashboard("30d");

  const metrics = dashboard?.metrics || {};

  // Extract real metric values from backend AI Analytics Engine
  const fluencyScore = metrics.fluency?.value ?? 0;
  const grammarScore = metrics.grammar_accuracy?.value ?? 0;
  const pronunciationScore = metrics.pronunciation_overall?.value ?? metrics.mora_timing?.value ?? 0;
  const vocabScore = metrics.vocabulary?.value ?? 0;
  const naturalnessScore = metrics.naturalness?.value ?? metrics.response_speed?.value ?? 0;

  const totalTurns = Object.values(metrics).reduce((acc, m) => acc + (m?.sample_size || 0), 0);
  const hasData = totalTurns > 0 || (fluencyScore > 0 || grammarScore > 0 || pronunciationScore > 0 || vocabScore > 0);

  const skills: SkillItem[] = [
    {
      key: "fluency",
      name: "Lưu loát (Fluency)",
      jaName: "流暢さ",
      score: Math.round(fluencyScore),
      color: "from-blue-500 to-indigo-500",
      sampleSize: metrics.fluency?.sample_size || 0,
    },
    {
      key: "grammar",
      name: "Độ chính xác ngữ pháp (Grammar)",
      jaName: "文法力",
      score: Math.round(grammarScore),
      color: "from-emerald-500 to-teal-500",
      sampleSize: metrics.grammar_accuracy?.sample_size || 0,
    },
    {
      key: "pronunciation",
      name: "Phát âm & Nhịp phách Mora",
      jaName: "発音・拍",
      score: Math.round(pronunciationScore),
      color: "from-pink-500 to-rose-500",
      sampleSize: metrics.pronunciation_overall?.sample_size || 0,
    },
    {
      key: "vocab",
      name: "Vốn từ vựng (Vocabulary)",
      jaName: "語彙力",
      score: Math.round(vocabScore),
      color: "from-amber-500 to-yellow-500",
      sampleSize: metrics.vocabulary?.sample_size || 0,
    },
    {
      key: "naturalness",
      name: "Độ tự nhiên & Phản xạ (Naturalness)",
      jaName: "自然さ",
      score: Math.round(naturalnessScore),
      color: "from-purple-500 to-indigo-500",
      sampleSize: metrics.naturalness?.sample_size || 0,
    },
  ];

  // Calculate real average score
  const activeSkills = skills.filter((s) => s.score > 0);
  const overallScore = activeSkills.length > 0
    ? Math.round(activeSkills.reduce((acc, s) => acc + s.score, 0) / activeSkills.length)
    : 0;

  return (
    <div
      className={cn(
        "relative rounded-[22px] border border-border/80 bg-card/95 washi-texture p-5 sm:p-5.5 flex flex-col justify-between transition-all duration-200 hover:border-border hover:shadow-sumi",
        className
      )}
    >
      {/* Top Ambient Highlight */}
      <div className="absolute top-0 left-0 right-0 h-[2.5px] bg-gradient-to-r from-indigo-500/60 via-primary/30 to-transparent opacity-90" />

      {/* Header */}
      <div className="space-y-1 pb-3.5 border-b border-border/60 relative z-10">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="h-7 w-7 rounded-xl bg-indigo-500/15 border border-indigo-500/25 flex items-center justify-center text-indigo-400 shadow-sm">
              <BarChart2 className="h-3.5 w-3.5" />
            </span>
            <div>
              <div className="flex items-center gap-1.5">
                <h3 className="text-sm font-black text-foreground font-sans tracking-tight">
                  Radar Năng Lực AI
                </h3>
                <span className="text-[10px] font-jp font-bold text-indigo-400 px-1.5 py-0.2 rounded bg-indigo-500/10 border border-indigo-500/20">
                  総合能力分析
                </span>
              </div>
            </div>
          </div>

          {hasData ? (
            <span className="px-2.5 py-1 rounded-full bg-indigo-500/15 border border-indigo-500/30 text-indigo-400 text-xs font-sans font-black">
              Tổng điểm: {overallScore} / 100
            </span>
          ) : (
            <span className="px-2 py-0.5 rounded-full bg-muted border border-border text-[10px] text-muted-foreground font-semibold">
              Chờ dữ liệu
            </span>
          )}
        </div>

        <p className="text-xs text-muted-foreground pt-0.5">
          Phân tích thời gian thực dựa trên nhịp điệu nói, độ chính xác mora và cấu trúc ngữ pháp
        </p>
      </div>

      {/* Content Area */}
      <div className="py-3.5 relative z-10 flex-1 flex flex-col justify-center">
        {loading ? (
          <div className="space-y-3 py-4 animate-pulse">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="space-y-1">
                <div className="h-3 bg-muted/80 rounded w-1/3" />
                <div className="h-2 bg-muted/60 rounded-full w-full" />
              </div>
            ))}
          </div>
        ) : !hasData ? (
          /* Clean Japanese Zen Empty State */
          <div className="py-6 px-4 rounded-2xl bg-muted/40 border border-border/70 text-center space-y-3">
            <div className="h-10 w-10 mx-auto rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary text-lg">
              🎯
            </div>
            <div className="space-y-1">
              <h4 className="text-xs font-black text-foreground">
                Chưa có dữ liệu bài nói thực tế
              </h4>
              <p className="text-[11px] text-muted-foreground max-w-xs mx-auto leading-relaxed">
                Hãy bắt đầu buổi luyện nói đầu tiên để hệ thống AI phân tích biểu đồ năng lực 5 chiều của bạn!
              </p>
            </div>
            <Link href="/speaking" className="inline-block pt-1">
              <Button variant="primary" size="sm" className="text-xs font-bold gap-1.5 shadow-sm">
                <Mic className="h-3.5 w-3.5" />
                <span>Luyện nói bài đầu tiên</span>
              </Button>
            </Link>
          </div>
        ) : (
          /* Real Data Bars */
          <div className="space-y-3.5">
            {skills.map((skill) => (
              <div key={skill.key} className="space-y-1">
                <div className="flex justify-between text-xs font-bold text-foreground">
                  <div className="flex items-center gap-1.5">
                    <span>{skill.name}</span>
                    <span className="text-[10px] font-jp text-muted-foreground">({skill.jaName})</span>
                  </div>
                  <span className="font-sans font-black text-foreground">{skill.score}%</span>
                </div>
                <div className="h-2 w-full bg-muted rounded-full overflow-hidden border border-border/50">
                  <div
                    className={cn("h-full bg-gradient-to-r rounded-full transition-all duration-700", skill.color)}
                    style={{ width: `${Math.max(4, skill.score)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer link to detailed analytics */}
      <div className="pt-2 border-t border-border/60 flex items-center justify-between text-xs relative z-10">
        <span className="text-[11px] text-muted-foreground">
          {hasData ? `Đã phân tích ${totalTurns} lượt đối thoại` : "Cập nhật tự động sau mỗi lượt nói"}
        </span>
        <Link
          href="/progress"
          className="font-bold text-primary hover:text-primary/80 flex items-center gap-1 transition-colors"
        >
          Xem chi tiết <ArrowRight className="h-3 w-3" />
        </Link>
      </div>
    </div>
  );
}
