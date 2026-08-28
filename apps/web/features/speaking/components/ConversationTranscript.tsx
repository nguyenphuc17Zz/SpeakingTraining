"use client";

import React, { useEffect, useRef } from "react";
import { ConversationTurn, CorrectionItem, RecordingState, TurnAnalysis } from "../types";
import { Volume2, Sparkles, Clock, CheckCircle2, ChevronRight, Mic, Zap } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface ConversationTranscriptProps {
  turns: ConversationTurn[];
  personaName: string;
  analysesMap?: Record<string, TurnAnalysis>;
  state?: RecordingState;
  isUserSpeaking?: boolean;
  interimTranscript?: string;
  sttModel?: string;
  onSelectCorrection?: (correction: CorrectionItem) => void;
  onReplayVoice?: (text: string) => void;
}

export function ConversationTranscript({
  turns,
  personaName,
  analysesMap = {},
  state = "idle",
  isUserSpeaking = false,
  interimTranscript = "",
  sttModel = "base",
  onSelectCorrection,
  onReplayVoice,
}: ConversationTranscriptProps) {
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns, state, isUserSpeaking, interimTranscript]);

  return (
    <div className="space-y-4 p-4 overflow-y-auto max-h-[380px] scrollbar-thin">
      {turns.length === 0 && !isUserSpeaking && state === "listening" && (
        <div className="flex flex-col items-center justify-center p-8 text-center text-muted-foreground space-y-2">
          <div className="h-10 w-10 rounded-full bg-card border border-border flex items-center justify-center text-muted-foreground">
            🎙️
          </div>
          <p className="text-xs font-medium text-muted-foreground">
            Start speaking in Japanese or type a message below.
          </p>
          <p className="text-[11px] text-slate-600">
            音声で話しかけると、AIが自然な日本語で返答します。
          </p>
        </div>
      )}

      {turns.map((turn) => {
        const isUser = turn.speaker === "user";
        const analysis = analysesMap[turn.id];
        const corrections = analysis?.corrections || [];

        return (
          <div
            key={turn.id}
            className={`flex flex-col ${isUser ? "items-end" : "items-start"} space-y-1.5 animate-in fade-in duration-200`}
          >
            {/* Header info */}
            <div className="flex items-center gap-2 text-[10px] text-muted-foreground px-1">
              <span className="font-semibold text-foreground">
                {isUser ? "You (あなた)" : personaName}
              </span>
              {isUser && (
                <span className="px-1.5 py-0.2 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono text-[9px]">
                  Faster-Whisper ({turn.stt_model || sttModel}) ✓
                </span>
              )}
              {turn.processing_time_ms && (
                <span className="flex items-center gap-1 font-mono text-[10px] text-muted-foreground">
                  <Clock className="h-2.5 w-2.5" />
                  {turn.processing_time_ms}ms
                </span>
              )}
              {isUser && analysis && (
                <span className="text-[9px] px-1.5 py-0.2 rounded bg-muted text-rose-300 font-mono">
                  Score: {analysis.overall_quality_score}/100
                </span>
              )}
            </div>

            {/* Turn Bubble */}
            <div
              className={`relative max-w-[85%] sm:max-w-[75%] p-3.5 rounded-2xl text-xs leading-relaxed ${
                isUser
                  ? "bg-muted/90 text-foreground border border-border/80 rounded-tr-none shadow-md shadow-slate-900/30"
                  : "bg-gradient-to-br from-slate-900/95 to-slate-950/95 text-foreground border border-primary/20 rounded-tl-none shadow-lg shadow-primary/5"
              }`}
            >
              <p className="whitespace-pre-wrap font-jp">{turn.transcript}</p>

              {/* User Turn Intelligence Corrections Pill List */}
              {isUser && corrections.length > 0 && onSelectCorrection && (
                <div className="mt-2.5 pt-2 border-t border-border/80 space-y-1.5">
                  <span className="text-[10px] font-bold text-primary flex items-center gap-1">
                    <Sparkles className="h-3 w-3" />
                    <span>Lưu ý chỉnh sửa (Click to view):</span>
                  </span>
                  <div className="flex flex-col gap-1">
                    {corrections.map((c) => (
                      <button
                        key={c.id}
                        onClick={() => onSelectCorrection(c)}
                        className={`text-left p-1.5 rounded-lg text-[11px] font-mono flex items-center justify-between border transition-all ${
                          c.severity === "MUST_FIX"
                            ? "bg-destructive/10 border-destructive/30 hover:bg-destructive/20 text-destructive"
                            : c.severity === "SHOULD_FIX"
                            ? "bg-amber-500/10 border-amber-500/30 hover:bg-amber-500/20 text-amber-400"
                            : "bg-aizome-500/10 border-aizome-500/30 hover:bg-aizome-500/20 text-aizome-300"
                        }`}
                      >
                        <span className="truncate max-w-[220px]">
                          {c.severity === "MUST_FIX" ? "🔴 " : c.severity === "SHOULD_FIX" ? "🟠 " : "⭐ "}
                          <span className="line-through opacity-80">{c.original}</span> ➔ {c.corrected}
                        </span>
                        <ChevronRight className="h-3 w-3 shrink-0 opacity-70" />
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Coaching Feedback Hint if present in assistant turn */}
              {!isUser && turn.feedback_hint && (
                <div className="mt-2.5 pt-2 border-t border-primary/20 text-[11px] bg-primary/5 p-2 rounded-lg text-primary space-y-1">
                  <div className="flex items-center gap-1.5 font-bold text-primary">
                    <Sparkles className="h-3 w-3" />
                    <span>Coaching Tip (アドバイス)</span>
                  </div>
                  <p className="text-foreground leading-snug">{turn.feedback_hint}</p>
                </div>
              )}

              {/* Action Bar for Assistant Turns */}
              {!isUser && onReplayVoice && (
                <div className="mt-2 pt-1.5 flex items-center justify-between border-t border-border/60 text-[10px] text-muted-foreground">
                  <div className="flex items-center gap-1.5 font-mono">
                    <Badge variant="outline" size="sm" className="text-[9px] py-0 px-1.5">
                      {turn.ai_model || "gemini"}
                    </Badge>
                  </div>
                  <button
                    onClick={() => onReplayVoice(turn.transcript)}
                    className="flex items-center gap-1 text-primary hover:text-primary/80 transition-colors py-0.5 px-1.5 rounded hover:bg-primary/10"
                    title="Replay Voice"
                  >
                    <Volume2 className="h-3 w-3" />
                    <span>Listen again</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        );
      })}

      {/* Live Interim State Bubbles */}
      {isUserSpeaking && (
        <div className="flex flex-col items-end space-y-1.5 animate-in fade-in duration-150">
          <div className="flex items-center gap-1.5 text-[10px] text-emerald-400 font-bold px-1">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-ping" />
            <span>You (Đang nói...)</span>
          </div>
          <div className="p-3.5 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-xs text-foreground rounded-tr-none flex flex-col gap-1.5 shadow-sm max-w-[85%]">
            <div className="flex items-center justify-between gap-2">
              <span className="text-emerald-400 font-medium flex items-center gap-1.5 text-[11px]">
                <Mic className="h-3 w-3 animate-pulse" />
                <span>Đang nghe giọng bạn nói tiếng Nhật...</span>
              </span>
              <span className="flex gap-0.5 items-center">
                <span className="h-1.5 w-1 bg-emerald-400 rounded animate-bounce" />
                <span className="h-2.5 w-1 bg-emerald-400 rounded animate-bounce delay-100" />
                <span className="h-1.5 w-1 bg-emerald-400 rounded animate-bounce delay-200" />
              </span>
            </div>
            {interimTranscript && (
              <p className="font-jp text-foreground bg-emerald-500/15 border border-emerald-500/25 p-2 rounded-xl text-xs font-semibold leading-relaxed">
                {interimTranscript}
              </p>
            )}
          </div>
        </div>
      )}

      {state === "processing_stt" && (
        <div className="flex flex-col items-end space-y-1.5 animate-in fade-in duration-150">
          <div className="flex items-center gap-1.5 text-[10px] text-amber-400 font-bold px-1">
            <span className="h-2 w-2 rounded-full bg-amber-400 animate-ping" />
            <span>Faster-Whisper ({sttModel})</span>
          </div>
          <div className="p-3 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-xs text-foreground rounded-tr-none flex items-center gap-2 shadow-sm">
            <Zap className="h-3.5 w-3.5 text-amber-400 animate-pulse" />
            <span className="text-amber-400 font-medium">⚡ Đang chuyển giọng nói thành văn bản tiếng Nhật...</span>
          </div>
        </div>
      )}

      {state === "ai_thinking" && (
        <div className="flex flex-col items-start space-y-1.5 animate-in fade-in duration-150">
          <div className="flex items-center gap-1.5 text-[10px] text-primary font-bold px-1">
            <span className="h-2 w-2 rounded-full bg-primary animate-ping" />
            <span>{personaName}</span>
          </div>
          <div className="p-3 rounded-2xl bg-card border border-primary/25 text-xs text-muted-foreground rounded-tl-none flex items-center gap-2 shadow-sm">
            <Sparkles className="h-3.5 w-3.5 text-primary animate-spin" />
            <span>Đang suy nghĩ câu phản hồi tiếng Nhật...</span>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
