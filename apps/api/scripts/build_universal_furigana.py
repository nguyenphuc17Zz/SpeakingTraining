import os

# 1. Update speech.py with /speech/furigana endpoint
SPEECH_FURIGANA_ENDPOINT = '''
# ── Universal Furigana Resolver Endpoints ──

class RubyChunkDTO(BaseModel):
    text: str
    reading: str | None = None

class FuriganaRequest(BaseModel):
    text: str

class FuriganaResponse(BaseModel):
    text: str
    hiragana: str
    ruby: list[RubyChunkDTO]

class BatchFuriganaRequest(BaseModel):
    texts: list[str]

class BatchFuriganaResponse(BaseModel):
    results: list[FuriganaResponse]

@router.post("/furigana", response_model=FuriganaResponse)
async def resolve_furigana(
    request: FuriganaRequest,
):
    """Resolves Japanese text into structured Ruby tokens with Hiragana readings."""
    from app.domains.pronunciation.japanese.reading_resolver import JapaneseReadingResolver
    text = request.text or ""
    hiragana = JapaneseReadingResolver.to_hiragana(text)
    ruby_raw = JapaneseReadingResolver.to_ruby_chunks(text)
    ruby_dtos = [RubyChunkDTO(text=c.get("text", ""), reading=c.get("reading")) for c in ruby_raw]
    return FuriganaResponse(text=text, hiragana=hiragana, ruby=ruby_dtos)

@router.post("/furigana/batch", response_model=BatchFuriganaResponse)
async def resolve_batch_furigana(
    request: BatchFuriganaRequest,
):
    """Resolves multiple Japanese sentences into structured Ruby tokens."""
    from app.domains.pronunciation.japanese.reading_resolver import JapaneseReadingResolver
    results = []
    for text in request.texts:
        hiragana = JapaneseReadingResolver.to_hiragana(text)
        ruby_raw = JapaneseReadingResolver.to_ruby_chunks(text)
        ruby_dtos = [RubyChunkDTO(text=c.get("text", ""), reading=c.get("reading")) for c in ruby_raw]
        results.append(FuriganaResponse(text=text, hiragana=hiragana, ruby=ruby_dtos))
    return BatchFuriganaResponse(results=results)
'''

# 2. UniversalFurigana.tsx
UNIVERSAL_FURIGANA = """\"use client\";

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

const KANJI_REGEX = /[\\u4E00-\\u9FAF\\u3400-\\u4DBF]/;

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
"""

# 3. GlobalFuriganaControl.tsx
GLOBAL_FURIGANA_CONTROL = """\"use client\";

import React, { useState } from "react";
import {
  useFuriganaSettings,
  FuriganaColorId,
  FURIGANA_COLORS,
} from "@/hooks/use-furigana-settings";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { soundFX } from "@/lib/sound-fx";
import { Sparkles, Palette, Eye, EyeOff, BookOpen, Settings2 } from "lucide-react";
import { cn } from "@/lib/utils";

export function GlobalFuriganaControl() {
  const {
    colorId,
    changeColor,
    activeHex,
    changeCustomColor,
    displayMode,
    setDisplayMode,
    options,
  } = useFuriganaSettings();

  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative inline-block">
      {/* Trigger Pill */}
      <button
        type="button"
        onClick={() => {
          soundFX.playFurin();
          setIsOpen((prev) => !prev);
        }}
        className={cn(
          "flex items-center gap-1.5 px-2.5 py-1 rounded-xl text-xs font-bold border transition-all shadow-2xs",
          isOpen
            ? "bg-primary text-primary-foreground border-primary"
            : "bg-card border-border/80 text-muted-foreground hover:text-foreground hover:border-primary/40"
        )}
        title="Tùy chỉnh hiển thị phiên âm Furigana toàn hệ thống"
      >
        <span className="font-jp text-primary font-black">ふ</span>
        <span className="hidden sm:inline text-[11px]">Furigana</span>
        <span
          className="w-2.5 h-2.5 rounded-full border border-black/10 shadow-2xs"
          style={{ backgroundColor: activeHex }}
        />
      </button>

      {/* Popover */}
      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 top-full mt-2 z-50 w-72 p-4 rounded-2xl bg-card border border-border/80 shadow-2xl washi-texture space-y-3.5 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between border-b border-border/60 pb-2">
              <span className="text-xs font-bold text-foreground flex items-center gap-1.5">
                <Settings2 className="h-3.5 w-3.5 text-primary" />
                <span>Phiên Âm Furigana Toàn Hệ Thống</span>
              </span>
              <Badge variant="outline" size="sm" className="text-[9px] font-mono">
                GLOBAL
              </Badge>
            </div>

            {/* Display Mode 3 Tabs */}
            <div className="space-y-1.5">
              <span className="text-[10px] text-muted-foreground font-semibold uppercase">Chế độ hiển thị:</span>
              <div className="grid grid-cols-3 gap-1 p-1 rounded-xl bg-muted/40 border border-border/60">
                <button
                  type="button"
                  onClick={() => {
                    soundFX.playFurin();
                    setDisplayMode("kanji_reading");
                  }}
                  className={cn(
                    "py-1.5 rounded-lg text-[10px] font-bold transition-all text-center",
                    displayMode === "kanji_reading"
                      ? "bg-primary text-primary-foreground shadow-2xs"
                      : "text-muted-foreground hover:text-foreground"
                  )}
                >
                  🌸 Đầy đủ
                </button>
                <button
                  type="button"
                  onClick={() => {
                    soundFX.playFurin();
                    setDisplayMode("kanji");
                  }}
                  className={cn(
                    "py-1.5 rounded-lg text-[10px] font-bold transition-all text-center",
                    displayMode === "kanji"
                      ? "bg-primary text-primary-foreground shadow-2xs"
                      : "text-muted-foreground hover:text-foreground"
                  )}
                >
                  🏯 Chỉ Kanji
                </button>
                <button
                  type="button"
                  onClick={() => {
                    soundFX.playFurin();
                    setDisplayMode("hidden");
                  }}
                  className={cn(
                    "py-1.5 rounded-lg text-[10px] font-bold transition-all text-center",
                    displayMode === "hidden"
                      ? "bg-primary text-primary-foreground shadow-2xs"
                      : "text-muted-foreground hover:text-foreground"
                  )}
                >
                  🎧 Ẩn chữ
                </button>
              </div>
            </div>

            {/* Color Palette */}
            <div className="space-y-1.5">
              <span className="text-[10px] text-muted-foreground font-semibold uppercase">Màu sắc Furigana:</span>
              <div className="grid grid-cols-3 gap-1.5">
                {options.map((opt) => (
                  <button
                    key={opt.id}
                    type="button"
                    onClick={() => {
                      soundFX.playSuikinkutsu();
                      changeColor(opt.id);
                    }}
                    className={cn(
                      "p-1.5 rounded-xl border flex items-center gap-1.5 text-[10px] font-semibold transition-all text-left",
                      colorId === opt.id
                        ? "border-primary bg-primary/10 shadow-2xs text-foreground font-bold"
                        : "border-border/60 bg-card text-muted-foreground hover:text-foreground"
                    )}
                  >
                    <span
                      className="w-3 h-3 rounded-full border border-black/10 shrink-0"
                      style={{ backgroundColor: opt.hex }}
                    />
                    <span className="truncate">{opt.nameVi.split(" ")[0]}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
"""

# 4. Japanese components index.ts
JAPANESE_INDEX = """export * from "./FuriganaRubyText";
export * from "./UniversalFurigana";
export * from "./GlobalFuriganaControl";
"""

FILES_FURIGANA = {
    r"E:\SpeakingTraining\apps\web\components\japanese\UniversalFurigana.tsx": UNIVERSAL_FURIGANA,
    r"E:\SpeakingTraining\apps\web\components\japanese\GlobalFuriganaControl.tsx": GLOBAL_FURIGANA_CONTROL,
    r"E:\SpeakingTraining\apps\web\components\japanese\index.ts": JAPANESE_INDEX,
}

for filepath, content in FILES_FURIGANA.items():
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"Successfully wrote {os.path.basename(filepath)}")

# Append Furigana endpoints to speech.py if not present
speech_api_path = r"E:\SpeakingTraining\apps\api\app\api\v1\speech.py"
with open(speech_api_path, "r", encoding="utf-8") as f:
    text = f.read()

if "resolve_furigana" not in text:
    with open(speech_api_path, "a", encoding="utf-8") as f:
        f.write(SPEECH_FURIGANA_ENDPOINT + "\n")
    print("Successfully appended Furigana resolver endpoints to speech.py")

print("Universal Furigana backend & frontend components written successfully!")
