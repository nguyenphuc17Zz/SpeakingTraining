"use client";

import React, { useMemo, useState } from "react";
import { ScaffoldingHint, ScaffoldingSuggestion, ScaffoldingVocab } from "../types";
import { Sparkles, Volume2, BookOpen, ChevronRight, Check, ArrowRight, Lightbulb } from "lucide-react";
import { speakJapaneseText } from "@/features/speaking/services/web-speech";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

interface LiveTurnScaffoldingProps {
  scaffolding?: ScaffoldingHint | null;
  lastAiText?: string | null;
  personaName?: string;
  onSelectSuggestion?: (text: string) => void;
  disabled?: boolean;
}

/** Client-side fallback scaffolding when backend scaffold is missing */
function buildClientFallback(text: string): ScaffoldingHint {
  const t = text.toLowerCase();

  if (/注文|メニュー|お飲み物|お食事|いかが|召し上がり/.test(t)) {
    return {
      suggestions: [
        { intent: "positive", ja: "おすすめのメニューを教えていただけますか？", vi: "Bạn có thể gợi ý món nổi bật được không?" },
        { intent: "concern",  ja: "もう少し見てから注文してもいいですか？",   vi: "Tôi xem thêm một chút rồi gọi món được không?" },
        { intent: "question", ja: "こちらで一番人気のお料理は何ですか？",      vi: "Món được yêu thích nhất ở đây là gì ạ?" },
      ],
      key_vocab: [
        { ja: "おすすめ",  reading: "おすすめ",    vi: "gợi ý / món đề xuất" },
        { ja: "注文",      reading: "ちゅうもん",  vi: "gọi món / đặt hàng" },
        { ja: "人気",      reading: "にんき",      vi: "được yêu thích" },
      ],
    };
  }
  if (/仕事|会議|資料|プレゼン|上司|部下|打ち合わせ|進捗|報告|締め切り/.test(t)) {
    return {
      suggestions: [
        { intent: "positive", ja: "はい、予定通り順調に進めております。",         vi: "Vâng, tôi đang tiến hành thuận lợi đúng kế hoạch ạ." },
        { intent: "concern",  ja: "実は1点だけ確認したい課題がございまして…",     vi: "Thực ra có một vấn đề tôi xin xác nhận lại..." },
        { intent: "question", ja: "資料についてご意見をいただけますでしょうか？",  vi: "Xin anh/chị có thể cho ý kiến về tài liệu này không?" },
      ],
      key_vocab: [
        { ja: "順調",  reading: "じゅんちょう",  vi: "thuận lợi / suôn sẻ" },
        { ja: "進捗",  reading: "しんちょく",    vi: "tiến độ công việc" },
        { ja: "確認",  reading: "かくにん",      vi: "xác nhận" },
      ],
    };
  }
  if (/休み|週末|旅行|趣味|どこ|天気|好き|どう|楽し/.test(t)) {
    return {
      suggestions: [
        { intent: "positive", ja: "とても楽しかったです！のんびり過ごしました。",   vi: "Rất vui ạ! Tôi đã thư giãn thoải mái." },
        { intent: "concern",  ja: "特に予定はなくて、家でゆっくりしていました。",   vi: "Tôi không có kế hoạch gì đặc biệt, chỉ ở nhà thôi." },
        { intent: "question", ja: "〇〇さんは週末どう過ごされましたか？",           vi: "Còn bạn thì cuối tuần đã làm gì?" },
      ],
      key_vocab: [
        { ja: "のんびり",  reading: "のんびり",    vi: "thong thả / thư giãn" },
        { ja: "過ごす",    reading: "すごす",      vi: "trải qua (thời gian)" },
        { ja: "週末",      reading: "しゅうまつ",  vi: "cuối tuần" },
      ],
    };
  }
  // Generic fallback
  return {
    suggestions: [
      { intent: "positive", ja: "そうですね、私もそう思います！",              vi: "Đúng vậy nhỉ, tôi cũng nghĩ như thế!" },
      { intent: "concern",  ja: "なるほど、少し意外ですね。",                  vi: "Ra là vậy, có chút bất ngờ nhỉ." },
      { intent: "question", ja: "それについてもう少し詳しく教えていただけますか？", vi: "Bạn có thể kể thêm chi tiết về điều đó không?" },
    ],
    key_vocab: [
      { ja: "詳しく",  reading: "くわしく",  vi: "chi tiết / rõ ràng" },
      { ja: "意外",    reading: "いがい",    vi: "bất ngờ / ngoài dự kiến" },
      { ja: "共感",    reading: "きょうかん", vi: "đồng cảm / thấu hiểu" },
    ],
  };
}

export function LiveTurnScaffolding({
  scaffolding,
  lastAiText,
  personaName,
  onSelectSuggestion,
  disabled = false,
}: LiveTurnScaffoldingProps) {
  const [playingItem, setPlayingItem] = useState<string | null>(null);

  // Use backend scaffolding if present, otherwise build from AI text client-side
  const effectiveScaffolding: ScaffoldingHint | null = useMemo(() => {
    if (scaffolding && (scaffolding.suggestions?.length || scaffolding.key_vocab?.length)) {
      return scaffolding;
    }
    if (lastAiText && lastAiText.trim().length > 0) {
      return buildClientFallback(lastAiText);
    }
    return null;
  }, [scaffolding, lastAiText]);

  if (!effectiveScaffolding) return null;

  const handlePlayAudio = (e: React.MouseEvent, text: string) => {
    e.stopPropagation();
    soundFX.playFurin();
    setPlayingItem(text);
    speakJapaneseText(text, { rate: 0.95 });
    setTimeout(() => setPlayingItem(null), 1500);
  };

  const handleSelect = (text: string) => {
    if (disabled) return;
    soundFX.playFurin();
    onSelectSuggestion?.(text);
  };

  const getIntentStyle = (intent?: string) => {
    switch (intent) {
      case "positive":
        return {
          badge: "🟢 Khẳng định / Thuận lợi",
          bg: "bg-emerald-500/10 hover:bg-emerald-500/20 border-emerald-500/30 text-emerald-700 dark:text-emerald-300",
          iconColor: "text-emerald-500",
        };
      case "concern":
        return {
          badge: "🟡 Khó khăn / Khéo léo",
          bg: "bg-amber-500/10 hover:bg-amber-500/20 border-amber-500/30 text-amber-700 dark:text-amber-300",
          iconColor: "text-amber-500",
        };
      case "question":
        return {
          badge: "🔵 Hỏi lại / Mở rộng",
          bg: "bg-indigo-500/10 hover:bg-indigo-500/20 border-indigo-500/30 text-indigo-700 dark:text-indigo-300",
          iconColor: "text-indigo-500",
        };
      default:
        return {
          badge: "✨ Gợi ý phản hồi",
          bg: "bg-primary/10 hover:bg-primary/20 border-primary/30 text-primary",
          iconColor: "text-primary",
        };
    }
  };

  return (
    <div className="w-full p-3.5 rounded-2xl bg-gradient-to-br from-card via-card/90 to-background border border-border/80 shadow-md space-y-3 animate-in fade-in zoom-in-95 duration-200">
      {/* Header */}
      <div className="flex items-center justify-between gap-2 border-b border-border/40 pb-2">
        <div className="flex items-center gap-1.5 text-xs font-black text-foreground">
          <Lightbulb className="h-4 w-4 text-amber-500 animate-pulse" />
          <span>Giàn Đỡ Phản Hồi Cho Lượt Nói Này</span>
          {personaName && (
            <span className="text-[10px] text-muted-foreground font-normal">
              (với {personaName})
            </span>
          )}
        </div>
        <span className="text-[10px] font-bold text-muted-foreground bg-muted/60 px-2 py-0.5 rounded-md">
          Bấm để nghe âm thanh / chèn câu
        </span>
      </div>

      {/* 3 Response Angle Cards */}
      {effectiveScaffolding.suggestions && effectiveScaffolding.suggestions.length > 0 && (
        <div className="space-y-1.5">
          <div className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1">
            <span>🎯 3 Hướng phản hồi tức thì:</span>
          </div>
          <div className="grid grid-cols-1 gap-1.5">
            {effectiveScaffolding.suggestions.map((sug, idx) => {
              const style = getIntentStyle(sug.intent);
              return (
                <div
                  key={idx}
                  onClick={() => handleSelect(sug.ja)}
                  className={cn(
                    "p-2 rounded-xl border text-left flex items-center justify-between gap-2 transition-all cursor-pointer group shadow-2xs",
                    style.bg,
                    disabled && "opacity-50 cursor-not-allowed"
                  )}
                  title="Bấm để chèn câu hoặc nghe phát âm"
                >
                  <div className="space-y-0.5 min-w-0 flex-1">
                    <div className="flex items-center gap-1.5 flex-wrap">
                      <span className="text-[9px] font-black uppercase px-1.5 py-0.2 rounded bg-background/80 border border-border/40">
                        {style.badge}
                      </span>
                    </div>
                    <p className="text-xs font-bold font-jp text-foreground leading-snug group-hover:text-primary transition-colors">
                      {sug.ja}
                    </p>
                    {sug.vi && (
                      <p className="text-[10px] text-muted-foreground line-clamp-1">
                        {sug.vi}
                      </p>
                    )}
                  </div>

                  <div className="flex items-center gap-1 shrink-0">
                    <button
                      type="button"
                      onClick={(e) => handlePlayAudio(e, sug.ja)}
                      className={cn(
                        "p-1.5 rounded-lg bg-background/80 border border-border/60 hover:bg-background transition-colors",
                        playingItem === sug.ja && "text-primary border-primary animate-pulse"
                      )}
                      title="Nghe mẫu phát âm"
                    >
                      <Volume2 className="h-3.5 w-3.5" />
                    </button>
                    <button
                      type="button"
                      onClick={() => handleSelect(sug.ja)}
                      className="p-1.5 rounded-lg bg-primary/10 border border-primary/20 text-primary hover:bg-primary/20 transition-colors"
                      title="Chèn vào câu trả lời"
                    >
                      <ArrowRight className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Strategic Key Vocab & Collocations */}
      {effectiveScaffolding.key_vocab && effectiveScaffolding.key_vocab.length > 0 && (
        <div className="pt-2 border-t border-border/40 space-y-1.5">
          <div className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1">
            <BookOpen className="h-3 w-3 text-indigo-500" />
            <span>Từ vựng & Collocation chiến lược:</span>
          </div>
          <div className="flex items-center gap-1.5 flex-wrap">
            {effectiveScaffolding.key_vocab.map((v, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleSelect(v.ja)}
                className="px-2.5 py-1 rounded-xl bg-background/80 border border-border/60 hover:border-primary/40 hover:bg-muted/40 text-[11px] font-medium flex items-center gap-1.5 transition-all shadow-2xs group"
                title={`Bấm để chèn từ "${v.ja}" (${v.vi})`}
              >
                <span className="font-bold font-jp text-primary group-hover:underline">
                  {v.ja}
                </span>
                {v.reading && v.reading !== v.ja && (
                  <span className="text-[10px] text-muted-foreground font-jp">
                    ({v.reading})
                  </span>
                )}
                <span className="text-[10px] text-muted-foreground font-normal">
                  • {v.vi}
                </span>
                <span
                  onClick={(e) => handlePlayAudio(e, v.ja)}
                  className="p-0.5 rounded text-muted-foreground hover:text-primary transition-colors ml-0.5"
                  title="Nghe phát âm từ này"
                >
                  <Volume2 className="h-3 w-3" />
                </span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
