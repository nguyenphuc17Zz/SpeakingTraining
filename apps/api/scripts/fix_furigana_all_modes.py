import os

# 1. Fixed UniversalFurigana.tsx
UNIVERSAL_FURIGANA_FIXED = """\"use client\";

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

const KANJI_REGEX = /[\\u4E00-\\u9FAF\\u3400-\\u4DBF]/;
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
"""

with open(r"E:\SpeakingTraining\apps\web\components\japanese\UniversalFurigana.tsx", "w", encoding="utf-8") as f:
    f.write(UNIVERSAL_FURIGANA_FIXED.strip() + "\n")
print("UniversalFurigana.tsx updated successfully!")

# 2. Update KeigoPromptCard.tsx
keigo_prompt_path = r"E:\SpeakingTraining\apps\web\features\keigo\components\KeigoPromptCard.tsx"
with open(keigo_prompt_path, "r", encoding="utf-8") as f:
    k_content = f.read()

if "import { UniversalFurigana }" not in k_content:
    k_content = k_content.replace('"use client";', '"use client";\n\nimport { UniversalFurigana } from "@/components/japanese/UniversalFurigana";')

# Replace prompt text with UniversalFurigana
k_content = k_content.replace(
    '<div className="text-2xl sm:text-3xl md:text-4xl font-black font-jp tracking-tight text-foreground px-2 leading-tight">\n              {prompt}\n            </div>',
    '<div className="text-xl sm:text-2xl md:text-3xl font-black font-jp tracking-tight text-foreground px-2 flex justify-center">\n              <UniversalFurigana text={prompt} fontSize="xl" />\n            </div>'
)

with open(keigo_prompt_path, "w", encoding="utf-8") as f:
    f.write(k_content)
print("KeigoPromptCard.tsx updated with UniversalFurigana!")

# 3. Update PitchPromptCard.tsx
pitch_prompt_path = r"E:\SpeakingTraining\apps\web\features\pitch\components\PitchPromptCard.tsx"
with open(pitch_prompt_path, "r", encoding="utf-8") as f:
    p_content = f.read()

if "import { UniversalFurigana }" not in p_content:
    p_content = p_content.replace('"use client";', '"use client";\n\nimport { UniversalFurigana } from "@/components/japanese/UniversalFurigana";')

p_content = p_content.replace(
    '<div className="text-2xl md:text-3xl font-black font-jp text-foreground tracking-wide leading-relaxed">\n              {canonical}\n            </div>',
    '<div className="text-xl md:text-2xl font-black font-jp text-foreground tracking-wide flex justify-center">\n              <UniversalFurigana text={canonical} fontSize="xl" />\n            </div>'
)

with open(pitch_prompt_path, "w", encoding="utf-8") as f:
    f.write(p_content)
print("PitchPromptCard.tsx updated with UniversalFurigana!")

# 4. Update SituationsPromptCard.tsx
sit_prompt_path = r"E:\SpeakingTraining\apps\web\features\situations\components\SituationsPromptCard.tsx"
with open(sit_prompt_path, "r", encoding="utf-8") as f:
    s_content = f.read()

if "import { UniversalFurigana }" not in s_content:
    s_content = s_content.replace('"use client";', '"use client";\n\nimport { UniversalFurigana } from "@/components/japanese/UniversalFurigana";')

s_content = s_content.replace(
    '<div className="text-xl md:text-2xl font-black font-jp text-foreground tracking-wide leading-relaxed">\n              「{openingDialogue}」\n            </div>',
    '<div className="text-lg md:text-xl font-black font-jp text-foreground tracking-wide flex justify-center">\n              <UniversalFurigana text={openingDialogue} fontSize="lg" />\n            </div>'
)

with open(sit_prompt_path, "w", encoding="utf-8") as f:
    f.write(s_content)
print("SituationsPromptCard.tsx updated with UniversalFurigana!")

# 5. Update ReflexPromptCard.tsx
reflex_prompt_path = r"E:\SpeakingTraining\apps\web\features\reflex\components\ReflexPromptCard.tsx"
with open(reflex_prompt_path, "r", encoding="utf-8") as f:
    r_content = f.read()

if "import { UniversalFurigana }" not in r_content:
    r_content = r_content.replace('"use client";', '"use client";\n\nimport { UniversalFurigana } from "@/components/japanese/UniversalFurigana";')

# Ensure container leading and flex layout are neat
r_content = r_content.replace(
    '<div className="text-3xl md:text-4xl font-black font-jp tracking-tight text-foreground">\n                {verb || prompt}\n              </div>',
    '<div className="text-2xl md:text-3xl font-black font-jp tracking-tight text-foreground flex justify-center">\n                <UniversalFurigana text={verb || prompt} fontSize="xl" />\n              </div>'
)
r_content = r_content.replace(
    '<div className="text-xl md:text-2xl font-bold font-jp leading-relaxed text-foreground tracking-tight">\n                {prompt}\n              </div>',
    '<div className="text-lg md:text-xl font-bold font-jp leading-relaxed text-foreground tracking-tight flex justify-center">\n                <UniversalFurigana text={prompt} fontSize="lg" />\n              </div>'
)

with open(reflex_prompt_path, "w", encoding="utf-8") as f:
    f.write(r_content)
print("ReflexPromptCard.tsx verified with UniversalFurigana!")

print("All modes updated and aligned!")
