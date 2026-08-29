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

  // Kanji + Furigana (HTML5 Ruby with pure inline ruby layout)
  return (
    <span
      className={cn(
        "font-jp tracking-wide inline-block leading-[2.2] sm:leading-[2.5]",
        fontSize === "sm" && "text-xs leading-[2.2]",
        fontSize === "normal" && "text-sm sm:text-base leading-[2.3]",
        fontSize === "lg" && "text-base sm:text-lg md:text-xl leading-[2.4]",
        fontSize === "xl" && "text-xl sm:text-2xl md:text-3xl font-black leading-[2.6]",
        className
      )}
    >
      {chunks.map((c, i) => {
        if (c.reading && KANJI_REGEX.test(c.text)) {
          return (
            <ruby
              key={i}
              className="mx-[0.5px] select-text"
              style={{ rubyPosition: "over" }}
            >
              {c.text}
              <rt
                style={{
                  ...furiganaStyle,
                  rubyPosition: "over",
                }}
                className={cn(
                  "font-jp text-[0.55em] font-medium leading-none select-none tracking-tight text-center transition-colors block",
                  furiganaClass,
                  furiganaClassName
                )}
              >
                {c.reading}
              </rt>
            </ruby>
          );
        }
        return <span key={i}>{c.text}</span>;
      })}
    </span>
  );
}
