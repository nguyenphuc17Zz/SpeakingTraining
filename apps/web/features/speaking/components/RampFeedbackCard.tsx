"use client";

import React, { useEffect } from "react";
import { SubmitAttemptResult } from "@/services/ramp-api";
import {
  CheckCircle,
  AlertTriangle,
  Target,
  RefreshCw,
  ArrowRight,
  Zap,
  Volume2,
  Trophy,
} from "lucide-react";
import { soundFX } from "@/lib/sound-fx";
import { speakJapaneseText, stopWebSpeech } from "@/features/speaking/services/web-speech";
import { HankoStamp } from "@/components/ui/hanko-stamp";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { UniversalFurigana } from "@/components/japanese/UniversalFurigana";

interface RampFeedbackCardProps {
  result: SubmitAttemptResult;
  onRetry: () => void;
  onNext: () => void;
  onElaborate?: () => void;
  stageChanged?: boolean;
}

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
    speakJapaneseText(text);
  };

  return (
    <div className={`p-5 rounded-3xl border washi-texture shadow-sm space-y-4 relative overflow-hidden transition-all ${
      isSuccess
        ? "bg-card border-primary/30"
        : "bg-card border-amber-500/30"
    }`}>
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
        <div key={i} className="flex items-center gap-2 p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/25 text-amber-700 dark:text-amber-300 font-bold text-xs">
          <Trophy className="h-4 w-4 text-amber-500" />
          <span>Mở khóa cột mốc: {m}</span>
        </div>
      ))}

      {/* Score and badges */}
      <div className="flex items-center gap-4">
        <div className={`h-16 w-16 rounded-full border-4 flex flex-col items-center justify-center shrink-0 ${
          isSuccess ? "border-primary text-primary" : "border-amber-500 text-amber-500"
        }`}>
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
            {isSuccess ? "Phát ngôn tốt, giữ vững nhịp độ!" : "Cố gắng nối dài câu hơn ở lượt sau."}
          </span>
        </div>
      </div>

      {/* Elaboration cue */}
      {feedback.elaboration_prompt && (
        <div className="p-3.5 rounded-2xl bg-amber-500/10 border border-amber-500/25 flex items-start gap-2.5 text-xs">
          <Target className="h-4 w-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            <span className="font-bold text-foreground font-jp block">
              <UniversalFurigana text={feedback.elaboration_prompt.cue_jp} />
            </span>
            {feedback.elaboration_prompt.cue_vi && (
              <span className="text-muted-foreground text-[11px] block">
                ({feedback.elaboration_prompt.cue_vi})
              </span>
            )}
          </div>
        </div>
      )}

      {/* Correction with TTS audio */}
      {feedback.correction && (
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
      )}

      {/* Contextual Follow-up with TTS audio */}
      {followup && (
        <div className="p-3.5 rounded-2xl bg-sky-500/10 border border-sky-500/20 space-y-1 text-xs">
          <div className="flex items-center justify-between">
            <span className="font-bold text-sky-700 dark:text-sky-300 flex items-center gap-1.5">
              💬 Câu hỏi mở rộng tiếp theo:
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

      {/* Sub-dimension score metrics */}
      <div className="grid grid-cols-5 gap-2 pt-1">
        <SubScore label="Độ chính xác" value={score.production_accuracy} />
        <SubScore label="Tự lập" value={score.independence} highlight />
        <SubScore label="Hoàn chỉnh" value={score.completeness} />
        <SubScore label="Trôi chảy" value={score.fluency} />
        <SubScore label="Mở rộng" value={score.elaboration} />
      </div>

      {/* Action buttons */}
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
          <span>Tiếp theo</span>
          <span className="text-[10px] opacity-80 hidden sm:inline">(N)</span>
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
    <div className={`p-2 rounded-xl bg-muted/30 border border-border/60 flex flex-col items-center gap-1 ${
      highlight ? "ring-1 ring-primary/40 bg-primary/5" : ""
    }`}>
      <span className="text-[10px] font-bold text-muted-foreground text-center truncate w-full">
        {label}
      </span>
      <div className="w-full h-1.5 rounded-full bg-border overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-[11px] font-extrabold text-foreground">{pct}%</span>
    </div>
  );
}
