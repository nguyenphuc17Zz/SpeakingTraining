"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useAnalyticsDashboard } from "@/features/analytics/hooks/useAnalyticsDashboard";
import {
  MetricCard,
  BottleneckCard,
  InsightFeed,
  GoalProgressCard,
  PracticeDistributionChart,
  SenseiDiagnosticCard,
  FourPillarsRadarCard,
} from "@/features/analytics";
import { MetricValueDTO } from "@/features/analytics/types/analytics";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  TrendingUp,
  Sparkles,
  Calendar,
  RefreshCw,
  Target,
  Mic,
  MessageSquare,
  ArrowRight,
  Shield,
  Lightbulb,
  Sliders,
} from "lucide-react";
import { soundFX } from "@/lib/sound-fx";

export default function ProgressDashboardPage() {
  const [period, setPeriod] = useState("30d");
  const [activeTab, setActiveTab] = useState<string>("all");
  const { dashboard, loading, error, refetch } = useAnalyticsDashboard(period);
  const [diagnostic, setDiagnostic] = useState<any>(null);
  const [diagnosticLoading, setDiagnosticLoading] = useState<boolean>(true);

  const fetchDiagnostic = async () => {
    try {
      setDiagnosticLoading(true);
      const res = await fetch(`http://localhost:8000/api/v1/analytics/diagnostic?period=${period}`);
      if (res.ok) {
        const data = await res.json();
        setDiagnostic(data);
      }
    } catch (e) {
      console.warn("Failed to fetch diagnostic:", e);
    } finally {
      setDiagnosticLoading(false);
    }
  };

  useEffect(() => {
    fetchDiagnostic();
  }, [period]);

  const metrics = dashboard?.metrics || {};

  // Group metrics by categories
  const reflexKeys = ["reflex_reaction_latency", "reflex_accuracy", "reflex_automaticity", "reflex_timeout_rate"];
  const keigoKeys = ["keigo_accuracy", "keigo_naturalness", "keigo_context_fit", "keigo_double_keigo_rate"];
  const pronKeys = ["pronunciation_overall", "pitch_accuracy", "mora_timing", "intonation"];
  const convKeys = ["fluency", "naturalness", "grammar_accuracy", "vocabulary", "response_speed", "filler_rate"];

  const filteredMetrics = Object.entries(metrics).filter(([key]) => {
    if (activeTab === "all") return true;
    if (activeTab === "reflex") return reflexKeys.includes(key);
    if (activeTab === "keigo") return keigoKeys.includes(key);
    if (activeTab === "pitch") return pronKeys.includes(key);
    if (activeTab === "conversation") return convKeys.includes(key);
    return true;
  });

  return (
    <div className="space-y-8 animate-in fade-in duration-300 max-w-6xl mx-auto pb-16">
      {/* 1. Top Header Haru Washi */}
      <div className="relative overflow-hidden rounded-3xl border border-border bg-card p-6 md:p-8 washi-texture shadow-sm space-y-4">
        <div className="absolute top-0 right-0 h-48 w-48 bg-primary/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 relative z-10">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Badge variant="matcha" size="sm" className="font-bold">
                EVIDENCE-BASED SPEAKING ANALYTICS
              </Badge>
              <span className="text-xs text-muted-foreground font-semibold">
                Chẩn Đoán & Tiến Độ Học Tập Động
              </span>
            </div>
            <h1 className="text-2xl md:text-3xl font-black text-foreground tracking-tight flex items-center gap-3">
              <span className="p-2 rounded-2xl bg-primary/10 border border-primary/20 text-primary inline-flex">
                <TrendingUp className="h-6 w-6" />
              </span>
              <span>Phân Tích Tiến Độ Thực Tế (学習分析・診断)</span>
            </h1>
            <p className="text-xs md:text-sm text-muted-foreground max-w-2xl leading-relaxed">
              Toàn bộ chỉ số được tổng hợp trực tiếp từ lịch sử các bài tập tại 4 phòng luyện, giúp bạn theo dõi chính xác từng mili-giây phản xạ và độ chuẩn xác ngữ âm.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5 shrink-0 self-start lg:self-auto">
            {/* Period Selector */}
            <div className="flex items-center bg-muted/60 p-1 rounded-2xl border border-border/80 text-xs">
              {["7d", "14d", "30d", "90d"].map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => {
                    soundFX.playFurin();
                    setPeriod(p);
                  }}
                  className={`px-3 py-1.5 rounded-xl font-bold transition-all ${
                    period === p
                      ? "bg-primary text-primary-foreground shadow-xs"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                soundFX.playFurin();
                refetch();
                fetchDiagnostic();
              }}
              className="h-10 w-10 p-0 rounded-2xl border-border"
              title="Làm mới dữ liệu"
            >
              <RefreshCw className={`h-4 w-4 ${loading || diagnosticLoading ? "animate-spin text-primary" : ""}`} />
            </Button>
          </div>
        </div>
      </div>

      {/* 2. Sensei 360 Diagnostic Report */}
      <SenseiDiagnosticCard diagnostic={diagnostic} loading={diagnosticLoading} />

      {/* 3. 4-Pillar Mastery Matrix */}
      <FourPillarsRadarCard pillars={diagnostic?.pillars} />

      {/* 4. Filter Tabs & Detailed Metrics Grid */}
      <div className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Sliders className="h-4 w-4 text-primary" />
            <h3 className="text-sm font-bold text-foreground">
              Bảng Chỉ Số Chi Tiết (22+ Realtime Metrics)
            </h3>
          </div>

          {/* Metric Category Filter Pills */}
          <div className="flex flex-wrap gap-1.5">
            {[
              { id: "all", label: "Tất Cả" },
              { id: "reflex", label: "⚡ Phản Xạ" },
              { id: "keigo", label: "👑 Kính Ngữ" },
              { id: "pitch", label: "🎵 Cao Độ & Phách" },
              { id: "conversation", label: "🗣️ Hội Thoại" },
            ].map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => {
                  soundFX.playFurin();
                  setActiveTab(tab.id);
                }}
                className={`px-3 py-1 rounded-xl text-xs font-semibold border transition-all ${
                  activeTab === tab.id
                    ? "bg-primary text-primary-foreground border-primary shadow-xs"
                    : "bg-muted/40 border-border text-muted-foreground hover:text-foreground"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
          {filteredMetrics.map(([key, mv]) => (
            <MetricCard key={key} metric={mv} />
          ))}
        </div>
      </div>

      {/* 5. Bottom Insights & Goal Progress */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <InsightFeed insights={dashboard?.top_insights || []} />
          {dashboard?.practice_distribution && (
            <PracticeDistributionChart distribution={dashboard.practice_distribution} />
          )}
        </div>

        <div className="space-y-6">
          {dashboard?.bottleneck && <BottleneckCard bottleneck={dashboard.bottleneck} />}
          {(dashboard?.goals || []).map((g) => (
            <GoalProgressCard key={g.goal_id} goal={g} />
          ))}
        </div>
      </div>
    </div>
  );
}
