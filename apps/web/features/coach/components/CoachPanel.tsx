"use client";

import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import {
  Sparkles,
  Send,
  X,
  Zap,
  ArrowRight,
  Volume2,
  RotateCcw,
  BookOpen,
  HelpCircle,
} from "lucide-react";
import { useCoachCore } from "../hooks/useCoachCore";
import { SENSEI_PERSONAS } from "./DailySenseiBriefingCard";
import { speakJapaneseText } from "@/features/speaking/services/web-speech";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

const ROUTE_QUICK_PROMPTS: Record<string, string[]> = {
  "/keigo": [
    "Tại sao dùng おっしゃる thay vì 言う?",
    "Giải thích quy tắc Uchi và Soto trong công sở",
    "Cách từ chối lịch sự với khách hàng",
    "Khi nào bắt buộc dùng Khiêm nhường ngữ Kenjougo?",
  ],
  "/pitch": [
    "Cách nhận biết và hạ giọng từ Atamadaka [1]?",
    "Phân biệt 雨 (mưa) và 飴 (kẹo) chuẩn giọng Tokyo",
    "Làm sao để không bị ngắt quãng trường âm?",
    "Tại sao nguyên âm i/u hay bị vô thanh hóa?",
  ],
  "/situations": [
    "Cách từ chối khéo khi sếp rủ đi nhậu Nomikai?",
    "Nghi thức trao đổi danh thiếp Meishi Koukan chuẩn Nhật",
    "Cách trả giá hoặc hỏi giảm giá trên app Mercari",
    "Hỏi thủ tục đăng ký cư trú tại Shiyakusho",
  ],
  "/learning": [
    "Đánh giá tiến độ lộ trình học hiện tại của tui",
    "Điểm yếu lớn nhất tui cần khắc phục hôm nay là gì?",
    "Tôi nên học chặng nào tiếp theo?",
    "Gợi ý bài luyện 15 phút hôm nay",
  ],
  "/speaking": [
    "Tại sao dạo này tui nói chậm vậy?",
    "Cách triệt tiêu từ đệm ano/etto khi nói",
    "Gợi ý bài luyện phản xạ 5 phút",
    "Làm sao để nói trôi chảy như người bản xứ?",
  ],
};

export function CoachPanel({
  open,
  onClose,
  route = "/dashboard",
  exerciseId,
  sessionId,
}: {
  open: boolean;
  onClose: () => void;
  route?: string;
  exerciseId?: string;
  sessionId?: string;
}) {
  const { messages, loading, error, persona, setPersona, ask, clear } = useCoachCore();
  const [input, setInput] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    if (!open) return;
    const h = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [open, onClose]);

  const handleSend = (q?: string) => {
    const text = q || input;
    if (!text.trim() || loading) return;
    soundFX.playKatana();
    ask(text, { route, exerciseId, sessionId });
    setInput("");
  };

  const handlePlayAudio = (text: string) => {
    soundFX.playFurin();
    speakJapaneseText(text);
  };

  const activePrompts =
    ROUTE_QUICK_PROMPTS[route] ||
    ROUTE_QUICK_PROMPTS["/speaking"] || [
      "Tại sao dạo này tui nói chậm vậy?",
      "Giải thích lỗi kính ngữ gần nhất",
      "Cho tui luyện phản xạ 5 phút",
      "Đánh giá điểm mạnh và điểm yếu",
    ];

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end" role="dialog" aria-modal="true" aria-label="AI Coach Panel">
      <button aria-label="Close Coach Panel" onClick={onClose} className="absolute inset-0 bg-black/40 backdrop-blur-xs" />

      <div className="relative w-full max-w-md bg-card border-l border-border shadow-2xl flex flex-col h-full washi-texture">
        {/* Top Header */}
        <div className="p-4 border-b border-border bg-card/90 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <span className="h-8 w-8 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary shadow-2xs">
                <Sparkles className="h-4 w-4" />
              </span>
              <div>
                <h3 className="text-sm font-bold text-foreground flex items-center gap-1.5">
                  <span>Hanasu AI Sensei 360°</span>
                </h3>
                <p className="text-[10px] text-muted-foreground">Trợ lý Cố Vấn Nói Tiếng Nhật Cá Nhân Hóa</p>
              </div>
            </div>

            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={clear}
                className="text-[11px] font-semibold px-2.5 py-1 rounded-lg bg-muted border border-border/80 hover:bg-muted/80 text-muted-foreground"
              >
                Xóa đoạn chat
              </button>
              <button
                type="button"
                onClick={onClose}
                className="h-8 w-8 rounded-xl bg-muted border border-border flex items-center justify-center text-muted-foreground hover:text-foreground"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Persona Switcher Buttons */}
          <div className="grid grid-cols-3 gap-1.5 bg-muted/40 p-1 rounded-2xl border border-border/80">
            {SENSEI_PERSONAS.map((p) => (
              <button
                key={p.id}
                type="button"
                onClick={() => {
                  soundFX.playFurin();
                  setPersona(p.id);
                }}
                className={cn(
                  "p-1.5 rounded-xl text-left transition-all space-y-0.5",
                  persona === p.id
                    ? "bg-card border border-border/80 shadow-xs ring-1 ring-primary/30"
                    : "hover:bg-muted text-muted-foreground"
                )}
              >
                <div className="flex items-center gap-1">
                  <span className="text-xs">{p.avatar}</span>
                  <span className="text-[11px] font-bold text-foreground truncate">{p.name}</span>
                </div>
                <div className="text-[9px] text-muted-foreground truncate">{p.tag.split("&")[0]}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Dynamic Context-Aware Quick Prompts */}
        {messages.length === 0 && (
          <div className="p-3.5 border-b border-border bg-muted/20 space-y-2">
            <div className="text-[11px] font-bold text-muted-foreground flex items-center gap-1">
              <HelpCircle className="h-3.5 w-3.5 text-primary" />
              <span>Gợi ý câu hỏi nhanh ({route}):</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {activePrompts.map((p, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSend(p)}
                  className="px-3 py-1 rounded-xl bg-card border border-border/80 text-[11px] font-semibold text-muted-foreground hover:text-foreground hover:border-primary/40 text-left transition-all shadow-2xs"
                >
                  💬 {p}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Chat Messages List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((m) => (
            <div key={m.id} className={m.sender === "user" ? "flex justify-end" : "flex gap-2.5"}>
              {m.sender === "coach" && (
                <span className="h-8 w-8 rounded-xl bg-card border border-border flex items-center justify-center text-base shrink-0 shadow-2xs">
                  {SENSEI_PERSONAS.find((p) => p.id === m.persona)?.avatar || "🎓"}
                </span>
              )}

              <div className={cn(
                "space-y-2",
                m.sender === "user" ? "max-w-[85%] p-3.5 rounded-2xl rounded-tr-xs bg-primary text-primary-foreground text-xs shadow-xs" : "flex-1"
              )}>
                {m.sender === "coach" ? (
                  <>
                    <div className="p-3.5 rounded-2xl rounded-tl-xs bg-muted/60 border border-border/80 text-xs whitespace-pre-wrap leading-relaxed space-y-2">
                      <div>{m.text}</div>

                      {/* Text-To-Speech Play Button */}
                      <button
                        type="button"
                        onClick={() => handlePlayAudio(m.text)}
                        className="text-[11px] font-bold text-primary flex items-center gap-1 hover:underline pt-1"
                      >
                        <Volume2 className="h-3.5 w-3.5" />
                        <span>Nghe phát âm Sensei (TTS)</span>
                      </button>
                    </div>

                    {/* Recommendations List */}
                    {m.raw?.recommendations && m.raw.recommendations.length > 0 && (
                      <div className="space-y-1.5 pt-1">
                        {m.raw.recommendations.map((rec: any, idx: number) => (
                          <div key={idx} className="p-2.5 rounded-xl bg-card border border-border/80 flex items-center justify-between gap-2 shadow-2xs">
                            <span className="text-[11px] font-semibold text-foreground">
                              {rec.reason || rec.target} • {rec.duration_minutes || 5} phút
                            </span>
                            <Link
                              href={rec.practice_url || "/speaking"}
                              onClick={onClose}
                              className="px-3 py-1 rounded-lg bg-primary text-primary-foreground text-[11px] font-bold flex items-center gap-1 shadow-xs"
                            >
                              Luyện ngay <ArrowRight className="h-3 w-3" />
                            </Link>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Next Action Trigger */}
                    {m.raw?.next_action && (
                      <Link
                        href={m.raw.next_action.payload?.navigate_to || m.raw.next_action.payload?.exercise_url || "/speaking"}
                        onClick={onClose}
                        className="inline-flex items-center gap-1.5 text-xs font-bold px-4 py-2 rounded-xl bg-primary text-primary-foreground shadow-md"
                      >
                        <Zap className="h-3.5 w-3.5" />
                        <span>{m.raw.next_action.label || "Bắt đầu luyện tập ngay"}</span>
                      </Link>
                    )}
                  </>
                ) : (
                  <span>{m.text}</span>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="text-xs text-muted-foreground flex items-center gap-2 p-2">
              <span className="h-2 w-2 rounded-full bg-primary animate-pulse" />
              <span>Sensei đang phân tích chuyên sâu...</span>
            </div>
          )}

          {error && (
            <div className="text-xs text-destructive bg-destructive/10 border border-destructive/20 p-3 rounded-2xl">
              {error}
            </div>
          )}

          <div ref={endRef} />
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-border bg-card/90">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex items-center gap-2"
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={`Hỏi ${SENSEI_PERSONAS.find((p) => p.id === persona)?.name}... (VD: Giải thích kính ngữ)`}
              className="flex-1 bg-background border border-border rounded-xl px-3.5 py-2.5 text-xs focus:outline-none focus:border-primary shadow-2xs"
            />
            <button
              type="submit"
              disabled={!input.trim() || loading}
              className="h-10 w-10 rounded-xl bg-primary text-primary-foreground flex items-center justify-center disabled:opacity-50 shadow-md shrink-0"
            >
              <Send className="h-4 w-4" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
