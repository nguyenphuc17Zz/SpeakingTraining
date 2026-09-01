import React from "react";
import { ZenLoadingState } from "@/components/ui/zen-loading-state";

export default function PitchLoading() {
  return (
    <ZenLoadingState
      variant="studio"
      title="Đang chuẩn bị phòng Cao Độ Ngữ Điệu (Pitch Studio)..."
      ja="ピッチ・アクセント準備中..."
      description="Hệ thống đang nạp biểu đồ cao độ âm thanh và mẫu đường sóng âm chuẩn Tokyo..."
    />
  );
}
