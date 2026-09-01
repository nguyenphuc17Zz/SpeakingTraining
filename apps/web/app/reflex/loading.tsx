import React from "react";
import { ZenLoadingState } from "@/components/ui/zen-loading-state";

export default function ReflexLoading() {
  return (
    <ZenLoadingState
      variant="studio"
      title="Đang chuẩn bị phòng Phản Xạ Nhanh (Reflex Studio)..."
      ja="瞬発スピーキング準備中..."
      description="Hệ thống đang chuẩn bị bộ đếm thời gian 2 giây và chuỗi phản xạ tức thì..."
    />
  );
}
