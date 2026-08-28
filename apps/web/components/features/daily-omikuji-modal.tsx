"use client";

import React, { useState, useEffect } from "react";
import { Sparkles, Volume2, CheckCircle2, RefreshCw, X, Award, Dices, Bot, Wand2, Flame } from "lucide-react";
import { Button } from "@/components/ui/button";
import { HankoStamp } from "@/components/ui/hanko-stamp";
import { soundFX } from "@/lib/sound-fx";
import { aiApi } from "@/services/ai-api";
import { cn } from "@/lib/utils";

export type OmikujiGenre = "zen" | "anime" | "daily" | "business" | "romance" | "mystery";

export interface OmikujiGenreMeta {
  id: OmikujiGenre;
  name: string;
  kanji: string;
  emoji: string;
  description: string;
  color: string;
}

export const OMIKUJI_GENRES: OmikujiGenreMeta[] = [
  {
    id: "zen",
    name: "Triết lý & Samurai",
    kanji: "禅・武士道",
    emoji: "⛩️",
    description: "Ngạn ngữ cổ, tinh thần võ sĩ đạo & kiên trì",
    color: "border-primary/30 text-primary bg-primary/10",
  },
  {
    id: "anime",
    name: "Anime & Manga",
    kanji: "アニメ・情熱",
    emoji: "⚡",
    description: "Câu thoại hào hùng, nhiệt huyết & ước mơ",
    color: "border-amber-500/30 text-amber-600 bg-amber-500/10",
  },
  {
    id: "daily",
    name: "Đời sống Tokyo",
    kanji: "日常・会話",
    emoji: "🍜",
    description: "Khẩu ngữ thường nhật, quán ăn & bạn bè",
    color: "border-matcha-500/30 text-matcha-600 bg-matcha-500/10",
  },
  {
    id: "business",
    name: "Kính ngữ & Công sở",
    kanji: "敬語・仕事",
    emoji: "💼",
    description: "Giao tiếp lịch thiệp, phỏng vấn & công việc",
    color: "border-fuji-500/30 text-fuji-500 bg-fuji-500/10",
  },
  {
    id: "romance",
    name: "Tình cảm & Thả thính",
    kanji: "恋愛・青春",
    emoji: "💖",
    description: "Cảm xúc chân thành & giới trẻ Tokyo",
    color: "border-sakura-500/30 text-sakura-600 bg-sakura-500/10",
  },
  {
    id: "mystery",
    name: "AI Thần Bí",
    kanji: "神託・神秘",
    emoji: "🎲",
    description: "AI thỏa sức sáng tạo bất ngờ không giới hạn",
    color: "border-kintsugi-400/30 text-kintsugi-500 bg-kintsugi-400/10",
  },
];

interface FortuneQuote {
  japanese: string;
  reading: string;
  vietnamese: string;
  meaning: string;
  theme: string;
}

type FortuneRank = "大吉" | "中吉" | "吉" | "小吉";

interface FortuneResult {
  rank: FortuneRank;
  rankName: string;
  color: string;
  bonusXp: number;
  quote: FortuneQuote;
  genre: OmikujiGenre;
  isAiGenerated: boolean;
  dateKey: string;
  claimed: boolean;
}

export function DailyOmikujiModal({
  isOpen,
  onClose,
  onXpAwarded,
}: {
  isOpen: boolean;
  onClose: () => void;
  onXpAwarded?: (xp: number) => void;
}) {
  const [selectedGenre, setSelectedGenre] = useState<OmikujiGenre>("zen");
  const [shaking, setShaking] = useState(false);
  const [aiGenerating, setAiGenerating] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);
  const [drawnResult, setDrawnResult] = useState<FortuneResult | null>(null);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);

  const getTodayKey = () => new Date().toISOString().slice(0, 10);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const today = getTodayKey();
    const stored = localStorage.getItem(`hanasu-omikuji-${today}`);
    if (stored) {
      try {
        setDrawnResult(JSON.parse(stored));
      } catch (e) {
        console.warn("Invalid omikuji cache", e);
      }
    }
  }, []);

  const generateWithAI = async (genre: OmikujiGenre): Promise<FortuneQuote | null> => {
    try {
      const genreObj = OMIKUJI_GENRES.find((g) => g.id === genre) || OMIKUJI_GENRES[0];
      const prompt = `Bạn là Thần Đền Shinto & Bậc thầy tiếng Nhật tạo quẻ xăm may mắn Daily Omikuji (おみくじ).
Chủ đề yêu cầu: "${genreObj.name} (${genreObj.kanji})".
Hãy sinh một quẻ xăm may mắn độc đáo, chuẩn văn hóa Nhật Bản.
Trả về DUY NHẤT một chuỗi JSON hợp lệ (không markdown block, không giải thích ngoài JSON) theo đúng cấu trúc:
{
  "japanese": "câu tiếng Nhật chuẩn tự nhiên 1-2 câu",
  "reading": "hiragana + romaji",
  "vietnamese": "bản dịch tiếng Việt súc tích",
  "meaning": "lời giải quẻ sâu sắc, khuyên người học cách áp dụng",
  "theme": "chủ đề tóm tắt 2-3 chữ"
}`;

      const res = await aiApi.generate({
        messages: [{ role: "user", content: prompt }],
        task: "conversation",
        temperature: 0.85,
        max_output_tokens: 400,
      });

      if (res && res.text) {
        let cleanText = res.text.trim();
        if (cleanText.startsWith("```json")) {
          cleanText = cleanText.replace(/```json\n?/, "").replace(/```$/, "").trim();
        } else if (cleanText.startsWith("```")) {
          cleanText = cleanText.replace(/```\n?/, "").replace(/```$/, "").trim();
        }
        const parsed = JSON.parse(cleanText);
        if (parsed.japanese && parsed.vietnamese) {
          return {
            japanese: parsed.japanese,
            reading: parsed.reading || parsed.japanese,
            vietnamese: parsed.vietnamese,
            meaning: parsed.meaning || "Lời chúc cát tường từ AI Master.",
            theme: parsed.theme || genreObj.name,
          };
        }
      }
    } catch (err) {
      console.warn("AI Omikuji generation fallback to curated bank:", err);
    }
    return null;
  };

  const handleDrawFortune = async () => {
    if (shaking || aiGenerating) return;

    soundFX.playFurin();
    setShaking(true);
    setAiGenerating(true);
    setAiError(null);

    const ranks: { rank: FortuneRank; name: string; color: string; xp: number; weight: number }[] = [
      { rank: "大吉", name: "Đại Cát (Tuyệt vời)", color: "text-primary", xp: 50, weight: 35 },
      { rank: "中吉", name: "Trung Cát (Rất tốt)", color: "text-kintsugi-500", xp: 35, weight: 35 },
      { rank: "吉", name: "Cát (May mắn)", color: "text-matcha-600", xp: 25, weight: 20 },
      { rank: "小吉", name: "Tiểu Cát (Bình an)", color: "text-fuji-500", xp: 20, weight: 10 },
    ];

    const totalWeight = ranks.reduce((acc, r) => acc + r.weight, 0);
    let rand = Math.random() * totalWeight;
    let selectedRank = ranks[0];
    for (const r of ranks) {
      if (rand < r.weight) {
        selectedRank = r;
        break;
      }
      rand -= r.weight;
    }

    // Try AI generation strictly without hidden fallback
    let aiQuote = await generateWithAI(selectedGenre);

    if (!aiQuote) {
      setAiError("Không thể kết nối AI Server để sinh quẻ xăm. Vui lòng kiểm tra backend hoặc API key!");
      setShaking(false);
      setAiGenerating(false);
      return;
    }

    soundFX.playTaiko();

    const result: FortuneResult = {
      rank: selectedRank.rank,
      rankName: selectedRank.name,
      color: selectedRank.color,
      bonusXp: selectedRank.xp,
      quote: aiQuote,
      genre: selectedGenre,
      isAiGenerated: true,
      dateKey: getTodayKey(),
      claimed: false,
    };

    setDrawnResult(result);
    localStorage.setItem(`hanasu-omikuji-${getTodayKey()}`, JSON.stringify(result));
    setShaking(false);
    setAiGenerating(false);
  };

  const handleRedrawWithGenre = (genre: OmikujiGenre) => {
    setSelectedGenre(genre);
    setDrawnResult(null);
  };

  const handleSpeakQuote = () => {
    if (!drawnResult || typeof window === "undefined") return;
    setIsPlayingAudio(true);
    soundFX.playSuikinkutsu();

    const utterance = new SpeechSynthesisUtterance(drawnResult.quote.japanese);
    utterance.lang = "ja-JP";
    utterance.rate = 0.9;
    utterance.onend = () => setIsPlayingAudio(false);
    utterance.onerror = () => setIsPlayingAudio(false);
    window.speechSynthesis.speak(utterance);
  };

  const handleClaimReward = () => {
    if (!drawnResult || drawnResult.claimed) return;

    soundFX.playHankoStamp();
    setTimeout(() => soundFX.playVictory(), 200);

    const updated: FortuneResult = { ...drawnResult, claimed: true };
    setDrawnResult(updated);
    localStorage.setItem(`hanasu-omikuji-${getTodayKey()}`, JSON.stringify(updated));

    onXpAwarded?.(drawnResult.bonusXp);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-lg rounded-[28px] border border-border bg-card/95 washi-texture shadow-sumi-lg p-6 sm:p-7 overflow-hidden">
        {/* Background Shoji & Enso */}
        <div className="absolute inset-0 shoji-grid opacity-30 pointer-events-none" />
        <div className="absolute -top-12 -right-12 h-44 w-44 rounded-full bg-enso-gradient opacity-40 pointer-events-none" />

        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 h-8 w-8 rounded-full bg-muted/80 hover:bg-muted flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors z-20"
          aria-label="Đóng"
        >
          <X className="h-4 w-4" />
        </button>

        {/* Modal Header */}
        <div className="flex items-center gap-3 relative z-10">
          <span className="h-10 w-10 rounded-2xl bg-gradient-to-br from-primary via-emerald-600 to-teal-700 flex items-center justify-center text-white font-display font-black text-lg shadow-md">
            籤
          </span>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-black text-foreground font-display tracking-tight">
                Quẻ Xăm AI Cát Tường
              </h2>
              <span className="text-[10px] font-jp font-bold text-primary px-2 py-0.5 rounded-full bg-primary/10 border border-primary/20 flex items-center gap-1">
                <Wand2 className="h-3 w-3" />
                AI おみくじ
              </span>
            </div>
            <p className="text-xs text-muted-foreground">
              Chọn chủ đề yêu thích — AI sẽ gieo quẻ xăm độc nhất vô nhị mỗi ngày!
            </p>
          </div>
        </div>

        {/* Main Content Area */}
        <div className="mt-5 relative z-10">
          {!drawnResult ? (
            /* State 1: Choose Genre & Shake */
            <div className="space-y-4">
              {/* Genre Selector Pills */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-foreground flex items-center gap-1.5">
                  <Dices className="h-3.5 w-3.5 text-primary" />
                  <span>Chọn thể loại quẻ xăm bạn muốn rút:</span>
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  {OMIKUJI_GENRES.map((g) => {
                    const isSelected = selectedGenre === g.id;
                    return (
                      <button
                        key={g.id}
                        type="button"
                        onClick={() => {
                          soundFX.playSuikinkutsu();
                          setSelectedGenre(g.id);
                        }}
                        className={cn(
                          "p-2.5 rounded-xl border text-left transition-all flex flex-col justify-between gap-1",
                          isSelected
                            ? "bg-primary/15 border-primary shadow-sm ring-1 ring-primary/40"
                            : "bg-card/70 border-border/80 hover:bg-muted/70 hover:border-border"
                        )}
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-lg leading-none">{g.emoji}</span>
                          <span className="text-[9px] font-jp font-semibold text-primary">{g.kanji}</span>
                        </div>
                        <div>
                          <p className="text-xs font-bold text-foreground line-clamp-1">{g.name}</p>
                          <p className="text-[10px] text-muted-foreground line-clamp-1">{g.description}</p>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Shaking Cylindrical Box */}
              <div className="py-4 flex flex-col items-center justify-center text-center space-y-3">
                <div
                  className={cn(
                    "w-24 h-32 rounded-2xl border-2 border-kintsugi-400/50 bg-gradient-to-b from-card via-kintsugi-50/10 to-amber-500/10 shadow-kintsugi flex flex-col items-center justify-between p-3 transition-transform duration-200",
                    shaking && "animate-bounce"
                  )}
                >
                  <span className="text-[10px] font-bold font-display text-kintsugi-500">AI 御神籤</span>
                  <span className="text-3xl leading-none select-none">{aiGenerating ? "✨" : "⛩️"}</span>
                  <span className="text-[9px] font-bold text-muted-foreground">
                    {aiGenerating ? "AI ĐANG GIEO QUẺ..." : "LẮC ỐNG XĂM"}
                  </span>
                </div>

                {aiError && (
                  <div className="p-3 rounded-xl bg-destructive/15 border border-destructive/30 text-destructive text-xs text-center max-w-sm mx-auto">
                    {aiError}
                  </div>
                )}

                <Button
                  variant="primary"
                  size="lg"
                  onClick={handleDrawFortune}
                  disabled={shaking || aiGenerating}
                  className="gap-2 shadow-lg w-full sm:w-auto px-8 font-bold"
                >
                  <Sparkles className={cn("h-4 w-4", aiGenerating && "animate-spin")} />
                  <span>{aiGenerating ? "AI Đang Gieo Quẻ..." : "Rút Quẻ May Mắn"}</span>
                  <span className="text-xs font-jp opacity-90">引く</span>
                </Button>
              </div>
            </div>
          ) : (
            /* State 2: Drawn Result & Speaking Activation */
            <div className="space-y-4 animate-in fade-in zoom-in-95 duration-300">
              {/* Slip Card */}
              <div className="rounded-2xl border-2 border-primary/30 bg-card/90 washi-texture shadow-sumi p-5 relative overflow-hidden">
                {/* Header Rank */}
                <div className="flex items-center justify-between border-b border-border/80 pb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl font-display font-black text-primary tracking-wider">
                      {drawnResult.rank}
                    </span>
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs font-bold text-foreground block leading-none">
                          {drawnResult.rankName}
                        </span>
                        {drawnResult.isAiGenerated && (
                          <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-primary/10 text-primary border border-primary/20 flex items-center gap-0.5">
                            <Bot className="h-2.5 w-2.5" /> AI Genre
                          </span>
                        )}
                      </div>
                      <span className="text-[10px] text-muted-foreground">
                        Thể loại: {OMIKUJI_GENRES.find((g) => g.id === drawnResult.genre)?.name}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500/15 border border-amber-500/30 text-amber-600 font-extrabold text-xs">
                    <Award className="h-3.5 w-3.5" />
                    <span>+{drawnResult.bonusXp} XP</span>
                  </div>
                </div>

                {/* Quote Content */}
                <div className="py-3.5 space-y-2">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h4 className="text-lg sm:text-xl font-display font-black text-foreground tracking-wide leading-snug">
                        {drawnResult.quote.japanese}
                      </h4>
                      <p className="text-xs font-jp text-primary/80 font-medium mt-1">
                        {drawnResult.quote.reading}
                      </p>
                    </div>

                    <button
                      onClick={handleSpeakQuote}
                      disabled={isPlayingAudio}
                      className="h-9 w-9 rounded-xl bg-primary/10 hover:bg-primary/20 border border-primary/20 flex items-center justify-center text-primary transition-colors shrink-0 shadow-sm"
                      title="Nghe phát âm chuẩn"
                    >
                      <Volume2 className={cn("h-4 w-4", isPlayingAudio && "animate-pulse")} />
                    </button>
                  </div>

                  <div className="rounded-xl bg-muted/60 p-2.5 text-xs space-y-1 border border-border/50">
                    <p className="font-bold text-foreground flex items-center gap-1">
                      <span>Ý nghĩa:</span>
                      <span className="text-primary font-semibold">{drawnResult.quote.vietnamese}</span>
                    </p>
                    <p className="text-muted-foreground leading-relaxed text-[11px]">
                      {drawnResult.quote.meaning}
                    </p>
                  </div>
                </div>

                {/* Hanko Claim Badge Stamp */}
                {drawnResult.claimed && (
                  <div className="absolute right-4 bottom-4 z-20 animate-in zoom-in-75 duration-200">
                    <HankoStamp text="大願" subtext="Đã nhận" variant="primary" size="md" />
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2.5 pt-1">
                <Button
                  variant="outline"
                  size="md"
                  onClick={handleSpeakQuote}
                  className="flex-1 text-xs font-semibold gap-1.5"
                >
                  <Volume2 className="h-4 w-4 text-primary" />
                  Nghe mẫu
                </Button>

                {!drawnResult.claimed ? (
                  <Button
                    variant="primary"
                    size="md"
                    onClick={handleClaimReward}
                    className="flex-[1.4] text-xs font-bold gap-1.5 shadow-md"
                  >
                    <Sparkles className="h-4 w-4" />
                    Đọc to & Nhận +{drawnResult.bonusXp} XP
                  </Button>
                ) : (
                  <div className="flex-[1.4] flex items-center justify-center gap-1.5 px-3 py-2.5 rounded-xl bg-matcha-500/15 border border-matcha-500/30 text-matcha-600 font-bold text-xs">
                    <CheckCircle2 className="h-4 w-4" />
                    Đã kích hoạt vận may hôm nay!
                  </div>
                )}
              </div>

              {/* Redraw Option with other genres */}
              <div className="text-center pt-1">
                <button
                  type="button"
                  onClick={() => setDrawnResult(null)}
                  className="text-[11px] text-muted-foreground hover:text-primary transition-colors inline-flex items-center gap-1 font-semibold"
                >
                  <RefreshCw className="h-3 w-3" />
                  Muốn thử gieo quẻ thể loại khác? Bấm vào đây
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

