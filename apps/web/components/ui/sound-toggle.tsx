"use client";

import React, { useState, useEffect } from "react";
import { Volume2, VolumeX } from "lucide-react";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

export function SoundToggle() {
  const [enabled, setEnabled] = useState(true);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    setEnabled(soundFX.getSoundEnabled());
  }, []);

  const handleToggle = () => {
    const nextState = soundFX.toggleMute();
    setEnabled(nextState);
    if (nextState) {
      soundFX.playFurin();
    }
  };

  if (!mounted) {
    return (
      <div className="h-9 w-9 rounded-xl border border-border bg-muted/40 animate-pulse" />
    );
  }

  return (
    <button
      type="button"
      onClick={handleToggle}
      className={cn(
        "h-9 px-2.5 rounded-xl border transition-all flex items-center gap-1.5 shadow-xs",
        enabled
          ? "border-primary/30 bg-primary/10 text-primary hover:bg-primary/20 hover:border-primary/50"
          : "border-border bg-muted/60 text-muted-foreground hover:bg-muted hover:text-foreground"
      )}
      title={enabled ? "Âm thanh truyền thống (Taiko, Furin, Suikinkutsu): BẬT" : "Âm thanh hiệu ứng: TẮT"}
      aria-label={enabled ? "Tắt âm thanh hiệu ứng" : "Bật âm thanh hiệu ứng"}
    >
      {enabled ? (
        <>
          <Volume2 className="h-4 w-4 shrink-0 animate-in zoom-in-75 duration-150" />
          <span className="hidden xl:inline text-xs font-bold font-jp">音あり</span>
        </>
      ) : (
        <>
          <VolumeX className="h-4 w-4 shrink-0 opacity-70 animate-in zoom-in-75 duration-150" />
          <span className="hidden xl:inline text-xs font-bold font-jp text-muted-foreground">消音</span>
        </>
      )}
    </button>
  );
}
