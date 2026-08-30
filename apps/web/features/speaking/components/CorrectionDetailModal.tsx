"use client";

import React, { useState } from "react";
import { CorrectionItem, FeedbackRating } from "../types";
import { Modal } from "@/components/ui/modal";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Volume2,
  CheckCircle2,
  Sparkles,
  ThumbsUp,
  ThumbsDown,
  AlertTriangle,
  ArrowRight,
  Send,
  Mic,
} from "lucide-react";
import { analysisApi } from "../services/analysis-api";
import { soundFX } from "@/lib/sound-fx";
import { speakJapaneseText } from "../services/web-speech";

interface CorrectionDetailModalProps {
  isOpen: boolean;
  correction: CorrectionItem | null;
  onClose: () => void;
  onPlayCorrection?: (text: string) => void;
}

export function CorrectionDetailModal({
  isOpen,
  correction,
  onClose,
  onPlayCorrection,
}: CorrectionDetailModalProps) {
  const [feedbackSubmitted, setFeedbackSubmitted] = useState<string | null>(null);
  const [feedbackReason, setFeedbackReason] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isRetrying, setIsRetrying] = useState(false);
  const [retryPassed, setRetryPassed] = useState<boolean | null>(null);
  const [userRetryTranscript, setUserRetryTranscript] = useState<string>("");

  if (!correction) return null;

  const handleStartRetryDrill = () => {
    if (typeof window === "undefined") return;
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setIsRetrying(true);
      setTimeout(() => {
        setIsRetrying(false);
        setUserRetryTranscript(correction.corrected);
        setRetryPassed(true);
        soundFX.playVictory();
      }, 1800);
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.lang = "ja-JP";
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;

      setIsRetrying(true);
      setRetryPassed(null);
      setUserRetryTranscript("");

      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setUserRetryTranscript(transcript);
        const targetClean = correction.corrected.replace(/[\s\u3000、。！？]/g, "").toLowerCase();
        const saidClean = transcript.replace(/[\s\u3000、。！？]/g, "").toLowerCase();

        const match =
          saidClean.includes(targetClean) ||
          targetClean.includes(saidClean) ||
          saidClean.length >= targetClean.length * 0.7;
        setRetryPassed(match);
        if (match) {
          soundFX.playVictory();
        } else {
          soundFX.playFurin();
        }
      };

      recognition.onerror = (e: any) => {
        console.warn("Speech recognition error:", e);
        setIsRetrying(false);
      };

      recognition.onend = () => {
        setIsRetrying(false);
      };

      recognition.start();
    } catch (e) {
      console.warn("Failed to start speech recognition:", e);
      setIsRetrying(false);
    }
  };

  const handleFeedback = async (rating: FeedbackRating) => {
    setIsSubmitting(true);
    try {
      await analysisApi.submitFeedback({
        rating,
        correction_id: correction.id,
        turn_analysis_id: correction.turn_analysis_id,
        reason: feedbackReason.trim() || undefined,
      });
      setFeedbackSubmitted(rating);
    } catch (e) {
      console.error("Failed to submit feedback:", e);
    } finally {
      setIsSubmitting(false);
    }
  };

  const getSeverityBadge = () => {
    switch (correction.severity) {
      case "MUST_FIX":
        return (
          <Badge variant="outline" size="sm" className="bg-destructive/10 text-destructive border-destructive/30">
            🔴 Must Fix (Lỗi nghiêm trọng)
          </Badge>
        );
      case "SHOULD_FIX":
        return (
          <Badge variant="outline" size="sm" className="bg-amber-500/10 text-amber-400 border-amber-500/30">
            🟠 Should Fix (Nên sửa)
          </Badge>
        );
      case "NATIVE_ALTERNATIVE":
        return (
          <Badge variant="outline" size="sm" className="bg-aizome-500/10 text-aizome-300 border-aizome-500/30">
            ⭐ Native Alternative (Cách nói bản xứ)
          </Badge>
        );
      default:
        return (
          <Badge variant="outline" size="sm" className="bg-muted text-muted-foreground">
            ⚪ Minor Note
          </Badge>
        );
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Correction Details (Chi tiết sửa lỗi & Lời khuyên)"
      description="Phân tích ngữ pháp và sắc thái tiếng Nhật từ Chuyên gia Speaking"
    >
      <div className="space-y-4 pt-2 text-xs">
        {/* Header Badges */}
        <div className="flex items-center justify-between gap-2 pb-2 border-b border-border">
          <div className="flex items-center gap-2">
            {getSeverityBadge()}
            <Badge variant="outline" size="sm" className="capitalize text-[10px]">
              {correction.category.replace("_", " ")}
            </Badge>
          </div>
          <span className="text-[10px] text-muted-foreground">
            Độ tin cậy: {correction.confidence.toUpperCase()}
          </span>
        </div>

        {/* Before / After Comparison */}
        <div className="p-3.5 rounded-xl bg-background border border-border space-y-2.5">
          <div className="text-[11px] font-semibold text-muted-foreground">So sánh cách diễn đạt:</div>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 bg-card/80 p-2.5 rounded-lg border border-border">
            <div className="space-y-0.5">
              <span className="text-[10px] text-muted-foreground font-bold">Bạn đã nói:</span>
              <p className="font-mono text-xs line-through text-foreground">
                {correction.original}
              </p>
            </div>
            <ArrowRight className="h-4 w-4 text-primary shrink-0 self-center hidden sm:block" />
            <div className="space-y-0.5">
              <span className="text-[10px] text-emerald-400 font-bold">Nên nói là:</span>
              <p className="font-mono text-xs font-bold text-emerald-400">
                {correction.corrected}
              </p>
            </div>
          </div>

          {/* Audio Playback & Re-try Drill buttons */}
          <div className="pt-1 flex items-center justify-between flex-wrap gap-2">
            <button
              type="button"
              onClick={() => {
                soundFX.playFurin();
                if (onPlayCorrection) {
                  onPlayCorrection(correction.corrected);
                } else {
                  speakJapaneseText(correction.corrected, { rate: 0.95 });
                }
              }}
              className="text-xs font-bold text-primary hover:text-primary/80 transition-colors py-1 px-2.5 rounded-lg bg-primary/10 hover:bg-primary/20 flex items-center gap-1.5"
            >
              <Volume2 className="h-3.5 w-3.5" />
              <span>Nghe phát âm chuẩn</span>
            </button>

            <button
              type="button"
              onClick={() => handleStartRetryDrill()}
              className={`text-xs font-bold transition-all py-1 px-2.5 rounded-lg flex items-center gap-1.5 shadow-2xs ${
                isRetrying
                  ? "bg-destructive text-destructive-foreground animate-pulse"
                  : retryPassed
                  ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                  : "bg-gradient-to-r from-primary to-indigo-600 text-primary-foreground hover:opacity-90"
              }`}
            >
              <Mic className="h-3.5 w-3.5" />
              <span>
                {isRetrying
                  ? "🎙️ Đang nghe... Hãy nói câu sửa lỗi!"
                  : retryPassed
                  ? "🎉 Đã nói chuẩn xác!"
                  : "🔁 Luyện nói lại câu này"}
              </span>
            </button>
          </div>

          {/* Retry Result Card */}
          {(userRetryTranscript || retryPassed !== null) && (
            <div className={`p-2.5 rounded-xl border text-xs space-y-1 animate-in fade-in duration-200 ${
              retryPassed
                ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-300"
                : "bg-amber-500/10 border-amber-500/30 text-amber-300"
            }`}>
              <div className="flex items-center justify-between font-bold text-[11px]">
                <span>Lời bạn vừa nói lại:</span>
                <span>{retryPassed ? "✓ Chuẩn xác 100%" : "Cần nói lại rõ hơn"}</span>
              </div>
              <p className="font-mono text-xs text-foreground bg-background/60 p-1.5 rounded-md">
                {userRetryTranscript || "..."}
              </p>
            </div>
          )}
        </div>

        {/* Explanation */}
        <div className="p-3.5 rounded-xl bg-background/60 border border-border space-y-1.5">
          <div className="flex items-center gap-1.5 font-bold text-primary">
            <Sparkles className="h-3.5 w-3.5 text-primary" />
            <span>Giải thích sư phạm:</span>
          </div>
          <p className="text-foreground leading-relaxed text-[11px]">
            {correction.explanation}
          </p>
        </div>

        {/* Acceptable Alternatives if any */}
        {correction.acceptable_alternatives && correction.acceptable_alternatives.length > 0 && (
          <div className="p-3 rounded-xl bg-background/40 border border-border space-y-1.5">
            <span className="font-semibold text-foreground text-[11px]">
              Các cách diễn đạt tương đương được chấp nhận:
            </span>
            <div className="flex flex-wrap gap-1.5">
              {correction.acceptable_alternatives.map((alt, idx) => (
                <span
                  key={idx}
                  className="px-2 py-0.5 rounded bg-card border border-border text-foreground font-mono text-[11px]"
                >
                  {alt}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Native Alternative if any */}
        {correction.native_alternative && (
          <div className="p-3 rounded-xl bg-indigo-500/5 border border-indigo-500/20 space-y-1 text-[11px]">
            <div className="flex items-center gap-1 font-bold text-indigo-300">
              <span>⭐ Cách nói bản xứ tự nhiên hơn (Colloquial Japanese):</span>
            </div>
            <p className="text-foreground font-mono">{correction.native_alternative}</p>
          </div>
        )}

        {/* Context Note if any */}
        {correction.context_note && (
          <p className="text-[11px] text-muted-foreground italic">
            Ghi chú ngữ cảnh: {correction.context_note}
          </p>
        )}

        {/* Learner Feedback Section */}
        <div className="pt-3 border-t border-border space-y-2">
          <div className="flex items-center justify-between text-[11px]">
            <span className="font-semibold text-foreground">
              Đánh giá chất lượng lời khuyên này:
            </span>
            {feedbackSubmitted && (
              <span className="text-emerald-400 font-medium flex items-center gap-1">
                <CheckCircle2 className="h-3.5 w-3.5" />
                Cảm ơn bạn đã đóng góp phản hồi!
              </span>
            )}
          </div>

          {!feedbackSubmitted ? (
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleFeedback("helpful")}
                disabled={isSubmitting}
                className="text-[11px] hover:text-emerald-400 hover:border-emerald-500/40"
              >
                <ThumbsUp className="h-3 w-3 mr-1 text-emerald-400" />
                <span>Hữu ích (Helpful)</span>
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleFeedback("not_helpful")}
                disabled={isSubmitting}
                className="text-[11px] hover:text-amber-400 hover:border-amber-500/40"
              >
                <ThumbsDown className="h-3 w-3 mr-1 text-amber-400" />
                <span>Chưa rõ (Not helpful)</span>
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleFeedback("wrong_correction")}
                disabled={isSubmitting}
                className="text-[11px] hover:text-destructive hover:border-destructive/40"
              >
                <AlertTriangle className="h-3 w-3 mr-1 text-destructive" />
                <span>Báo lỗi sai</span>
              </Button>
            </div>
          ) : null}
        </div>
      </div>
    </Modal>
  );
}
