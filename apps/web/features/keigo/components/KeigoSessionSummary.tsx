"use client";

import React, { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  RotateCcw,
  Sparkles,
  Volume2,
  Crown,
} from "lucide-react";
import type { KeigoResult } from "../services/keigo-api";
import { speakJapaneseText, stopWebSpeech } from "@/features/speaking/services/web-speech";
import { UniversalFurigana } from "@/components/japanese/UniversalFurigana";
import { cn } from "@/lib/utils";

interface Props {
  results: KeigoResult[];
  onRestart?: () => void;
  onToLobby?: () => void;
  onRetryWeak?: (weakResults: KeigoResult[]) => void;
}

export function KeigoSessionSummary({ results, onRestart, onToLobby, onRetryWeak }: Props) {
  const [playingTTSId, setPlayingTTSId] = useState<string | null>(null);

  if (!results.length) return null;

  const total = results.length;
  const correct = results.filter((r) => r.success).length;
  const perfect = results.filter((r) => r.isPerfect).length;
  const acc = total ? Math.round((correct / total) * 100) : 0;
  const latencies = results
    .map((r) => r.reactionLatencyMs)
    .filter((v): v is number => v != null)
    .sort((a, b) => a - b);
  const avg = latencies.length ? Math.round(latencies.reduce((a, b) => a + b, 0) / latencies.length) : null;
  const best = latencies.length ? Math.round(Math.min(...latencies)) : null;
  const incorrectResults = results.filter((r) => !r.success);

  const grade =
    acc >= 90 && (avg == null || avg < 2500)
      ? { text: "S", stamp: "大変よくできました", color: "text-amber-500 border-amber-500 bg-amber-500/10" }
      : acc >= 75
      ? { text: "A", stamp: "合格", color: "text-emerald-600 border-emerald-600 bg-emerald-500/10" }
      : acc >= 50
      ? { text: "B", stamp: "良好", color: "text-sky-600 border-sky-600 bg-sky-500/10" }
      : { text: "C", stamp: "がんばろう", color: "text-rose-600 border-rose-600 bg-rose-500/10" };

  const handlePlayTTS = (text: string, id: string) => {
    if (playingTTSId === id) {
      stopWebSpeech();
      setPlayingTTSId(null);
      return;
    }
    setPlayingTTSId(id);
    speakJapaneseText(text, {
      rate: 0.95,
      onEnd: () => setPlayingTTSId(null),
      onError: () => setPlayingTTSId(null),
    });
  };

  return (
    <div className="p-6 md:p-8 rounded-3xl border border-border bg-card washi-texture shadow-lg space-y-6 animate-in fade-in zoom-in-95 duration-300 max-w-4xl mx-auto">
      {/* Top Banner with Japanese Hanko Stamp */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-border/80">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Badge variant="kintsugi" size="sm">
              <Crown className="h-3 w-3 mr-1" />
              Tổng Kết Phiên Luyện
            </Badge>
          </div>
          <h3 className="text-xl md:text-2xl font-black text-foreground">
            Báo Cáo Phản Xạ Kính Ngữ Công Sở
          </h3>
          <p className="text-xs text-muted-foreground">
            Đã hoàn thành toàn bộ {total} câu luyện tập phản xạ Kính ngữ & Uchi/Soto
          </p>
        </div>

        {/* Hanko Stamp */}
        <div
          className={cn(
            "hanko-badge shrink-0 self-start sm:self-center px-4 py-2 rounded-2xl border-2 rotate-[-4deg] text-center shadow-sm select-none",
            grade.color
          )}
        >
          <div className="text-[10px] font-extrabold tracking-widest uppercase">HANKO STAMP</div>
          <div className="text-sm font-black font-jp">{grade.stamp}</div>
        </div>
      </div>

      {/* 4 Performance Metric Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 text-center">
        <div className="p-4 rounded-2xl bg-card border border-border/80 shadow-xs space-y-1">
          <div className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
            Số câu luyện
          </div>
          <div className="text-2xl md:text-3xl font-black font-mono text-foreground">{total}</div>
          <div className="text-[10px] text-muted-foreground">câu hoàn thành</div>
        </div>

        <div className="p-4 rounded-2xl bg-emerald-500/8 border border-emerald-500/20 shadow-xs space-y-1">
          <div className="text-[10px] font-bold uppercase tracking-wider text-emerald-700 dark:text-emerald-300">
            Độ chính xác
          </div>
          <div className="text-2xl md:text-3xl font-black font-mono text-emerald-600 dark:text-emerald-400">
            {acc}%
          </div>
          <div className="text-[10px] text-muted-foreground">{correct}/{total} câu chuẩn</div>
        </div>

        <div className="p-4 rounded-2xl bg-amber-500/8 border border-amber-500/20 shadow-xs space-y-1">
          <div className="text-[10px] font-bold uppercase tracking-wider text-amber-700 dark:text-amber-300">
            Tốc độ trung bình
          </div>
          <div className="text-2xl md:text-3xl font-black font-mono text-amber-600 dark:text-amber-400">
            {avg ? `${avg}ms` : "—"}
          </div>
          <div className="text-[10px] text-muted-foreground font-mono">
            Nhanh nhất: {best ? `${best}ms` : "—"}
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-fuji-500/8 border border-fuji-500/20 shadow-xs space-y-1">
          <div className="text-[10px] font-bold uppercase tracking-wider text-fuji-600 dark:text-fuji-400">
            Kính ngữ Hoàn hảo
          </div>
          <div className="text-2xl md:text-3xl font-black font-mono text-fuji-600 dark:text-fuji-400">
            {perfect}
          </div>
          <div className="text-[10px] text-muted-foreground">điểm tuyệt đối</div>
        </div>
      </div>

      {/* Review Exercises List */}
      <div className="space-y-3 pt-2">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-bold text-foreground flex items-center gap-1.5">
            <Sparkles className="h-4 w-4 text-primary" />
            <span>Danh sách câu đã luyện trong phiên</span>
          </h4>
          <span className="text-xs text-muted-foreground font-mono">{results.length} câu</span>
        </div>

        <div className="max-h-[320px] overflow-y-auto space-y-2 pr-1">
          {results.map((r, index) => {
            const isCorrectItem = r.success;
            return (
              <div
                key={`${r.exerciseId}-${index}`}
                className={cn(
                  "p-3.5 rounded-2xl border transition-all flex items-start justify-between gap-3 text-xs",
                  isCorrectItem
                    ? "bg-emerald-500/5 border-emerald-500/20"
                    : "bg-rose-500/5 border-rose-500/20"
                )}
              >
                <div className="space-y-1 flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-muted-foreground">#{index + 1}</span>
                    <Badge variant={isCorrectItem ? "matcha" : "sakura"} size="sm">
                      {isCorrectItem ? "Đúng" : "Cần sửa"}
                    </Badge>
                    {r.reactionLatencyMs && (
                      <span className="text-[10px] font-mono text-muted-foreground">
                        {Math.round(r.reactionLatencyMs)}ms
                      </span>
                    )}
                  </div>

                  <div className="font-jp text-sm font-bold text-foreground">
                    Đáp án: <UniversalFurigana text={r.canonicalAnswer || r.transcript || "—"} fontSize="normal" />
                  </div>

                  {r.transcript && r.transcript !== r.canonicalAnswer && (
                    <div className="text-[11px] text-muted-foreground flex items-center gap-1">
                      <span>Bạn đã nói:</span>
                      <UniversalFurigana text={r.transcript} fontSize="sm" />
                    </div>
                  )}
                </div>

                {r.canonicalAnswer && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handlePlayTTS(r.canonicalAnswer!, `${r.exerciseId}-${index}`)}
                    className="h-8 w-8 rounded-full p-0 shrink-0 text-primary"
                    title="Nghe mẫu phát âm"
                  >
                    <Volume2 className={cn("h-4 w-4", playingTTSId === `${r.exerciseId}-${index}` && "animate-bounce")} />
                  </Button>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Bottom Actions */}
      <div className="pt-4 border-t border-border/80 flex flex-wrap items-center gap-3">
        {onRestart && (
          <Button variant="akane" size="lg" onClick={onRestart} className="flex-1 gap-2 font-bold min-w-[160px]">
            <RotateCcw className="h-4 w-4" />
            <span>Luyện tiếp phiên mới</span>
          </Button>
        )}

        {incorrectResults.length > 0 && onRetryWeak && (
          <Button
            variant="outline"
            size="lg"
            onClick={() => onRetryWeak(incorrectResults)}
            className="gap-2 font-bold border-rose-500/30 text-rose-600 hover:bg-rose-500/10"
          >
            <RotateCcw className="h-4 w-4" />
            <span>Luyện lại {incorrectResults.length} câu sai</span>
          </Button>
        )}

        {onToLobby && (
          <Button variant="ghost" size="lg" onClick={onToLobby} className="font-bold">
            Về sảnh chính
          </Button>
        )}
      </div>
    </div>
  );
}
