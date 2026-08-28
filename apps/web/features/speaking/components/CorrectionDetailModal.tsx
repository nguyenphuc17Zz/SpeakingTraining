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
} from "lucide-react";
import { analysisApi } from "../services/analysis-api";

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

  if (!correction) return null;

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

          {/* Audio Playback button */}
          {onPlayCorrection && (
            <div className="pt-1 flex justify-end">
              <Button
                variant="primary"
                size="sm"
                onClick={() => onPlayCorrection(correction.corrected)}
                className="text-xs"
              >
                <Volume2 className="h-3.5 w-3.5 mr-1" />
                <span>Listen to correction (Nghe phát âm chuẩn)</span>
              </Button>
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
