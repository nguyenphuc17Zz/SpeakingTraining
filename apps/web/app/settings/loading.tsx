import React from "react";
import { ZenLoadingState } from "@/components/ui/zen-loading-state";

export default function SettingsLoading() {
  return (
    <ZenLoadingState
      variant="card"
      title="Đang nạp Cài Đặt Hệ Thống & Âm Thanh..."
      ja="設定読み込み中..."
      description="Hệ thống đang kiểm tra trạng thái động cơ giọng đọc VOICEVOX và Micro..."
    />
  );
}
