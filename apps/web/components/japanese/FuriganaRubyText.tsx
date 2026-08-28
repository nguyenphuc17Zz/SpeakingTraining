"use client";

import React, { useMemo } from "react";
import { RubyChunk, ExtractedVocabulary } from "@/types/shadowing";
import { cn } from "@/lib/utils";

interface FuriganaRubyTextProps {
  text: string;
  reading?: string | null;
  ruby?: RubyChunk[] | null;
  vocabulary?: ExtractedVocabulary[];
  displayMode?: "kanji_reading" | "kanji" | "hidden";
  fontSize?: "normal" | "large";
  furiganaStyle?: React.CSSProperties;
  className?: string;
  isActive?: boolean;
}

const KANJI_REGEX = /[\u4E00-\u9FAF\u3400-\u4DBF]/;

/**
 * Parses raw text and vocabulary into structured Ruby chunks when pre-parsed ruby is unavailable.
 */
function alignClientRuby(text: string, vocabulary?: ExtractedVocabulary[]): RubyChunk[] {
  if (!text) return [];
  if (!KANJI_REGEX.test(text)) {
    return [{ text, reading: null }];
  }

  // Sort vocabulary words by length descending to match longest Kanji phrases first
  const knownVocab = (vocabulary || [])
    .filter((v) => v.word && v.reading && KANJI_REGEX.test(v.word))
    .sort((a, b) => b.word.length - a.word.length);

  const chunks: RubyChunk[] = [];
  let remaining = text;

  while (remaining.length > 0) {
    let matched = false;

    // Check against known vocabulary words
    for (const v of knownVocab) {
      if (remaining.startsWith(v.word)) {
        chunks.push({
          text: v.word,
          reading: v.reading,
        });
        remaining = remaining.slice(v.word.length);
        matched = true;
        break;
      }
    }

    if (!matched) {
      // Find next kanji or push single non-kanji char
      const nextChar = remaining[0];
      if (chunks.length > 0 && !chunks[chunks.length - 1].reading && !KANJI_REGEX.test(nextChar)) {
        chunks[chunks.length - 1].text += nextChar;
      } else {
        chunks.push({
          text: nextChar,
          reading: null,
        });
      }
      remaining = remaining.slice(1);
    }
  }

  return chunks;
}

export function FuriganaRubyText({
  text,
  reading,
  ruby,
  vocabulary,
  displayMode = "kanji_reading",
  fontSize = "normal",
  furiganaStyle,
  className,
  isActive = false,
}: FuriganaRubyTextProps) {
  // Compute chunks: use pre-parsed ruby from backend if present, else client-side aligner
  const resolvedChunks = useMemo<RubyChunk[]>(() => {
    if (ruby && ruby.length > 0) {
      return ruby;
    }
    return alignClientRuby(text, vocabulary);
  }, [ruby, text, vocabulary]);

  if (displayMode === "hidden") {
    return (
      <span className="text-xs text-muted-foreground italic font-sans py-1 block">
        [Chế độ Immersion — Nghe và lặp lại theo tai]
      </span>
    );
  }

  if (displayMode === "kanji") {
    return (
      <span
        className={cn(
          "font-jp tracking-wide leading-relaxed block",
          fontSize === "large" ? "text-lg sm:text-xl font-bold" : "text-base font-semibold",
          isActive ? "text-primary font-bold" : "text-foreground",
          className
        )}
      >
        {text}
      </span>
    );
  }

  // Default: Kanji + Furigana (HTML5 Ruby)
  return (
    <span
      className={cn(
        "font-jp tracking-wide inline-block leading-[2.2] sm:leading-[2.4]",
        fontSize === "large" ? "text-lg sm:text-xl font-bold" : "text-base font-semibold",
        isActive ? "text-foreground font-bold" : "text-foreground/95",
        className
      )}
    >
      {resolvedChunks.map((chunk, index) => {
        if (chunk.reading && KANJI_REGEX.test(chunk.text)) {
          return (
            <ruby
              key={index}
              className="mx-[0.5px] select-text"
              style={{ rubyPosition: "over" }}
            >
              {chunk.text}
              <rt
                style={{
                  ...furiganaStyle,
                  rubyPosition: "over",
                }}
                className="font-jp text-[0.56em] font-medium leading-none select-none tracking-tight text-center transition-colors"
              >
                {chunk.reading}
              </rt>
            </ruby>
          );
        }
        return <span key={index}>{chunk.text}</span>;
      })}
    </span>
  );
}
