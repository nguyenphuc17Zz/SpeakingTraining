"use client";

import React, { useEffect, useState } from "react";
import { SubmitAttemptResult, RampSampleAnswer } from "@/services/ramp-api";
import {
  CheckCircle,
  AlertTriangle,
  Target,
  RefreshCw,
  ArrowRight,
  Zap,
  Volume2,
  Trophy,
  Sparkles,
  Lightbulb,
  CheckCircle2,
  TrendingUp,
  MessageSquare,
  Copy,
  Check,
} from "lucide-react";
import { soundFX } from "@/lib/sound-fx";
import { speakJapaneseText, stopWebSpeech } from "@/features/speaking/services/web-speech";
import { HankoStamp } from "@/components/ui/hanko-stamp";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { UniversalFurigana } from "@/components/japanese/UniversalFurigana";
import { cn } from "@/lib/utils";
import { toast } from "@/lib/toast";

interface RampFeedbackCardProps {
  result: SubmitAttemptResult;
  onRetry: () => void;
  onNext: () => void;
  onElaborate?: () => void;
  stageChanged?: boolean;
}

const STYLE_META: Record<string, { label: string; bg: string; border: string; text: string; badge: string }> = {
  casual: {
    label: "Thường ngày (Casual)",
    bg: "bg-emerald-500/5 dark:bg-emerald-500/10",
    border: "border-emerald-500/30",
    text: "text-emerald-700 dark:text-emerald-300",
    badge: "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border-emerald-500/30",
  },
  polite: {
    label: "Lịch sự / Công sở (Polite)",
    bg: "bg-sky-500/5 dark:bg-sky-500/10",
    border: "border-sky-500/30",
    text: "text-sky-700 dark:text-sky-300",
    badge: "bg-sky-500/15 text-sky-700 dark:text-sky-300 border-sky-500/30",
  },
  advanced: {
    label: "Mở rộng & Nâng cao (Advanced)",
    bg: "bg-purple-500/5 dark:bg-purple-500/10",
    border: "border-purple-500/30",
    text: "text-purple-700 dark:text-purple-300",
    badge: "bg-purple-500/15 text-purple-700 dark:text-purple-300 border-purple-500/30",
  },
};

export function RampFeedbackCard({
  result,
  onRetry,
  onNext,
  onElaborate,
  stageChanged,
}: RampFeedbackCardProps) {
  const { feedback, score, delta, followup } = result;
  const isSuccess = score.overall >= 60;
  const isHighPass = score.overall >= 80;

  const [activeTab, setActiveTab] = useState<"samples" | "coaching">("samples");
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  // Sound effects on review
  useEffect(() => {
    if (delta.stage_changed && delta.new_stage > (delta.new_stage - 1)) {
      soundFX.playVictory();
    } else if (isHighPass) {
      soundFX.playVictory();
    } else if (isSuccess) {
      soundFX.playFurin();
    } else {
      soundFX.playSuikinkutsu();
    }
  }, [delta.stage_changed, delta.new_stage, isHighPass, isSuccess]);

  const handlePlayAudio = (text: string) => {
    stopWebSpeech();
    soundFX.playFurin();
    speakJapaneseText(text);
  };

  const handleCopyText = (text: string, idx: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(idx);
    toast.success("Đã sao chép câu mẫu vào bộ nhớ tạm!");
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const sampleAnswers = feedback.sample_answers || [];
  const coaching = feedback.coaching_advice;

  return (
    <div
      className={cn(
        "p-5 sm:p-6 rounded-3xl border washi-texture shadow-sm space-y-4 relative overflow-hidden transition-all",
        isSuccess ? "bg-card border-primary/30" : "bg-card border-amber-500/30"
      )}
    >
      {/* Hanko stamp on high performance */}
      {isHighPass && (
        <div className="absolute top-4 right-4 pointer-events-none opacity-85 scale-90 rotate-6">
          <HankoStamp text="素晴らしい" variant="gold" size="md" />
        </div>
      )}

      {/* Stage change banner */}
      {delta.stage_changed && delta.new_stage > (delta.new_stage - 1) && (
        <div className="flex items-center gap-2 p-2.5 rounded-xl bg-primary/10 border border-primary/20 text-primary font-bold text-xs">
          <Zap className="h-4 w-4 animate-bounce" />
          <span>Thăng hạng! Bạn đã tiến lên Stage {delta.new_stage} 🎉</span>
        </div>
      )}

      {/* Milestone banner */}
      {delta.new_milestones?.map((m, i) => (
        <div
          key={i}
          className="flex items-center gap-2 p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/25 text-amber-700 dark:text-amber-300 font-bold text-xs"
        >
          <Trophy className="h-4 w-4 text-amber-500" />
          <span>Mở khóa cột mốc: {m}</span>
        </div>
      ))}

      {/* 1. Score & Overview Deck */}
      <div className="flex items-center gap-4">
        <div
          className={cn(
            "h-16 w-16 rounded-full border-4 flex flex-col items-center justify-center shrink-0",
            isSuccess ? "border-primary text-primary" : "border-amber-500 text-amber-500"
          )}
        >
          <span className="text-xl font-extrabold leading-none">{Math.round(score.overall)}</span>
          <span className="text-[9px] font-bold uppercase tracking-wider text-muted-foreground mt-0.5">Điểm</span>
        </div>

        <div className="flex-1 space-y-1.5 min-w-0">
          <div className="flex flex-wrap gap-1.5">
            {feedback.badges.map((b, i) => (
              <Badge key={i} variant="outline" className="text-xs font-bold py-0.5 px-2 bg-muted/40">
                {b}
              </Badge>
            ))}
          </div>
          <span className="text-xs text-muted-foreground block truncate">
            {isSuccess ? "Phát ngôn tốt, giữ vững nhịp độ tự nhiên!" : "Cố gắng nối dài câu và cấu trúc trọn vẹn hơn ở lượt sau."}
          </span>
        </div>
      </div>

      {/* 2. Mode Selector: Gợi Ý Các Cách Trả Lời vs Tư Vấn AI Coach */}
      <div className="flex items-center justify-between border-b border-border/60 pb-2.5 pt-1">
        <div className="flex items-center gap-1.5 p-1 bg-muted/40 rounded-2xl border border-border/60">
          <button
            type="button"
            onClick={() => {
              soundFX.playSuikinkutsu();
              setActiveTab("samples");
            }}
            className={cn(
              "px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5",
              activeTab === "samples"
                ? "bg-primary text-primary-foreground shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            <Sparkles className="h-3.5 w-3.5" />
            <span>Gợi Ý Cách Trả Lời (3 Kiểu)</span>
          </button>
          <button
            type="button"
            onClick={() => {
              soundFX.playSuikinkutsu();
              setActiveTab("coaching");
            }}
            className={cn(
              "px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5",
              activeTab === "coaching"
                ? "bg-primary text-primary-foreground shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            <Lightbulb className="h-3.5 w-3.5" />
            <span>Tư Vấn Chuyên Sâu Từ AI</span>
          </button>
        </div>

        <span className="text-[11px] text-muted-foreground hidden sm:inline">
          {activeTab === "samples" ? "Bấm vào loa để nghe mẫu phát âm" : "Phân tích điểm sáng & cải thiện"}
        </span>
      </div>

      {/* 3A. TAB CONTENT: Gợi Ý Các Cách Trả Lời (Sample Answers) */}
      {activeTab === "samples" && (
        <div className="space-y-3 animate-in fade-in duration-150">
          {sampleAnswers.length > 0 ? (
            <div className="grid grid-cols-1 gap-2.5">
              {sampleAnswers.map((ans, idx) => {
                const meta = STYLE_META[ans.style] || STYLE_META.casual;
                return (
                  <div
                    key={idx}
                    className={cn(
                      "p-3.5 rounded-2xl border washi-texture space-y-2 transition-all",
                      meta.bg,
                      meta.border
                    )}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className={cn("px-2.5 py-0.5 rounded-lg text-[10px] font-bold border", meta.badge)}>
                        {ans.style_label || meta.label}
                      </span>

                      <div className="flex items-center gap-1">
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => handleCopyText(ans.japanese, idx)}
                          className="h-7 w-7 p-0 rounded-lg text-muted-foreground hover:text-foreground"
                          title="Sao chép câu này"
                        >
                          {copiedIndex === idx ? (
                            <Check className="h-3.5 w-3.5 text-emerald-500" />
                          ) : (
                            <Copy className="h-3.5 w-3.5" />
                          )}
                        </Button>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => handlePlayAudio(ans.japanese)}
                          className={cn("h-7 px-2 rounded-lg text-xs font-bold gap-1", meta.text)}
                          title="Nghe phát âm chuẩn Tokyo"
                        >
                          <Volume2 className="h-3.5 w-3.5" />
                          <span>Nghe phát âm</span>
                        </Button>
                      </div>
                    </div>

                    <div className="text-sm sm:text-base font-bold font-jp text-foreground leading-relaxed">
                      「<UniversalFurigana text={ans.japanese} />」
                    </div>

                    <div className="text-xs text-muted-foreground leading-normal flex items-start gap-1.5">
                      <span className="text-primary font-bold">🇻🇳</span>
                      <span>{ans.vietnamese}</span>
                    </div>

                    {ans.nuance && (
                      <p className="text-[11px] text-muted-foreground/80 italic pl-5">
                        💡 {ans.nuance}
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            /* Fallback single correction */
            feedback.correction && (
              <div className="p-3.5 rounded-2xl bg-muted/40 border border-border flex items-center justify-between gap-3 text-xs">
                <div className="space-y-0.5 min-w-0">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                    Mẫu câu tự nhiên hơn:
                  </span>
                  <div className="font-bold text-foreground font-jp text-sm">
                    「<UniversalFurigana text={feedback.correction} />」
                  </div>
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => handlePlayAudio(feedback.correction!)}
                  className="h-8 w-8 p-0 rounded-lg shrink-0 text-muted-foreground hover:text-primary"
                  title="Nghe phát âm chuẩn"
                >
                  <Volume2 className="h-4 w-4" />
                </Button>
              </div>
            )
          )}
        </div>
      )}

      {/* 3B. TAB CONTENT: Tư Vấn Chuyên Sâu Từ AI Coach */}
      {activeTab === "coaching" && (
        <div className="space-y-3 animate-in fade-in duration-150">
          {coaching ? (
            <div className="p-4 rounded-2xl bg-primary/5 border border-primary/20 space-y-3">
              {/* Overall comment */}
              {coaching.overall_comment && (
                <div className="flex items-start gap-2.5">
                  <span className="h-6 w-6 rounded-lg bg-primary/10 text-primary flex items-center justify-center shrink-0 mt-0.5">
                    <MessageSquare className="h-3.5 w-3.5" />
                  </span>
                  <div className="space-y-0.5">
                    <span className="text-[11px] font-bold text-primary uppercase tracking-wider block">
                      Đánh giá của AI Coach:
                    </span>
                    <p className="text-xs font-semibold text-foreground leading-relaxed">
                      {coaching.overall_comment}
                    </p>
                  </div>
                </div>
              )}

              {/* Strengths */}
              {coaching.strengths?.length > 0 && (
                <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/25 space-y-1.5">
                  <span className="text-[11px] font-bold text-emerald-700 dark:text-emerald-300 flex items-center gap-1.5">
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                    Điểm sáng phát huy:
                  </span>
                  <ul className="space-y-1 text-xs text-foreground pl-4 list-disc">
                    {coaching.strengths.map((str, i) => (
                      <li key={i} className="leading-normal">{str}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Improvements */}
              {coaching.improvements?.length > 0 && (
                <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/25 space-y-1.5">
                  <span className="text-[11px] font-bold text-amber-700 dark:text-amber-300 flex items-center gap-1.5">
                    <TrendingUp className="h-3.5 w-3.5 text-amber-500" />
                    Lời khuyên bứt phá phản xạ:
                  </span>
                  <ul className="space-y-1 text-xs text-foreground pl-4 list-disc">
                    {coaching.improvements.map((imp, i) => (
                      <li key={i} className="leading-normal">{imp}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Grammar notes */}
              {coaching.grammar_notes?.length > 0 && (
                <div className="p-3 rounded-xl bg-sky-500/10 border border-sky-500/25 space-y-1.5">
                  <span className="text-[11px] font-bold text-sky-700 dark:text-sky-300 flex items-center gap-1.5">
                    <Lightbulb className="h-3.5 w-3.5 text-sky-500" />
                    Ghi chú ngữ pháp & ngữ dụng:
                  </span>
                  <ul className="space-y-1 text-xs text-foreground pl-4 list-disc">
                    {coaching.grammar_notes.map((note, i) => (
                      <li key={i} className="leading-normal">{note}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <div className="p-4 rounded-2xl bg-muted/40 border border-border text-center text-xs text-muted-foreground">
              Chưa có dữ liệu tư vấn bổ sung cho câu này.
            </div>
          )}
        </div>
      )}

      {/* 4. Contextual Follow-up with TTS audio */}
      {followup && (
        <div className="p-3.5 rounded-2xl bg-sky-500/10 border border-sky-500/20 space-y-1 text-xs">
          <div className="flex items-center justify-between">
            <span className="font-bold text-sky-700 dark:text-sky-300 flex items-center gap-1.5">
              💬 Thử thách câu hỏi mở rộng tiếp theo:
            </span>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => handlePlayAudio(followup.question_jp)}
              className="h-7 w-7 p-0 rounded-lg text-sky-600 hover:text-sky-700"
              title="Nghe câu hỏi"
            >
              <Volume2 className="h-3.5 w-3.5" />
            </Button>
          </div>
          <div className="font-bold text-foreground font-jp text-sm">
            「<UniversalFurigana text={followup.question_jp} />」
          </div>
          {followup.question_vi && (
            <p className="text-muted-foreground text-[11px]">{followup.question_vi}</p>
          )}
        </div>
      )}

      {/* 5. Sub-dimension score metrics */}
      <div className="grid grid-cols-5 gap-2 pt-1">
        <SubScore label="Độ chính xác" value={score.production_accuracy} />
        <SubScore label="Tự lập" value={score.independence} highlight />
        <SubScore label="Hoàn chỉnh" value={score.completeness} />
        <SubScore label="Trôi chảy" value={score.fluency} />
        <SubScore label="Mở rộng" value={score.elaboration} />
      </div>

      {/* 6. Action buttons */}
      <div className="flex items-center justify-end gap-2 pt-2">
        <Button
          variant="outline"
          size="sm"
          onClick={onRetry}
          className="gap-1.5 rounded-xl text-xs font-bold border-border"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          <span>Làm lại</span>
          <span className="text-[10px] text-muted-foreground hidden sm:inline">(R)</span>
        </Button>

        {feedback.next_action === "elaborate" && onElaborate && (
          <Button
            variant="secondary"
            size="sm"
            onClick={onElaborate}
            className="gap-1.5 rounded-xl text-xs font-bold"
          >
            <Target className="h-3.5 w-3.5 text-amber-500" />
            <span>Mở rộng thêm</span>
          </Button>
        )}

        <Button
          variant={isSuccess ? "primary" : "outline"}
          size="sm"
          onClick={onNext}
          className="gap-1.5 rounded-xl text-xs font-bold"
        >
          <span>Nấc thang tiếp theo</span>
          <span className="text-[10px] opacity-80 hidden sm:inline">(Space/Enter)</span>
          <ArrowRight className="h-3.5 w-3.5" />
        </Button>
      </div>
    </div>
  );
}

function SubScore({ label, value, highlight }: { label: string; value: number; highlight?: boolean }) {
  const pct = Math.round(value);
  const color = pct >= 75 ? "bg-emerald-500" : pct >= 50 ? "bg-amber-500" : "bg-primary/60";
  return (
    <div
      className={cn(
        "p-2 rounded-xl bg-muted/30 border border-border/60 flex flex-col items-center gap-1",
        highlight ? "ring-1 ring-primary/40 bg-primary/5" : ""
      )}
    >
      <span className="text-[10px] font-bold text-muted-foreground text-center truncate w-full">
        {label}
      </span>
      <div className="w-full h-1.5 rounded-full bg-border overflow-hidden">
        <div className={cn("h-full rounded-full", color)} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-[11px] font-extrabold text-foreground">{pct}%</span>
    </div>
  );
}
