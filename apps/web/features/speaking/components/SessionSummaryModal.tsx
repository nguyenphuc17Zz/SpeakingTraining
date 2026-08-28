"use client";

import React, { useEffect, useState } from "react";
import {
  ConversationAnalysisSummary,
  CorrectionItem,
  SessionSummary,
} from "../types";
import { Modal } from "@/components/ui/modal";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Clock,
  Mic,
  Sparkles,
  Zap,
  CheckCircle2,
  BarChart2,
  ArrowRight,
  Award,
  AlertTriangle,
  BookOpen,
  Volume2,
  TrendingUp,
} from "lucide-react";
import { analysisApi } from "../services/analysis-api";
import { CorrectionDetailModal } from "./CorrectionDetailModal";

interface SessionSummaryModalProps {
  isOpen: boolean;
  summary: SessionSummary | null;
  onClose: () => void;
  onReplayVoice?: (text: string) => void;
}

export function SessionSummaryModal({
  isOpen,
  summary,
  onClose,
  onReplayVoice,
}: SessionSummaryModalProps) {
  const [activeTab, setActiveTab] = useState<
    "overview" | "strengths" | "corrections" | "native" | "recommendations"
  >("overview");
  const [analysisSummary, setAnalysisSummary] =
    useState<ConversationAnalysisSummary | null>(null);
  const [selectedCorrection, setSelectedCorrection] =
    useState<CorrectionItem | null>(null);
  const [isLoadingAnalysis, setIsLoadingAnalysis] = useState(false);

  useEffect(() => {
    if (isOpen && summary?.session_id) {
      setIsLoadingAnalysis(true);
      analysisApi
        .getSessionAnalysisSummary(summary.session_id)
        .then((data) => {
          setAnalysisSummary(data);
        })
        .catch((e) => {
          console.warn("[SessionSummaryModal] Failed to fetch session analysis:", e);
        })
        .finally(() => {
          setIsLoadingAnalysis(false);
        });
    }
  }, [isOpen, summary?.session_id]);

  if (!summary) return null;

  const mins = Math.floor(summary.duration_seconds / 60);
  const secs = summary.duration_seconds % 60;
  const formattedDuration = `${mins}m ${secs}s`;

  const sessionAnalysis = analysisSummary?.session_analysis;
  const turnAnalyses = analysisSummary?.turn_analyses || [];
  const allCorrections = turnAnalyses.flatMap((ta) => ta.corrections);

  const mustFixCorrections = allCorrections.filter((c) => c.severity === "MUST_FIX");
  const shouldFixCorrections = allCorrections.filter((c) => c.severity === "SHOULD_FIX");
  const nativeAltCorrections = allCorrections.filter(
    (c) => c.severity === "NATIVE_ALTERNATIVE"
  );

  return (
    <>
      <Modal
        isOpen={isOpen}
        onClose={onClose}
        title="Conversation Review & Intelligence (Báo Cáo Đánh Giá Buổi Nói)"
        description={`Tổng kết toàn diện năng lực phản xạ và chất lượng tiếng Nhật cùng ${summary.persona_name}.`}
      >
        <div className="space-y-4 pt-1 max-h-[75vh] overflow-y-auto pr-1">
          {/* Top KPI Score Banner */}
          <div className="p-4 rounded-2xl bg-gradient-to-r from-primary/15 via-primary/10 to-aizome-500/15 border border-primary/30 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="h-12 w-12 rounded-2xl bg-gradient-to-tr from-primary to-aizome-600 flex items-center justify-center text-primary-foreground font-extrabold text-lg shadow-lg shadow-primary/20 shrink-0">
                {sessionAnalysis?.overall_score ?? 80}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-bold text-foreground">
                    Speaking Performance Score
                  </h3>
                  <Badge variant="fuji" size="sm">
                    {sessionAnalysis ? "Phân tích AI hoàn tất" : "Đang tính toán..."}
                  </Badge>
                </div>
                <p className="text-[11px] text-muted-foreground mt-0.5">
                  Đánh giá dựa trên ngữ pháp, phản xạ, độ trôi chảy và mức độ tự nhiên.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 self-start sm:self-center text-xs font-mono">
              <span className="px-2.5 py-1 rounded-xl bg-card/90 border border-border text-kintsugi-400">
                {allCorrections.length} lưu ý
              </span>
              <span className="px-2.5 py-1 rounded-xl bg-card/90 border border-border text-emerald-300">
                {sessionAnalysis?.strengths?.length ?? 2} điểm sáng
              </span>
            </div>
          </div>

          {/* Quick Metrics 4-Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
            <div className="p-2.5 rounded-xl bg-background border border-border space-y-0.5">
              <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground">
                <Clock className="h-3 w-3 text-aizome-400" />
                <span>Thời gian</span>
              </div>
              <p className="text-sm font-bold text-foreground font-mono">
                {formattedDuration}
              </p>
            </div>

            <div className="p-2.5 rounded-xl bg-background border border-border space-y-0.5">
              <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground">
                <Mic className="h-3 w-3 text-emerald-400" />
                <span>Thời lượng nói</span>
              </div>
              <p className="text-sm font-bold text-emerald-400 font-mono">
                {summary.total_speaking_time_seconds}s
              </p>
            </div>

            <div className="p-2.5 rounded-xl bg-background border border-border space-y-0.5">
              <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground">
                <Sparkles className="h-3 w-3 text-primary" />
                <span>Số lượt nói</span>
              </div>
              <p className="text-sm font-bold text-primary font-mono">
                {summary.turn_count} turns
              </p>
            </div>

            <div className="p-2.5 rounded-xl bg-background border border-border space-y-0.5">
              <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground">
                <Zap className="h-3 w-3 text-amber-400" />
                <span>Độ trễ TB</span>
              </div>
              <p className="text-sm font-bold text-amber-400 font-mono">
                {summary.avg_turn_latency_ms}ms
              </p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center gap-1 bg-card/80 p-1 rounded-xl border border-border text-xs overflow-x-auto scrollbar-none">
            <button
              onClick={() => setActiveTab("overview")}
              className={`px-3 py-1.5 font-bold rounded-lg transition-colors shrink-0 ${
                activeTab === "overview"
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              📊 Tổng quan
            </button>
            <button
              onClick={() => setActiveTab("strengths")}
              className={`px-3 py-1.5 font-bold rounded-lg transition-colors shrink-0 ${
                activeTab === "strengths"
                  ? "bg-emerald-600 text-white shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              🟢 Điểm sáng ({sessionAnalysis?.strengths?.length ?? 0})
            </button>
            <button
              onClick={() => setActiveTab("corrections")}
              className={`px-3 py-1.5 font-bold rounded-lg transition-colors shrink-0 ${
                activeTab === "corrections"
                  ? "bg-kintsugi-600 text-white shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              🟠 Lỗi cần sửa ({mustFixCorrections.length + shouldFixCorrections.length})
            </button>
            <button
              onClick={() => setActiveTab("native")}
              className={`px-3 py-1.5 font-bold rounded-lg transition-colors shrink-0 ${
                activeTab === "native"
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              ⭐ Khẩu ngữ bản xứ ({nativeAltCorrections.length})
            </button>
            <button
              onClick={() => setActiveTab("recommendations")}
              className={`px-3 py-1.5 font-bold rounded-lg transition-colors shrink-0 ${
                activeTab === "recommendations"
                  ? "bg-purple-600 text-white shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              💡 Top Lời khuyên
            </button>
          </div>

          {/* Tab 1: Overview */}
          {activeTab === "overview" && (
            <div className="space-y-3 animate-in fade-in duration-200">
              {/* Mandatory Strengths Highlight */}
              <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/25 space-y-2">
                <div className="flex items-center gap-2 text-emerald-400 font-bold text-xs">
                  <Award className="h-4 w-4" />
                  <span>Điểm mạnh trong buổi nói chuyện:</span>
                </div>
                <ul className="text-xs text-foreground space-y-1 list-disc list-inside">
                  {(sessionAnalysis?.strengths || [
                    "Phản xạ đối thoại liên tục và chủ động",
                    "Dùng từ vựng phong phú và biểu đạt ý định rõ ràng",
                  ]).map((st, i) => (
                    <li key={i}>{st}</li>
                  ))}
                </ul>
              </div>

              {/* Priority Issues & Weaknesses Summary */}
              <div className="p-3.5 rounded-xl bg-background border border-border space-y-2">
                <div className="flex items-center gap-2 text-kintsugi-400 font-bold text-xs">
                  <AlertTriangle className="h-4 w-4" />
                  <span>Trọng tâm cần cải thiện:</span>
                </div>
                <ul className="text-xs text-foreground space-y-1 list-disc list-inside">
                  {(sessionAnalysis?.weaknesses || [
                    "Chú ý trợ từ và chia động từ trong câu phức",
                  ]).map((wk, i) => (
                    <li key={i}>{wk}</li>
                  ))}
                </ul>
              </div>

              {/* Repeated Issue Patterns */}
              {sessionAnalysis?.repeated_issues &&
                sessionAnalysis.repeated_issues.length > 0 && (
                  <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/25 space-y-2">
                    <div className="flex items-center gap-1.5 text-amber-400 font-bold text-xs">
                      <TrendingUp className="h-4 w-4" />
                      <span>Mẫu câu hoặc lỗi bị lặp lại nhiều lần:</span>
                    </div>
                    <div className="space-y-1.5">
                      {sessionAnalysis.repeated_issues.map((rp, idx) => (
                        <div
                          key={idx}
                          className="p-2 rounded-lg bg-card/90 border border-amber-500/20 text-xs text-foreground"
                        >
                          <span className="font-bold text-amber-300 font-mono">
                            {rp.pattern} ({rp.occurrences_count} lần)
                          </span>
                          <p className="text-[11px] text-muted-foreground mt-0.5">
                            {rp.recommendation}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
            </div>
          )}

          {/* Tab 2: Strengths */}
          {activeTab === "strengths" && (
            <div className="space-y-2.5 animate-in fade-in duration-200">
              {(sessionAnalysis?.strengths || []).map((s, idx) => (
                <div
                  key={idx}
                  className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-start gap-3 text-xs"
                >
                  <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
                  <div>
                    <h4 className="font-bold text-emerald-300">Điểm sáng #{idx + 1}</h4>
                    <p className="text-foreground mt-0.5 leading-relaxed">{s}</p>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Tab 3: Corrections */}
          {activeTab === "corrections" && (
            <div className="space-y-2 animate-in fade-in duration-200">
              {mustFixCorrections.length === 0 && shouldFixCorrections.length === 0 ? (
                <div className="p-8 text-center text-xs text-muted-foreground bg-background rounded-xl border border-border">
                  🎉 Tuyệt vời! Bạn không mắc lỗi ngữ pháp nghiêm trọng nào trong buổi nói này.
                </div>
              ) : (
                [...mustFixCorrections, ...shouldFixCorrections].map((corr) => (
                  <div
                    key={corr.id}
                    onClick={() => setSelectedCorrection(corr)}
                    className="p-3 rounded-xl bg-background border border-border hover:border-primary/50 cursor-pointer transition-all space-y-1.5 text-xs"
                  >
                    <div className="flex items-center justify-between">
                      <Badge
                        variant="outline"
                        size="sm"
                        className={
                          corr.severity === "MUST_FIX"
                            ? "bg-destructive/20 text-destructive border-destructive/40 text-[10px]"
                            : "bg-amber-500/20 text-amber-300 border-amber-500/40 text-[10px]"
                        }
                      >
                        {corr.severity === "MUST_FIX" ? "🔴 Must Fix" : "🟠 Should Fix"}
                      </Badge>
                      <span className="text-[10px] text-muted-foreground capitalize">
                        {corr.category}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 font-mono text-xs">
                      <span className="line-through text-muted-foreground">{corr.original}</span>
                      <ArrowRight className="h-3 w-3 text-primary shrink-0" />
                      <span className="font-bold text-emerald-400">{corr.corrected}</span>
                    </div>

                    <p className="text-[11px] text-muted-foreground line-clamp-1">
                      {corr.explanation}
                    </p>
                  </div>
                ))
              )}
            </div>
          )}

          {/* Tab 4: Native Alternatives */}
          {activeTab === "native" && (
            <div className="space-y-2 animate-in fade-in duration-200">
              {nativeAltCorrections.length === 0 ? (
                <div className="p-8 text-center text-xs text-muted-foreground bg-background rounded-xl border border-border">
                  Chưa có gợi ý khẩu ngữ bản xứ đặc biệt cho lượt nói này.
                </div>
              ) : (
                nativeAltCorrections.map((corr) => (
                  <div
                    key={corr.id}
                    onClick={() => setSelectedCorrection(corr)}
                    className="p-3 rounded-xl bg-indigo-500/5 border border-indigo-500/25 hover:border-indigo-500/50 cursor-pointer transition-all space-y-1.5 text-xs"
                  >
                    <div className="flex items-center justify-between">
                      <Badge
                        variant="outline"
                        size="sm"
                        className="bg-indigo-500/20 text-indigo-300 border-indigo-500/40 text-[10px]"
                      >
                        ⭐ Native Alternative
                      </Badge>
                      <span className="text-[10px] text-muted-foreground">Tự nhiên & gần gũi</span>
                    </div>

                    <div className="flex items-center gap-2 font-mono text-xs">
                      <span className="text-foreground">{corr.original}</span>
                      <ArrowRight className="h-3 w-3 text-indigo-400 shrink-0" />
                      <span className="font-bold text-indigo-300">
                        {corr.native_alternative || corr.corrected}
                      </span>
                    </div>

                    <p className="text-[11px] text-foreground line-clamp-1">
                      {corr.explanation}
                    </p>
                  </div>
                ))
              )}
            </div>
          )}

          {/* Tab 5: Recommendations */}
          {activeTab === "recommendations" && (
            <div className="space-y-3 animate-in fade-in duration-200">
              {(
                sessionAnalysis?.top_recommendations || [
                  "Thực hành nối câu tự nhiên bằng thể Te (〜て) và các liên từ khẩu ngữ.",
                  "Tăng tốc độ phản xạ bằng cách trả lời ngắn gọn trong 1-2 giây đầu.",
                  "Lắng nghe và nhại lại (shadowing) ngữ điệu của Persona.",
                ]
              ).map((rec, idx) => (
                <div
                  key={idx}
                  className="p-3.5 rounded-xl bg-gradient-to-r from-purple-500/10 to-indigo-500/10 border border-purple-500/30 flex items-start gap-3 text-xs"
                >
                  <div className="h-6 w-6 rounded-full bg-purple-500/20 flex items-center justify-center text-purple-300 font-bold shrink-0">
                    {idx + 1}
                  </div>
                  <div>
                    <h4 className="font-bold text-purple-300">
                      Khuyến nghị hành động #{idx + 1}
                    </h4>
                    <p className="text-foreground mt-0.5 leading-relaxed">{rec}</p>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Actions Bar */}
          <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-border sticky bottom-0 bg-card">
            <Button
              variant="outline"
              size="md"
              onClick={onClose}
              className="w-full sm:w-auto text-xs"
            >
              <span>Đóng báo cáo (Về danh sách)</span>
            </Button>
            <Button
              variant="sakura"
              size="md"
              onClick={onClose}
              className="w-full sm:w-auto text-xs"
            >
              <span>Luyện tập tiếp (Practice Again)</span>
              <ArrowRight className="h-4 w-4 ml-1.5" />
            </Button>
          </div>
        </div>
      </Modal>

      {/* Selected Correction Detail Modal */}
      <CorrectionDetailModal
        isOpen={selectedCorrection !== null}
        correction={selectedCorrection}
        onClose={() => setSelectedCorrection(null)}
        onPlayCorrection={onReplayVoice}
      />
    </>
  );
}
