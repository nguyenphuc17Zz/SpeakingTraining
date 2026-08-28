"use client";

import React from "react";
import { AudioQualityReport } from "../types/pronunciation";
import { CheckCircle, AlertTriangle, XCircle, Mic } from "lucide-react";

interface Props {
  quality?: AudioQualityReport | null;
}

export const RecordingQualityBadge: React.FC<Props> = ({ quality }) => {
  if (!quality) return null;

  const isGood = quality.is_usable && quality.issues.length === 0;
  const isWarning = quality.is_usable && quality.issues.length > 0;
  const isBad = !quality.is_usable;

  return (
    <div
      className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-medium backdrop-blur-md transition-all ${
        isGood
          ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
          : isWarning
          ? "bg-amber-500/10 border-amber-500/30 text-amber-300"
          : "bg-destructive/10 border-destructive/30 text-destructive"
      }`}
    >
      {isGood ? (
        <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
      ) : isWarning ? (
        <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
      ) : (
        <XCircle className="w-3.5 h-3.5 text-destructive" />
      )}

      <span>
        {isGood
          ? "Chất lượng âm thanh: Tốt"
          : isWarning
          ? "Âm thanh: Có tạp âm / hơi nhỏ"
          : "Âm thanh: Không đạt yêu cầu"}
      </span>

      {quality.snr_estimate_db !== undefined && quality.snr_estimate_db !== null && (
        <span className="opacity-70 border-l border-current pl-2">
          SNR: {quality.snr_estimate_db} dB
        </span>
      )}
    </div>
  );
};
