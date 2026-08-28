"use client";

import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { useCoach } from "@/features/analytics/hooks/useCoach";
import { CoachMessage } from "@/features/analytics/components/CoachMessage";
import { CoachQuickCard } from "@/features/analytics/components/CoachQuickCard";
import {
  Sparkles,
  Send,
  ArrowLeft,
  Zap,
  Target,
  AlertTriangle,
  Flame,
  Clock,
  RefreshCw,
} from "lucide-react";

export default function PersonalCoachPage() {
  const { messages, loading, error, quickCards, briefing, askCoach, submitFeedback } = useCoach();
  const [inputQuestion, setInputQuestion] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const suggestedChips = [
    "Dạo này tôi có tiến bộ gì không?",
    "Điểm yếu lớn nhất hiện tại của tôi là gì?",
    "Hôm nay tôi nên luyện bài tập gì?",
    "Tại sao ngữ pháp đúng mà nói vẫn chưa tự nhiên?",
    "Tổng kết tuần qua của tôi như thế nào?",
    "Chuỗi streak của tôi là mấy ngày?",
  ];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = (q?: string) => {
    const text = q || inputQuestion;
    if (!text.trim() || loading) return;
    askCoach(text);
    setInputQuestion("");
  };

  return (
    <div className="flex flex-col min-h-[calc(100vh-120px)] -m-4 md:-m-6 lg:-m-8">
      {/* Top Header — washi */}
      <header className="border-b border-border bg-card/80 backdrop-blur-md sticky top-0 z-20 px-4 md:px-6 py-4">
        <div className="max-w-5xl mx-auto flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Link
              href="/progress"
              className="p-2 rounded-xl bg-muted border border-border text-muted-foreground hover:text-foreground transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h1 className="text-base font-black text-foreground flex items-center gap-2">
                  <span className="h-7 w-7 rounded-lg bg-primary/10 border border-primary/15 flex items-center justify-center text-primary">
                    <Sparkles className="w-4 h-4" />
                  </span>
                  AI Coach <span className="font-jp text-sm font-normal text-muted-foreground">コーチ</span>
                </h1>
                <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-700 border border-emerald-500/20 dark:text-emerald-400">
                  Trực tuyến
                </span>
              </div>
              <p className="text-sm text-muted-foreground hidden sm:block">
                Giải thích tiến độ, chẩn đoán nguyên nhân và gợi ý bài tập kế tiếp.
              </p>
            </div>
          </div>

          <Link href="/progress" className="hidden sm:flex py-2 px-3 rounded-xl bg-muted border border-border hover:bg-muted/80 text-sm font-semibold text-foreground items-center gap-1.5">
            Xem phân tích
          </Link>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-5xl w-full mx-auto p-4 md:p-6 space-y-6">
        {/* Daily Briefing Banner */}
        {briefing && (
          <div className="p-4 md:p-5 rounded-2xl bg-card border border-border shadow-washi washi-texture flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="space-y-1.5">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-primary/10 text-primary border border-primary/15">
                  Hôm nay — {briefing.date}
                </span>
                <span className="text-xs text-amber-600 dark:text-amber-400 font-bold flex items-center gap-1">
                  <Flame className="w-3 h-3" />
                  {briefing.streak_status}
                </span>
              </div>
              <h3 className="text-sm font-bold text-foreground">
                Trọng tâm hôm nay: <span className="text-primary">{briefing.today_focus_title}</span>
              </h3>
              <p className="text-sm text-muted-foreground">{briefing.today_focus_reason}</p>
            </div>

            {briefing.recommendation && (
              <Link href={briefing.recommendation.practice_url || "/speaking"} className="shrink-0">
                <span className="py-2.5 px-4 rounded-xl bg-primary hover:bg-primary/90 text-primary-foreground text-sm font-bold flex items-center gap-1.5 shadow-md">
                  <Zap className="w-4 h-4" />
                  Bắt đầu ngay ({briefing.recommendation.duration_minutes} phút)
                </span>
              </Link>
            )}
          </div>
        )}

        {/* Precomputed Quick Cards */}
        {quickCards.length > 0 && messages.length === 0 && (
          <div className="space-y-3">
            <span className="text-xs font-bold text-muted-foreground uppercase tracking-widest">
              Gợi ý nhanh
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {quickCards.map((card, idx) => (
                <CoachQuickCard
                  key={idx}
                  card={card}
                  onClick={() => handleSend(`Cho tôi biết chi tiết về ${card.title.toLowerCase()}`)}
                />
              ))}
            </div>
          </div>
        )}

        {/* Suggested Question Chips */}
        {messages.length === 0 && (
          <div className="space-y-2 pt-2">
            <span className="text-xs font-bold text-muted-foreground uppercase tracking-widest">
              Câu hỏi gợi ý
            </span>
            <div className="flex flex-wrap gap-2">
              {suggestedChips.map((chip, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSend(chip)}
                  className="px-3.5 py-2 rounded-xl bg-card hover:bg-muted border border-border text-sm text-foreground transition-colors text-left"
                >
                  💬 {chip}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Conversation Thread */}
        <div className="space-y-4 pt-2">
          {messages.map((msg) => (
            <CoachMessage key={msg.id} message={msg} onFeedback={submitFeedback} />
          ))}

          {loading && (
            <div className="flex items-center gap-3">
              <span className="h-8 w-8 rounded-xl bg-primary flex items-center justify-center text-primary-foreground shrink-0 animate-pulse">
                <Sparkles className="w-4 h-4" />
              </span>
              <span className="p-4 rounded-2xl rounded-tl-none bg-card border border-border text-sm text-muted-foreground flex items-center gap-2">
                <RefreshCw className="w-3.5 h-3.5 animate-spin text-primary" />
                Coach đang phân tích và soạn câu trả lời…
              </span>
            </div>
          )}

          {error && (
            <div className="p-3 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-sm">
              {error}
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </main>

      <footer className="border-t border-border bg-card/90 backdrop-blur-md sticky bottom-0 z-20 p-4">
        <div className="max-w-5xl mx-auto flex items-center gap-3">
          <input
            type="text"
            value={inputQuestion}
            onChange={(e) => setInputQuestion(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSend();
            }}
            placeholder="Hỏi Coach về tiến độ, lỗi thường gặp, bài tập hôm nay…"
            disabled={loading}
            className="flex-1 bg-background border border-border focus:border-ring rounded-2xl px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none transition-colors"
          />

          <button
            onClick={() => handleSend()}
            disabled={!inputQuestion.trim() || loading}
            className="p-3 rounded-2xl bg-primary hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed text-primary-foreground shadow-md transition-all shrink-0"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </footer>
    </div>
  );
}
