"use client";

import React, { useMemo } from "react";
import { Sparkles, Star, Volume2, Eye, EyeOff, Languages } from "lucide-react";
import { TranscriptSegment } from "@/types/shadowing";
import { FuriganaRubyText } from "@/components/japanese/FuriganaRubyText";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

export interface KaraokeSubtitleBarProps {
  segment: TranscriptSegment | null;
  currentPlaybackTime: number;
  displayMode?: "bilingual" | "japanese" | "japanese_reading" | "hidden";
  onToggleDisplayMode?: () => void;
  isBookmarked?: boolean;
  onToggleBookmark?: () => void;
  onPlaySegment?: () => void;
  highestScore?: number | null;
}

export function KaraokeSubtitleBar({
  segment,
  currentPlaybackTime,
  displayMode = "bilingual",
  onToggleDisplayMode,
  isBookmarked = false,
  onToggleBookmark,
  onPlaySegment,
  highestScore,
}: KaraokeSubtitleBarProps) {
  if (!segment) {
    return (
      <div className="p-4 rounded-2xl border border-dashed border-border/80 bg-card/60 washi-texture flex items-center justify-center text-xs text-muted-foreground">
        <span>Chọn một câu trong danh sách hoặc bấm phát video để bắt đầu</span>
      </div>
    );
  }

  // Calculate segment progress
  const duration = Math.max(0.1, segment.end_time - segment.start_time);
  const elapsed = Math.max(0, Math.min(duration, currentPlaybackTime - segment.start_time));
  const progressPercent = Math.round((elapsed / duration) * 100);

  const isHidden = displayMode === "hidden";
  const isJapaneseOnly = displayMode === "japanese" || displayMode === "japanese_reading";

  return (
    <div className="p-3.5 sm:p-4 rounded-2xl border border-border/90 bg-card/95 washi-texture shadow-xs space-y-2 relative overflow-hidden transition-all">
      {/* Top micro toolbar */}
      <div className="flex items-center justify-between gap-2 text-[11px] font-bold text-muted-foreground border-b border-border/50 pb-1.5">
        <div className="flex items-center gap-2">
          <span className="font-mono text-primary bg-primary/10 px-1.5 py-0.5 rounded text-[10px]">
            {formatTime(segment.start_time)} - {formatTime(segment.end_time)}
          </span>
          {segment.speaker_id && (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-muted border border-border font-medium">
              {segment.speaker_id}
            </span>
          )}
          {highestScore !== undefined && highestScore !== null && (
            <span className={cn(
              "text-[10px] font-mono font-black px-1.5 py-0.5 rounded border",
              highestScore >= 80 ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-600 dark:text-emerald-400" : "bg-amber-500/10 border-amber-500/30 text-amber-600 dark:text-amber-400"
            )}>
              ⭐ {highestScore}đ
            </span>
          )}
        </div>

        <div className="flex items-center gap-1.5">
          {/* Quick audio play button */}
          {onPlaySegment && (
            <button
              type="button"
              onClick={() => {
                soundFX.playFurin();
                onPlaySegment();
              }}
              className="p-1 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
              title="Phát lại câu này (C)"
            >
              <Volume2 className="h-3.5 w-3.5" />
            </button>
          )}

          {/* Bookmark Button */}
          {onToggleBookmark && (
            <button
              type="button"
              onClick={() => {
                soundFX.playSuikinkutsu();
                onToggleBookmark();
              }}
              className={cn(
                "p-1 rounded-lg transition-colors",
                isBookmarked
                  ? "text-amber-500 hover:bg-amber-500/10"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted"
              )}
              title={isBookmarked ? "Bỏ lưu câu" : "Lưu câu yêu thích"}
            >
              <Star className={cn("h-3.5 w-3.5", isBookmarked && "fill-current")} />
            </button>
          )}

          {/* Display Mode Toggle */}
          {onToggleDisplayMode && (
            <button
              type="button"
              onClick={() => {
                soundFX.playFurin();
                onToggleDisplayMode();
              }}
              className="px-2 py-0.5 rounded-lg border border-border bg-background hover:bg-muted text-[10px] font-bold text-foreground transition-colors flex items-center gap-1"
              title="Đổi chế độ phụ đề"
            >
              {isHidden ? (
                <>
                  <EyeOff className="h-3 w-3 text-rose-500" />
                  <span>Ẩn Sub</span>
                </>
              ) : isJapaneseOnly ? (
                <>
                  <Eye className="h-3 w-3 text-sky-500" />
                  <span>Chỉ tiếng Nhật</span>
                </>
              ) : (
                <>
                  <Languages className="h-3 w-3 text-emerald-500" />
                  <span>Song ngữ</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Main Subtitle Display */}
      {isHidden ? (
        <div className="py-3 text-center space-y-1">
          <div className="text-xs font-bold text-muted-foreground flex items-center justify-center gap-1.5">
            <EyeOff className="h-3.5 w-3.5 text-amber-500" />
            <span>Chế độ Blind Shadowing (Audio-Only) — Hãy lắng nghe và lặp lại theo tai!</span>
          </div>
          <p className="text-[10px] text-muted-foreground">Bấm nút mắt ở trên nếu muốn xem lại chữ</p>
        </div>
      ) : (
        <div className="space-y-1.5 py-0.5">
          {/* Japanese Text with Furigana */}
          <div className="text-base sm:text-lg md:text-xl font-bold font-jp text-foreground leading-relaxed">
            <FuriganaRubyText
              text={segment.text}
              reading={segment.reading}
              ruby={segment.ruby}
              vocabulary={segment.vocabulary}
              displayMode={displayMode === "japanese" ? "kanji" : "kanji_reading"}
            />
          </div>

          {/* Translation */}
          {!isJapaneseOnly && segment.vietnamese_translation && (
            <div className="text-xs sm:text-sm text-muted-foreground font-medium italic">
              {segment.vietnamese_translation}
            </div>
          )}
        </div>
      )}

      {/* Real-time segment progress bar */}
      <div className="w-full h-1 rounded-full bg-muted/60 overflow-hidden">
        <div
          className="h-full bg-primary rounded-full transition-all duration-100"
          style={{ width: `${progressPercent}%` }}
        />
      </div>
    </div>
  );
}

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}
