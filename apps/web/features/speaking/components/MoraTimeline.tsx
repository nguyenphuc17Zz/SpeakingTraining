"use client";

import React, { useState } from "react";
import { MoraUnit } from "../types/pronunciation";
import { Check, AlertCircle, Info, Clock } from "lucide-react";

interface Props {
  moras: MoraUnit[];
  speechRate?: number;
}

export const MoraTimeline: React.FC<Props> = ({ moras, speechRate }) => {
  const [selectedMora, setSelectedMora] = useState<MoraUnit | null>(null);

  if (!moras || moras.length === 0) {
    return (
      <div className="p-4 rounded-xl bg-card/50 border border-border text-center text-muted-foreground text-sm">
        Chưa có dữ liệu phân tích nhịp Mora.
      </div>
    );
  }

  return (
    <div className="p-5 rounded-2xl bg-gradient-to-b from-slate-900/80 to-slate-950/80 border border-border shadow-xl backdrop-blur-xl">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-indigo-500 animate-pulse" />
          <h3 className="font-semibold text-foreground text-sm tracking-wide">
            Phân tích trường độ & Nhịp điệu Mora (Isochrony)
          </h3>
        </div>
        {speechRate !== undefined && (
          <div className="flex items-center gap-1.5 text-xs text-indigo-300 font-mono bg-indigo-500/10 px-2.5 py-1 rounded-md border border-indigo-500/20">
            <Clock className="w-3.5 h-3.5" />
            <span>{speechRate} mora/giây</span>
          </div>
        )}
      </div>

      {/* Horizontal Mora Strip */}
      <div className="flex flex-wrap gap-2.5 py-2">
        {moras.map((m, idx) => {
          const isWarning = Boolean(m.issue) || (m.score !== null && m.score !== undefined && m.score < 80);
          const isSelected = selectedMora?.mora_index === m.mora_index;

          return (
            <button
              key={idx}
              onClick={() => setSelectedMora(m)}
              className={`group relative flex flex-col items-center justify-center min-w-[3.5rem] px-3 py-2.5 rounded-xl border transition-all duration-200 ${
                isSelected
                  ? "bg-indigo-600/30 border-indigo-400 shadow-lg shadow-indigo-500/20 scale-105"
                  : isWarning
                  ? "bg-amber-500/10 border-amber-500/30 hover:border-amber-400/50"
                  : "bg-muted/60 border-border/60 hover:border-slate-500"
              }`}
            >
              {/* Kana character */}
              <span className="text-xl font-bold text-foreground font-japanese">
                {m.kana}
              </span>

              {/* Phoneme subtext */}
              <span className="text-[10px] text-muted-foreground font-mono tracking-tighter">
                {m.phonemes.join("")}
              </span>

              {/* Status Badge */}
              <div className="mt-1.5">
                {isWarning ? (
                  <span className="flex items-center justify-center w-4 h-4 rounded-full bg-amber-500/20 text-amber-400 text-[10px]">
                    ⚠
                  </span>
                ) : (
                  <span className="flex items-center justify-center w-4 h-4 rounded-full bg-emerald-500/20 text-emerald-400 text-[10px]">
                    <Check className="w-2.5 h-2.5" />
                  </span>
                )}
              </div>

              {/* Timing indicator bar */}
              {m.actual_duration_ms && (
                <div className="mt-1 text-[9px] text-muted-foreground font-mono">
                  {m.actual_duration_ms}ms
                </div>
              )}
            </button>
          );
        })}
      </div>

      {/* Selected Mora Detail Modal/Card */}
      {selectedMora && (
        <div className="mt-4 p-3.5 rounded-xl bg-muted/70 border border-border text-xs animate-in fade-in slide-in-from-top-1 duration-200">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold text-indigo-400 font-japanese">
                「{selectedMora.kana}」
              </span>
              <span className="px-2 py-0.5 rounded bg-slate-700 text-foreground font-mono text-[11px]">
                Mora #{selectedMora.mora_index + 1}
              </span>
              {selectedMora.special_type && (
                <span className="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-[10px]">
                  {selectedMora.special_type === "gemination"
                    ? "促音 (っ)"
                    : selectedMora.special_type === "long_vowel"
                    ? "長音 (Trường âm)"
                    : selectedMora.special_type === "nasal"
                    ? "撥音 (ん)"
                    : "拗音 (Yōon)"}
                </span>
              )}
            </div>
            <button
              onClick={() => setSelectedMora(null)}
              className="text-muted-foreground hover:text-foreground text-xs px-2 py-0.5 rounded hover:bg-slate-700"
            >
              ✕ Đóng
            </button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mt-3 text-foreground">
            <div className="p-2 rounded-lg bg-card/60 border border-border">
              <div className="text-[10px] text-muted-foreground">Thời lượng thực tế</div>
              <div className="text-sm font-semibold text-foreground font-mono">
                {selectedMora.actual_duration_ms ?? "—"} ms
              </div>
            </div>
            <div className="p-2 rounded-lg bg-card/60 border border-border">
              <div className="text-[10px] text-muted-foreground">Thời lượng kỳ vọng</div>
              <div className="text-sm font-semibold text-foreground font-mono">
                {selectedMora.expected_duration_ms ?? "—"} ms
              </div>
            </div>
            <div className="p-2 rounded-lg bg-card/60 border border-border col-span-2 sm:col-span-1">
              <div className="text-[10px] text-muted-foreground">Tỷ lệ tương đối</div>
              <div className="text-sm font-semibold text-indigo-300 font-mono">
                {selectedMora.duration_ratio ? `${selectedMora.duration_ratio}x` : "1.0x"}
              </div>
            </div>
          </div>

          {selectedMora.issue && (
            <div className="mt-2.5 p-2 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{selectedMora.issue}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
