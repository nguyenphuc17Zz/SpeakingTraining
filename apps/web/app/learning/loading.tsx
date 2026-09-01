import React from "react";
import { ZenLoadingState } from "@/components/ui/zen-loading-state";

export default function LearningLoading() {
  return (
    <ZenLoadingState
      variant="studio"
      title="Đang nạp Lộ Trình Học Cá Nhân Hóa..."
      ja="学習ロードマップ準備中..."
      description="AI đang đồng bộ bài học đề xuất theo trình độ và mục tiêu của bạn..."
    />
  );
}
