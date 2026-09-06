"use client";

import React, { useState, useEffect } from "react";
import {
  Volume2,
  Play,
  Square,
  Check,
  CheckCircle2,
  Sparkles,
  Sliders,
  RefreshCw,
  Cpu,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import {
  getJapaneseWebVoices,
  getPreferredJapaneseVoice,
  getPreferredVoiceURI,
  setPreferredJapaneseVoice,
  speakJapaneseText,
  stopWebSpeech,
} from "@/features/speaking/services/web-speech";
import { soundFX } from "@/lib/sound-fx";

const SAMPLE_SENTENCES = [
  {
    title: "Chào hỏi & Giới thiệu",
    text: "こんにちは！今日も一緒に楽しく日本語を話しましょう。",
  },
  {
    title: "Kính ngữ thương mại",
    text: "お忙しいところ恐れ入りますが、ご確認のほどよろしくお願い申し上げます。",
  },
  {
    title: "Phản xạ thường ngày",
    text: "今週末は友達と京都へ旅行に行く予定です。とても楽しみにしています。",
  },
  {
    title: "Hỏi đường & Du lịch",
    text: "すみません、一番近い駅へ行く道を教えていただけますか？",
  },
];

export function WebSpeechStudioCard() {
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [selectedURI, setSelectedURI] = useState<string>("");
  const [preferredURI, setPreferredURI] = useState<string>("");
  const [sampleIdx, setSampleIdx] = useState(0);
  const [customText, setCustomText] = useState("");
  const [rate, setRate] = useState(1.0);
  const [pitch, setPitch] = useState(1.0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  const refreshVoiceList = () => {
    const list = getJapaneseWebVoices();
    setVoices(list);

    const saved = getPreferredVoiceURI();
    if (saved) {
      setPreferredURI(saved);
      setSelectedURI((prev) => prev || saved);
    } else {
      const best = getPreferredJapaneseVoice();
      if (best) {
        setPreferredURI(best.voiceURI);
        setSelectedURI((prev) => prev || best.voiceURI);
      }
    }
  };

  useEffect(() => {
    refreshVoiceList();

    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.onvoiceschanged = () => {
        refreshVoiceList();
      };
    }
  }, []);

  const activeText = customText.trim() || SAMPLE_SENTENCES[sampleIdx].text;

  const handlePreview = () => {
    if (isPlaying) {
      stopWebSpeech();
      setIsPlaying(false);
      return;
    }

    setIsPlaying(true);
    soundFX.playFurin();

    speakJapaneseText(activeText, {
      voiceURI: selectedURI,
      rate,
      pitch,
      onEnd: () => setIsPlaying(false),
      onError: () => setIsPlaying(false),
    });
  };

  const handleSetDefault = () => {
    if (!selectedURI) return;
    setPreferredJapaneseVoice(selectedURI);
    setPreferredURI(selectedURI);
    soundFX.playTaiko();
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
  };

  const getVoiceOrigin = (v: SpeechSynthesisVoice) => {
    const n = v.name.toLowerCase();
    if (n.includes("microsoft")) return "Microsoft (Windows Native)";
    if (n.includes("google")) return "Google Chrome Engine";
    if (n.includes("apple") || n.includes("kyoko") || n.includes("otoya")) return "Apple macOS";
    return (v as any).localService ? "Offline System Voice" : "Web Speech Service";
  };

  return (
    <Card className="p-5 md:p-6 space-y-6 border border-border/80 bg-card washi-texture shadow-washi">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border/70 pb-4">
        <div className="flex items-center gap-3">
          <span className="h-10 w-10 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary shrink-0">
            <Volume2 className="h-5 w-5" />
          </span>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="text-base font-bold text-foreground">
                Web Speech Studio — Giọng Đọc Bản Địa Tiếng Nhật
              </h3>
              <Badge variant="outline" className="text-[10px] bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20">
                100% Offline • Độ trễ 0ms
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">
              Tận dụng giọng nói tiếng Nhật chất lượng cao tích hợp sẵn trên thiết bị của bạn (Haruka, Ayumi, Ichiro, Google 日本語...).
            </p>
          </div>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={refreshVoiceList}
          className="self-start sm:self-center text-xs h-8 gap-1.5 rounded-xl border-border"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          <span>Làm mới danh sách ({voices.length})</span>
        </Button>
      </div>

      {/* Voice Selection Grid */}
      <div className="space-y-3">
        <div className="flex items-center justify-between text-xs text-muted-foreground font-medium">
          <span>Chọn giọng đọc để nghe thử & tùy biến:</span>
          <span>Phát hiện <strong>{voices.length}</strong> giọng tiếng Nhật</span>
        </div>

        {voices.length === 0 ? (
          <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-700 dark:text-amber-300">
            Đang tải danh sách giọng nói tiếng Nhật từ trình duyệt... Nếu chưa xuất hiện, hãy nhấn nút Làm mới danh sách phía trên.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {voices.map((v) => {
              const isSelected = selectedURI === v.voiceURI;
              const isDefault = preferredURI === v.voiceURI;
              const origin = getVoiceOrigin(v);

              return (
                <div
                  key={v.voiceURI}
                  onClick={() => setSelectedURI(v.voiceURI)}
                  className={cn(
                    "p-3.5 rounded-2xl border transition-all cursor-pointer relative flex flex-col justify-between gap-2 group",
                    isSelected
                      ? "border-primary bg-primary/5 ring-1 ring-primary/30 shadow-xs"
                      : "border-border hover:border-border/80 hover:bg-muted/40",
                    isDefault && "bg-card shadow-xs"
                  )}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="space-y-0.5 min-w-0 flex-1">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="font-bold text-xs text-foreground truncate block">
                          {v.name.replace(" - Japanese (Japan)", "").replace("Japanese", "")}
                        </span>
                        {isDefault && (
                          <Badge variant="default" className="text-[9px] py-0 px-1.5 h-4 bg-primary text-primary-foreground font-mono">
                            Mặc định
                          </Badge>
                        )}
                      </div>
                      <p className="text-[10px] text-muted-foreground truncate">{origin}</p>
                    </div>

                    <div
                      className={cn(
                        "h-5 w-5 rounded-full border flex items-center justify-center shrink-0 transition-colors",
                        isSelected
                          ? "border-primary bg-primary text-primary-foreground"
                          : "border-border/80 group-hover:border-primary/50"
                      )}
                    >
                      {isSelected && <Check className="h-3 w-3" />}
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-[10px] text-muted-foreground pt-1 border-t border-border/40 font-mono">
                    <span>Lang: {v.lang}</span>
                    <span className="text-emerald-500 font-semibold">Ready</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Audition & Fine-Tuning Box */}
      <div className="p-4 rounded-2xl border border-border/80 bg-muted/20 space-y-4">
        <div className="flex items-center gap-2 text-xs font-bold text-foreground">
          <Sliders className="h-4 w-4 text-primary" />
          <span>Thử nghiệm & Tinh chỉnh Giọng nói</span>
        </div>

        {/* Sentence Selection */}
        <div className="space-y-2">
          <label className="text-xs text-muted-foreground block font-medium">
            Chọn câu mẫu để phát thử:
          </label>
          <div className="flex flex-wrap gap-2">
            {SAMPLE_SENTENCES.map((s, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => {
                  setSampleIdx(idx);
                  setCustomText("");
                }}
                className={cn(
                  "px-3 py-1.5 rounded-xl border text-xs font-medium transition-all",
                  sampleIdx === idx && !customText
                    ? "bg-primary/15 border-primary/40 text-primary font-bold shadow-xs"
                    : "bg-card border-border hover:bg-muted text-muted-foreground"
                )}
              >
                {s.title}
              </button>
            ))}
          </div>

          <div className="mt-2">
            <input
              type="text"
              value={customText}
              onChange={(e) => setCustomText(e.target.value)}
              placeholder="Hoặc gõ câu tiếng Nhật bất kỳ để nghe thử... (例: お名前は何とおっしゃいますか？)"
              className="w-full text-xs font-jp p-2.5 rounded-xl border border-border bg-card focus:outline-none focus:ring-1 focus:ring-primary/50 text-foreground placeholder:text-muted-foreground/60"
            />
          </div>
        </div>

        {/* Sliders: Rate & Pitch */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>Tốc độ đọc (Speed Rate)</span>
              <span className="font-mono font-bold text-foreground">{rate.toFixed(2)}x</span>
            </div>
            <input
              type="range"
              min="0.75"
              max="1.25"
              step="0.05"
              value={rate}
              onChange={(e) => setRate(parseFloat(e.target.value))}
              className="w-full accent-primary h-1.5 bg-border rounded-lg cursor-pointer"
            />
            <div className="flex justify-between text-[9px] text-muted-foreground/80 font-mono">
              <span>0.75x (Chậm)</span>
              <span>1.0x (Tự nhiên)</span>
              <span>1.25x (Nhanh)</span>
            </div>
          </div>

          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>Cao độ giọng (Pitch)</span>
              <span className="font-mono font-bold text-foreground">{pitch.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0.85"
              max="1.15"
              step="0.05"
              value={pitch}
              onChange={(e) => setPitch(parseFloat(e.target.value))}
              className="w-full accent-primary h-1.5 bg-border rounded-lg cursor-pointer"
            />
            <div className="flex justify-between text-[9px] text-muted-foreground/80 font-mono">
              <span>0.85 (Trầm)</span>
              <span>1.0 (Chuẩn)</span>
              <span>1.15 (Cao)</span>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-between gap-3 pt-2 border-t border-border/60 flex-wrap">
          <Button
            type="button"
            variant="primary"
            size="sm"
            onClick={handlePreview}
            disabled={!selectedURI}
            className="h-9 px-4 rounded-xl gap-2 font-bold text-xs"
          >
            {isPlaying ? (
              <>
                <Square className="h-3.5 w-3.5 fill-current" />
                <span>Dừng phát âm</span>
              </>
            ) : (
              <>
                <Play className="h-3.5 w-3.5 fill-current" />
                <span>Nghe thử câu mẫu</span>
              </>
            )}
          </Button>

          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleSetDefault}
            disabled={!selectedURI || preferredURI === selectedURI}
            className={cn(
              "h-9 px-4 rounded-xl gap-2 font-bold text-xs transition-all",
              savedSuccess && "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30"
            )}
          >
            {savedSuccess ? (
              <>
                <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                <span>Đã lưu làm mặc định!</span>
              </>
            ) : (
              <>
                <Sparkles className="h-3.5 w-3.5 text-primary" />
                <span>Đặt làm giọng mặc định toàn hệ thống</span>
              </>
            )}
          </Button>
        </div>
      </div>
    </Card>
  );
}
