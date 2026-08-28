"use client";

import React, { useState } from "react";
import { ConversationAnalysisSummary, CorrectionItem, TurnAnalysis } from "../types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  ChevronRight,
  X,
  Volume2,
  Award,
} from "lucide-react";

interface ConversationReviewPanelProps {
  summary: ConversationAnalysisSummary | null;
  isOpen: boolean;
  onClose: () => void;
  onSelectCorrection: (correction: CorrectionItem) => void;
  onPlayCorrection?: (text: string) => void;
}

export function ConversationReviewPanel({
  summary,
  isOpen,
  onClose,
  onSelectCorrection,
  onPlayCorrection,
}: ConversationReviewPanelProps) {
  if (!isOpen) return null;

  const turnAnalyses = summary?.turn_analyses || [];
  const allCorrections = turnAnalyses.flatMap((ta) => ta.corrections);
  const mustFixCount = allCorrections.filter((c) => c.severity === "MUST_FIX").length;
  const shouldFixCount = allCorrections.filter((c) => c.severity === "SHOULD_FIX").length;
  const nativeAltCount = allCorrections.filter((c) => c.severity === "NATIVE_ALTERNATIVE").length;

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full max-w-md bg-background/95 border-l border-border shadow-2xl p-5 overflow-y-auto backdrop-blur-xl animate-in slide-in-from-right duration-300">
      {/* Top Header */}
      <div className="flex items-center justify-between pb-3 border-b border-border">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-primary" />
          <h2 className="text-sm font-bold text-foreground">
            Live Conversation Intelligence (Phân tích trực tiếp)
          </h2>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Metrics Bar */}
      <div className="grid grid-cols-3 gap-2 py-4">
        <div className="p-2.5 rounded-xl bg-destructive/10 border border-destructive/20 text-center">
          <span className="text-[10px] text-destructive block font-medium">Must Fix</span>
          <span className="text-base font-bold text-destructive font-mono">{mustFixCount}</span>
        </div>
        <div className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-center">
          <span className="text-[10px] text-amber-300 block font-medium">Should Fix</span>
          <span className="text-base font-bold text-amber-400 font-mono">{shouldFixCount}</span>
        </div>
        <div className="p-2.5 rounded-xl bg-aizome-500/10 border border-aizome-500/20 text-center">
          <span className="text-[10px] text-aizome-300 block font-medium">Native Alt</span>
          <span className="text-base font-bold text-aizome-300 font-mono">{nativeAltCount}</span>
        </div>
      </div>

      {/* List of Analyzed Turns */}
      <div className="space-y-4 pt-1">
        <div className="flex items-center justify-between text-xs font-semibold text-muted-foreground">
          <span>Turn-by-turn Analysis ({turnAnalyses.length} lượt đã phân tích)</span>
          {summary?.pending_jobs_count ? (
            <span className="text-[11px] text-primary animate-pulse">
              Đang phân tích {summary.pending_jobs_count} lượt...
            </span>
          ) : null}
        </div>

        {turnAnalyses.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground text-xs rounded-xl bg-card/40 border border-border">
            Chưa có dữ liệu phân tích. Hãy nói một câu tiếng Nhật để hệ thống phân tích nền.
          </div>
        ) : (
          turnAnalyses.map((ta, idx) => (
            <div
              key={ta.id || idx}
              className="p-3.5 rounded-xl bg-card/70 border border-border/80 space-y-2.5 text-xs"
            >
              {/* Turn Header */}
              <div className="flex items-center justify-between">
                <span className="font-bold text-foreground text-[11px]">
                  Turn #{idx + 1} • Điểm chất lượng: {ta.overall_quality_score}/100
                </span>
                <Badge variant={ta.overall_quality_score >= 80 ? "matcha" : "outline"} size="sm">
                  {ta.communicative_success ? "✅ Đạt mục tiêu giao tiếp" : "⚠️ Cần cải thiện"}
                </Badge>
              </div>

              {/* Strengths */}
              {ta.strengths && ta.strengths.length > 0 && (
                <div className="p-2 rounded-lg bg-emerald-500/5 border border-emerald-500/20 space-y-1">
                  <div className="flex items-center gap-1 text-emerald-400 font-bold text-[10px]">
                    <Award className="h-3 w-3" />
                    <span>Điểm sáng:</span>
                  </div>
                  <ul className="text-[11px] text-foreground list-disc list-inside space-y-0.5">
                    {ta.strengths.map((str, sIdx) => (
                      <li key={sIdx}>{str}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Corrections in this turn */}
              {ta.corrections.length > 0 ? (
                <div className="space-y-1.5 pt-1">
                  {ta.corrections.map((corr) => (
                    <div
                      key={corr.id}
                      onClick={() => onSelectCorrection(corr)}
                      className="p-2 rounded-lg bg-background border border-border/90 hover:border-primary/40 cursor-pointer transition-colors flex items-center justify-between gap-2"
                    >
                      <div className="space-y-0.5 flex-1 min-w-0">
                        <div className="flex items-center gap-1.5">
                          <span
                            className={`text-[9px] font-bold px-1.5 py-0.2 rounded ${
                              corr.severity === "MUST_FIX"
                                ? "bg-destructive/20 text-destructive"
                                : corr.severity === "SHOULD_FIX"
                                ? "bg-amber-500/20 text-amber-400"
                                : "bg-aizome-500/20 text-aizome-300"
                            }`}
                          >
                            {corr.severity}
                          </span>
                          <span className="text-[10px] text-muted-foreground capitalize">
                            {corr.category}
                          </span>
                        </div>
                        <div className="flex items-center gap-1 font-mono text-[11px] truncate">
                          <span className="line-through text-muted-foreground">{corr.original}</span>
                          <span className="text-muted-foreground">→</span>
                          <span className="font-bold text-emerald-400">{corr.corrected}</span>
                        </div>
                      </div>
                      <ChevronRight className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-[11px] text-emerald-400 flex items-center gap-1">
                  <CheckCircle2 className="h-3 w-3" />
                  Câu nói tự nhiên, không cần sửa lỗi ngữ pháp.
                </p>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
