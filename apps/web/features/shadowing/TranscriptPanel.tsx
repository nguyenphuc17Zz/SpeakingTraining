"use client";

import React, { useEffect, useRef, useState, useMemo, useCallback } from "react";
import {
  Search,
  Star,
  Volume2,
  CheckCircle2,
  AlertTriangle,
  Play,
  RotateCcw,
  Sparkles,
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
  const [autoScrollEnabled, setAutoScrollEnabled] = useState(true);
  const [isAutoScrollPaused, setIsAutoScrollPaused] = useState(false);

  const containerRef = useRef<HTMLDivElement | null>(null);
  const itemRefs = useRef<Map<string, HTMLDivElement>>(new Map());
  const lastScrolledIdRef = useRef<string | null>(null);

  // Binary search helper for sorted segments
  const playingSegment = useMemo(() => {
    if (!segments || segments.length === 0) return null;
    let low = 0;
    let high = segments.length - 1;

    while (low <= high) {
      const mid = (low + high) >> 1;
      const s = segments[mid];
      if (currentPlaybackTime < s.start_time) {
        high = mid - 1;
      } else if (currentPlaybackTime > s.end_time) {
        low = mid + 1;
      } else {
        return s;
      }
    }
    return null;
  }, [segments, currentPlaybackTime]);

  const playingSegmentId = playingSegment?.id;

  // Target ID to track and scroll to
  const activeTargetId = playingSegmentId || selectedSegmentId;

  // Auto-scroll logic: smoothly center the active sentence in the container
  useEffect(() => {
    if (!autoScrollEnabled || isAutoScrollPaused || !activeTargetId) return;

    if (lastScrolledIdRef.current === activeTargetId) return;

    const container = containerRef.current;
    const targetEl = itemRefs.current.get(activeTargetId);

    if (container && targetEl) {
      lastScrolledIdRef.current = activeTargetId;

      const targetOffsetTop = targetEl.offsetTop;
      const targetHeight = targetEl.offsetHeight;
      const containerHeight = container.clientHeight;
      const scrollToY = targetOffsetTop - containerHeight / 2 + targetHeight / 2;

      container.scrollTo({
        top: Math.max(0, scrollToY),
        behavior: "smooth",
      });
    }
  }, [activeTargetId, autoScrollEnabled, isAutoScrollPaused]);

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

  // User manual scroll detection
  const handleUserScroll = useCallback(() => {
    if (!isAutoScrollPaused && autoScrollEnabled) {
      setIsAutoScrollPaused(true);
    }
  }, [isAutoScrollPaused, autoScrollEnabled]);

  const setItemRef = useCallback((id: string, el: HTMLDivElement | null) => {
    if (el) {
      itemRefs.current.set(id, el);
    } else {
      itemRefs.current.delete(id);
    }
  }, []);

  const handleSegmentClick = useCallback(
    (segment: TranscriptSegment) => {
      soundFX.playFurin();
      setIsAutoScrollPaused(false);
      lastScrolledIdRef.current = null;
      onSelectSegment(segment);
      onSeek(segment.start_time);
    },
    [onSelectSegment, onSeek]
  );

  return (
    <div className="flex flex-col h-full rounded-2xl bg-card/95 border border-border/90 washi-texture shadow-xs overflow-hidden relative">
      {/* Header & Tabs */}
      <div className="p-3 border-b border-border/60 space-y-2 bg-muted/20">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-foreground">
              Lời Thoại ({segments.length})
            </span>

            {/* Auto-scroll Toggle Button */}
            <button
              type="button"
              onClick={() => {
                const next = !autoScrollEnabled;
                setAutoScrollEnabled(next);
                if (next) {
                  setIsAutoScrollPaused(false);
                  lastScrolledIdRef.current = null;
                }
              }}
              className={cn(
                "px-2 py-0.5 rounded-lg text-[10px] font-bold border transition-all flex items-center gap-1 cursor-pointer",
                autoScrollEnabled
                  ? "bg-primary/10 border-primary/30 text-primary shadow-2xs"
                  : "bg-muted border-border text-muted-foreground hover:text-foreground"
              )}
              title={
                autoScrollEnabled
                  ? "Đang bật tự động cuộn (Bấm để tắt)"
                  : "Đang tắt tự động cuộn (Bấm để bật)"
              }
            >
              <span
                className={cn(
                  "h-1.5 w-1.5 rounded-full",
                  autoScrollEnabled ? "bg-primary animate-pulse" : "bg-muted-foreground"
                )}
              />
              <span>Cuộn: {autoScrollEnabled ? "Bật" : "Tắt"}</span>
            </button>
          </div>

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
      <div
        ref={containerRef}
        onWheel={handleUserScroll}
        onTouchMove={handleUserScroll}
        className="flex-1 overflow-y-auto p-2 space-y-1.5 divide-y divide-border/20 max-h-[500px] lg:max-h-[620px] scrollbar-thin relative"
      >
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
            const isPlayingNow = playingSegmentId === segment.id;
            const isBookmarked = bookmarkedSegmentIds.has(segment.id);
            const score = segmentScores[segment.id];

            return (
              <TranscriptSegmentRow
                key={segment.id}
                segment={segment}
                index={idx}
                isSelected={isSelected}
                isPlayingNow={isPlayingNow}
                isBookmarked={isBookmarked}
                score={score}
                setItemRef={setItemRef}
                onClick={handleSegmentClick}
                onToggleBookmark={onToggleBookmark}
              />
            );
          })
        )}
      </div>

      {/* Floating Resume Auto-scroll Button */}
      {autoScrollEnabled && isAutoScrollPaused && playingSegment && (
        <div className="absolute bottom-3 left-1/2 -translate-y-0 -translate-x-1/2 z-20 animate-in fade-in slide-in-from-bottom-2 duration-200 pointer-events-auto">
          <button
            type="button"
            onClick={() => {
              soundFX.playFurin();
              setIsAutoScrollPaused(false);
              lastScrolledIdRef.current = null;
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-primary text-primary-foreground text-xs font-bold shadow-lg hover:bg-primary/90 transition-all cursor-pointer ring-2 ring-primary/30 active:scale-95"
          >
            <Play className="h-3 w-3 fill-current" />
            <span>Tiếp tục cuộn theo video</span>
          </button>
        </div>
      )}
    </div>
  );
}

interface TranscriptSegmentRowProps {
  segment: TranscriptSegment;
  index: number;
  isSelected: boolean;
  isPlayingNow: boolean;
  isBookmarked: boolean;
  score?: number;
  setItemRef: (id: string, el: HTMLDivElement | null) => void;
  onClick: (segment: TranscriptSegment) => void;
  onToggleBookmark?: (segmentId: string) => void;
}

const TranscriptSegmentRow = React.memo(function TranscriptSegmentRow({
  segment,
  index,
  isSelected,
  isPlayingNow,
  isBookmarked,
  score,
  setItemRef,
  onClick,
  onToggleBookmark,
}: TranscriptSegmentRowProps) {
  return (
    <div
      ref={(el) => setItemRef(segment.id, el)}
      onClick={() => onClick(segment)}
      className={cn(
        "p-2.5 rounded-xl border transition-all cursor-pointer space-y-1 pt-2 relative",
        isSelected
          ? "border-primary bg-primary/10 ring-1 ring-primary/30 shadow-2xs"
          : isPlayingNow
          ? "border-emerald-500/50 bg-emerald-500/10 ring-1 ring-emerald-500/30 shadow-2xs"
          : "border-border/60 bg-card/60 hover:bg-muted/40 hover:border-primary/30"
      )}
    >
      {/* Meta Top line */}
      <div className="flex items-center justify-between gap-1.5 text-[10px] font-bold">
        <div className="flex items-center gap-1.5">
          <span className="font-mono text-muted-foreground">
            {(index + 1).toString().padStart(2, "0")}.
          </span>
          <span className="font-mono text-primary/80">
            {formatTime(segment.start_time)}
          </span>
          {isPlayingNow && (
            <span className="flex h-2 w-2 relative" title="Đang phát câu này">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
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
});

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}
