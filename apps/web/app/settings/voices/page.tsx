"use client";

import React from "react";
import Link from "next/link";
import { ArrowLeft, Volume2, Sparkles } from "lucide-react";
import { VoiceSettingsHub } from "@/components/settings/voice-settings-hub";

export default function VoiceLibraryPage() {
  return (
    <div className="max-w-6xl mx-auto space-y-6 animate-in fade-in duration-200">
      {/* Top Breadcrumbs / Back Navigation */}
      <div className="flex items-center justify-between pb-3 border-b border-border">
        <div className="flex items-center gap-3">
          <Link
            href="/settings"
            className="p-2 rounded-xl bg-card border border-border text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div>
            <h1 className="text-xl font-bold text-foreground flex items-center gap-2">
              <Volume2 className="h-5 w-5 text-primary" />
              Studio Giọng Nói & Âm Thanh <span className="font-jp text-sm font-normal text-muted-foreground">音声スタジオ</span>
            </h1>
            <p className="text-xs text-muted-foreground mt-0.5">
              Khám phá các giọng đọc Nhật Bản biểu cảm, nghe thử câu mẫu và cá nhân hóa giọng AI.
            </p>
          </div>
        </div>
      </div>

      {/* Main Unified Voice Hub */}
      <VoiceSettingsHub />
    </div>
  );
}
