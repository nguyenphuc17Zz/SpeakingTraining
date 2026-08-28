"use client";

import React from "react";
import { Check, X, AlertCircle, Sparkles, Volume2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface WordDiffDisplayProps {
  targetText: string;
  userText?: string | null;
  className?: string;
}

interface DiffToken {
  text: string;
  type: "correct" | "incorrect" | "missing" | "extra";
  expected?: string;
}

// Convert Katakana to Hiragana for phonetic normalization
function katakanaToHiragana(str: string): string {
  return str.replace(/[\u30a1-\u30f6]/g, (match) => {
    const chr = match.charCodeAt(0) - 0x60;
    return String.fromCharCode(chr);
  });
}

// Segment string into Japanese Mora units
function segmentIntoMoras(text: string): string[] {
  const clean = katakanaToHiragana(text.trim().replace(/[、。！？\s\.,!\?…・~〜]+/g, ""));
  if (!clean) return [];

  const smallKana = new Set(["ゃ", "ゅ", "ょ", "ぁ", "ぃ", "ぅ", "ぇ", "ぉ", "ゎ"]);
  const moras: string[] = [];
  let i = 0;

  while (i < clean.length) {
    const curr = clean[i];
    const next = i + 1 < clean.length ? clean[i + 1] : "";
    if (smallKana.has(next)) {
      moras.push(curr + next);
      i += 2;
    } else {
      moras.push(curr);
      i += 1;
    }
  }

  return moras;
}

function areMorasEquivalent(m1: string, m2: string): boolean {
  if (m1 === m2) return true;
  const eqMap: Record<string, Set<string>> = {
    "じ": new Set(["ぢ"]),
    "ぢ": new Set(["じ"]),
    "ず": new Set(["づ"]),
    "づ": new Set(["ず"]),
    "ー": new Set(["う", "お", "あ", "い", "え"]),
    "を": new Set(["お"]),
    "お": new Set(["を"]),
    "は": new Set(["わ"]),
    "へ": new Set(["え"]),
  };
  return eqMap[m1]?.has(m2) || false;
}

// Full 2D Levenshtein Alignment for Japanese Moras
function computeJapaneseMoraDiff(target: string, user: string): DiffToken[] {
  const cleanTarget = target.trim();
  const cleanUser = user.trim();

  if (!cleanUser) {
    return [{ text: cleanTarget, type: "missing" }];
  }

  const targetMoras = segmentIntoMoras(cleanTarget);
  const userMoras = segmentIntoMoras(cleanUser);

  if (targetMoras.length === 0) {
    return [{ text: cleanUser, type: "extra" }];
  }
  if (userMoras.length === 0) {
    return [{ text: cleanTarget, type: "missing" }];
  }

  const n = targetMoras.length;
  const m = userMoras.length;

  const dp: number[][] = Array.from({ length: n + 1 }, () => Array(m + 1).fill(0));
  for (let i = 0; i <= n; i++) dp[i][0] = i;
  for (let j = 0; j <= m; j++) dp[0][j] = j;

  for (let i = 1; i <= n; i++) {
    for (let j = 1; j <= m; j++) {
      const cost = areMorasEquivalent(targetMoras[i - 1], userMoras[j - 1]) ? 0 : 1;
      dp[i][j] = Math.min(
        dp[i - 1][j] + 1, // Del
        dp[i][j - 1] + 1, // Ins
        dp[i - 1][j - 1] + cost // Match/Sub
      );
    }
  }

  let i = n;
  let j = m;
  const ops: Array<{ op: "match" | "sub" | "del" | "ins"; t?: string; u?: string }> = [];

  while (i > 0 || j > 0) {
    if (i > 0 && j > 0) {
      const cost = areMorasEquivalent(targetMoras[i - 1], userMoras[j - 1]) ? 0 : 1;
      if (dp[i][j] === dp[i - 1][j - 1] + cost) {
        ops.push({
          op: cost === 0 ? "match" : "sub",
          t: targetMoras[i - 1],
          u: userMoras[j - 1],
        });
        i -= 1;
        j -= 1;
        continue;
      }
    }
    if (i > 0 && dp[i][j] === dp[i - 1][j] + 1) {
      ops.push({ op: "del", t: targetMoras[i - 1] });
      i -= 1;
      continue;
    }
    if (j > 0 && dp[i][j] === dp[i][j - 1] + 1) {
      ops.push({ op: "ins", u: userMoras[j - 1] });
      j -= 1;
      continue;
    }
  }

  ops.reverse();

  return ops.map((op) => {
    if (op.op === "match") {
      return { text: op.u || op.t || "", type: "correct" };
    }
    if (op.op === "sub") {
      return { text: op.u || "", type: "incorrect", expected: op.t };
    }
    if (op.op === "del") {
      return { text: op.t || "", type: "missing", expected: op.t };
    }
    return { text: op.u || "", type: "extra" };
  });
}

export function WordDiffDisplay({
  targetText,
  userText,
  className,
}: WordDiffDisplayProps) {
  const [showDetailedMora, setShowDetailedMora] = React.useState(false);

  if (!userText) {
    return (
      <div className={cn("p-4 rounded-2xl bg-card border border-border space-y-3 shadow-sm", className)}>
        {/* Target Reference Sentence */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold text-primary uppercase tracking-wider flex items-center gap-1.5">
              <span>🎯</span>
              <span>Câu mẫu chuẩn:</span>
            </span>
            <span className="text-[10px] text-muted-foreground font-mono">Video Gốc</span>
          </div>
          <p className="font-jp text-base sm:text-lg text-foreground font-black leading-relaxed">
            {targetText}
          </p>
        </div>

        {/* Missing Speech Notice */}
        <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-200 text-xs flex items-center gap-2">
          <span>🎙️</span>
          <span>Chưa ghi nhận được giọng nói. Hãy kiểm tra micro và phát âm lại.</span>
        </div>
      </div>
    );
  }

  const diff = computeJapaneseMoraDiff(targetText, userText);

  return (
    <div className={cn("p-4 rounded-2xl bg-card/95 border border-border/90 space-y-3 shadow-sm", className)}>
      {/* 1. Target Native Reference Sentence */}
      <div className="p-3.5 rounded-xl bg-background/80 border border-border/70 space-y-1 shadow-xs">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-bold text-primary uppercase tracking-wider flex items-center gap-1.5">
            <span>🎯</span>
            <span>Câu mẫu chuẩn:</span>
          </span>
          <span className="text-[10px] text-muted-foreground font-mono">Video Gốc</span>
        </div>
        <p className="font-jp text-base sm:text-lg text-foreground font-black leading-relaxed">
          {targetText}
        </p>
      </div>

      {/* 2. User Spoken Output (Clean & Natural) */}
      <div className="p-3.5 rounded-xl bg-background/80 border border-border/70 space-y-1 shadow-xs">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
            <span>🎙️</span>
            <span>Bạn vừa nói:</span>
          </span>
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-muted-foreground font-mono hidden sm:inline">AI Nhận Diện</span>
            <button
              type="button"
              onClick={() => setShowDetailedMora((prev) => !prev)}
              className="text-[10px] font-semibold text-primary hover:underline"
            >
              {showDetailedMora ? "Thu gọn phân tích" : "Chi tiết từng âm"}
            </button>
          </div>
        </div>
        <p className="font-jp text-base sm:text-lg text-emerald-300 font-bold leading-relaxed">
          {userText}
        </p>
      </div>

      {/* 3. Optional Deep Phoneme Breakdown (Collapsible) */}
      {showDetailedMora && (
        <div className="p-3 rounded-xl bg-muted/40 border border-border/60 space-y-2 animate-in fade-in duration-150">
          <div className="flex items-center justify-between">
            <span className="text-[10.5px] font-bold text-muted-foreground uppercase tracking-wider">
              Đối chiếu từng âm tiết:
            </span>
            <div className="flex items-center gap-2 text-[10px] font-medium">
              <span className="text-emerald-400">● Đúng</span>
              <span className="text-rose-400">● Lệch</span>
              <span className="text-amber-400">● Nuốt âm</span>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-1 font-jp text-sm leading-loose">
            {diff.map((tok, i) => {
              if (tok.type === "correct") {
                return (
                  <span
                    key={i}
                    className="px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 font-bold"
                  >
                    {tok.text}
                  </span>
                );
              }
              if (tok.type === "incorrect") {
                return (
                  <span
                    key={i}
                    className="px-1.5 py-0.5 rounded bg-rose-950/40 text-rose-300 border border-rose-500/40 font-bold inline-flex items-baseline gap-1"
                    title={`Lệch: '${tok.text}' (chuẩn: '${tok.expected}')`}
                  >
                    <span>{tok.text}</span>
                    {tok.expected && <span className="text-[10px] opacity-75">({tok.expected})</span>}
                  </span>
                );
              }
              if (tok.type === "missing") {
                return (
                  <span
                    key={i}
                    className="px-1.5 py-0.5 rounded bg-amber-500/15 text-amber-300 border border-amber-500/35 border-dashed font-bold"
                    title={`Nuốt âm: '${tok.text}'`}
                  >
                    [{tok.text}]
                  </span>
                );
              }
              return (
                <span
                  key={i}
                  className="px-1.5 py-0.5 rounded bg-amber-500/15 text-amber-300 border border-amber-500/30 font-bold"
                >
                  +{tok.text}
                </span>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

