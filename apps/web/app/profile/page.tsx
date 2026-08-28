"use client";

import React, { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { profileApi } from "@/services/profile-api";
import {
  LearnerMemory,
  LearnerMemoryDetail,
  LearnerProfile,
  LearningPriority,
  MemoryEvidence,
} from "@/types/profile";
import { SpeakingCertificateCard, FourSkillGaugesCard } from "@/features/profile";
import { coachCoreApi } from "@/features/coach/services/coachCoreApi";
import {
  Brain,
  TrendingUp,
  TrendingDown,
  Minus,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  Eye,
  XCircle,
  HelpCircle,
  Clock,
  Award,
  Zap,
  Target,
  ArrowRight,
  RotateCcw,
  Sliders,
} from "lucide-react";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";
import Link from "next/link";

export default function LearnerProfilePage() {
  const [profile, setProfile] = useState<LearnerProfile | null>(null);
  const [weaknesses, setWeaknesses] = useState<LearnerMemory[]>([]);
  const [strengths, setStrengths] = useState<LearnerMemory[]>([]);
  const [priorities, setPriorities] = useState<LearningPriority[]>([]);
  const [selectedMemory, setSelectedMemory] = useState<LearnerMemoryDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [recalculating, setRecalculating] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"weaknesses" | "strengths" | "priorities">("weaknesses");

  const loadData = async () => {
    try {
      setLoading(true);
      const [profData, weakData, strData, prioData] = await Promise.all([
        profileApi.getProfile(),
        profileApi.getTopWeaknesses(10),
        profileApi.getTopStrengths(10),
        profileApi.getLearningPriorities(5),
      ]);
      setProfile(profData);
      setWeaknesses(weakData);
      setStrengths(strData);
      setPriorities(prioData);
    } catch (err) {
      console.error("Failed to load learner profile:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRecalculate = async () => {
    try {
      setRecalculating(true);
      const updated = await profileApi.recalculateProfile();
      setProfile(updated);
      const [weakData, strData, prioData] = await Promise.all([
        profileApi.getTopWeaknesses(10),
        profileApi.getTopStrengths(10),
        profileApi.getLearningPriorities(5),
      ]);
      setWeaknesses(weakData);
      setStrengths(strData);
      setPriorities(prioData);
    } catch (err) {
      console.error("Failed to recalculate profile:", err);
    } finally {
      setRecalculating(false);
    }
  };

  const handleOpenEvidence = async (memoryId: string) => {
    try {
      setDetailLoading(true);
      const detail = await profileApi.getMemoryDetail(memoryId);
      setSelectedMemory(detail);
    } catch (err) {
      console.error("Failed to load memory detail:", err);
    } finally {
      setDetailLoading(false);
    }
  };

  const getTrendBadge = (trend: string, isRegression: boolean) => {
    if (isRegression) {
      return (
        <Badge variant="sakura" size="sm" className="gap-1 animate-pulse">
          <RotateCcw className="h-3 w-3" />
          <span>Tái phát (Regression)</span>
        </Badge>
      );
    }
    switch (trend) {
      case "improving":
        return (
          <Badge variant="matcha" size="sm" className="gap-1">
            <TrendingUp className="h-3 w-3 text-emerald-400" />
            <span>Đang tiến bộ</span>
          </Badge>
        );
      case "worsening":
        return (
          <Badge variant="sakura" size="sm" className="gap-1">
            <TrendingDown className="h-3 w-3 text-rose-400" />
            <span>Cần chú ý</span>
          </Badge>
        );
      case "resolved":
        return (
          <Badge variant="fuji" size="sm" className="gap-1">
            <CheckCircle2 className="h-3 w-3 text-indigo-400" />
            <span>Đã khắc phục</span>
          </Badge>
        );
      default:
        return (
          <Badge variant="outline" size="sm" className="gap-1 text-muted-foreground">
            <Minus className="h-3 w-3" />
            <span>Ổn định</span>
          </Badge>
        );
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300 max-w-6xl mx-auto pb-16">
      {/* 1. Speaking Certificate Card */}
      <SpeakingCertificateCard
        profile={profile}
        recalculating={recalculating}
        onRecalculate={handleRecalculate}
      />

      {/* 2. Four Skill Competency Gauges */}
      <FourSkillGaugesCard profile={profile} />

      {/* 3. Error Memory & Linguistic Strengths Intelligence */}
      <div className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-primary" />
            <h3 className="text-sm font-bold text-foreground">
              Sổ Tay Trí Tuệ Lỗi & Điểm Sáng Ngôn Ngữ (Learner Memory Intelligence)
            </h3>
          </div>

          {/* Filter Pills */}
          <div className="flex items-center gap-1.5">
            <button
              type="button"
              onClick={() => {
                soundFX.playFurin();
                setActiveTab("weaknesses");
              }}
              className={cn(
                "px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all",
                activeTab === "weaknesses"
                  ? "bg-primary text-primary-foreground border-primary shadow-xs"
                  : "bg-muted/40 border-border text-muted-foreground hover:text-foreground"
              )}
            >
              ⚠️ Điểm Cần Khắc Phục ({weaknesses.length})
            </button>

            <button
              type="button"
              onClick={() => {
                soundFX.playFurin();
                setActiveTab("strengths");
              }}
              className={cn(
                "px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all",
                activeTab === "strengths"
                  ? "bg-primary text-primary-foreground border-primary shadow-xs"
                  : "bg-muted/40 border-border text-muted-foreground hover:text-foreground"
              )}
            >
              ✨ Điểm Sáng Ngôn Ngữ ({strengths.length})
            </button>

            <button
              type="button"
              onClick={() => {
                soundFX.playFurin();
                setActiveTab("priorities");
              }}
              className={cn(
                "px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all",
                activeTab === "priorities"
                  ? "bg-primary text-primary-foreground border-primary shadow-xs"
                  : "bg-muted/40 border-border text-muted-foreground hover:text-foreground"
              )}
            >
              🎯 Ưu Tiên Ôn Tập ({priorities.length})
            </button>
          </div>
        </div>

        {/* Tab Content */}
        {loading ? (
          <div className="p-8 text-center text-xs text-muted-foreground animate-pulse">
            Đang tải trí tuệ lỗi từ cơ sở dữ liệu...
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
            {activeTab === "weaknesses" && (
              weaknesses.length === 0 ? (
                <div className="col-span-2 p-8 text-center text-xs text-muted-foreground border rounded-2xl">
                  Chưa ghi nhận lỗi sai nào lặp lại. Tuyệt vời!
                </div>
              ) : (
                weaknesses.map((w) => (
                  <div
                    key={w.id}
                    className="p-4 rounded-2xl border border-border/80 bg-card shadow-2xs space-y-2.5 hover:border-primary/40 transition-all"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="space-y-1">
                        <span className="text-xs font-bold text-foreground font-jp">{w.statement}</span>
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] text-muted-foreground uppercase font-mono">{w.category || w.memory_type}</span>
                          <span className="text-[10px] text-muted-foreground">• {w.evidence_count} lần ghi nhận</span>
                        </div>
                      </div>
                      {getTrendBadge(w.trend, w.is_regression)}
                    </div>

                    <div className="flex items-center justify-between pt-1 border-t border-border/60">
                      <button
                        type="button"
                        onClick={() => handleOpenEvidence(w.id)}
                        className="text-[11px] font-bold text-primary flex items-center gap-1 hover:underline"
                      >
                        <Eye className="h-3.5 w-3.5" />
                        <span>Xem bằng chứng ({w.evidence_count})</span>
                      </button>

                      <Link href="/learning">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 text-[11px] font-bold text-muted-foreground hover:text-foreground gap-1 px-2"
                        >
                          <span>Luyện bài khắc phục</span>
                          <ArrowRight className="h-3 w-3" />
                        </Button>
                      </Link>
                    </div>
                  </div>
                ))
              )
            )}

            {activeTab === "strengths" && (
              strengths.map((s) => (
                <div
                  key={s.id}
                  className="p-4 rounded-2xl border border-emerald-500/20 bg-emerald-500/5 shadow-2xs space-y-2"
                >
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                    <span className="text-xs font-bold text-foreground font-jp">{s.statement}</span>
                  </div>
                  <div className="text-[10px] text-muted-foreground pl-6">
                    Đã kiểm chứng qua {s.evidence_count} lượt hội thoại thành công.
                  </div>
                </div>
              ))
            )}

            {activeTab === "priorities" && (
              priorities.map((p, idx) => (
                <div
                  key={idx}
                  className="p-4 rounded-2xl border border-amber-500/20 bg-amber-500/5 shadow-2xs space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-foreground">{p.recommended_focus}</span>
                    <Badge variant="outline" size="sm" className="text-[10px] text-amber-600 dark:text-amber-400 font-mono">
                      Ưu tiên {Math.round(p.priority_score * 100)}%
                    </Badge>
                  </div>
                  <p className="text-[11px] text-muted-foreground leading-snug">{p.reason}</p>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* Evidence Detail Modal */}
      {selectedMemory && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs" role="dialog">
          <div className="bg-card border border-border rounded-3xl max-w-lg w-full p-6 space-y-4 shadow-2xl washi-texture">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div className="space-y-0.5">
                <span className="text-[10px] text-muted-foreground uppercase font-mono font-bold">BẰNG CHỨNG LỖI NGỮ CẢNH</span>
                <h3 className="text-sm font-bold text-foreground">{selectedMemory.statement}</h3>
              </div>
              <button
                type="button"
                onClick={() => setSelectedMemory(null)}
                className="p-1 rounded-lg hover:bg-muted text-muted-foreground"
              >
                <XCircle className="h-5 w-5" />
              </button>
            </div>

            <div className="max-h-80 overflow-y-auto space-y-2.5 pr-1">
              {selectedMemory.evidences?.map((e) => (
                <div key={e.id} className="p-3 rounded-xl bg-muted/40 border border-border/80 space-y-1.5 text-xs">
                  {e.original_snippet && (
                    <div className="text-rose-600 dark:text-rose-400 font-mono">
                      ❌ Câu bạn nói: "{e.original_snippet}"
                    </div>
                  )}
                  {e.corrected_snippet && (
                    <div className="text-emerald-600 dark:text-emerald-400 font-mono">
                      ✨ Gợi ý chuẩn: "{e.corrected_snippet}"
                    </div>
                  )}
                  <div className="text-[10px] text-muted-foreground">
                    Ngữ cảnh: {e.context_tag || "Hội thoại"} • {new Date(e.created_at).toLocaleDateString("vi-VN")}
                  </div>
                </div>
              ))}
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setSelectedMemory(null)}
              className="w-full text-xs font-bold rounded-xl"
            >
              Đóng
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
