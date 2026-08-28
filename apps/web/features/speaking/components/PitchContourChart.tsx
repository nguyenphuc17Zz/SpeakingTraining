"use client";

import React, { useMemo } from "react";
import { MoraUnit, PitchAssessment, PitchCurve } from "../types/pronunciation";
import { Activity, TrendingUp, Music2 } from "lucide-react";

interface Props {
  pitchAssessment?: PitchAssessment | null;
  moras?: MoraUnit[];
}

export const PitchContourChart: React.FC<Props> = ({ pitchAssessment, moras }) => {
  const curve = pitchAssessment?.pitch_curve;
  const points = curve?.points || [];

  // Generate SVG path for voiced pitch points
  const chartData = useMemo(() => {
    if (!points || points.length === 0) return null;

    const voicedPoints = points.filter((p) => p.is_voiced);
    if (voicedPoints.length === 0) return null;

    const minTime = points[0].timestamp_ms;
    const maxTime = Math.max(minTime + 100, points[points.length - 1].timestamp_ms);
    const timeSpan = maxTime - minTime;

    // Semitone bounds: clamp between [-8, +8] semitones
    const minSemi = -6.0;
    const maxSemi = 6.0;
    const semiSpan = maxSemi - minSemi;

    const svgWidth = 600;
    const svgHeight = 160;
    const padX = 30;
    const padY = 20;
    const plotW = svgWidth - padX * 2;
    const plotH = svgHeight - padY * 2;

    // Generate path segments (split across unvoiced gaps)
    const paths: string[] = [];
    let currentPath = "";

    points.forEach((p, idx) => {
      if (!p.is_voiced) {
        if (currentPath) {
          paths.push(currentPath);
          currentPath = "";
        }
        return;
      }

      const x = padX + ((p.timestamp_ms - minTime) / timeSpan) * plotW;
      const clampedSemi = Math.max(minSemi, Math.min(maxSemi, p.normalized_semitones));
      // Invert Y: higher semitone -> lower Y coordinate
      const y = padY + (1.0 - (clampedSemi - minSemi) / semiSpan) * plotH;

      if (!currentPath) {
        currentPath = `M ${x.toFixed(1)} ${y.toFixed(1)}`;
      } else {
        currentPath += ` L ${x.toFixed(1)} ${y.toFixed(1)}`;
      }
    });

    if (currentPath) {
      paths.push(currentPath);
    }

    // Zero-semitone baseline Y
    const zeroY = padY + (1.0 - (0.0 - minSemi) / semiSpan) * plotH;

    return {
      paths,
      zeroY,
      svgWidth,
      svgHeight,
      padX,
      padY,
      plotW,
      plotH,
      minTime,
      maxTime,
    };
  }, [points]);

  if (!pitchAssessment || !chartData || chartData.paths.length === 0) {
    return (
      <div className="p-6 rounded-2xl bg-card/60 border border-border text-center text-muted-foreground text-xs flex flex-col items-center justify-center gap-2">
        <Activity className="w-6 h-6 text-muted-foreground opacity-50" />
        <span>Không có dữ liệu đường cong cao độ âm thanh rõ ràng.</span>
      </div>
    );
  }

  const targetPattern = pitchAssessment.accent_pattern_target;
  const observedPattern = pitchAssessment.accent_pattern_observed;
  const isMatched = pitchAssessment.pattern_matched;

  return (
    <div className="p-5 rounded-2xl bg-gradient-to-b from-slate-900/80 to-slate-950/80 border border-border shadow-xl backdrop-blur-xl">
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <Music2 className="w-4 h-4 text-cyan-400" />
          <h3 className="font-semibold text-foreground text-sm tracking-wide">
            Đường cong cao độ Tokyo Pitch Accent (F₀ Contour)
          </h3>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs px-2.5 py-1 rounded-full bg-muted border border-border text-foreground">
            Mục tiêu: <strong className="text-cyan-300 uppercase font-mono">{targetPattern}</strong>
          </span>
          <span
            className={`text-xs px-2.5 py-1 rounded-full border font-medium ${
              isMatched
                ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
                : "bg-amber-500/10 border-amber-500/30 text-amber-300"
            }`}
          >
            Thực tế: <strong className="uppercase font-mono">{observedPattern}</strong>
          </span>
        </div>
      </div>

      {/* SVG Canvas */}
      <div className="relative w-full overflow-hidden rounded-xl bg-background/60 border border-border/80 p-2">
        <svg
          viewBox={`0 0 ${chartData.svgWidth} ${chartData.svgHeight}`}
          className="w-full h-auto max-h-48"
        >
          {/* Subtle Gridlines */}
          <line
            x1={chartData.padX}
            y1={chartData.zeroY}
            x2={chartData.svgWidth - chartData.padX}
            y2={chartData.zeroY}
            stroke="#334155"
            strokeDasharray="4 4"
            strokeWidth="1"
          />
          <text
            x={chartData.padX - 8}
            y={chartData.zeroY + 3}
            fill="#64748b"
            fontSize="9"
            textAnchor="end"
            fontFamily="monospace"
          >
            0
          </text>
          <text
            x={chartData.padX - 8}
            y={chartData.padY + 8}
            fill="#64748b"
            fontSize="9"
            textAnchor="end"
            fontFamily="monospace"
          >
            +4st
          </text>
          <text
            x={chartData.padX - 8}
            y={chartData.svgHeight - chartData.padY}
            fill="#64748b"
            fontSize="9"
            textAnchor="end"
            fontFamily="monospace"
          >
            -4st
          </text>

          {/* Mora separator lines along X axis */}
          {moras &&
            moras.length > 0 &&
            moras.map((m, idx) => {
              const xPos =
                chartData.padX + (idx / Math.max(1, moras.length)) * chartData.plotW;
              return (
                <g key={idx}>
                  <line
                    x1={xPos}
                    y1={chartData.padY}
                    x2={xPos}
                    y2={chartData.svgHeight - chartData.padY}
                    stroke="#1e293b"
                    strokeWidth="1"
                  />
                  <text
                    x={xPos + 12}
                    y={chartData.svgHeight - 6}
                    fill="#94a3b8"
                    fontSize="11"
                    fontFamily="sans-serif"
                    fontWeight="bold"
                  >
                    {m.kana}
                  </text>
                </g>
              );
            })}

          {/* User Voiced Pitch Curve */}
          {chartData.paths.map((p, idx) => (
            <path
              key={idx}
              d={p}
              fill="none"
              stroke="#38bdf8"
              strokeWidth="3.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="drop-shadow-[0_0_8px_rgba(56,189,248,0.5)]"
            />
          ))}
        </svg>
      </div>

      {pitchAssessment.explanation && (
        <div className="mt-3 text-xs text-foreground bg-muted/40 p-2.5 rounded-lg border border-border/50 flex items-center gap-2">
          <TrendingUp className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
          <span>{pitchAssessment.explanation}</span>
        </div>
      )}
    </div>
  );
};
