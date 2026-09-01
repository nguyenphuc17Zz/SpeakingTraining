"use client";
import React from "react";

interface RampStageIndicatorProps {
  currentStage: number;
  totalStages?: number;
  showLabels?: boolean;
}

const STAGE_NAMES = [
  "Echo", "Sub", "Fill", "1文", "拡張",
  "理由", "例示", "KW", "誘導", "自由", "独立",
];

export function RampStageIndicator({
  currentStage,
  totalStages = 11,
  showLabels = false,
}: RampStageIndicatorProps) {
  return (
    <div className="ramp-stage-indicator">
      <div className="ramp-stage-dots">
        {Array.from({ length: totalStages }).map((_, i) => {
          const isPast = i < currentStage;
          const isCurrent = i === currentStage;
          const isFuture = i > currentStage;
          return (
            <div
              key={i}
              className={`ramp-stage-dot ${
                isCurrent ? "ramp-stage-dot--current" : ""
              } ${isPast ? "ramp-stage-dot--past" : ""} ${
                isFuture ? "ramp-stage-dot--future" : ""
              }`}
              title={STAGE_NAMES[i]}
            >
              {isCurrent && <span className="ramp-stage-dot-inner" />}
            </div>
          );
        })}
      </div>
      {showLabels && (
        <div className="ramp-stage-label">
          <span className="ramp-stage-zone">
            ゾーン {currentStage + 1}/11 — {STAGE_NAMES[currentStage]}
          </span>
        </div>
      )}
    </div>
  );
}
