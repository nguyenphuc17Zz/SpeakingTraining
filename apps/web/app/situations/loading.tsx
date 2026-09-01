import React from "react";
import { ZenLoadingState } from "@/components/ui/zen-loading-state";

export default function SituationsLoading() {
  return (
    <ZenLoadingState
      variant="studio"
      title="Đang chuẩn bị phòng Luyện Tình Huống (Situations Studio)..."
      ja="場面別ロールプレイ準備中..."
      description="AI đang khởi tạo bối cảnh giao tiếp thực chiến và thiết lập đối tác AI..."
    />
  );
}
