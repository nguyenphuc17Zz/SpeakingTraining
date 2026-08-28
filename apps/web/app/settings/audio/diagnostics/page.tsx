"use client";

import React from "react";
import Link from "next/link";
import { ArrowLeft, Activity } from "lucide-react";
import { AudioDiagnosticsCard } from "@/features/audio/components/AudioDiagnosticsCard";

export default function AudioDiagnosticsPage() {
  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in duration-200">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-border">
        <div className="flex items-center gap-3">
          <Link
            href="/settings/audio"
            className="p-2 rounded-xl bg-card border border-border text-muted-foreground hover:text-foreground hover:bg-muted"
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div>
            <h1 className="text-xl font-bold text-foreground flex items-center gap-2">
              <Activity className="h-5 w-5 text-indigo-400" />
              Audio System Diagnostics & Latency Monitor
            </h1>
            <p className="text-xs text-muted-foreground mt-0.5">
              Kiểm tra tình trạng hoạt động thực tế, độ trễ và bộ nhớ đệm âm thanh của toàn hệ thống.
            </p>
          </div>
        </div>
      </div>

      <AudioDiagnosticsCard />
    </div>
  );
}
