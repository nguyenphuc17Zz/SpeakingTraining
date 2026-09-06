"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Zap, Sparkles, Timer, ShieldCheck, ArrowRight, Gauge } from "lucide-react";
import { getReflexStats, ReflexStats } from "@/features/reflex";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { soundFX } from "@/lib/sound-fx";

interface ReflexEloFlowCardProps {
  period?: string;
}

export const ReflexEloFlowCard: React.FC<ReflexEloFlowCardProps> = ({ period = "30d" }) => {
  const [stats, setStats] = useState<ReflexStats | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    let isMounted = true;
    async function loadStats() {
      try {
        setLoading(true);
        const data = await getReflexStats(period);
        if (isMounted) setStats(data);
      } catch (err) {
        console.warn("Failed to load reflex stats for flow card:", err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadStats();
    return () => {
      isMounted = false;
    };
  }, [period]);

  const elo = stats?.reflex_elo_rating ?? 1200;
  const flowState = stats?.cognitive_flow_state || "insufficient_data";
  const targetTimer = stats?.target_timer_ms ?? 3000;
  const accuracyPct = Math.round((stats?.accuracy_rate ?? 0) * 100);

  // Determine Japanese Swordsman Rank based on Elo
  const getRankInfo = (rating: number) => {
    if (rating >= 1900) return { title: "Kiếm hào", kanji: "剣豪", color: "text-amber-400 border-amber-500/30 bg-amber-500/10" };
    if (rating >= 1600) return { title: "Cao thủ", kanji: "達人", color: "text-indigo-400 border-indigo-500/30 bg-indigo-500/10" };
    if (rating >= 1300) return { title: "Chiến binh", kanji: "武者", color: "text-emerald-400 border-emerald-500/30 bg-emerald-500/10" };
    if (rating >= 1000) return { title: "Kiếm sinh", kanji: "剣生", color: "text-sky-400 border-sky-500/30 bg-sky-500/10" };
    return { title: "Tập sự", kanji: "見習い", color: "text-muted-foreground border-border bg-muted/40" };
  };

  // Determine Flow State Badge
  const getFlowStateBadge = (state: string) => {
    switch (state) {
      case "flow":
        return {
          label: "🌊 Trạng thái Dòng chảy (Flow Zone)",
          badgeVariant: "matcha" as const,
          desc: "Tỷ lệ chuẩn xác 70–85%, thời gian thử thách tối ưu cho việc hình thành phản xạ vô điều kiện.",
        };
      case "comfort_plateau":
        return {
          label: "🛡️ Vùng an toàn (Comfort Plateau)",
          badgeVariant: "sakura" as const,
          desc: "Độ chính xác cao & phản xạ nhanh. Bạn đã sẵn sàng nâng cấp lên bậc áp lực thời gian cao hơn!",
        };
      case "cognitive_overload":
        return {
          label: "⚡ Quá tải nhận thức (Overload)",
          badgeVariant: "akane" as const,
          desc: "Tốc độ hiện tại đang gây áp lực quá lớn. Hệ thống khuyến nghị mở rộng timer để lấy lại nhịp.",
        };
      case "speed_inaccuracy_trap":
        return {
          label: "⚠️ Bẫy đoán mò (Inaccuracy Trap)",
          badgeVariant: "akane" as const,
          desc: "Phản xạ rất nhanh nhưng độ chuẩn xác thấp. Cần chậm lại 0.5s để tái củng cố phát âm chuẩn.",
        };
      case "reaction_hesitation":
        return {
          label: "⏳ Ngập ngừng (Hesitation)",
          badgeVariant: "matcha" as const,
          desc: "Độ chính xác tốt nhưng độ trễ còn sát giờ. Hãy duy trì mức này để rèn luyện tính tự động hóa.",
        };
      default:
        return {
          label: "🌱 Khởi động (Calibrating)",
          badgeVariant: "default" as const,
          desc: "Hãy luyện tập thêm từ 5–8 lượt phản xạ để thuật toán IRT tính toán Flow Zone chính xác.",
        };
    }
  };

  const rank = getRankInfo(elo);
  const flow = getFlowStateBadge(flowState);

  return (
    <div className="relative overflow-hidden rounded-3xl border border-border bg-card p-5 md:p-6 washi-texture shadow-sm space-y-4">
      {/* Decorative Glow */}
      <div className="absolute top-0 right-0 h-40 w-40 bg-primary/10 rounded-full blur-2xl pointer-events-none" />

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 relative z-10">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center shrink-0">
            <Zap className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-black text-foreground tracking-tight">
                Phản Xạ Thần Tốc & Flow Zone (瞬発・フロー)
              </h3>
              <span className={`text-[11px] font-bold px-2 py-0.5 rounded-lg border ${rank.color}`}>
                {rank.kanji} {rank.title}
              </span>
            </div>
            <p className="text-xs text-muted-foreground">
              Định vị năng lực phản xạ theo mô hình Item Response Theory & Elo Rating
            </p>
          </div>
        </div>

        <Badge variant={flow.badgeVariant} size="sm" className="font-bold self-start sm:self-auto">
          {flow.label}
        </Badge>
      </div>

      {/* Main Stats Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 relative z-10">
        {/* Elo Rating */}
        <div className="p-3.5 rounded-2xl bg-muted/40 border border-border/80 space-y-1">
          <span className="text-[11px] font-semibold text-muted-foreground flex items-center gap-1.5">
            <Gauge className="w-3.5 h-3.5 text-amber-400" />
            Reflex Elo Rating
          </span>
          <div className="text-xl md:text-2xl font-black text-foreground font-mono">
            {loading ? "..." : Math.round(elo)}
            <span className="text-xs font-normal text-muted-foreground ml-1">pts</span>
          </div>
          <p className="text-[10px] text-muted-foreground">Khởi điểm 1200 Elo</p>
        </div>

        {/* Target Reaction Timer */}
        <div className="p-3.5 rounded-2xl bg-muted/40 border border-border/80 space-y-1">
          <span className="text-[11px] font-semibold text-muted-foreground flex items-center gap-1.5">
            <Timer className="w-3.5 h-3.5 text-primary" />
            Timer Mục Tiêu (ZPD)
          </span>
          <div className="text-xl md:text-2xl font-black text-foreground font-mono">
            {loading ? "..." : `${(targetTimer / 1000).toFixed(2)}`}
            <span className="text-xs font-normal text-muted-foreground ml-1">giây</span>
          </div>
          <p className="text-[10px] text-muted-foreground">Khung: {stats?.comfort_window || "~3.0s"}</p>
        </div>

        {/* Accuracy Rate */}
        <div className="p-3.5 rounded-2xl bg-muted/40 border border-border/80 space-y-1">
          <span className="text-[11px] font-semibold text-muted-foreground flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            Độ Chính Xác
          </span>
          <div className="text-xl md:text-2xl font-black text-foreground font-mono">
            {loading ? "..." : `${accuracyPct}%`}
          </div>
          <p className="text-[10px] text-muted-foreground">{stats?.total_attempts ?? 0} lượt phản xạ</p>
        </div>

        {/* Avg Reaction */}
        <div className="p-3.5 rounded-2xl bg-muted/40 border border-border/80 space-y-1">
          <span className="text-[11px] font-semibold text-muted-foreground flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            Tốc Độ Trung Bình
          </span>
          <div className="text-xl md:text-2xl font-black text-foreground font-mono">
            {loading ? "..." : (stats?.avg_reaction_ms ? `${Math.round(stats.avg_reaction_ms)}ms` : "—")}
          </div>
          <p className="text-[10px] text-muted-foreground">P50: {stats?.p50_reaction_ms ? `${Math.round(stats.p50_reaction_ms)}ms` : "—"}</p>
        </div>
      </div>

      {/* Description & Action Footer */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1 border-t border-border/60 relative z-10">
        <p className="text-xs text-muted-foreground max-w-xl leading-relaxed">
          {flow.desc}
        </p>

        <Link href="/reflex" onClick={() => soundFX.playTaiko()}>
          <Button variant="akane" size="sm" className="rounded-xl gap-1.5 font-bold shadow-xs shrink-0 w-full sm:w-auto">
            <span>Vào Đấu Trường Phản Xạ</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Button>
        </Link>
      </div>
    </div>
  );
};
