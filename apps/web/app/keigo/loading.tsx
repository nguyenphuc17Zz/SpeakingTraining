import React from "react";
import { ZenLoadingState } from "@/components/ui/zen-loading-state";

export default function KeigoLoading() {
  return (
    <ZenLoadingState
      variant="studio"
      title="Đang chuẩn bị phòng Luyện Kính Ngữ (Keigo Studio)..."
      ja="敬語トレーニング準備中..."
      description="Hệ thống đang nạp kho ngữ liệu Tôn kính ngữ, Khiêm nhường ngữ và chuẩn mực Uchi-Soto..."
    />
  );
}
