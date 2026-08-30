"use client";

import React from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Compass,
  CheckCircle2,
  Circle,
  Play,
  Sparkles,
  ArrowRight,
  Clock,
  BookOpen,
  Volume2,
  Crown,
  Lock,
} from "lucide-react";
import { CurriculumNode, CurriculumRoadmap, CurriculumStage } from "@/types/learning";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

interface InteractiveRoadmapViewProps {
  roadmap: CurriculumRoadmap | null;
  onSelectNode: (node: CurriculumNode) => void;
  onOpenOnboarding: () => void;
  isLoading: boolean;
}

export function InteractiveRoadmapView({
  roadmap,
  onSelectNode,
  onOpenOnboarding,
  isLoading,
}: InteractiveRoadmapViewProps) {
  if (!roadmap) {
    return (
      <div className="p-8 text-center rounded-3xl border border-dashed border-border bg-card washi-texture space-y-3">
        <Sparkles className="h-8 w-8 text-primary mx-auto animate-bounce" />
        <h3 className="text-base font-bold text-foreground">Bạn chưa có Lộ Trình Học Cá Nhân Hóa</h3>
        <p className="text-xs text-muted-foreground max-w-md mx-auto">
          Hãy để AI phân tích trình độ và mục tiêu của bạn để thiết kế lộ trình 4 chặng chi tiết.
        </p>
        <Button
          variant="akane"
          size="sm"
          onClick={onOpenOnboarding}
          className="text-xs font-bold gap-1.5 rounded-xl px-5 h-9 shadow-md"
        >
          <Sparkles className="h-3.5 w-3.5" />
          <span>Tạo Lộ Trình Bằng AI Ngay</span>
        </Button>
      </div>
    );
  }

  // Calculate total completed nodes
  let totalNodes = 0;
  let completedNodes = 0;

  roadmap.stages?.forEach((stage) => {
    stage.nodes?.forEach((node) => {
      totalNodes++;
      if (node.is_completed) completedNodes++;
    });
  });

  const progressPercent = totalNodes > 0 ? Math.round((completedNodes / totalNodes) * 100) : 0;

  return (
    <div className="space-y-4">
      {/* Top Roadmap Overview Card */}
      <div className="p-4 sm:p-5 rounded-2xl border border-border bg-card washi-texture shadow-2xs space-y-3 relative overflow-hidden">
        <div className="absolute top-0 right-0 h-32 w-32 bg-purple-500/10 rounded-full blur-2xl pointer-events-none" />

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 relative z-10">
          <div className="space-y-1">
            <div className="flex items-center gap-1.5">
              <Badge variant="kintsugi" size="sm" className="font-bold text-[10px]">
                AI DYNAMIC ROADMAP
              </Badge>
              <Badge variant="outline" size="sm" className="text-[10px] font-semibold">
                {roadmap.level_label || roadmap.level}
              </Badge>
              <Badge variant="matcha" size="sm" className="text-[10px] font-semibold">
                {roadmap.target_goal_label || roadmap.target_goal}
              </Badge>
            </div>

            <h2 className="text-lg md:text-xl font-black text-foreground tracking-tight">
              {roadmap.title}
            </h2>
            <p className="text-xs text-muted-foreground max-w-2xl leading-snug">
              {roadmap.description}
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0 self-start md:self-auto">
            <div className="text-right">
              <div className="text-[10px] font-bold text-muted-foreground">Tiến độ toàn khóa</div>
              <div className="text-lg font-black font-mono text-primary">
                {progressPercent}% <span className="text-[10px] text-muted-foreground font-normal">({completedNodes}/{totalNodes} bài)</span>
              </div>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                soundFX.playFurin();
                onOpenOnboarding();
              }}
              className="text-xs font-bold gap-1.5 rounded-xl border-primary/30 text-primary hover:bg-primary/10 h-8 px-2.5"
            >
              <Sparkles className="h-3 w-3" />
              <span>Tinh chỉnh AI</span>
            </Button>
          </div>
        </div>

        {/* Global Progress Bar */}
        <div className="w-full h-1.5 rounded-full bg-muted/60 overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-primary via-emerald-500 to-amber-500 transition-all duration-500 rounded-full"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      {/* 4 Milestone Stages */}
      <div className="space-y-3">
        {roadmap.stages?.map((stage: CurriculumStage, stageIdx: number) => {
          const stageCompleted = stage.nodes?.filter((n) => n.is_completed).length || 0;
          const stageTotal = stage.nodes?.length || 0;
          const isStageFinished = stageTotal > 0 && stageCompleted === stageTotal;

          return (
            <div
              key={stage.stage_number || stageIdx}
              className="p-4 sm:p-5 rounded-2xl border border-border bg-card washi-texture shadow-2xs space-y-3 relative"
            >
              {/* Stage Header */}
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/60 pb-2.5">
                <div className="flex items-center gap-2.5">
                  <span className={cn(
                    "h-8 w-8 rounded-xl font-bold font-mono text-xs flex items-center justify-center border shadow-2xs",
                    isStageFinished
                      ? "bg-emerald-500/20 border-emerald-500 text-emerald-600 dark:text-emerald-400"
                      : "bg-primary/10 border-primary text-primary"
                  )}>
                    {isStageFinished ? <CheckCircle2 className="h-4 w-4" /> : stage.stage_number}
                  </span>

                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-bold text-foreground font-jp">{stage.title}</h3>
                      <Badge variant="outline" size="sm" className="text-[10px] font-bold">
                        {stage.badge}
                      </Badge>
                    </div>
                    <p className="text-[11px] text-muted-foreground">{stage.objective}</p>
                  </div>
                </div>

                <div className="text-xs font-mono font-bold text-muted-foreground">
                  {stageCompleted}/{stageTotal} hoàn thành
                </div>
              </div>

              {/* Lesson Nodes Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {stage.nodes?.map((node: CurriculumNode, nodeIdx: number) => {
                  return (
                    <div
                      key={node.id || nodeIdx}
                      onClick={() => {
                        soundFX.playFurin();
                        onSelectNode(node);
                      }}
                      className={cn(
                        "p-4 rounded-2xl border transition-all cursor-pointer bg-card shadow-2xs space-y-2.5 hover:shadow-md hover:border-primary/50 relative overflow-hidden group",
                        node.is_completed
                          ? "border-emerald-500/30 bg-emerald-500/5"
                          : "border-border/80 hover:bg-muted/30"
                      )}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <span className={cn(
                            "h-5 w-5 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0",
                            node.is_completed
                              ? "bg-emerald-500 text-white"
                              : "bg-muted text-muted-foreground border border-border"
                          )}>
                            {node.is_completed ? "✓" : nodeIdx + 1}
                          </span>
                          <Badge variant="fuji" size="sm" className="text-[10px] font-bold">
                            {node.mode_label}
                          </Badge>
                        </div>

                        <span className="text-[10px] font-mono font-bold text-muted-foreground">
                          {node.estimated_minutes}p
                        </span>
                      </div>

                      <div className="space-y-1">
                        <h4 className="text-xs font-bold text-foreground leading-snug group-hover:text-primary transition-colors">
                          {node.title}
                        </h4>
                        <p className="text-[11px] text-muted-foreground leading-snug line-clamp-2">
                          {node.description}
                        </p>
                      </div>

                      {/* Key Patterns Pill Tags */}
                      {node.key_patterns && node.key_patterns.length > 0 && (
                        <div className="flex flex-wrap gap-1 pt-1">
                          {node.key_patterns.map((kp, i) => (
                            <span key={i} className="px-2 py-0.5 rounded-md bg-muted text-[10px] font-mono text-muted-foreground">
                              {kp}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
