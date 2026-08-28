"use client";

import React, { useState, useRef } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Trophy,
  Zap,
  CheckCircle2,
  Clock,
  RotateCcw,
  Sparkles,
  ArrowRight,
  TrendingUp,
  Award,
  Volume2,
  Mic,
} from "lucide-react";
import type { ReflexResult } from "../services/reflex-api";
import { speakJapaneseText, stopWebSpeech } from "@/features/speaking/services/web-speech";
import { cn } from "@/lib/utils";

interface Props {
  results: ReflexResult[];
  onRestart?: () => void;
  onToPlan?: () => void;
}

export function ReflexSessionSummary({ results, onRestart, onToPlan }: Props) {
  if (!results.length) return null;

  const total = results.length;
  const correct = results.filter((r) => r.success).length;
  const acc = total ? Math.round((correct / total) * 100) : 0;
  const latencies = results
    .map((r) => r.reactionLatencyMs)
    .filter((v): v is number => v != null)
    .sort((a, b) => a - b);
  const avg = latencies.length
    ? Math.round(latencies.reduce((a, b) => a + b, 0) / latencies.length)
    : null;
  const best = latencies.length ? Math.round(Math.min(...latencies)) : null;
  const timeouts = results.filter((r) => r.timedOut).length;

  // Grade & Hanko Stamp
  const grade =
    acc >= 90 && (avg == null || avg < 1800)
      ? { text: "S", label: "Xuất sắc", stamp: "大変よくできました", color: "text-amber-500 border-amber-500 bg-amber-500/10" }
      : acc >= 75
      ? { text: "A", label: "Rất tốt", stamp: "合格", color: "text-emerald-600 border-emerald-600 bg-emerald-500/10" }
      : acc >= 50
      ? { text: "B", label: "Đạt yêu cầu", stamp: "良好", color: "text-sky-600 border-sky-600 bg-sky-500/10" }
      : { text: "C", label: "Cần rèn thêm", stamp: "がんばろう", color: "text-rose-600 border-rose-600 bg-rose-500/10" };

  return (
    <div className="p-6 md:p-8 rounded-3xl border border-border bg-card washi-texture shadow-lg space-y-6 animate-in fade-in zoom-in-95 duration-300">
      {/* Top Banner with Japanese Hanko Stamp */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-border/80">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Badge variant="kintsugi" size="sm">
              <Trophy className="h-3 w-3 mr-1" />
              Tổng Kết Phiên Luyện Phản Xạ
            </Badge>
          </div>
          <h3 className="text-xl md:text-2xl font-black text-foreground">
            Báo cáo hiệu suất phản xạ tức thì
          </h3>
          <p className="text-xs text-muted-foreground">
            Hoàn thành {total} câu thử thách phản xạ dưới áp lực thời gian
          </p>
        </div>

        {/* Hanko Stamp */}
        <div
          className={cn(
            "hanko-badge shrink-0 self-start sm:self-center px-4 py-2 rounded-2xl border-2 rotate-[-4deg] text-center shadow-sm",
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
          <div className="text-2xl md:text-3xl font-black font-mono text-foreground">
            {total}
          </div>
          <div className="text-[10px] text-muted-foreground">Câu hoàn thành</div>
        </div>

        <div className="p-4 rounded-2xl bg-emerald-500/8 border border-emerald-500/20 shadow-xs space-y-1">
          <div className="text-[10px] font-bold uppercase tracking-wider text-emerald-700 dark:text-emerald-300">
            Độ chính xác
          </div>
          <div className="text-2xl md:text-3xl font-black font-mono text-emerald-600 dark:text-emerald-400">
            {acc}%
          </div>
          <div className="text-[10px] text-muted-foreground">{correct}/{total} câu đúng</div>
        </div>

        <div className="p-4 rounded-2xl bg-primary/8 border border-primary/20 shadow-xs space-y-1">
          <div className="text-[10px] font-bold uppercase tracking-wider text-primary">
            Tốc độ trung bình
          </div>
          <div className="text-2xl md:text-3xl font-black font-mono text-primary">
            {avg != null ? `${avg}ms` : "—"}
          </div>
          <div className="text-[10px] text-muted-foreground">Thời gian phản xạ TB</div>
        </div>

        <div className="p-4 rounded-2xl bg-amber-500/8 border border-amber-500/20 shadow-xs space-y-1">
          <div className="text-[10px] font-bold uppercase tracking-wider text-amber-700 dark:text-amber-300">
            Tốc độ nhanh nhất
          </div>
          <div className="text-2xl md:text-3xl font-black font-mono text-amber-600 dark:text-amber-400">
            {best != null ? `${best}ms` : "—"}
          </div>
          <div className="text-[10px] text-muted-foreground flex items-center justify-center gap-1">
            <Zap className="h-3 w-3 text-amber-500" /> Kỷ lục phiên
          </div>
        </div>
      </div>

      {/* Adaptive Insights & Analysis Note */}
      <div className="p-4 rounded-2xl bg-muted/40 border border-border/80 space-y-2">
        <div className="flex items-center gap-2 text-xs font-bold text-foreground">
          <Sparkles className="h-4 w-4 text-primary" />
          <span>Ghi nhận từ AI Coach & Learning Engine</span>
        </div>
        <p className="text-xs text-muted-foreground leading-relaxed">
          {acc >= 80 && avg != null && avg < 2000
            ? "Tốc độ phản xạ của bạn rất nhạy bén và ổn định. Hệ thống đề xuất tăng áp lực lên cấp Fast hoặc Reflex ở phiên tới."
            : acc < 60
            ? "Bạn đang phản xạ hơi vội dẫn đến một số lỗi chia thể. Hãy thử chuyển sang Relaxed Mode (6s) để tập trung độ chuẩn xác trước."
            : "Độ chính xác tốt! Hãy tiếp tục duy trì nhịp độ phản xạ dưới 2.5s để biến từ vựng và ngữ pháp thành phản xạ tự nhiên."}
        </p>
      </div>

      {/* Question-by-Question Review List with User Audio & Model Answer */}
      <div className="space-y-3 pt-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-wider text-foreground">
            Chi tiết các câu đã luyện ({results.length})
          </span>
          <span className="text-[11px] text-muted-foreground">Bấm để nghe lại giọng bạn & đáp án mẫu</span>
        </div>

        <div className="space-y-2.5 max-h-[280px] overflow-y-auto pr-1">
          {results.map((r, idx) => (
            <SummaryItemRow key={idx} result={r} index={idx + 1} />
          ))}
        </div>
      </div>

      {/* Action CTA Buttons */}
      <div className="flex flex-col sm:flex-row gap-3 pt-2">
        <Button
          size="lg"
          variant="akane"
          className="flex-1 font-bold rounded-2xl shadow-md gap-2"
          onClick={onRestart}
        >
          <RotateCcw className="h-4 w-4" />
          <span>Luyện Thêm Phiên Khác</span>
        </Button>

        <Button
          size="lg"
          variant="outline"
          className="flex-1 font-bold rounded-2xl border-border gap-2"
          onClick={onToPlan}
        >
          <span>Về Lộ Trình Hôm Nay</span>
          <ArrowRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

function SummaryItemRow({ result, index }: { result: ReflexResult; index: number }) {
  const [isPlayingUser, setIsPlayingUser] = useState(false);
  const [isPlayingTTS, setIsPlayingTTS] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const isSuccess = result.success;
  const isTimeout = result.timedOut;

  const toggleUserAudio = () => {
    if (!audioRef.current || !result.userAudioUrl) return;
    if (isPlayingUser) {
      audioRef.current.pause();
      setIsPlayingUser(false);
    } else {
      stopWebSpeech();
      setIsPlayingTTS(false);
      audioRef.current.play().then(() => setIsPlayingUser(true)).catch(() => {});
    }
  };

  const playTTS = () => {
    if (!result.canonicalAnswer) return;
    if (isPlayingUser && audioRef.current) {
      audioRef.current.pause();
      setIsPlayingUser(false);
    }
    if (isPlayingTTS) {
      stopWebSpeech();
      setIsPlayingTTS(false);
      return;
    }
    setIsPlayingTTS(true);
    speakJapaneseText(result.canonicalAnswer, {
      rate: 0.95,
      onEnd: () => setIsPlayingTTS(false),
      onError: () => setIsPlayingTTS(false),
    });
  };

  return (
    <div className="p-3.5 rounded-2xl bg-card border border-border/80 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
      {result.userAudioUrl && (
        <audio
          ref={audioRef}
          src={result.userAudioUrl}
          onEnded={() => setIsPlayingUser(false)}
          onError={() => setIsPlayingUser(false)}
        />
      )}

      <div className="flex items-start gap-3 min-w-0 flex-1">
        <span
          className={cn(
            "h-6 w-6 rounded-full flex items-center justify-center shrink-0 font-mono text-[11px] font-black",
            isSuccess
              ? "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30"
              : isTimeout
              ? "bg-muted text-muted-foreground border border-border"
              : "bg-rose-500/15 text-rose-600 dark:text-rose-400 border border-rose-500/30"
          )}
        >
          {index}
        </span>

        <div className="space-y-1 min-w-0 flex-1">
          {result.promptText && (
            <div className="font-bold font-jp text-foreground truncate">
              Đề: {result.promptText}
            </div>
          )}

          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px]">
            <span className="text-muted-foreground">
              Bạn nói: <span className="font-semibold text-foreground font-jp">{result.transcript || "(Trống / Hết giờ)"}</span>
            </span>

            {result.canonicalAnswer && (
              <span className="text-primary font-bold">
                Đáp án: <span className="font-jp">{result.canonicalAnswer}</span>
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
        {result.reactionLatencyMs != null && (
          <span className="text-[10px] font-mono text-muted-foreground mr-1">
            {Math.round(result.reactionLatencyMs)}ms
          </span>
        )}

        {/* Play User Audio */}
        {result.userAudioUrl && (
          <button
            type="button"
            onClick={toggleUserAudio}
            className={cn(
              "px-2.5 py-1 rounded-xl border text-[11px] font-bold flex items-center gap-1 transition-all",
              isPlayingUser
                ? "bg-primary text-primary-foreground border-primary animate-pulse"
                : "bg-muted/70 text-foreground border-border hover:bg-muted"
            )}
            title="Nghe lại giọng bạn"
          >
            <Mic className="h-3 w-3 text-primary" />
            <span>{isPlayingUser ? "Dừng" : "Giọng bạn"}</span>
          </button>
        )}

        {/* Play Model Answer TTS */}
        {result.canonicalAnswer && (
          <button
            type="button"
            onClick={playTTS}
            className={cn(
              "px-2.5 py-1 rounded-xl border text-[11px] font-bold flex items-center gap-1 transition-all",
              isPlayingTTS
                ? "bg-primary text-primary-foreground border-primary animate-pulse"
                : "bg-primary/10 text-primary border-primary/20 hover:bg-primary/20"
            )}
            title="Nghe đáp án mẫu"
          >
            <Volume2 className="h-3 w-3" />
            <span>{isPlayingTTS ? "Dừng" : "Mẫu"}</span>
          </button>
        )}
      </div>
    </div>
  );
}

