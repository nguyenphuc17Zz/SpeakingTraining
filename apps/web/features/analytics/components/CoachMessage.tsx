"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ChatMessage } from "../hooks/useCoach";
import { Sparkles, ThumbsUp, ThumbsDown, Zap, Shield, ArrowRight, CheckCircle2 } from "lucide-react";

interface CoachMessageProps {
  message: ChatMessage;
  onFeedback?: (conversationId: string, rating: "helpful" | "not_helpful" | "incorrect") => void;
}

export const CoachMessage: React.FC<CoachMessageProps> = ({ message, onFeedback }) => {
  const [feedbackSent, setFeedbackSent] = useState<string | null>(null);
  const [showEvidence, setShowEvidence] = useState(false);

  const isCoach = message.sender === "coach";
  const dto = message.answerDTO;

  const handleFeedback = (rating: "helpful" | "not_helpful" | "incorrect") => {
    if (dto?.context_hash && onFeedback) {
      onFeedback(message.id, rating);
      setFeedbackSent(rating);
    }
  };

  if (!isCoach) {
    return (
      <div className="flex justify-end">
        <div className="max-w-xl p-4 rounded-2xl rounded-tr-none bg-rose-600 text-white text-xs leading-relaxed shadow-md">
          {message.text}
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start gap-3 max-w-3xl">
      <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-rose-600 flex items-center justify-center text-white shadow-md shrink-0">
        <Sparkles className="w-5 h-5" />
      </div>

      <div className="flex-1 space-y-3">
        {/* Main Response Box */}
        <div className="p-5 rounded-2xl rounded-tl-none bg-card/90 border border-border shadow-xl space-y-4">
          <div className="text-xs text-foreground leading-relaxed whitespace-pre-line">
            {message.text}
          </div>

          {/* Key points tags */}
          {dto?.key_points && dto.key_points.length > 0 && (
            <div className="space-y-1.5 pt-2 border-t border-border/80">
              <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
                Key Takeaways
              </span>
              <div className="flex flex-wrap gap-1.5">
                {dto.key_points.map((pt, idx) => (
                  <span
                    key={idx}
                    className="px-2.5 py-1 rounded-lg bg-muted text-[11px] font-medium text-foreground font-jp"
                  >
                    ✓ {pt}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Actionable Recommendations with "Practice now" */}
          {dto?.recommendations && dto.recommendations.length > 0 && (
            <div className="space-y-2 pt-2 border-t border-border/80">
              <span className="text-[10px] font-bold text-rose-400 uppercase tracking-wider flex items-center gap-1">
                <Zap className="w-3 h-3" />
                <span>Recommended Practice</span>
              </span>
              <div className="space-y-2">
                {dto.recommendations.map((rec, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-background/60 border border-rose-500/20 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                  >
                    <div>
                      <h5 className="text-xs font-bold text-foreground font-jp">{rec.reason}</h5>
                      <p className="text-[10px] text-muted-foreground">
                        {rec.duration_minutes} min • {rec.action_type}
                      </p>
                    </div>
                    <Link href={rec.practice_url || "/speaking"} className="shrink-0">
                      <button className="py-1.5 px-3 rounded-lg bg-rose-500 hover:bg-rose-600 text-white text-xs font-bold flex items-center gap-1 shadow-sm">
                        <span>Practice now</span>
                        <ArrowRight className="w-3 h-3" />
                      </button>
                    </Link>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Evidence transparency & feedback */}
          <div className="pt-2 border-t border-border/80 flex items-center justify-between text-[11px] text-muted-foreground">
            <button
              onClick={() => setShowEvidence(!showEvidence)}
              className="hover:text-foreground flex items-center gap-1 underline underline-offset-2"
            >
              <Shield className="w-3 h-3 text-cyan-400" />
              <span>{showEvidence ? "Hide Evidence" : "Why do you say this? (根拠)"}</span>
            </button>

            {/* Feedback Thumbs */}
            <div className="flex items-center gap-2">
              {feedbackSent ? (
                <span className="text-[10px] text-emerald-400 font-bold">Feedback sent ✓</span>
              ) : (
                <>
                  <button
                    onClick={() => handleFeedback("helpful")}
                    className="p-1 rounded hover:bg-muted hover:text-emerald-400 transition-colors"
                    title="Helpful"
                  >
                    <ThumbsUp className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => handleFeedback("incorrect")}
                    className="p-1 rounded hover:bg-muted hover:text-rose-400 transition-colors"
                    title="Incorrect / Flag"
                  >
                    <ThumbsDown className="w-3.5 h-3.5" />
                  </button>
                </>
              )}
            </div>
          </div>

          {/* Expanded Evidence Details */}
          {showEvidence && dto?.evidence_refs && (
            <div className="p-3 rounded-xl bg-background border border-border text-[10px] space-y-1 font-mono text-foreground animate-in fade-in duration-150">
              <span className="font-bold text-muted-foreground uppercase font-sans">Grounded Evidence Sources:</span>
              <pre className="overflow-x-auto whitespace-pre-wrap">{JSON.stringify(dto.evidence_refs, null, 2)}</pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
