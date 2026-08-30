"use client";

import React, { useEffect, useRef, useState, useMemo } from "react";
import {
  Search,
  Star,
  Volume2,
  CheckCircle2,
  AlertTriangle,
  Play,
  Filter,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { TranscriptSegment } from "@/types/shadowing";
import { FuriganaRubyText } from "@/components/japanese/FuriganaRubyText";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

export interface TranscriptPanelProps {
  segments: TranscriptSegment[];
  currentPlaybackTime: number;
  selectedSegmentId?: string;
  recommendedSegmentIds?: Set<string>;
  bookmarkedSegmentIds?: Set<string>;
  onToggleBookmark?: (segmentId: string) => void;
  segmentScores?: Record<string, number>;
  onSelectSegment: (segment: TranscriptSegment) => void;
  onSeek: (seconds: number) => void;
}

type FilterTab = "all" | "bookmarked" | "weak";

export function TranscriptPanel({
  segments,
  currentPlaybackTime,
  selectedSegmentId,
  recommendedSegmentIds,
  bookmarkedSegmentIds = new Set(),
  onToggleBookmark,
  segmentScores = {},
  onSelectSegment,
  onSeek,
}: TranscriptPanelProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState<FilterTab>("all");
  const activeItemRef = useRef<HTMLDivElement | null>(null);

  // Filtered segments
  const filteredSegments = useMemo(() => {
    let list = segments;

    if (activeTab === "bookmarked") {
      list = list.filter((s) => bookmarkedSegmentIds.has(s.id));
    } else if (activeTab === "weak") {
      list = list.filter((s) => {
        const score = segmentScores[s.id];
        return score !== undefined && score < 80;
      });
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      list = list.filter(
        (s) =>
          s.text.toLowerCase().includes(q) ||
          (s.vietnamese_translation && s.vietnamese_translation.toLowerCase().includes(q))
      );
    }

    return list;
  }, [segments, activeTab, bookmarkedSegmentIds, segmentScores, searchQuery]);

  const bookmarkedCount = bookmarkedSegmentIds.size;
  const weakCount = useMemo(() => {
    return Object.values(segmentScores).filter((sc) => sc < 80).length;
  }, [segmentScores]);

  return (
    <div className="flex flex-col h-full rounded-2xl bg-card/95 border border-border/90 washi-texture shadow-xs overflow-hidden">
      {/* Header & Tabs */}
      <div className="p-3 border-b border-border/60 space-y-2 bg-muted/20">
        <div className="flex items-center justify-between gap-2">
          <span className="text-xs font-bold text-foreground">
            Danh Sách Lời Thoại ({segments.length} câu)
          </span>

          <div className="flex items-center gap-1 p-0.5 rounded-xl bg-muted border border-border text-[10px] font-bold">
            <button
              type="button"
              onClick={() => {
                soundFX.playFurin();
                setActiveTab("all");
              }}
              className={cn(
                "px-2 py-0.5 rounded-lg transition-all",
                activeTab === "all"
                  ? "bg-card text-foreground border border-border shadow-2xs"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              Tất cả ({segments.length})
            </button>
            <button
              type="button"
              onClick={() => {
                soundFX.playFurin();
                setActiveTab("bookmarked");
              }}
              className={cn(
                "px-2 py-0.5 rounded-lg transition-all flex items-center gap-1",
                activeTab === "bookmarked"
                  ? "bg-card text-amber-500 border border-border shadow-2xs"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              <Star className="h-2.5 w-2.5 fill-current" />
              <span>Đã lưu ({bookmarkedCount})</span>
            </button>
            {weakCount > 0 && (
              <button
                type="button"
                onClick={() => {
                  soundFX.playFurin();
                  setActiveTab("weak");
                }}
                className={cn(
                  "px-2 py-0.5 rounded-lg transition-all flex items-center gap-1",
                  activeTab === "weak"
                    ? "bg-card text-rose-500 border border-border shadow-2xs"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                <AlertTriangle className="h-2.5 w-2.5" />
                <span>Cần sửa ({weakCount})</span>
              </button>
            )}
          </div>
        </div>

        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Tìm theo tiếng Nhật hoặc nghĩa tiếng Việt..."
            className="w-full bg-background border border-border rounded-xl pl-8 pr-3 py-1.5 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary"
          />
        </div>
      </div>

      {/* Playlist Scrollable Items List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1.5 divide-y divide-border/20 max-h-[380px] lg:max-h-[460px]">
        {filteredSegments.length === 0 ? (
          <div className="p-8 text-center text-xs text-muted-foreground space-y-1">
            <p>Không tìm thấy câu thoại nào.</p>
            {activeTab !== "all" && (
              <button
                type="button"
                onClick={() => setActiveTab("all")}
                className="text-primary font-bold hover:underline"
              >
                Xem tất cả câu
              </button>
            )}
          </div>
        ) : (
          filteredSegments.map((segment, idx) => {
            const isSelected = selectedSegmentId === segment.id;
            const isPlayingNow =
              currentPlaybackTime >= segment.start_time &&
              currentPlaybackTime <= segment.end_time;
            const isBookmarked = bookmarkedSegmentIds.has(segment.id);
            const score = segmentScores[segment.id];

            return (
              <div
                key={segment.id}
                ref={isSelected ? activeItemRef : undefined}
                onClick={() => {
                  soundFX.playFurin();
                  onSelectSegment(segment);
                  onSeek(segment.start_time);
                }}
                className={cn(
                  "p-2.5 rounded-xl border transition-all cursor-pointer space-y-1 pt-2",
                  isSelected
                    ? "border-primary bg-primary/10 ring-1 ring-primary/30 shadow-2xs"
                    : isPlayingNow
                    ? "border-emerald-500/40 bg-emerald-500/5"
                    : "border-border/60 bg-card/60 hover:bg-muted/40 hover:border-primary/30"
                )}
              >
                {/* Meta Top line */}
                <div className="flex items-center justify-between gap-1.5 text-[10px] font-bold">
                  <div className="flex items-center gap-1.5">
                    <span className="font-mono text-muted-foreground">
                      {(idx + 1).toString().padStart(2, "0")}.
                    </span>
                    <span className="font-mono text-primary/80">
                      {formatTime(segment.start_time)}
                    </span>
                    {isPlayingNow && (
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-ping" />
                    )}
                  </div>

                  <div className="flex items-center gap-1">
                    {score !== undefined && (
                      <Badge
                        variant={score >= 80 ? "matcha" : "sakura"}
                        size="sm"
                        className="text-[9px] px-1 py-0 font-mono font-bold"
                      >
                        {score}đ
                      </Badge>
                    )}

                    {onToggleBookmark && (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          soundFX.playSuikinkutsu();
                          onToggleBookmark(segment.id);
                        }}
                        className={cn(
                          "p-0.5 rounded hover:bg-muted transition-colors",
                          isBookmarked ? "text-amber-500" : "text-muted-foreground/50 hover:text-foreground"
                        )}
                        title={isBookmarked ? "Bỏ lưu câu" : "Lưu câu yêu thích"}
                      >
                        <Star className={cn("h-3 w-3", isBookmarked && "fill-current")} />
                      </button>
                    )}
                  </div>
                </div>

                {/* Japanese Sentence Text */}
                <div className="text-xs font-bold font-jp text-foreground leading-snug">
                  <FuriganaRubyText
                    text={segment.text}
                    reading={segment.reading}
                    ruby={segment.ruby}
                    vocabulary={segment.vocabulary}
                    displayMode="kanji_reading"
                  />
                </div>

                {/* Translation */}
                {segment.vietnamese_translation && (
                  <div className="text-[10px] text-muted-foreground italic truncate">
                    {segment.vietnamese_translation}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}
