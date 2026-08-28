"use client";

import React, { useEffect, useRef, useState } from "react";
import {
  Search,
  Sparkles,
  Volume2,
  Eye,
  EyeOff,
  BookOpen,
  Clock,
  Tag,
  Play,
  Type,
  Palette,
  Check,
  X,
  Repeat,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { TranscriptSegment } from "@/types/shadowing";
import { FuriganaRubyText } from "@/components/japanese/FuriganaRubyText";
import { useFuriganaSettings, FuriganaColorOption } from "@/hooks/use-furigana-settings";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

interface TranscriptPanelProps {
  segments: TranscriptSegment[];
  currentPlaybackTime: number;
  selectedSegmentId?: string;
  recommendedSegmentIds?: Set<string>;
  isLooping?: boolean;
  loopRange?: { start: number; end: number } | null;
  onSelectSegment: (segment: TranscriptSegment) => void;
  onLoopSegment?: (segment: TranscriptSegment) => void;
  onSeek: (seconds: number) => void;
}

type DisplayMode = "kanji_reading" | "kanji" | "hidden";
type FontSize = "normal" | "large";

export function TranscriptPanel({
  segments,
  currentPlaybackTime,
  selectedSegmentId,
  recommendedSegmentIds,
  isLooping,
  loopRange,
  onSelectSegment,
  onLoopSegment,
  onSeek,
}: TranscriptPanelProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [displayMode, setDisplayMode] = useState<DisplayMode>("kanji_reading");
  const [fontSize, setFontSize] = useState<FontSize>("normal");
  const [autoScroll, setAutoScroll] = useState(true);
  const [showColorPicker, setShowColorPicker] = useState(false);

  const { colorId, changeColor, changeCustomColor, furiganaClass, furiganaStyle, options, activeOption, activeHex } = useFuriganaSettings();

  const activeSegmentRef = useRef<HTMLDivElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const colorPickerRef = useRef<HTMLButtonElement | null>(null);
  const popoverRef = useRef<HTMLDivElement | null>(null);

  // Check if video is multi-speaker or single monologue
  const uniqueSpeakers = React.useMemo(() => {
    return Array.from(new Set(segments.map((s) => s.speaker_id).filter(Boolean)));
  }, [segments]);
  const hasMultipleSpeakers = uniqueSpeakers.length > 1;

  const getSpeakerBadgeStyle = (speakerId: string) => {
    const index = uniqueSpeakers.indexOf(speakerId);
    const colors = [
      "bg-aizome-500/15 text-aizome-300 border-aizome-500/30",
      "bg-primary/15 text-primary border-primary/30",
      "bg-matcha-500/15 text-matcha-300 border-matcha-500/30",
      "bg-kintsugi-500/15 text-kintsugi-300 border-kintsugi-500/30",
    ];
    return colors[index % colors.length] || "bg-muted text-muted-foreground border-border";
  };

  // Close color picker on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      const target = event.target as Node;
      const isClickInsideButton = colorPickerRef.current && colorPickerRef.current.contains(target);
      const isClickInsidePopover = popoverRef.current && popoverRef.current.contains(target);

      if (!isClickInsideButton && !isClickInsidePopover) {
        setShowColorPicker(false);
      }
    }
    if (showColorPicker) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [showColorPicker]);

  // Determine active segment based on current player timestamp
  const activeSegment = segments.find(
    (s) => s.start_time <= currentPlaybackTime && currentPlaybackTime < s.end_time
  );

  // Auto-scroll to active segment within bounded container
  useEffect(() => {
    if (autoScroll && activeSegmentRef.current && containerRef.current) {
      activeSegmentRef.current.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
    }
  }, [activeSegment?.id, autoScroll]);

  const filteredSegments = segments.filter((s) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      s.text.toLowerCase().includes(q) ||
      s.normalized_text.toLowerCase().includes(q) ||
      (s.reading && s.reading.toLowerCase().includes(q))
    );
  });

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs < 10 ? "0" : ""}${secs}`;
  };

  return (
    <div className="flex flex-col h-full max-h-full rounded-2xl bg-card/85 border border-border/80 washi-texture backdrop-blur-xl overflow-hidden shadow-sumi-lg">
      {/* Panel Header */}
      <div className="p-3.5 border-b border-border/80 space-y-2.5 bg-card/50 shrink-0 relative z-30">
        {/* Top Row: Title & Action Tools */}
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <div className="p-1.5 rounded-lg bg-primary/15 text-primary border border-primary/20 shrink-0">
              <BookOpen className="h-4 w-4" />
            </div>
            <div className="truncate">
              <h2 className="text-sm font-bold text-foreground font-sans tracking-wide truncate">
                Transcript Phụ Đề
              </h2>
            </div>
            <span className="text-[11px] px-2 py-0.5 rounded-full bg-muted/80 text-muted-foreground font-mono font-semibold shrink-0">
              {segments.length} câu
            </span>
          </div>

          {/* Quick Tools */}
          <div className="flex items-center gap-1.5 shrink-0">
            {/* Furigana Color Picker Trigger Button */}
            <button
              ref={colorPickerRef}
              onClick={() => {
                soundFX.playFurin();
                setShowColorPicker((prev) => !prev);
              }}
              className={cn(
                "flex items-center gap-1.5 px-2 py-1 rounded-lg border text-xs font-semibold transition-all shadow-xs",
                showColorPicker
                  ? "bg-primary/20 text-primary border-primary/40"
                  : "bg-background/90 text-muted-foreground border-border hover:text-foreground hover:bg-accent/50"
              )}
              title="Tùy chỉnh màu sắc phiên âm Furigana"
            >
              <span
                className="w-3.5 h-3.5 rounded-full border border-black/30 shrink-0 shadow-inner"
                style={{ backgroundColor: activeHex }}
              />
              <span className="text-[11px]">Màu</span>
            </button>

            {/* Font Size Toggle */}
            <button
              onClick={() => {
                soundFX.playFurin();
                setFontSize(fontSize === "normal" ? "large" : "normal");
              }}
              className={cn(
                "flex items-center gap-1 px-2 py-1 rounded-lg border text-xs font-semibold transition-all",
                fontSize === "large"
                  ? "bg-primary/20 text-primary border-primary/40 shadow-sm"
                  : "bg-background/80 text-muted-foreground border-border hover:text-foreground"
              )}
              title="Chuyển kích thước chữ (Chuẩn / To)"
            >
              <Type className="h-3 w-3" />
              <span className="text-[11px]">{fontSize === "large" ? "Chữ to" : "Chữ vừa"}</span>
            </button>
          </div>
        </div>

        {/* Furigana Color Dropdown Popover (Guaranteed to fit 100% inside container) */}
        {showColorPicker && (
          <div
            ref={popoverRef}
            className="absolute left-2 right-2 top-12 p-3 rounded-2xl bg-card border border-border shadow-2xl z-50 space-y-2.5 animate-in fade-in zoom-in-95 backdrop-blur-2xl ring-1 ring-border/50"
          >
            {/* Header */}
            <div className="flex items-center justify-between pb-1.5 border-b border-border/60">
              <div className="flex items-center gap-1.5 min-w-0">
                <Palette className="h-3.5 w-3.5 text-primary shrink-0" />
                <span className="text-xs font-bold text-foreground font-sans truncate">
                  Màu sắc Furigana
                </span>
              </div>
              <button
                onClick={() => setShowColorPicker(false)}
                className="p-1 rounded-md text-muted-foreground hover:text-foreground transition-colors shrink-0"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>

            {/* Free Custom Color Picker (Input Color + Hex) */}
            <div className="p-2 rounded-xl bg-background/90 border border-border space-y-1.5">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-foreground text-[11px]">Chọn màu bất kỳ:</span>
                <span className="font-mono text-[11px] text-primary font-bold uppercase">{activeHex}</span>
              </div>
              <div className="flex items-center gap-2">
                <label className="relative w-7 h-7 rounded-lg border border-border overflow-hidden cursor-pointer shrink-0 shadow-sm block bg-card">
                  <input
                    type="color"
                    value={activeHex}
                    onChange={(e) => changeCustomColor(e.target.value)}
                    className="absolute -top-3 -left-3 w-14 h-14 cursor-pointer border-0 p-0"
                  />
                </label>
                <input
                  type="text"
                  value={activeHex}
                  onChange={(e) => {
                    const val = e.target.value;
                    if (/^#[0-9A-Fa-f]{0,6}$/.test(val)) {
                      changeCustomColor(val);
                    }
                  }}
                  placeholder="#fb7185"
                  maxLength={7}
                  className="flex-1 min-w-0 h-7 px-2 rounded-lg border border-border bg-card text-xs font-mono text-foreground focus:outline-none focus:ring-1 focus:ring-primary/50 uppercase"
                />
              </div>
            </div>

            {/* Preset Quick Swatches */}
            <div className="space-y-1">
              <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider block">
                Bảng màu gợi ý
              </span>
              <div className="grid grid-cols-2 gap-1 max-h-32 overflow-y-auto pr-0.5 scrollbar-thin">
                {options.map((opt) => {
                  const isSelected = colorId === opt.id || (colorId !== "custom" && activeHex.toLowerCase() === opt.hex.toLowerCase());
                  return (
                    <button
                      key={opt.id}
                      onClick={() => {
                        soundFX.playFurin();
                        changeColor(opt.id);
                      }}
                      className={cn(
                        "flex items-center gap-1.5 px-1.5 py-1 rounded-lg text-xs font-medium transition-all text-left border min-w-0",
                        isSelected
                          ? "bg-primary/15 font-bold text-foreground border-primary/40 shadow-xs"
                          : "border-transparent hover:bg-accent/40 text-muted-foreground hover:text-foreground"
                      )}
                    >
                      <span
                        className="w-2.5 h-2.5 rounded-full shrink-0 shadow-xs border border-black/20"
                        style={{ backgroundColor: opt.hex }}
                      />
                      <span className="truncate text-[10.5px]">{opt.name}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Live Preview */}
            <div className="pt-1.5 border-t border-border/60 flex items-center justify-between text-xs">
              <span className="text-[10px] text-muted-foreground font-jp">Xem trước:</span>
              <span className="font-jp font-bold text-xs" style={{ color: activeHex }}>
                日本語 (にほんご)
              </span>
            </div>
          </div>
        )}

        {/* Second Row: Display Modes & Search Bar */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Reading Display Mode Switcher (Compact Segmented Control) */}
          <div className="flex items-center gap-0.5 p-0.5 rounded-xl bg-background/90 border border-border text-[11px]">
            <button
              onClick={() => {
                soundFX.playFurin();
                setDisplayMode("kanji_reading");
              }}
              className={cn(
                "px-2.5 py-1 rounded-lg font-jp text-xs font-semibold transition-all",
                displayMode === "kanji_reading"
                  ? "bg-primary text-primary-foreground shadow-sm font-bold"
                  : "text-muted-foreground hover:text-foreground"
              )}
              title="Hiện chữ Hán kèm Furigana nổi trên đầu"
            >
              漢字+読み
            </button>
            <button
              onClick={() => {
                soundFX.playFurin();
                setDisplayMode("kanji");
              }}
              className={cn(
                "px-2.5 py-1 rounded-lg font-jp text-xs font-semibold transition-all",
                displayMode === "kanji"
                  ? "bg-primary text-primary-foreground shadow-sm font-bold"
                  : "text-muted-foreground hover:text-foreground"
              )}
              title="Chỉ hiện chữ Hán Kanji tự nhiên (Không phiên âm)"
            >
              漢字
            </button>
            <button
              onClick={() => {
                soundFX.playFurin();
                setDisplayMode(displayMode === "hidden" ? "kanji_reading" : "hidden");
              }}
              className={cn(
                "flex items-center gap-1 px-2 py-1 rounded-lg text-xs transition-all",
                displayMode === "hidden"
                  ? "bg-amber-500/20 text-amber-300 font-bold"
                  : "text-muted-foreground hover:text-foreground"
              )}
              title="Immersion Mode (Che chữ để luyện nghe phản xạ)"
            >
              {displayMode === "hidden" ? (
                <>
                  <EyeOff className="h-3.5 w-3.5 text-amber-400" />
                  <span className="text-[11px] font-semibold">Ẩn</span>
                </>
              ) : (
                <>
                  <Eye className="h-3.5 w-3.5" />
                  <span className="text-[11px]">Ẩn</span>
                </>
              )}
            </button>
          </div>

          {/* Search Input */}
          <div className="relative flex-1 min-w-[140px]">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
            <input
              type="text"
              placeholder="Tìm câu thoại..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full h-8 pl-8 pr-7 rounded-xl border border-border bg-background/90 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary/40"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                className="absolute right-2 top-2 text-muted-foreground hover:text-foreground"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Segments List: Fixed constrained scroll container with min-h-0 */}
      <div
        ref={containerRef}
        className="flex-1 min-h-0 overflow-y-auto p-3 space-y-2 scrollbar-thin scrollbar-thumb-border"
      >
        {filteredSegments.length === 0 ? (
          <div className="py-16 text-center text-xs text-muted-foreground">
            Không tìm thấy câu thoại phù hợp với từ khóa tìm kiếm.
          </div>
        ) : (
          filteredSegments.map((segment) => {
            const isActive = activeSegment?.id === segment.id;
            const isSelected = selectedSegmentId === segment.id;
            const isRecommended = recommendedSegmentIds?.has(segment.id) || false;

            return (
              <div
                key={segment.id}
                ref={isActive ? activeSegmentRef : null}
                onClick={() => {
                  soundFX.playFurin();
                  onSelectSegment(segment);
                  onSeek(segment.start_time);
                }}
                className={cn(
                  "group relative p-3 rounded-2xl cursor-pointer transition-all duration-200 border",
                  isActive
                    ? "bg-primary/15 border-primary/50 shadow-md ring-1 ring-primary/30"
                    : isSelected
                    ? "bg-aizome-950/40 border-aizome-500/40 shadow-sm"
                    : "bg-background/40 border-border/60 hover:bg-card hover:border-border hover:shadow-sm"
                )}
              >
                {/* Meta header: Optional Speaker, Timestamp and Optional Top Recommendation Star */}
                <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
                  <div className="flex items-center gap-1.5 min-w-0 whitespace-nowrap">
                    {hasMultipleSpeakers && (
                      <span className={cn("px-1.5 py-0.2 rounded font-mono text-[10px] font-bold border", getSpeakerBadgeStyle(segment.speaker_id))}>
                        {segment.speaker_id || "Speaker"}
                      </span>
                    )}
                    <span className="flex items-center gap-1 font-mono text-[11px] text-muted-foreground font-semibold">
                      <Clock className="h-2.5 w-2.5" />
                      {formatTime(segment.start_time)} - {formatTime(segment.end_time)}
                    </span>
                  </div>

                  <div className="flex items-center gap-1.5 shrink-0">
                    {isRecommended && (
                      <span className="inline-flex items-center gap-1 px-1.5 py-0.2 rounded-md bg-kintsugi-500/15 text-kintsugi-300 border border-kintsugi-500/30 text-[10px] font-bold">
                        <Sparkles className="h-2.5 w-2.5 text-kintsugi-400" />
                        <span>Gợi ý</span>
                      </span>
                    )}

                    {/* 1-Click Sentence Loop Button */}
                    {onLoopSegment && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          soundFX.playTaiko();
                          onLoopSegment(segment);
                          onSeek(segment.start_time);
                        }}
                        className={cn(
                          "h-5 px-1.5 rounded-md flex items-center gap-1 text-[10px] font-semibold transition-all border",
                          isLooping && loopRange && loopRange.start === segment.start_time && loopRange.end === segment.end_time
                            ? "bg-primary text-primary-foreground border-primary shadow-xs ring-1 ring-primary/50 font-bold"
                            : "bg-background/80 hover:bg-primary/15 text-muted-foreground hover:text-primary border-border/80"
                        )}
                        title="Lặp đi lặp lại câu này"
                      >
                        <Repeat className="h-2.5 w-2.5" />
                        <span>Lặp</span>
                      </button>
                    )}

                    <span
                      className={cn(
                        "h-5 w-5 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity",
                        isActive ? "opacity-100 bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
                      )}
                      title="Phát câu này"
                    >
                      <Play className="h-2.5 w-2.5 fill-current ml-0.5" />
                    </span>
                  </div>
                </div>

                {/* Japanese Sentence Text with HTML5 Ruby & Scale */}
                <div className="py-0.5">
                  <FuriganaRubyText
                    text={segment.normalized_text}
                    reading={segment.reading}
                    ruby={segment.ruby}
                    vocabulary={segment.vocabulary}
                    displayMode={displayMode}
                    fontSize={fontSize}
                    furiganaStyle={furiganaStyle}
                    isActive={isActive}
                  />
                </div>

                {/* Linguistic tags (Vocabulary, Grammar badges) */}
                {(segment.vocabulary?.length || segment.grammar?.length || segment.expressions?.length) ? (
                  <div className="flex flex-wrap items-center gap-1 mt-1.5 pt-1 border-t border-border/40">
                    {segment.vocabulary?.slice(0, 2).map((v, i) => (
                      <span
                        key={i}
                        className="text-[11px] px-1.5 py-0.2 rounded-md bg-aizome-500/15 text-aizome-200 border border-aizome-500/25 font-jp font-medium"
                      >
                        {v.word}
                      </span>
                    ))}
                    {segment.grammar?.slice(0, 1).map((g, i) => (
                      <span
                        key={i}
                        className="text-[11px] px-1.5 py-0.2 rounded-md bg-kintsugi-500/15 text-kintsugi-300 border border-kintsugi-500/25 font-jp font-medium"
                      >
                        {g.pattern}
                      </span>
                    ))}
                    {segment.expressions?.slice(0, 1).map((e, i) => (
                      <span
                        key={i}
                        className="text-[11px] px-1.5 py-0.2 rounded-md bg-emerald-500/10 text-emerald-300 border border-emerald-500/25 font-jp font-medium"
                      >
                        {e.expression}
                      </span>
                    ))}
                  </div>
                ) : null}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
