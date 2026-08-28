"use client";

import React, { useState } from "react";
import { Headphones, X } from "lucide-react";

export function HeadphoneRecommendation() {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;

  return (
    <div className="flex items-center justify-between gap-3 px-3.5 py-2.5 rounded-xl bg-aizome-950/50 border border-aizome-500/30 text-xs text-aizome-200 animate-in fade-in shadow-sm">
      <div className="flex items-center gap-2.5">
        <Headphones className="h-4 w-4 text-aizome-400 shrink-0 animate-pulse" />
        <span>
          <strong className="font-semibold text-washi-100">Khuyến nghị đeo tai nghe:</strong> Đeo tai nghe giúp hệ thống tránh thu âm lại tiếng video từ loa, cho kết quả chấm phát âm và ngữ điệu chính xác nhất.
        </span>
      </div>
      <button
        onClick={() => setDismissed(true)}
        className="p-1 rounded-md text-aizome-400 hover:text-aizome-200 hover:bg-aizome-900/50 transition"
        aria-label="Dismiss"
      >
        <X className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}
