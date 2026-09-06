"use client";

import React from "react";
import { Zap, Activity, Waves, CheckCircle2, AlertTriangle, Clock, Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface ShadowingAcousticVisualizerProps {
  metrics?: {
    acoustic_lag_ms?: number | null;
    lag_rating?: "optimal" | "too_fast" | "hesitant" | "trailing" | string | null;
    lag_score?: number | null;
    pitch_contour_similarity?: number | null;
    [key: string]: any;
  } | null;
}

export function ShadowingAcousticVisualizer({ metrics }: ShadowingAcousticVisualizerProps) {
  if (!metrics) return null;

  const lagMs = metrics.acoustic_lag_ms;
  const lagRating = metrics.lag_rating || (lagMs != null ? (lagMs < 100 ? "too_fast" : lagMs <= 400 ? "optimal" : lagMs <= 700 ? "hesitant" : "trailing") : null);
  const lagScore = metrics.lag_score;
  const pitchContour = metrics.pitch_contour_similarity;

  // Don't render if neither acoustic lag nor pitch contour similarity is available
  if (lagMs == null && pitchContour == null) {
    return null;
  }

  // Calculate percentage along 0 - 1000ms spectrum
  const clampedLag = lagMs != null ? Math.max(0, Math.min(1000, lagMs)) : 250;
  const needlePercent = (clampedLag / 1000) * 100;

  const RATING_MAP: Record<
    string,
    {
      label: string;
      sublabel: string;
      badgeClass: string;
      icon: React.ReactNode;
      advice: string;
    }
  > = {
    optimal: {
      label: "Đồng bộ hoàn hảo",
      sublabel: "Sweet Spot: ~250ms",
      badgeClass: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30",
      icon: <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />,
      advice: "Tuyệt vời! Bạn đang duy trì đúng nhịp phản xạ âm học, bám sát âm thanh bản xứ mà không bị nói đè.",
    },
    too_fast: {
      label: "Nói đè lên audio mẫu",
      sublabel: "Đồng thanh quá sớm (<100ms)",
      badgeClass: "bg-rose-500/15 text-rose-600 dark:text-rose-400 border-rose-500/30",
      icon: <AlertTriangle className="h-3.5 w-3.5 text-rose-500" />,
      advice: "Bạn đang nói đè lên giọng mẫu! Hãy chờ người bản xứ phát âm được 1–2 âm tiết (~250ms) rồi mới bám theo.",
    },
    hesitant: {
      label: "Khởi phát ngập ngừng",
      sublabel: "Xử lý trễ (401 - 700ms)",
      badgeClass: "bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30",
      icon: <Clock className="h-3.5 w-3.5 text-amber-500" />,
      advice: "Độ trễ hơi dài. Hãy tin vào đôi tai và phản xạ bật âm tức thì thay vì cố gắng dịch nghĩa câu chữ trong đầu.",
    },
    trailing: {
      label: "Lặp lại thụ động",
      sublabel: "Tụt lại phía sau (>700ms)",
      badgeClass: "bg-purple-500/15 text-purple-600 dark:text-purple-400 border-purple-500/30",
      icon: <Activity className="h-3.5 w-3.5 text-purple-500" />,
      advice: "Bạn đang chờ audio nói xong hẳn rồi mới lặp lại (Repeating). Hãy thử bám sát ngay gót chân người bản xứ!",
    },
  };

  const ratingConfig = RATING_MAP[lagRating || "optimal"] || RATING_MAP.optimal;

  return (
    <div className="p-3.5 sm:p-4 rounded-2xl bg-card border border-border/80 shadow-xs space-y-3.5 animate-in fade-in duration-200">
      {/* 1. Header with Cognitive Telemetry & Dynamic Badge */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/50 pb-2.5">
        <div className="flex items-center gap-2">
          <Zap className="h-4 w-4 text-primary" />
          <span className="text-xs font-bold text-foreground">
            Phân Tích Độ Trễ Thính Giác & Ngữ Điệu (Acoustic SLA Profiler)
          </span>
        </div>

        {lagRating && (
          <span
            className={cn(
              "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold border shadow-2xs",
              ratingConfig.badgeClass
            )}
          >
            {ratingConfig.icon}
            <span>{ratingConfig.label}</span>
          </span>
        )}
      </div>

      {/* 2. Horizontal Latency Meter (0ms -> 1000ms) */}
      {lagMs != null && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-[11px] font-mono">
            <span className="text-muted-foreground font-sans flex items-center gap-1">
              <span>Độ trễ khởi phát:</span>
              <strong className="text-foreground font-mono">{Math.round(lagMs)}ms</strong>
            </span>
            {lagScore != null && (
              <span className="text-[10px] text-muted-foreground">
                Điểm nhịp bám: <strong className="text-primary font-mono">{Math.round(lagScore)}%</strong>
              </span>
            )}
          </div>

          {/* Spectrum Bar with Marked Zones */}
          <div className="relative h-4 w-full bg-muted/60 rounded-full overflow-hidden border border-border/70 p-0.5">
            {/* Zone 1: Too Fast (<100ms, 0 - 10%) */}
            <div
              className="absolute left-0 top-0 bottom-0 bg-rose-500/30 border-r border-rose-500/50"
              style={{ width: "10%" }}
              title="Nói đè (<100ms)"
            />

            {/* Zone 2: Pre-sweet (100 - 150ms, 10 - 15%) */}
            <div
              className="absolute top-0 bottom-0 bg-amber-500/20"
              style={{ left: "10%", width: "5%" }}
            />

            {/* Zone 3: Cognitive Sweet Spot (150 - 400ms, 15 - 40%) */}
            <div
              className="absolute top-0 bottom-0 bg-emerald-500/35 border-x border-emerald-500/60 flex items-center justify-center shadow-inner"
              style={{ left: "15%", width: "25%" }}
              title="Vùng vàng Shadowing (150 - 400ms)"
            >
              <span className="text-[9px] font-bold text-emerald-700 dark:text-emerald-300 tracking-tighter opacity-80 hidden sm:inline">
                ✨ Vùng vàng: ~250ms
              </span>
            </div>

            {/* Zone 4: Hesitant (400 - 700ms, 40 - 70%) */}
            <div
              className="absolute top-0 bottom-0 bg-amber-500/25 border-r border-amber-500/40"
              style={{ left: "40%", width: "30%" }}
              title="Ngập ngừng (400 - 700ms)"
            />

            {/* Zone 5: Trailing (>700ms, 70 - 100%) */}
            <div
              className="absolute right-0 top-0 bottom-0 bg-purple-500/30"
              style={{ left: "70%", width: "30%" }}
              title="Lặp lại thụ động (>700ms)"
            />

            {/* Moving Indicator Needle / Cursor */}
            <div
              className="absolute top-0 bottom-0 w-2 -ml-1 bg-foreground rounded-full shadow-md z-10 transition-all duration-500 border border-background"
              style={{ left: `${needlePercent}%` }}
            />
          </div>

          {/* Scale Labels */}
          <div className="flex justify-between text-[9px] font-mono text-muted-foreground px-0.5">
            <span>0ms (Đồng thanh)</span>
            <span className="text-emerald-600 dark:text-emerald-400 font-bold">250ms (Chuẩn SLA)</span>
            <span>500ms</span>
            <span>700ms+ (Lặp lại)</span>
          </div>
        </div>
      )}

      {/* 3. DTW Intonation Similarity Bar */}
      {pitchContour != null && (
        <div className="p-2.5 rounded-xl bg-muted/40 border border-border/70 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Waves className="h-4 w-4 text-sky-500 shrink-0" />
            <div>
              <div className="text-xs font-bold text-foreground flex items-center gap-1.5">
                <span>So khớp Đường cong Ngữ điệu DTW:</span>
                <span className="text-sky-600 dark:text-sky-400 font-mono font-black">
                  {Math.round(pitchContour)}%
                </span>
              </div>
              <p className="text-[10px] text-muted-foreground">
                {pitchContour >= 85
                  ? "Ngữ điệu rất mượt, uốn lượn khớp tự nhiên với ngữ điệu mẫu bản xứ."
                  : pitchContour >= 70
                  ? "Đường cong ngữ điệu tương đối tốt, chú ý nhấn nhá ngữ điệu ở cuối câu."
                  : "Cao độ còn hơi bằng phẳng hoặc đảo ngược ngữ điệu, hãy chú ý cao trào câu."}
              </p>
            </div>
          </div>

          <Badge variant={pitchContour >= 85 ? "matcha" : pitchContour >= 70 ? "secondary" : "outline"} size="sm" className="text-[10px] shrink-0">
            {pitchContour >= 85 ? "Chuẩn Tokyo" : pitchContour >= 70 ? "Khá tốt" : "Cần chỉnh"}
          </Badge>
        </div>
      )}

      {/* 4. Actionable Pacing Coaching Advice */}
      {ratingConfig.advice && (
        <div className="text-[11px] text-muted-foreground bg-muted/30 p-2 rounded-xl border border-border/50 flex items-start gap-1.5">
          <Sparkles className="h-3.5 w-3.5 text-primary shrink-0 mt-0.5" />
          <span>{ratingConfig.advice}</span>
        </div>
      )}
    </div>
  );
}
