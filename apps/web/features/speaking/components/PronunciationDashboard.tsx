"use client";

import React, { useState } from "react";
import { PronunciationResult } from "../types/pronunciation";
import { MoraTimeline } from "./MoraTimeline";
import { PitchContourChart } from "./PitchContourChart";
import { PronunciationFeedbackPanel } from "./PronunciationFeedbackPanel";
import { RecordingQualityBadge } from "./RecordingQualityBadge";
import {
  Award,
  Sparkles,
  Layers,
  Music,
  Clock,
  Volume2,
  ChevronDown,
  ChevronUp,
  Activity,
} from "lucide-react";

interface Props {
  result: PronunciationResult;
  onPlayReference?: () => void;
  onPlayUserAudio?: () => void;
}

export const PronunciationDashboard: React.FC<Props> = ({
  result,
  onPlayReference,
  onPlayUserAudio,
}) => {
  const [showAdvanced, setShowAdvanced] = useState(false);

  const getTierBadge = (score: number) => {
    if (score >= 90) return { label: "Xuất sắc (Excellent)", color: "emerald" };
    if (score >= 80) return { label: "Rất tốt (Very Good)", color: "indigo" };
    if (score >= 70) return { label: "Tốt (Good)", color: "blue" };
    if (score >= 60) return { label: "Đang phát triển (Developing)", color: "amber" };
    return { label: "Cần cải thiện (Needs Attention)", color: "rose" };
  };

  const tier = getTierBadge(result.overall_score);

  return (
    <div className="space-y-6">
      {/* Top Header Card — Overall Score & Quality */}
      <div className="relative overflow-hidden p-6 rounded-3xl bg-gradient-to-br from-slate-900 via-indigo-950/40 to-slate-900 border border-border shadow-2xl backdrop-blur-2xl">
        <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20" />

        <div className="flex flex-col md:flex-row items-center justify-between gap-6 relative z-10">
          {/* Left: Overall Score Circle & Tier */}
          <div className="flex items-center gap-5">
            <div className="relative flex items-center justify-center w-24 h-24 rounded-2xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-purple-500 p-0.5 shadow-xl shadow-indigo-500/25">
              <div className="flex flex-col items-center justify-center w-full h-full bg-background rounded-[14px]">
                <span className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-br from-indigo-200 via-white to-indigo-300 font-mono">
                  {result.overall_score.toFixed(0)}
                </span>
                <span className="text-[10px] text-muted-foreground uppercase tracking-widest font-mono">
                  / 100
                </span>
              </div>
            </div>

            <div>
              <div className="flex items-center gap-2 mb-1">
                <span
                  className={`text-xs font-semibold px-2.5 py-0.5 rounded-full border ${
                    tier.color === "emerald"
                      ? "bg-emerald-500/20 border-emerald-500/30 text-emerald-300"
                      : tier.color === "indigo"
                      ? "bg-indigo-500/20 border-indigo-500/30 text-indigo-300"
                      : tier.color === "amber"
                      ? "bg-amber-500/20 border-amber-500/30 text-amber-300"
                      : "bg-destructive/20 border-destructive/30 text-destructive"
                  }`}
                >
                  {tier.label}
                </span>
                <span className="text-xs text-muted-foreground font-mono">
                  Độ tin cậy: {result.overall_confidence.toUpperCase()}
                </span>
              </div>
              <h2 className="text-xl font-bold text-foreground tracking-tight">
                Đánh giá phát âm chuẩn Nhật
              </h2>
              <p className="text-xs text-muted-foreground mt-0.5">
                Phân tích toàn diện 5 trụ cột âm thanh tiếng Nhật
              </p>
            </div>
          </div>

          {/* Right: Audio Quality Badge */}
          <div className="flex flex-col items-end gap-2">
            <RecordingQualityBadge quality={result.audio_quality} />
            <div className="text-[11px] text-muted-foreground font-mono">
              Engine v{result.engine_version}
            </div>
          </div>
        </div>

        {/* 5 Component Subscore Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 mt-6 pt-6 border-t border-border/80">
          {/* 1. Phoneme */}
          <div className="p-3 rounded-xl bg-card/60 border border-border/80 flex flex-col justify-between">
            <div className="flex items-center justify-between text-muted-foreground text-xs mb-1">
              <span className="flex items-center gap-1">
                <Volume2 className="w-3.5 h-3.5 text-blue-400" />
                Ngữ âm
              </span>
              <span className="text-[10px] text-muted-foreground font-mono">25%</span>
            </div>
            <div className="text-lg font-bold text-foreground font-mono">
              {result.phoneme_score?.available
                ? `${result.phoneme_score.score.toFixed(0)}`
                : "—"}
            </div>
            <div className="text-[10px] text-muted-foreground mt-1">
              {result.phoneme_score?.interpretation || "Không khả dụng"}
            </div>
          </div>

          {/* 2. Mora Timing */}
          <div className="p-3 rounded-xl bg-card/60 border border-border/80 flex flex-col justify-between">
            <div className="flex items-center justify-between text-muted-foreground text-xs mb-1">
              <span className="flex items-center gap-1">
                <Clock className="w-3.5 h-3.5 text-indigo-400" />
                Trường độ Mora
              </span>
              <span className="text-[10px] text-muted-foreground font-mono">25%</span>
            </div>
            <div className="text-lg font-bold text-foreground font-mono">
              {result.mora_timing_score?.available
                ? `${result.mora_timing_score.score.toFixed(0)}`
                : "—"}
            </div>
            <div className="text-[10px] text-muted-foreground mt-1">
              {result.mora_timing_score?.interpretation || "Không khả dụng"}
            </div>
          </div>

          {/* 3. Pitch Accent */}
          <div className="p-3 rounded-xl bg-card/60 border border-border/80 flex flex-col justify-between">
            <div className="flex items-center justify-between text-muted-foreground text-xs mb-1">
              <span className="flex items-center gap-1">
                <Music className="w-3.5 h-3.5 text-cyan-400" />
                Cao độ (Pitch)
              </span>
              <span className="text-[10px] text-muted-foreground font-mono">20%</span>
            </div>
            <div className="text-lg font-bold text-foreground font-mono">
              {result.pitch_score?.available
                ? `${result.pitch_score.score.toFixed(0)}`
                : "—"}
            </div>
            <div className="text-[10px] text-muted-foreground mt-1">
              {result.pitch_score?.interpretation || "Không khả dụng"}
            </div>
          </div>

          {/* 4. Rhythm */}
          <div className="p-3 rounded-xl bg-card/60 border border-border/80 flex flex-col justify-between">
            <div className="flex items-center justify-between text-muted-foreground text-xs mb-1">
              <span className="flex items-center gap-1">
                <Activity className="w-3.5 h-3.5 text-purple-400" />
                Nhịp điệu
              </span>
              <span className="text-[10px] text-muted-foreground font-mono">15%</span>
            </div>
            <div className="text-lg font-bold text-foreground font-mono">
              {result.rhythm_score?.available
                ? `${result.rhythm_score.score.toFixed(0)}`
                : "—"}
            </div>
            <div className="text-[10px] text-muted-foreground mt-1">
              {result.rhythm_score?.interpretation || "Không khả dụng"}
            </div>
          </div>

          {/* 5. Intonation */}
          <div className="p-3 rounded-xl bg-card/60 border border-border/80 flex flex-col justify-between col-span-2 sm:col-span-1">
            <div className="flex items-center justify-between text-muted-foreground text-xs mb-1">
              <span className="flex items-center gap-1">
                <Layers className="w-3.5 h-3.5 text-emerald-400" />
                Ngữ điệu câu
              </span>
              <span className="text-[10px] text-muted-foreground font-mono">15%</span>
            </div>
            <div className="text-lg font-bold text-foreground font-mono">
              {result.intonation_score?.available
                ? `${result.intonation_score.score.toFixed(0)}`
                : "—"}
            </div>
            <div className="text-[10px] text-muted-foreground mt-1">
              {result.intonation_score?.interpretation || "Không khả dụng"}
            </div>
          </div>
        </div>
      </div>

      {/* Visual Analytics: Mora Timeline & Pitch Contour Chart */}
      <div className="space-y-4">
        {result.mora_assessment && (
          <MoraTimeline
            moras={result.mora_assessment.mora_units}
            speechRate={result.mora_assessment.speech_rate_mora_per_sec}
          />
        )}

        {result.pitch_assessment && (
          <PitchContourChart
            pitchAssessment={result.pitch_assessment}
            moras={result.mora_assessment?.mora_units}
          />
        )}
      </div>

      {/* Actionable Feedback Panel */}
      <PronunciationFeedbackPanel
        topIssues={result.top_issues}
        strengths={result.strengths}
        practiceRecommendation={result.practice_recommendation}
        onPlayReference={onPlayReference}
        onPlayUserAudio={onPlayUserAudio}
      />

      {/* Advanced Technical Details Collapsible */}
      <div className="p-4 rounded-2xl bg-background/60 border border-border text-xs text-muted-foreground">
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="w-full flex items-center justify-between text-left text-foreground font-medium"
        >
          <span>Thông số âm học nâng cao (Acoustic Metadata)</span>
          {showAdvanced ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>

        {showAdvanced && (
          <div className="mt-4 pt-3 border-t border-border/80 space-y-2 font-mono text-[11px] animate-in fade-in duration-200">
            <div>Loại tham chiếu: {result.reference_type}</div>
            <div>Phiên bản chấm điểm: {result.scoring_version}</div>
            {result.partial_reasons.length > 0 && (
              <div className="text-amber-300">
                Ghi chú bộ phân tích: {result.partial_reasons.join(", ")}
              </div>
            )}
            {result.pitch_assessment?.pitch_curve?.speaker_f0_mean && (
              <div>
                F₀ Trung bình của người nói: {result.pitch_assessment.pitch_curve.speaker_f0_mean} Hz
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
