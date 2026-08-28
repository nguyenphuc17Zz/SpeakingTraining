"use client";

import React from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Trophy,
  RotateCcw,
  Zap,
  Home,
  Volume2,
  Compass,
} from "lucide-react";
import { SituationsResult } from "../services/situations-api";
import { speakJapaneseText } from "@/features/speaking/services/web-speech";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

interface SituationsSessionSummaryProps {
  results: SituationsResult[];
  onRestart: () => void;
  onToLobby: () => void;
  onRetryWeak: () => void;
}

export function SituationsSessionSummary({
  results,
  onRestart,
  onToLobby,
  onRetryWeak,
}: SituationsSessionSummaryProps) {
  const total = results.length;
  const correct = results.filter((r) => r.success).length;
  const perfect = results.filter((r) => r.isPerfect || (r.score ?? 0) >= 90).length;
  const accuracy = total > 0 ? Math.round((correct / total) * 100) : 0;
  const avgLatency =
    total > 0
      ? Math.round(results.reduce((acc, r) => acc + (r.reactionLatencyMs || 0), 0) / total)
      : 0;

  // Japanese Hanko Stamp Grade
  const getHankoGrade = (acc: number) => {
    if (acc >= 90) return { kanji: "大変よくできました", grade: "S", variant: "bg-rose-500/10 border-rose-500 text-rose-600" };
    if (acc >= 80) return { kanji: "合格", grade: "A", variant: "bg-emerald-500/10 border-emerald-500 text-emerald-600" };
    if (acc >= 70) return { kanji: "良好", grade: "B", variant: "bg-amber-500/10 border-amber-500 text-amber-600" };
    return { kanji: "がんばろう", grade: "C", variant: "bg-slate-500/10 border-slate-500 text-slate-600" };
  };

  const hanko = getHankoGrade(accuracy);

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in zoom-in-95 duration-300 pb-12">
      {/* Top Victory Card with Hanko Stamp */}
      <div className="p-8 rounded-3xl border border-border bg-card shadow-md washi-texture relative overflow-hidden text-center space-y-4">
        <div className="flex flex-col items-center space-y-2">
          <Badge variant="kintsugi" size="sm" className="font-bold">
            総括 • TỔNG KẾT PHIÊN LUYỆN
          </Badge>
          <h2 className="text-2xl md:text-3xl font-black text-foreground tracking-tight">
            Báo Cáo Phản Xạ Tình Huống Thực Chiến
          </h2>
          <p className="text-xs text-muted-foreground max-w-md">
            Tổng kết mức độ hoàn thành nhiệm vụ, ngữ dụng tiếng Nhật và tốc độ đối thoại của bạn
          </p>
        </div>

        {/* Japanese Hanko Stamp */}
        <div className="py-2 flex justify-center">
          <div
            className={cn(
              "w-28 h-28 rounded-full border-4 flex flex-col items-center justify-center p-2 transform rotate-[-8deg] shadow-lg animate-in zoom-in duration-500 select-none",
              hanko.variant
            )}
          >
            <span className="text-[10px] font-bold tracking-widest uppercase">HANASU</span>
            <span className="text-sm font-black font-jp leading-tight my-0.5">{hanko.kanji}</span>
            <span className="text-xs font-mono font-bold">Grade {hanko.grade}</span>
          </div>
        </div>

        {/* 4 Summary Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2">
          <div className="p-4 rounded-2xl bg-muted/40 border border-border/80 space-y-1">
            <div className="text-xs font-bold text-muted-foreground">Tình huống đã luyện</div>
            <div className="text-2xl font-black font-mono text-foreground">{total}</div>
            <div className="text-[10px] text-muted-foreground">cảnh hoàn thành</div>
          </div>

          <div className="p-4 rounded-2xl bg-muted/40 border border-border/80 space-y-1">
            <div className="text-xs font-bold text-muted-foreground">Độ đạt mục tiêu</div>
            <div className="text-2xl font-black font-mono text-emerald-600 dark:text-emerald-400">{accuracy}%</div>
            <div className="text-[10px] text-muted-foreground">{correct}/{total} tình huống chuẩn</div>
          </div>

          <div className="p-4 rounded-2xl bg-muted/40 border border-border/80 space-y-1">
            <div className="text-xs font-bold text-muted-foreground">Tốc độ trung bình</div>
            <div className="text-2xl font-black font-mono text-sky-600 dark:text-sky-400">{avgLatency}ms</div>
            <div className="text-[10px] text-muted-foreground">phản xạ âm thanh</div>
          </div>

          <div className="p-4 rounded-2xl bg-muted/40 border border-border/80 space-y-1">
            <div className="text-xs font-bold text-muted-foreground">Hoàn hảo (Perfect)</div>
            <div className="text-2xl font-black font-mono text-amber-600 dark:text-amber-400">{perfect}</div>
            <div className="text-[10px] text-muted-foreground">điểm tuyệt đối</div>
          </div>
        </div>
      </div>

      {/* Practiced Situations List */}
      <div className="p-6 rounded-3xl border border-border bg-card shadow-xs washi-texture space-y-4">
        <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
          <Compass className="h-4 w-4 text-primary" />
          <span>Danh sách tình huống đã nhập vai ({total} cảnh)</span>
        </h3>

        <div className="space-y-2 max-h-[320px] overflow-y-auto pr-1">
          {results.map((r, i) => {
            const canonical = (r as any).canonical || r.userTranscript || `Tình huống ${i + 1}`;
            return (
              <div
                key={i}
                className="p-3 rounded-xl border border-border/70 bg-muted/30 flex items-center justify-between gap-3 text-xs"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <span className="font-mono text-xs text-muted-foreground font-bold shrink-0">
                    #{i + 1}
                  </span>
                  <div className="min-w-0">
                    <div className="font-bold font-jp text-foreground truncate">{canonical}</div>
                    <div className="text-[10px] text-muted-foreground">
                      Điểm: {r.score ?? 0} • Phản xạ: {r.reactionLatencyMs ? `${Math.round(r.reactionLatencyMs)}ms` : "—"}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <Badge variant={r.success ? "matcha" : "akane"} size="sm">
                    {r.success ? "Đạt" : "Cần sửa"}
                  </Badge>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      soundFX.playFurin();
                      speakJapaneseText(canonical, { rate: 1.0 });
                    }}
                    className="h-7 w-7 p-0"
                    title="Nghe lại phát âm chuẩn"
                  >
                    <Volume2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
        <Button
          variant="outline"
          size="lg"
          onClick={() => {
            soundFX.playFurin();
            onToLobby();
          }}
          className="font-bold text-xs gap-1.5 rounded-xl"
        >
          <Home className="h-4 w-4" />
          <span>Về sảnh chính</span>
        </Button>

        {correct < total && (
          <Button
            variant="outline"
            size="lg"
            onClick={() => {
              soundFX.playSuikinkutsu();
              onRetryWeak();
            }}
            className="font-bold text-xs gap-1.5 rounded-xl border-amber-500/40 text-amber-700 dark:text-amber-300 hover:bg-amber-500/10"
          >
            <Zap className="h-4 w-4 text-amber-500" />
            <span>Luyện lại {total - correct} tình huống chưa đạt</span>
          </Button>
        )}

        <Button
          variant="akane"
          size="lg"
          onClick={() => {
            soundFX.playKatana();
            onRestart();
          }}
          className="font-bold text-xs gap-1.5 rounded-xl shadow-md"
        >
          <RotateCcw className="h-4 w-4" />
          <span>Luyện tiếp phiên mới</span>
        </Button>
      </div>
    </div>
  );
}
