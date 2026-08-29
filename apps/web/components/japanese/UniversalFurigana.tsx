"use client";

import React, { useState, useEffect, useMemo } from "react";
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

// Global memory cache for resolved ruby chunks across components
const clientRubyCache = new Map<string, RubyChunk[]>();

function fastClientChunk(text: string): RubyChunk[] {
  if (!text) return [];
  if (!KANJI_REGEX.test(text)) {
    return [{ text, reading: null }];
  }
  return [{ text, reading: null }];
}

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
    return fastClientChunk(text);
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
    // Async fetch from backend resolver
    fetch("http://localhost:8000/api/v1/speech/furigana", {
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

  if (displayMode === "hidden") {
    return (
      <span className={cn("text-muted-foreground italic font-sans text-xs select-none", className)}>
        [Đã ẩn chữ — Chế độ luyện nghe]
      </span>
    );
  }

  if (displayMode === "kanji") {
    return (
      <span className={cn("font-jp inline-block leading-normal", className)}>
        {text}
      </span>
    );
  }

  // Kanji + Furigana HTML5 <ruby>
  return (
    <span
      className={cn(
        "font-jp inline-flex flex-wrap items-end leading-loose tracking-wide",
        fontSize === "sm" && "text-xs leading-loose",
        fontSize === "normal" && "text-sm leading-loose",
        fontSize === "lg" && "text-base leading-loose",
        fontSize === "xl" && "text-lg md:text-xl leading-loose",
        className
      )}
    >
      {chunks.map((c, i) => {
        if (c.reading) {
          return (
            <ruby key={i} className="group inline-flex flex-col items-center px-0.5">
              <span className="text-foreground font-bold">{c.text}</span>
              <rp>(</rp>
              <rt
                style={furiganaStyle}
                className={cn(
                  "text-[10px] md:text-[11px] font-normal leading-none select-none tracking-normal font-jp mb-0.5",
                  furiganaClass,
                  furiganaClassName
                )}
              >
                {c.reading}
              </rt>
              <rp>)</rp>
            </ruby>
          );
        }
        return (
          <span key={i} className="text-foreground">
            {c.text}
          </span>
        );
      })}
    </span>
  );
}
