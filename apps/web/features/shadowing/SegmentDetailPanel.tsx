"use client";

import React, { useState } from "react";
import {
  Bookmark,
  Languages,
  BookOpen,
  Sparkles,
  Zap,
  PlusCircle,
  CheckCircle2,
  HelpCircle,
  Volume2,
  Layers,
  MessageSquare,
  BookmarkCheck,
  Flame,
  Lightbulb,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { shadowingApi } from "@/services/shadowing-api";
import { TranscriptSegment } from "@/types/shadowing";
import { FuriganaRubyText } from "@/components/japanese/FuriganaRubyText";
import { useFuriganaSettings } from "@/hooks/use-furigana-settings";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

interface SegmentDetailPanelProps {
  segment?: TranscriptSegment | null;
  onBookmark?: (segmentId: string, note?: string) => void;
  onAddToLearning?: (itemKey: string, title: string, itemType: string) => void;
}

export function SegmentDetailPanel({
  segment,
  onBookmark,
  onAddToLearning,
}: SegmentDetailPanelProps) {
  const { furiganaClass, furiganaStyle } = useFuriganaSettings();
  const [translation, setTranslation] = useState<string | null>(null);
  const [nuanceNote, setNuanceNote] = useState<string | null>(null);
  const [isTranslating, setIsTranslating] = useState(false);
  const [bookmarkNote, setBookmarkNote] = useState("");
  const [isBookmarked, setIsBookmarked] = useState(false);
  const [addedItems, setAddedItems] = useState<Record<string, boolean>>({});

  if (!segment) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-center rounded-2xl bg-card/85 border border-border/80 washi-texture text-muted-foreground shadow-sumi-lg">
        <div className="p-4 rounded-2xl bg-aizome-500/15 text-aizome-300 border border-aizome-500/30 mb-4 animate-pulse">
          <BookOpen className="h-8 w-8" />
        </div>
        <p className="text-sm font-bold text-foreground">Chọn câu thoại để phân tích</p>
        <p className="text-xs text-muted-foreground mt-1.5 max-w-xs leading-relaxed">
          Bấm vào bất kỳ dòng nào trong danh sách phụ đề để xem từ vựng, ngữ pháp, dịch nghĩa tiếng Việt và mẹo phát âm chi tiết.
        </p>
      </div>
    );
  }

  const handleTranslate = async (targetLang: string = "vi") => {
    soundFX.playFurin();
    setIsTranslating(true);
    try {
      const res = await shadowingApi.translateSegment(segment.id, targetLang);
      setTranslation(res.translated_text);
      setNuanceNote(res.explanation || null);
    } catch (e) {
      console.error("Translation error:", e);
    } finally {
      setIsTranslating(false);
    }
  };

  const handleBookmarkToggle = async () => {
    soundFX.playFurin();
    if (isBookmarked) {
      await shadowingApi.removeBookmark(segment.id);
      setIsBookmarked(false);
    } else {
      await shadowingApi.bookmarkSegment(segment.id, bookmarkNote || undefined);
      setIsBookmarked(true);
      onBookmark?.(segment.id, bookmarkNote);
    }
  };

  const handleAddLearningItem = (key: string, title: string, type: string) => {
    soundFX.playTaiko();
    setAddedItems((prev) => ({ ...prev, [key]: true }));
    onAddToLearning?.(key, title, type);
  };

  return (
    <div className="flex flex-col h-full max-h-full rounded-2xl bg-card/85 border border-border/80 washi-texture backdrop-blur-xl overflow-hidden shadow-sumi-lg">
      {/* Header */}
      <div className="p-4 border-b border-border/80 flex items-center justify-between gap-2 bg-card/50 shrink-0">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-aizome-500/15 text-aizome-300 border border-aizome-500/30">
            <Layers className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-foreground font-sans tracking-wide">
              Phân Tích Ngôn Ngữ
            </h3>
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          <button
            onClick={handleBookmarkToggle}
            className={cn(
              "p-2 rounded-xl border transition-all flex items-center gap-1 text-xs font-semibold",
              isBookmarked
                ? "bg-amber-500/15 text-amber-300 border-amber-500/30"
                : "bg-background/80 text-muted-foreground border-border hover:text-foreground"
            )}
            title={isBookmarked ? "Đã lưu vào bộ nhớ câu" : "Lưu câu này để ôn tập"}
          >
            <Bookmark className={cn("h-3.5 w-3.5", isBookmarked && "fill-current")} />
            <span className="hidden sm:inline">{isBookmarked ? "Đã lưu" : "Lưu câu"}</span>
          </button>
        </div>
      </div>

      {/* Scrollable Content Body */}
      <div className="flex-1 min-h-0 overflow-y-auto p-4 space-y-4 scrollbar-thin">
        {/* Selected Sentence Card with Furigana (Scaleable & Ruby-supported) */}
        <div className="p-4 rounded-2xl bg-card border border-border/90 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span className="font-mono font-semibold">
              {segment.speaker_id && `${segment.speaker_id} • `}
              {Math.floor(segment.start_time / 60)}:{(segment.start_time % 60).toFixed(1).padStart(4, "0")} - {Math.floor(segment.end_time / 60)}:{(segment.end_time % 60).toFixed(1).padStart(4, "0")}
            </span>
            <span className="font-mono text-muted-foreground">
              {(segment.end_time - segment.start_time).toFixed(1)}s
            </span>
          </div>

          <div className="py-1">
            <FuriganaRubyText
              text={segment.normalized_text}
              reading={segment.reading}
              ruby={segment.ruby}
              vocabulary={segment.vocabulary}
              displayMode="kanji_reading"
              fontSize="normal"
              furiganaStyle={furiganaStyle}
            />
          </div>

          {/* Translation section */}
          {translation ? (
            <div className="pt-3 mt-2 border-t border-border/80 space-y-1.5 animate-in fade-in">
              <div className="flex items-start gap-2 p-3 rounded-xl bg-aizome-950/40 border border-aizome-500/30">
                <Lightbulb className="h-4 w-4 text-aizome-300 shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <p className="text-sm font-semibold text-aizome-200 leading-relaxed font-sans">
                    {translation}
                  </p>
                  {nuanceNote && (
                    <p className="text-xs text-aizome-300/80 italic font-sans">
                      Ngữ khí: {nuanceNote}
                    </p>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="pt-2 mt-1 border-t border-border/60 flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                className="text-xs h-8 px-3 rounded-xl border-border bg-card hover:border-aizome-500/40 text-foreground font-semibold gap-1.5"
                onClick={() => handleTranslate("vi")}
                disabled={isTranslating}
              >
                <Languages className="h-3.5 w-3.5 text-aizome-500" />
                <span>{isTranslating ? "Đang dịch nghĩa..." : "Dịch nghĩa Tiếng Việt"}</span>
              </Button>
            </div>
          )}
        </div>

        {/* Speed & Difficulty Metrics */}
        {segment.difficulty && (
          <div className="p-3.5 rounded-2xl bg-background/60 border border-border/80 space-y-2.5">
            <div className="flex items-center justify-between text-xs sm:text-sm">
              <span className="text-muted-foreground font-medium">Tốc độ phát âm:</span>
              <span className="font-mono text-aizome-300 font-bold">
                {segment.difficulty.speed_mora_per_sec} mora/giây
              </span>
            </div>
            {segment.difficulty.reasons.length > 0 && (
              <div className="pt-2 border-t border-border/60 text-xs text-muted-foreground space-y-1">
                {segment.difficulty.reasons.map((r, i) => (
                  <p key={i} className="flex items-start gap-1.5">
                    <span className="text-aizome-400 font-bold">•</span>
                    <span>{r}</span>
                  </p>
                ))}
              </div>
            )}
          </div>
        )}

        {/* High-Value Spoken Vocabulary */}
        {segment.vocabulary && segment.vocabulary.length > 0 && (
          <div className="space-y-2.5">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold text-foreground uppercase tracking-wider flex items-center gap-1.5">
                <Sparkles className="h-4 w-4 text-aizome-400" />
                <span>Từ vựng trọng tâm ({segment.vocabulary.length})</span>
              </h4>
            </div>

            <div className="space-y-2.5">
              {segment.vocabulary.map((vocab, i) => {
                const key = `vocab:${vocab.word}`;
                const isAdded = addedItems[key];

                return (
                  <div
                    key={i}
                    className="p-3 rounded-2xl bg-background/90 border border-border/80 space-y-1.5 hover:border-aizome-500/40 transition shadow-sm"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <span className="text-sm font-bold text-aizome-300 font-jp mr-2">
                          {vocab.word}
                        </span>
                        {vocab.reading && vocab.reading !== vocab.word && (
                          <span className="text-xs text-muted-foreground font-jp font-light">
                            [{vocab.reading}]
                          </span>
                        )}
                        <span className="text-[11px] ml-2 px-1.5 py-0.5 rounded-md bg-muted text-muted-foreground font-mono font-semibold">
                          {vocab.difficulty || "N3"}
                        </span>
                      </div>

                      <button
                        onClick={() => handleAddLearningItem(key, vocab.word, "vocabulary")}
                        disabled={isAdded}
                        className={cn(
                          "text-xs px-2.5 py-1 rounded-lg flex items-center gap-1 font-semibold transition-all",
                          isAdded
                            ? "bg-matcha-500/20 text-matcha-300 border border-matcha-500/30"
                            : "bg-aizome-500/15 text-aizome-300 border border-aizome-500/30 hover:bg-aizome-500/25"
                        )}
                      >
                        {isAdded ? (
                          <>
                            <CheckCircle2 className="h-3 w-3" />
                            <span>Đã lưu</span>
                          </>
                        ) : (
                          <>
                            <PlusCircle className="h-3 w-3" />
                            <span>Học từ này</span>
                          </>
                        )}
                      </button>
                    </div>

                    <p className="text-xs text-foreground/90 font-medium">
                      {vocab.meaning}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Grammar Patterns */}
        {segment.grammar && segment.grammar.length > 0 && (
          <div className="space-y-2.5">
            <h4 className="text-xs font-bold text-foreground uppercase tracking-wider flex items-center gap-1.5">
              <BookOpen className="h-4 w-4 text-amber-400" />
              <span>Mẫu ngữ pháp ({segment.grammar.length})</span>
            </h4>

            <div className="space-y-2.5">
              {segment.grammar.map((grammar, i) => {
                const key = `grammar:${grammar.pattern}`;
                const isAdded = addedItems[key];

                return (
                  <div
                    key={i}
                    className="p-3 rounded-2xl bg-background/90 border border-border/80 space-y-1.5 hover:border-amber-500/40 transition shadow-sm"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <span className="text-sm font-bold text-amber-300 font-jp mr-2">
                          {grammar.pattern}
                        </span>
                        <span className="text-[11px] px-1.5 py-0.5 rounded-md bg-amber-500/20 text-amber-300 font-mono font-semibold">
                          {grammar.level}
                        </span>
                      </div>

                      <button
                        onClick={() => handleAddLearningItem(key, grammar.pattern, "grammar")}
                        disabled={isAdded}
                        className={cn(
                          "text-xs px-2.5 py-1 rounded-lg flex items-center gap-1 font-semibold transition-all",
                          isAdded
                            ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                            : "bg-amber-500/15 text-amber-300 border border-amber-500/30 hover:bg-amber-500/25"
                        )}
                      >
                        {isAdded ? (
                          <>
                            <CheckCircle2 className="h-3 w-3" />
                            <span>Đã lưu</span>
                          </>
                        ) : (
                          <>
                            <PlusCircle className="h-3 w-3" />
                            <span>Luyện mẫu này</span>
                          </>
                        )}
                      </button>
                    </div>

                    <p className="text-xs sm:text-sm text-foreground font-medium leading-snug">
                      {grammar.meaning}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Spoken Natural Expressions */}
        {segment.expressions && segment.expressions.length > 0 && (
          <div className="space-y-2.5">
            <h4 className="text-xs font-bold text-foreground uppercase tracking-wider flex items-center gap-1.5">
              <MessageSquare className="h-4 w-4 text-emerald-400" />
              <span>Khẩu ngữ & Ngữ điệu tự nhiên</span>
            </h4>

            <div className="space-y-2.5">
              {segment.expressions.map((expr, i) => (
                <div
                  key={i}
                  className="p-3 rounded-2xl bg-background/90 border border-border/80 space-y-1.5 hover:border-emerald-500/40 transition shadow-sm"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-emerald-300 font-jp">
                      {expr.expression}
                    </span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 uppercase font-mono font-semibold">
                      {expr.category}
                    </span>
                  </div>
                  <p className="text-xs sm:text-sm text-foreground font-medium leading-snug">
                    {expr.meaning}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
