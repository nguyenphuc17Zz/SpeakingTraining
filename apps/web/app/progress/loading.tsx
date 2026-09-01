import React from "react";
import { ZenLoadingState } from "@/components/ui/zen-loading-state";

export default function ProgressLoading() {
  return (
    <ZenLoadingState
      variant="studio"
      title="Đang phân tích Tiến Độ Học Tập & Radar Skills..."
      ja="進捗分析中..."
      description="Hệ thống đang tổng hợp dữ liệu phản xạ, chuỗi ngày học và điểm số phát âm..."
    />
  );
}
