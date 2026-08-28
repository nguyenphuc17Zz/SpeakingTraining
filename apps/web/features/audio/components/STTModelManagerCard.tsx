"use client";

import React, { useEffect, useState } from "react";
import {
  Cpu,
  Download,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Zap,
  HardDrive,
  Check,
  Star,
  Loader2,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { STTModelInfo } from "@/types/audio";
import { audioApi } from "../services/audio-api";

interface STTModelManagerCardProps {
  onModelChange?: (modelId: string) => void;
  className?: string;
}

export function STTModelManagerCard({ onModelChange, className = "" }: STTModelManagerCardProps) {
  const [models, setModels] = useState<STTModelInfo[]>([]);
  const [activeModelId, setActiveModelId] = useState<string>("base");
  const [loading, setLoading] = useState(true);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [selectingId, setSelectingId] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const fetchModels = async () => {
    setLoading(true);
    try {
      const data = await audioApi.listSTTModels(activeModelId);
      setModels(data);
      const currentActive = data.find((m) => m.is_active);
      if (currentActive) {
        setActiveModelId(currentActive.id);
      }
    } catch (e: any) {
      console.warn("Failed to load STT models:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchModels();
  }, []);

  const handleDownload = async (model: STTModelInfo) => {
    setDownloadingId(model.id);
    setFeedback(null);
    try {
      const res = await audioApi.downloadSTTModel(model.id);
      if (res.models) {
        setModels(res.models);
      } else {
        await fetchModels();
      }
      setFeedback({
        type: "success",
        text: `Đã tải thành công model ${model.name} (${model.size_display})!`,
      });
      setTimeout(() => setFeedback(null), 4000);
    } catch (e: any) {
      setFeedback({ type: "error", text: `Lỗi tải model: ${e.message}` });
    } finally {
      setDownloadingId(null);
    }
  };

  const handleSelect = async (model: STTModelInfo) => {
    setSelectingId(model.id);
    setFeedback(null);
    try {
      const res = await audioApi.selectSTTModel(model.id);
      setActiveModelId(model.id);
      if (res.models) {
        setModels(res.models);
      } else {
        await fetchModels();
      }
      onModelChange?.(model.id);
      setFeedback({
        type: "success",
        text: `Đã kích hoạt model ${model.name} cho toàn bộ hệ thống!`,
      });
      setTimeout(() => setFeedback(null), 4000);
    } catch (e: any) {
      setFeedback({ type: "error", text: `Lỗi kích hoạt model: ${e.message}` });
    } finally {
      setSelectingId(null);
    }
  };

  const activeModel = models.find((m) => m.id === activeModelId) || models[1] || models[0];
  const isGpu = activeModel?.device === "cuda";

  return (
    <div className={`rounded-2xl border border-border bg-card/95 washi-texture shadow-sumi p-4 sm:p-5 space-y-4 ${className}`}>
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-primary/15 to-kintsugi-400/20 border border-primary/25 flex items-center justify-center text-primary shrink-0 shadow-sm">
            <Cpu className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="text-sm font-bold text-foreground">
                Quản lý Model Nhận Diện Giọng Nói (Faster-Whisper STT)
              </h3>
              <Badge
                variant={isGpu ? "matcha" : "outline"}
                size="sm"
                className={isGpu ? "gap-1 shadow-sm" : "gap-1 border-border text-muted-foreground"}
              >
                <Zap className="h-3 w-3" />
                {isGpu ? "Tăng tốc phần cứng: NVIDIA CUDA GPU" : "Chế độ CPU CTranslate2"}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">
              Chọn hoặc tải về các kích cỡ model Whisper để tối ưu độ chính xác và tài nguyên máy tính.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchModels}
            disabled={loading}
            className="text-xs h-8 rounded-xl font-semibold"
            title="Làm mới danh sách model"
          >
            <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} />
            Làm mới
          </Button>
        </div>
      </div>

      {/* Feedback Toast */}
      {feedback && (
        <div
          className={`p-2.5 rounded-xl border text-xs flex items-center justify-between gap-2 animate-in fade-in ${
            feedback.type === "success"
              ? "bg-matcha-500/15 border-matcha-500/30 text-matcha-600 dark:text-matcha-400 font-medium"
              : "bg-destructive/15 border-destructive/30 text-destructive font-medium"
          }`}
        >
          <div className="flex items-center gap-2">
            {feedback.type === "success" ? (
              <CheckCircle2 className="h-4 w-4 shrink-0" />
            ) : (
              <AlertCircle className="h-4 w-4 shrink-0" />
            )}
            <span>{feedback.text}</span>
          </div>
          <button onClick={() => setFeedback(null)} className="text-xs font-bold px-1.5 py-0.5 opacity-70 hover:opacity-100">
            ✕
          </button>
        </div>
      )}

      {/* Models Grid */}
      {loading && models.length === 0 ? (
        <div className="py-10 text-center text-xs text-muted-foreground flex items-center justify-center gap-2">
          <Loader2 className="h-4 w-4 animate-spin text-primary" />
          <span>Đang kiểm tra bộ nhớ đệm Faster-Whisper...</span>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {models.map((m) => {
            const isActive = m.id === activeModelId;
            const isDownloading = downloadingId === m.id;
            const isSelecting = selectingId === m.id;

            return (
              <div
                key={m.id}
                className={`p-3.5 rounded-2xl border transition-all flex flex-col justify-between ${
                  isActive
                    ? "bg-primary/5 border-primary/50 shadow-kintsugi ring-1 ring-primary/30"
                    : "bg-card/70 border-border/80 hover:border-border hover:bg-card shadow-sm"
                }`}
              >
                <div className="space-y-2">
                  {/* Top Row: Name, Badges */}
                  <div className="flex items-start justify-between gap-1.5">
                    <div>
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="text-xs font-bold text-foreground">{m.name}</span>
                        {m.is_recommended && (
                          <span className="px-1.5 py-0.2 rounded text-[9px] font-extrabold bg-kintsugi-400/20 text-kintsugi-500 border border-kintsugi-400/35">
                            Khuyên dùng
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-1.5 mt-0.5 text-[11px] text-muted-foreground font-mono">
                        <span>{m.size_display}</span>
                        <span>•</span>
                        <span>{m.ram_required}</span>
                      </div>
                    </div>

                    {/* Status Pill */}
                    <div>
                      {isActive ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg text-[10px] font-bold bg-primary/15 text-primary border border-primary/30 shadow-sm">
                          <Check className="h-3 w-3" /> Đang dùng
                        </span>
                      ) : m.is_downloaded ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg text-[10px] font-medium bg-matcha-500/15 text-matcha-600 border border-matcha-500/30">
                          ✓ Có sẵn
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg text-[10px] font-medium bg-muted text-muted-foreground border border-border">
                          ☁️ Chưa tải
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Stars & Speed */}
                  <div className="flex items-center justify-between text-[11px] pt-1">
                    <div className="flex items-center gap-0.5" title={`Độ chính xác: ${m.accuracy_rating}`}>
                      {Array.from({ length: 5 }).map((_, i) => (
                        <Star
                          key={i}
                          className={`h-3 w-3 ${
                            i < m.stars ? "text-amber-400 fill-amber-400" : "text-muted-foreground/25"
                          }`}
                        />
                      ))}
                      <span className="text-[10px] text-muted-foreground ml-1">{m.accuracy_rating}</span>
                    </div>
                    <span className="text-[10px] text-muted-foreground font-semibold">{m.speed_rating}</span>
                  </div>

                  {/* Description */}
                  <p className="text-[11px] text-muted-foreground leading-relaxed line-clamp-2">
                    {m.description_vi}
                  </p>
                </div>

                {/* Bottom Action Button */}
                <div className="pt-3 mt-2 border-t border-border/60 flex items-center justify-between gap-2">
                  <span className="text-[10px] text-muted-foreground truncate">{m.recommended_for}</span>

                  <div className="shrink-0">
                    {isActive ? (
                      <span className="text-[11px] font-bold text-primary px-2 py-1 flex items-center gap-1">
                        <Check className="h-3 w-3" /> Mặc định
                      </span>
                    ) : m.is_downloaded ? (
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => handleSelect(m)}
                        disabled={isSelecting}
                        className="h-7 px-2.5 text-[11px] rounded-lg gap-1 font-semibold"
                      >
                        {isSelecting ? <Loader2 className="h-3 w-3 animate-spin" /> : <Check className="h-3 w-3" />}
                        Chọn dùng
                      </Button>
                    ) : (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDownload(m)}
                        disabled={isDownloading}
                        className="h-7 px-2.5 text-[11px] rounded-lg gap-1 border-primary/40 text-primary hover:bg-primary/10 font-semibold"
                      >
                        {isDownloading ? (
                          <>
                            <Loader2 className="h-3 w-3 animate-spin" />
                            <span>Đang tải...</span>
                          </>
                        ) : (
                          <>
                            <Download className="h-3 w-3" />
                            <span>Tải ({m.size_display})</span>
                          </>
                        )}
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
