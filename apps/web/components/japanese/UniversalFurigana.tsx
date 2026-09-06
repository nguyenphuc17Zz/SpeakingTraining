"use client";

import React, { useState, useEffect } from "react";
import { Volume2 } from "lucide-react";
import { useFuriganaSettings } from "@/hooks/use-furigana-settings";
import { speakJapaneseText, stopWebSpeech } from "@/features/speaking/services/web-speech";
import { cn } from "@/lib/utils";

interface RubyChunk {
  text: string;
  reading?: string | null;
}

export interface UniversalFuriganaProps {
  text: string;
  ruby?: RubyChunk[] | null;
  className?: string;
  furiganaClassName?: string;
  fontSize?: "sm" | "normal" | "lg" | "xl";
  forceDisplayMode?: "kanji_reading" | "kanji" | "hidden";
  showAudioButton?: boolean;
  enableClickToSpeak?: boolean;
}

const KANJI_REGEX = /[\u4E00-\u9FAF\u3400-\u4DBF]/;
const clientRubyCache = new Map<string, RubyChunk[]>();

export function UniversalFurigana({
  text,
  ruby: propRuby,
  className,
  furiganaClassName,
  fontSize = "normal",
  forceDisplayMode,
  showAudioButton = false,
  enableClickToSpeak = false,
}: UniversalFuriganaProps) {
  const { displayMode: globalDisplayMode, furiganaStyle, furiganaClass } = useFuriganaSettings();
  const displayMode = forceDisplayMode || globalDisplayMode || "kanji_reading";
  const [isPlaying, setIsPlaying] = useState(false);

  const [chunks, setChunks] = useState<RubyChunk[]>(() => {
    if (propRuby && propRuby.length > 0) return propRuby;
    if (clientRubyCache.has(text)) return clientRubyCache.get(text)!;
    return [{ text, reading: null }];
  });

  useEffect(() => {
    if (propRuby && propRuby.length > 0) {
      setChunks(propRuby);
      return;
    }

    if (!text || !KANJI_REGEX.test(text)) {
      setChunks([{ text, reading: null }]);
      return;
    }

    if (clientRubyCache.has(text)) {
      setChunks(clientRubyCache.get(text)!);
      return;
    }

    let isMounted = true;
    const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
    fetch(`${apiBase}/speech/furigana`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (isMounted && data && data.ruby && data.ruby.length > 0) {
          clientRubyCache.set(text, data.ruby);
          setChunks(data.ruby);
        }
      })
      .catch((e) => console.warn("[UniversalFurigana] Resolver error:", e));

    return () => {
      isMounted = false;
    };
  }, [text, propRuby]);

  const handleSpeak = (e?: React.MouseEvent) => {
    if (e) {
      e.stopPropagation();
    }
    if (isPlaying) {
      stopWebSpeech();
      setIsPlaying(false);
      return;
    }
    setIsPlaying(true);
    speakJapaneseText(text, {
      rate: 0.95,
      onEnd: () => setIsPlaying(false),
      onError: () => setIsPlaying(false),
    });
  };

  if (!text) return null;

  const audioBtnNode = showAudioButton ? (
    <button
      type="button"
      onClick={handleSpeak}
      title={isPlaying ? "Dừng phát âm" : "Nghe phát âm chuẩn Tokyo"}
      className={cn(
        "inline-flex items-center justify-center rounded-full p-1 transition-all ml-1.5 align-middle shrink-0 text-muted-foreground hover:text-primary hover:bg-primary/10",
        isPlaying && "text-primary animate-pulse bg-primary/15 scale-110"
      )}
    >
      <Volume2
        className={cn(
          fontSize === "sm" && "h-3 w-3",
          fontSize === "normal" && "h-3.5 w-3.5",
          (fontSize === "lg" || fontSize === "xl") && "h-4 w-4"
        )}
      />
    </button>
  ) : null;

  if (displayMode === "hidden") {
    return (
      <span className={cn("text-muted-foreground italic font-sans text-xs select-none inline-flex items-center gap-1", className)}>
        <span>[Đã ẩn chữ — Chế độ luyện nghe]</span>
        {audioBtnNode}
      </span>
    );
  }

  if (displayMode === "kanji") {
    return (
      <span
        onClick={enableClickToSpeak ? handleSpeak : undefined}
        title={enableClickToSpeak ? "Nhấp để nghe phát âm Tokyo" : undefined}
        className={cn(
          "font-jp inline-flex items-center gap-1",
          enableClickToSpeak && "cursor-pointer hover:opacity-85 transition-opacity",
          className
        )}
      >
        <span>{text}</span>
        {audioBtnNode}
      </span>
    );
  }

  // Micro-stacking Architecture: Guarantees Furigana strictly on TOP of Kanji with 100% baseline alignment
  return (
    <span
      onClick={enableClickToSpeak ? handleSpeak : undefined}
      title={enableClickToSpeak ? "Nhấp để nghe phát âm Tokyo" : undefined}
      className={cn(
        "font-jp tracking-wide inline-flex flex-wrap items-end justify-center gap-y-2 select-text",
        enableClickToSpeak && "cursor-pointer hover:opacity-85 transition-opacity active:scale-[0.99]",
        isPlaying && "underline decoration-primary/50 decoration-2 underline-offset-4",
        fontSize === "sm" && "text-xs",
        fontSize === "normal" && "text-sm sm:text-base",
        fontSize === "lg" && "text-base sm:text-lg md:text-xl",
        fontSize === "xl" && "text-xl sm:text-2xl md:text-3xl font-black",
        className
      )}
    >
      {chunks.map((c, i) => {
        if (c.reading && KANJI_REGEX.test(c.text)) {
          return (
            <span
              key={i}
              className="inline-flex flex-col-reverse items-center justify-end align-bottom mx-[1.5px] relative"
            >
              {/* 1. Base Kanji text at the bottom */}
              <span className="font-bold text-foreground leading-none">{c.text}</span>

              {/* 2. Furigana reading strictly on TOP */}
              <span
                style={furiganaStyle}
                className={cn(
                  "font-jp text-[0.52em] font-medium leading-none select-none tracking-tight text-center mb-1.5 transition-colors",
                  furiganaClass,
                  furiganaClassName
                )}
              >
                {c.reading}
              </span>
            </span>
          );
        }
        return (
          <span key={i} className="inline-block align-bottom leading-none text-foreground">
            {c.text}
          </span>
        );
      })}
      {audioBtnNode}
    </span>
  );
}
