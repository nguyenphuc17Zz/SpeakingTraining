"use client";

import React, { useState } from "react";
import { Volume2, Loader2, Check, Sparkles, Star } from "lucide-react";
import { Button } from "@/components/ui/button";
import { VoiceProfile } from "@/types/audio";
import { useTTS } from "../hooks/useTTS";
import { getVoiceCharacterMeta } from "../services/voice-meta";

interface VoicePreviewProps {
  voice: VoiceProfile;
  sampleText?: string;
  speed?: number;
  pitch?: number;
  isSelected?: boolean;
  isDefault?: boolean;
  onSelect?: () => void;
  onSetDefault?: () => void;
  className?: string;
}

export function VoicePreview({
  voice,
  sampleText = "こんにちは！今日も一緒に楽しく日本語を練習しましょう。",
  speed = 1.0,
  pitch = 0.0,
  isSelected = false,
  isDefault = false,
  onSelect,
  onSetDefault,
  className = "",
}: VoicePreviewProps) {
  const { isGenerating, isPlaying, previewVoice, stop } = useTTS();
  const meta = getVoiceCharacterMeta(voice);

  const handlePreview = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (isPlaying) {
      stop();
    } else {
      previewVoice(sampleText, voice.voice_id, voice.provider, speed, pitch, voice.style || undefined);
    }
  };

  const handleSetDefaultClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onSetDefault?.();
  };

  return (
    <div
      onClick={onSelect}
      className={`group relative p-4 rounded-2xl border transition-all duration-200 cursor-pointer select-none flex flex-col justify-between ${
        isSelected
          ? "bg-card border-primary shadow-md shadow-primary/10 ring-2 ring-primary/30"
          : "bg-card/70 border-border hover:bg-card hover:border-border/80 hover:shadow-sm"
      } ${className}`}
    >
      {/* Top row: Avatar & Identity & Action button */}
      <div>
        <div className="flex items-start justify-between gap-2.5">
          <div className="flex items-center gap-3 min-w-0">
            {/* Avatar Letter / Kanji */}
            <div
              className={`w-11 h-11 rounded-2xl bg-gradient-to-br ${meta.gradient} flex items-center justify-center font-bold text-white text-base shadow-sm shrink-0 font-jp`}
            >
              {meta.avatarLetter}
            </div>

            <div className="min-w-0">
              <div className="flex items-center gap-1.5 flex-wrap">
                <h4 className="font-bold text-foreground text-sm truncate font-jp">{voice.name}</h4>
                {isDefault && (
                  <span className="inline-flex items-center gap-0.5 px-2 py-0.5 rounded-md text-[10px] font-medium bg-amber-500/15 text-amber-600 dark:text-amber-300 border border-amber-500/30">
                    <Star className="h-2.5 w-2.5 fill-current" />
                    Giọng chính
                  </span>
                )}
              </div>

              <div className="flex items-center gap-1.5 mt-0.5 flex-wrap">
                <span className={`px-1.5 py-0.2 rounded text-[10px] border font-medium ${meta.badgeClass}`}>
                  {meta.genderLabel}
                </span>
                <span className="text-[11px] text-muted-foreground truncate">
                  {meta.vibeLabel}
                </span>
              </div>
            </div>
          </div>

          {/* Quick Play Audio Button */}
          <div className="flex items-center gap-1.5 shrink-0">
            <Button
              size="sm"
              variant={isPlaying ? "primary" : "outline"}
              onClick={handlePreview}
              disabled={isGenerating}
              className={`h-9 px-3 rounded-xl gap-1.5 text-xs font-semibold ${
                isPlaying ? "bg-primary hover:bg-primary/90 text-primary-foreground animate-pulse" : ""
              }`}
              title="Nghe thử giọng mẫu"
            >
              {isGenerating ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin text-primary" />
              ) : isPlaying ? (
                <>
                  {/* Waveform mini bars */}
                  <span className="flex items-end gap-0.5 h-3">
                    <span className="w-0.5 bg-white h-2 animate-bounce" style={{ animationDelay: "0ms" }} />
                    <span className="w-0.5 bg-white h-3 animate-bounce" style={{ animationDelay: "150ms" }} />
                    <span className="w-0.5 bg-white h-1.5 animate-bounce" style={{ animationDelay: "300ms" }} />
                  </span>
                  <span className="text-[11px]">Dừng</span>
                </>
              ) : (
                <>
                  <Volume2 className="h-3.5 w-3.5 text-primary" />
                  <span className="text-[11px] hidden sm:inline">Nghe thử</span>
                </>
              )}
            </Button>
          </div>
        </div>

        {/* Short description / vibe */}
        <p className="text-xs text-muted-foreground mt-2.5 line-clamp-2 leading-relaxed">
          {meta.descriptionVi}
        </p>
      </div>

      {/* Bottom row: Recommended badge & Select button */}
      <div className="pt-3 mt-3 border-t border-border/70 flex items-center justify-between gap-2 text-xs">
        <span className="text-[11px] text-muted-foreground flex items-center gap-1 truncate">
          <Sparkles className="h-3 w-3 text-amber-500 shrink-0" />
          <span className="truncate">{meta.recommendedFor}</span>
        </span>

        <div className="flex items-center gap-1 shrink-0">
          {isSelected ? (
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-primary/10 text-primary font-semibold text-[11px] border border-primary/20">
              <Check className="h-3.5 w-3.5" />
              Đang chọn
            </span>
          ) : (
            <button
              onClick={onSelect}
              className="text-[11px] font-medium text-muted-foreground hover:text-foreground px-2 py-1 rounded-lg hover:bg-muted transition-colors"
            >
              Chọn giọng
            </button>
          )}

          {!isDefault && onSetDefault && (
            <button
              onClick={handleSetDefaultClick}
              className="text-[11px] font-medium text-primary hover:text-primary/80 px-2 py-1 rounded-lg hover:bg-primary/10 transition-colors"
              title="Đặt làm giọng AI mặc định cho các buổi hội thoại"
            >
              Đặt mặc định
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
