"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Mic, Clock, Award, ArrowRight, History, MessageSquare, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { conversationApi, RecentSessionItem } from "@/services/conversation-api";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

function formatDuration(seconds: number): string {
  if (!seconds || seconds <= 0) return "10s";
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  if (mins === 0) return `${secs}s`;
  return `${mins}m ${secs.toString().padStart(2, "0")}s`;
}

function formatRelativeTime(dateStr: string): string {
  try {
    const d = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - d.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 2) return "Vừa xong";
    if (diffMins < 60) return `${diffMins} phút trước`;
    if (diffHours < 24) {
      const hours = d.getHours().toString().padStart(2, "0");
      const mins = d.getMinutes().toString().padStart(2, "0");
      return `Hôm nay, ${hours}:${mins}`;
    }
    if (diffDays === 1) return "Hôm qua";
    return d.toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit" });
  } catch {
    return dateStr;
  }
}

export function RecentSessions({ className }: { className?: string }) {
  const [sessions, setSessions] = useState<RecentSessionItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    async function loadSessions() {
      try {
        setLoading(true);
        const data = await conversationApi.getRecentSessions(4);
        if (isMounted) {
          setSessions(data || []);
        }
      } catch (err) {
        console.warn("[RecentSessions] Could not fetch recent sessions:", err);
        if (isMounted) setSessions([]);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadSessions();
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div
      className={cn(
        "relative rounded-[22px] border border-border/80 bg-card/95 washi-texture p-5 sm:p-5.5 flex flex-col justify-between transition-all duration-200 hover:border-border hover:shadow-sumi",
        className
      )}
    >
      {/* Top Ambient Highlight */}
      <div className="absolute top-0 left-0 right-0 h-[2.5px] bg-gradient-to-r from-primary/60 via-emerald-500/30 to-transparent opacity-90" />

      {/* Header */}
      <div className="space-y-1 pb-3.5 border-b border-border/60 relative z-10">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="h-7 w-7 rounded-xl bg-primary/15 border border-primary/25 flex items-center justify-center text-primary shadow-sm">
              <History className="h-3.5 w-3.5" />
            </span>
            <div>
              <div className="flex items-center gap-1.5">
                <h3 className="text-sm font-black text-foreground font-sans tracking-tight">
                  Lịch Sử Luyện Nói
                </h3>
                <span className="text-[10px] font-jp font-bold text-primary px-1.5 py-0.2 rounded bg-primary/10 border border-primary/20">
                  学習履歴
                </span>
              </div>
            </div>
          </div>

          <span className="px-2 py-0.5 rounded-full bg-muted border border-border text-[10px] text-muted-foreground font-semibold">
            {sessions.length > 0 ? `${sessions.length} phiên gần nhất` : "Dữ liệu thật"}
          </span>
        </div>

        <p className="text-xs text-muted-foreground pt-0.5">
          Nhật ký các phiên hội thoại, thời lượng nói và kết quả tương tác gần nhất
        </p>
      </div>

      {/* Content */}
      <div className="py-3.5 relative z-10 flex-1 flex flex-col justify-center">
        {loading ? (
          <div className="space-y-2.5 animate-pulse">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-14 bg-muted/60 rounded-xl border border-border/60" />
            ))}
          </div>
        ) : sessions.length === 0 ? (
          /* Clean Japanese Zen Empty State */
          <div className="py-6 px-4 rounded-2xl bg-muted/40 border border-border/70 text-center space-y-3">
            <div className="h-10 w-10 mx-auto rounded-2xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary text-lg">
              🎋
            </div>
            <div className="space-y-1">
              <h4 className="text-xs font-black text-foreground">
                Chưa có buổi luyện nói nào
              </h4>
              <p className="text-[11px] text-muted-foreground max-w-xs mx-auto leading-relaxed">
                Hãy chọn một người bạn hội thoại phía trên để bắt đầu ghi lại lịch sử bài tập của bạn!
              </p>
            </div>
            <Link href="/speaking" className="inline-block pt-1">
              <Button
                variant="primary"
                size="sm"
                onClick={() => soundFX.playTaiko()}
                className="text-xs font-bold gap-1.5 shadow-sm"
              >
                <MessageSquare className="h-3.5 w-3.5" />
                <span>Bắt đầu trò chuyện ngay</span>
              </Button>
            </Link>
          </div>
        ) : (
          /* Real Sessions List */
          <div className="space-y-2.5">
            {sessions.map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between p-3 rounded-xl bg-background/60 border border-border/80 hover:border-primary/40 hover:bg-card transition-all group"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div className="h-9 w-9 rounded-xl bg-primary/10 border border-primary/25 flex items-center justify-center text-primary shrink-0 group-hover:scale-105 transition-transform">
                    <Mic className="h-4 w-4" />
                  </div>

                  <div className="min-w-0">
                    <p className="text-xs font-bold text-foreground truncate group-hover:text-primary transition-colors">
                      {item.persona_name}
                    </p>
                    <div className="flex items-center gap-2 text-[10px] text-muted-foreground mt-0.5 truncate">
                      <span className="truncate max-w-[140px] sm:max-w-[180px]">{item.topic || "Luyện nói tự do"}</span>
                      <span>•</span>
                      <span className="flex items-center gap-0.5 shrink-0">
                        <Clock className="h-2.5 w-2.5" />
                        <span>{formatDuration(item.duration_seconds)}</span>
                      </span>
                      <span>•</span>
                      <span className="shrink-0">{formatRelativeTime(item.started_at)}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0 pl-2">
                  {item.turns_count > 0 && (
                    <span className="text-[10px] font-jp text-muted-foreground px-1.5 py-0.5 rounded bg-muted border border-border hidden sm:inline-block">
                      {item.turns_count} ターン
                    </span>
                  )}
                  {item.score ? (
                    <div className="flex items-center gap-1 text-xs font-bold font-sans text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-lg border border-emerald-500/25">
                      <Award className="h-3 w-3" />
                      <span>{item.score}%</span>
                    </div>
                  ) : (
                    <span className="text-[10px] font-bold text-primary bg-primary/10 px-1.5 py-0.5 rounded border border-primary/20">
                      Đang xử lý
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="pt-2 border-t border-border/60 flex items-center justify-between text-xs relative z-10">
        <span className="text-[11px] text-muted-foreground">
          {sessions.length > 0 ? "Tự động đồng bộ với phiên hội thoại" : "Dữ liệu được lưu trữ an toàn"}
        </span>
        <Link
          href="/progress"
          className="font-bold text-primary hover:text-primary/80 flex items-center gap-1 transition-colors"
        >
          Toàn bộ lịch sử <ArrowRight className="h-3 w-3" />
        </Link>
      </div>
    </div>
  );
}
