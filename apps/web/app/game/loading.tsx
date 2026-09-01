import React from "react";
import { ZenLoadingState } from "@/components/ui/zen-loading-state";

export default function GameLoading() {
  return (
    <ZenLoadingState
      variant="studio"
      title="Đang vào Đạo trường (Dojo Arena)..."
      ja="道場準備中..."
      description="Hệ thống đang nạp thông số Nhân vật, Kỹ năng và các Trùm thử thách..."
    />
  );
}
