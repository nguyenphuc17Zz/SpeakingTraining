import React from "react";
import { ZenLoadingState } from "@/components/ui/zen-loading-state";

export default function ProfileLoading() {
  return (
    <ZenLoadingState
      variant="card"
      title="Đang nạp Hồ Sơ Học Tập (Bệnh án tiếng Nhật)..."
      ja="カルテ読み込み中..."
      description="Hệ thống đang tải phân tích điểm mạnh, điểm nghẽn và thói quen phát ngôn..."
    />
  );
}
