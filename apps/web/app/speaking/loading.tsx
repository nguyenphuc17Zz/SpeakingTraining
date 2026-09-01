import React from "react";
import { ZenLoadingState } from "@/components/ui/zen-loading-state";

export default function SpeakingLoading() {
  return (
    <ZenLoadingState
      variant="studio"
      title="Đang chuẩn bị phòng Luyện Nói Tự Do..."
      ja="AI会話ルーム準備中..."
      description="Hệ thống đang nạp danh sách Đối tác AI, giọng đọc VOICEVOX và phòng thu âm..."
    />
  );
}
