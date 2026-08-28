"use client";

import React, { useEffect, useState } from "react";
import {
  CheckCircle2,
  Loader2,
  AlertCircle,
  Circle,
  Sparkles,
  Youtube,
  Layers,
  FileText,
  Clock,
} from "lucide-react";
import { shadowingApi } from "@/services/shadowing-api";
import { ShadowingJobStatus } from "@/types/shadowing";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

interface ImportProgressTrackerProps {
  jobId: string;
  onCompleted?: (videoId: string) => void;
  onFailed?: (error: string) => void;
}

interface StageStep {
  key: string;
  label: string;
  jaLabel: string;
  description: string;
}

const STAGES: StageStep[] = [
  {
    key: "metadata",
    label: "Thông tin Video (Metadata)",
    jaLabel: "動画メタ情報",
    description: "Xác thực URL, lấy tiêu đề, thumbnail và thời lượng",
  },
  {
    key: "transcript_resolution",
    label: "Phụ đề tiếng Nhật (Japanese Captions)",
    jaLabel: "日本語字幕抽出",
    description: "Lấy phụ đề YouTube hoặc chạy Whisper STT fallback",
  },
  {
    key: "segmentation",
    label: "Phân đoạn câu & Phiên âm (Segmentation)",
    jaLabel: "文分割・発音解析",
    description: "Chuẩn hóa câu, gán phiên âm Hiragana và định danh người nói",
  },
  {
    key: "ai_analysis",
    label: "Phân tích Ngôn ngữ AI (Linguistic Intelligence)",
    jaLabel: "言語AI分析",
    description: "Trích xuất từ vựng trọng tâm, mẫu ngữ pháp và khẩu ngữ đời thường",
  },
  {
    key: "candidate_selection",
    label: "Cá nhân hóa đoạn luyện (Personalized Shadowing)",
    jaLabel: "個別最適化抽出",
    description: "Chọn lọc các câu thoại phù hợp nhất với điểm yếu và mục tiêu của bạn",
  },
];

export function ImportProgressTracker({
  jobId,
  onCompleted,
  onFailed,
}: ImportProgressTrackerProps) {
  const [jobStatus, setJobStatus] = useState<ShadowingJobStatus | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    let intervalId: NodeJS.Timeout | null = null;
    let isCompletedFired = false;

    const checkStatus = async () => {
      try {
        const res = await shadowingApi.getJobStatus(jobId);
        setJobStatus(res);

        if ((res.status === "ready" || res.status === "completed") && !isCompletedFired) {
          isCompletedFired = true;
          if (intervalId) clearInterval(intervalId);
          soundFX.playTaiko();
          setTimeout(() => {
            onCompleted?.(res.video_id);
          }, 600);
        } else if (res.status === "failed" || res.status === "partial") {
          if (intervalId) clearInterval(intervalId);
          const err = res.error_message || (res.status === "partial" ? "Không tìm thấy phụ đề tiếng Nhật hợp lệ cho video này." : "Xử lý video thất bại.");
          setErrorMsg(err);
          onFailed?.(err);
        }
      } catch (e: any) {
        console.warn("[ImportProgressTracker] Polling status error:", e);
      }
    };

    checkStatus();
    intervalId = setInterval(checkStatus, 900);

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [jobId, onCompleted, onFailed]);

  const getStageStatus = (stageIndex: number, stepKey: string) => {
    if (!jobStatus) return "pending";

    if (jobStatus.status === "ready" || jobStatus.status === "completed" || jobStatus.stage === "done") {
      return "completed";
    }

    const statuses = jobStatus.stage_statuses || (jobStatus as any).stage_statuses_json || {};

    // 1. Direct status check
    if (statuses[stepKey]) {
      const s = statuses[stepKey];
      if (s.startsWith("completed") || s.startsWith("partial")) return "completed";
      if (s.startsWith("failed")) return "failed";
    }

    if (jobStatus.status === "failed" || jobStatus.status === "partial") {
      const stageMap: Record<string, number> = {
        queued: 0,
        fetching_metadata: 0,
        resolving_transcript: 1,
        transcribing: 1,
        segmenting: 2,
        analyzing: 3,
        candidate_selection: 4,
        done: 5,
      };
      const currentStageIndex = stageMap[jobStatus.stage] ?? 0;
      if (currentStageIndex === stageIndex) return "failed";
      if (currentStageIndex > stageIndex) return "completed";
      return "pending";
    }

    // 2. Stage mapping fallback
    const stageMap: Record<string, number> = {
      queued: 0,
      fetching_metadata: 0,
      resolving_transcript: 1,
      transcribing: 1,
      segmenting: 2,
      analyzing: 3,
      candidate_selection: 4,
      done: 5,
    };

    const currentStageIndex = stageMap[jobStatus.stage] ?? 0;

    if (currentStageIndex > stageIndex) return "completed";
    if (currentStageIndex === stageIndex) return "in_progress";
    return "pending";
  };

  // Calculate completed count for progress percentage
  const completedCount = STAGES.reduce((acc, s, idx) => {
    return acc + (getStageStatus(idx, s.key) === "completed" ? 1 : 0);
  }, 0);
  const progressPercent = Math.min(100, Math.round((completedCount / STAGES.length) * 100));

  return (
    <div className="relative rounded-[28px] border border-border/90 bg-card/95 washi-texture shadow-sumi-lg p-6 sm:p-8 space-y-6 max-w-xl mx-auto animate-in fade-in duration-200">
      {/* Top Ambient Highlight */}
      <div className="absolute top-0 left-0 right-0 h-[3px] bg-gradient-to-r from-primary via-accent to-matcha-500 opacity-90" />

      {/* Header */}
      <div className="space-y-2 text-center relative z-10">
        <div className="inline-flex items-center justify-center p-3.5 rounded-2xl bg-primary/15 text-primary mb-1 border border-primary/25 shadow-sm">
          <Sparkles className="h-7 w-7 animate-pulse" />
        </div>
        <h3 className="text-lg sm:text-xl font-black text-foreground font-sans tracking-tight">
          Đang Phân Tích & Tạo Khóa Luyện Shadowing
        </h3>
        <p className="text-xs sm:text-sm text-muted-foreground max-w-md mx-auto leading-relaxed font-sans">
          Hệ thống đang trích xuất phụ đề, đồng bộ từng mili-giây và phân loại câu thoại phù hợp nhất với trình độ của bạn.
        </p>

        {/* Progress Bar */}
        <div className="pt-4 space-y-2 max-w-md mx-auto">
          <div className="flex justify-between text-xs font-bold text-muted-foreground">
            <span>Tiến độ hoàn tất</span>
            <span className="font-mono text-foreground font-black text-sm">{progressPercent}%</span>
          </div>
          <div className="h-2.5 w-full bg-muted/80 rounded-full overflow-hidden border border-border/70 shadow-inner">
            <div
              className="h-full bg-gradient-to-r from-primary via-accent to-matcha-500 rounded-full transition-all duration-500"
              style={{ width: `${Math.max(8, progressPercent)}%` }}
            />
          </div>
        </div>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-2xl bg-rose-950/50 border border-rose-500/50 text-rose-200 text-xs sm:text-sm flex items-start gap-3 shadow-md animate-in fade-in">
          <AlertCircle className="h-5 w-5 text-rose-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <p className="font-bold text-sm">Xử lý không thành công</p>
            <p className="text-rose-300/90 leading-relaxed">{errorMsg}</p>
          </div>
        </div>
      )}

      {/* Steps Progression */}
      <div className="space-y-3 pt-1 relative z-10">
        {STAGES.map((step, idx) => {
          const status = getStageStatus(idx, step.key);

          return (
            <div
              key={step.key}
              className={cn(
                "flex items-start gap-4 p-3.5 sm:p-4 rounded-2xl border transition-all duration-300",
                status === "completed"
                  ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400 shadow-sm"
                  : status === "in_progress"
                  ? "bg-primary/10 border-primary/40 shadow-md ring-1 ring-primary/25"
                  : status === "failed"
                  ? "bg-rose-500/10 border-rose-500/30 text-rose-300"
                  : "bg-background/40 border-border/60 opacity-60"
              )}
            >
              <div className="mt-0.5 shrink-0">
                {status === "completed" ? (
                  <div className="h-6 w-6 rounded-full bg-emerald-500/20 flex items-center justify-center text-emerald-400 shadow-sm">
                    <CheckCircle2 className="h-4 w-4" />
                  </div>
                ) : status === "in_progress" ? (
                  <div className="h-6 w-6 rounded-full bg-primary/20 flex items-center justify-center text-primary shadow-sm">
                    <Loader2 className="h-4 w-4 animate-spin" />
                  </div>
                ) : status === "failed" ? (
                  <div className="h-6 w-6 rounded-full bg-rose-500/20 flex items-center justify-center text-rose-500 shadow-sm">
                    <AlertCircle className="h-4 w-4" />
                  </div>
                ) : (
                  <Circle className="h-5 w-5 text-muted-foreground/40" />
                )}
              </div>

              <div className="flex-1 min-w-0 space-y-1">
                <div className="flex items-center gap-2">
                  <p
                    className={cn(
                      "text-xs sm:text-sm font-bold font-sans truncate",
                      status === "completed"
                        ? "text-emerald-400 font-black"
                        : status === "in_progress"
                        ? "text-foreground font-black"
                        : "text-muted-foreground"
                    )}
                  >
                    {step.label}
                  </p>
                  <span className="text-xs font-jp text-muted-foreground/70 hidden sm:inline">
                    ({step.jaLabel})
                  </span>
                </div>

                <p className="text-xs text-muted-foreground leading-relaxed">
                  {step.description}
                </p>
              </div>

              <div className="shrink-0 text-xs font-bold font-jp">
                {status === "completed" && (
                  <span className="px-2 py-0.5 rounded-md bg-emerald-500/20 text-emerald-400">
                    完了
                  </span>
                )}
                {status === "in_progress" && (
                  <span className="px-2 py-0.5 rounded-md bg-primary/20 text-primary animate-pulse">
                    処理中
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
