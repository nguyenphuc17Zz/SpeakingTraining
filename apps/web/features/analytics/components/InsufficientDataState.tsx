"use client";

import React from "react";
import Link from "next/link";
import { Mic, ArrowRight, ShieldAlert } from "lucide-react";

interface InsufficientDataStateProps {
  neededCount?: number;
  metricName?: string;
}

export const InsufficientDataState: React.FC<InsufficientDataStateProps> = ({
  neededCount = 3,
  metricName = "kỹ năng này",
}) => {
  return (
    <div className="p-8 rounded-3xl bg-card/60 border border-dashed border-border text-center space-y-4 max-w-md mx-auto">
      <div className="w-12 h-12 rounded-2xl bg-muted text-muted-foreground flex items-center justify-center mx-auto">
        <ShieldAlert className="w-6 h-6 text-amber-400" />
      </div>

      <div className="space-y-1">
        <h4 className="text-sm font-bold text-foreground">Chưa đủ dữ liệu để tính xu hướng</h4>
        <p className="text-xs text-muted-foreground leading-relaxed">
          Hệ thống cần tối thiểu <strong>{neededCount} buổi luyện tập</strong> tương đương để phân tích chính xác {metricName}.
        </p>
      </div>

      <Link href="/speaking">
        <button className="py-2.5 px-5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold inline-flex items-center gap-2 shadow-lg shadow-rose-600/20 transition-all">
          <Mic className="w-4 h-4" />
          <span>Bắt đầu buổi nói ngay</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </Link>
    </div>
  );
};
