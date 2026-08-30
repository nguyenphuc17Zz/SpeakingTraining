"use client";

import React, { useState, useEffect } from "react";
import { useFuriganaSettings } from "@/hooks/use-furigana-settings";
import { cn } from "@/lib/utils";

interface RubyChunk {
  text: string;
  reading?: string | null;
}

interface UniversalFuriganaProps {
  text: string;
  ruby?: RubyChunk[] | null;
  className?: string;
  furiganaClassName?: string;
  fontSize?: "sm" | "normal" | "lg" | "xl";
  forceDisplayMode?: "kanji_reading" | "kanji" | "hidden";
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
}: UniversalFuriganaProps) {
  const { displayMode: globalDisplayMode, furiganaStyle, furiganaClass } = useFuriganaSettings();
  const displayMode = forceDisplayMode || globalDisplayMode || "kanji_reading";

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

  if (!text) return null;

  if (displayMode === "hidden") {
    return (
      <span className={cn("text-muted-foreground italic font-sans text-xs select-none", className)}>
        [Đã ẩn chữ — Chế độ luyện nghe]
      </span>
    );
  }

  if (displayMode === "kanji") {
    return (
      <span className={cn("font-jp inline-block", className)}>
        {text}
      </span>
    );
  }

  // Micro-stacking Architecture: Guarantees Furigana strictly on TOP of Kanji with 100% baseline alignment
  return (
    <span
      className={cn(
        "font-jp tracking-wide inline-flex flex-wrap items-end justify-center gap-y-2 select-text",
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
    </span>
  );
}
