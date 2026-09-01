import React from "react";
import { ZenLoadingState } from "@/components/ui/zen-loading-state";

export default function RampLoading() {
  return (
    <ZenLoadingState
      variant="studio"
      title="Đang chuẩn bị phòng Phục Hồi Phát Ngôn (Mode 6)..."
      ja="アウトプット・リハビリ準備中..."
      description="Hệ thống đang nạp nấc thang 11 cấp độ và chuẩn bị giàn giáo AI..."
    />
  );
}
