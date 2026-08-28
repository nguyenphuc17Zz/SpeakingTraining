"use client";

import React, { useState } from "react";
import { PronunciationFeedbackItem } from "../types/pronunciation";
import { Sparkles, AlertCircle, Volume2, Play, CheckCircle2, ChevronDown, ChevronUp } from "lucide-react";

interface Props {
  topIssues: PronunciationFeedbackItem[];
  strengths: string[];
  practiceRecommendation?: string | null;
  referenceAudioUrl?: string | null;
  userAudioBlobUrl?: string | null;
  onPlayReference?: () => void;
  onPlayUserAudio?: () => void;
}

export const PronunciationFeedbackPanel: React.FC<Props> = ({
  topIssues,
  strengths,
  practiceRecommendation,
  onPlayReference,
  onPlayUserAudio,
}) => {
  const [showAllStrengths, setShowAllStrengths] = useState(false);

  return (
    <div className="space-y-4">
      {/* Primary Practice Recommendation Banner */}
      {practiceRecommendation && (
        <div className="p-4 rounded-2xl bg-gradient-to-r from-indigo-500/15 via-purple-500/15 to-pink-500/15 border border-indigo-500/30 backdrop-blur-md shadow-lg flex items-start gap-3">
          <Sparkles className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
          <div className="text-sm">
            <h4 className="font-semibold text-indigo-200 mb-0.5">Lời khuyên luyện tập cốt lõi</h4>
            <p className="text-foreground leading-relaxed">{practiceRecommendation}</p>
          </div>
        </div>
      )}

      {/* Top 3 Prioritized Issues */}
      <div className="p-5 rounded-2xl bg-gradient-to-b from-slate-900/80 to-slate-950/80 border border-border shadow-xl backdrop-blur-xl space-y-3">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-amber-400" />
            <h3 className="font-semibold text-foreground text-sm tracking-wide">
              Điểm cần cải thiện trọng tâm (Top Focus)
            </h3>
          </div>
          {topIssues.length > 0 && (
            <span className="text-xs text-amber-300 font-mono bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
              {topIssues.length} điểm cần chú ý
            </span>
          )}
        </div>

        {topIssues.length === 0 ? (
          <div className="py-6 text-center text-muted-foreground text-sm flex flex-col items-center gap-2">
            <CheckCircle2 className="w-8 h-8 text-emerald-400 opacity-80" />
            <p className="font-medium text-foreground">Phát âm rất chuẩn xác!</p>
            <span className="text-xs text-muted-foreground">Không phát hiện lỗi ngữ âm hoặc nhịp điệu đáng kể.</span>
          </div>
        ) : (
          topIssues.map((issue, idx) => {
            const isMustFix = issue.severity === "MUST_FIX";
            return (
              <div
                key={idx}
                className={`p-4 rounded-xl border transition-all ${
                  isMustFix
                    ? "bg-destructive/5 border-destructive/30 hover:border-destructive/50"
                    : "bg-muted/40 border-border/60 hover:border-slate-600"
                }`}
              >
                <div className="flex items-start justify-between gap-3 mb-1.5">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="flex items-center justify-center w-5 h-5 rounded-full bg-muted text-foreground font-mono text-xs border border-border">
                      {idx + 1}
                    </span>
                    <h4 className="font-bold text-foreground text-sm">{issue.title}</h4>
                    {issue.target_snippet && (
                      <span className="px-2 py-0.5 rounded bg-aizome-500/20 text-aizome-300 border border-aizome-500/30 font-japanese text-xs">
                        「{issue.target_snippet}」
                      </span>
                    )}
                  </div>
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded font-mono uppercase border ${
                      isMustFix
                        ? "bg-destructive/20 text-destructive border-destructive/30"
                        : "bg-amber-500/20 text-amber-300 border-amber-500/30"
                    }`}
                  >
                    {isMustFix ? "Cần sửa ngay" : "Nên cải thiện"}
                  </span>
                </div>

                <p className="text-xs text-foreground mb-2.5 leading-relaxed">{issue.explanation}</p>

                <div className="p-2.5 rounded-lg bg-card/60 border border-border/80 text-xs text-indigo-200 flex items-start gap-2">
                  <Sparkles className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5" />
                  <div>
                    <strong className="text-indigo-300 font-medium">Mẹo luyện tập: </strong>
                    <span>{issue.practice_tip}</span>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Strengths Card */}
      {strengths.length > 0 && (
        <div className="p-4 rounded-2xl bg-gradient-to-b from-slate-900/60 to-slate-950/60 border border-border/80 shadow-md">
          <button
            onClick={() => setShowAllStrengths(!showAllStrengths)}
            className="w-full flex items-center justify-between text-left"
          >
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <h3 className="font-semibold text-foreground text-xs tracking-wide">
                Điểm mạnh phát âm đã ghi nhận ({strengths.length})
              </h3>
            </div>
            {showAllStrengths ? (
              <ChevronUp className="w-4 h-4 text-muted-foreground" />
            ) : (
              <ChevronDown className="w-4 h-4 text-muted-foreground" />
            )}
          </button>

          {showAllStrengths && (
            <ul className="mt-3 space-y-2 text-xs text-foreground pl-6 list-disc marker:text-emerald-400 animate-in fade-in duration-150">
              {strengths.map((s, idx) => (
                <li key={idx} className="leading-relaxed">
                  {s}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
};
