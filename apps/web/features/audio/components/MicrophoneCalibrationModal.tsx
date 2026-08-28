"use client";

import React, { useState } from "react";
import { Mic, Volume2, CheckCircle2, AlertTriangle, X, RefreshCw, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { AudioQualityReport } from "@/types/audio";
import { audioApi } from "../services/audio-api";
import { useAudioRecorder } from "../hooks/useAudioRecorder";
import { AudioLevelMeter } from "./AudioLevelMeter";
import { RecordingWaveform } from "./RecordingWaveform";

interface MicrophoneCalibrationModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function MicrophoneCalibrationModal({
  isOpen,
  onClose,
}: MicrophoneCalibrationModalProps) {
  const [report, setReport] = useState<AudioQualityReport | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const {
    state,
    isRecording,
    volumeLevel,
    startRecording,
    stopRecording,
    releaseMicrophone,
    requestPermission,
  } = useAudioRecorder();

  React.useEffect(() => {
    if (!isOpen) {
      releaseMicrophone();
    }
    return () => {
      releaseMicrophone();
    };
  }, [isOpen, releaseMicrophone]);

  if (!isOpen) return null;

  const handleStartTest = async () => {
    setReport(null);
    await startRecording();
  };

  const handleStopTest = async () => {
    const blob = await stopRecording();
    if (blob.size === 0) return;

    setIsAnalyzing(true);
    try {
      const reader = new FileReader();
      reader.onloadend = async () => {
        const base64Data = (reader.result as string).split(",")[1];
        if (base64Data) {
          const res = await audioApi.checkAudioQuality(base64Data);
          setReport(res);
        }
        setIsAnalyzing(false);
      };
      reader.readAsDataURL(blob);
    } catch (e) {
      console.error("[Calibration] Analysis failed:", e);
      setIsAnalyzing(false);
    }
  };

  const getStatusBadge = () => {
    if (!report) return null;
    const colors = {
      good: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
      acceptable: "bg-indigo-500/20 text-indigo-300 border-indigo-500/30",
      noisy: "bg-amber-500/20 text-amber-300 border-amber-500/30",
      clipping: "bg-rose-500/20 text-rose-300 border-rose-500/30",
      too_quiet: "bg-amber-500/20 text-amber-300 border-amber-500/30",
      silent: "bg-slate-700 text-foreground border-slate-600",
    };
    return (
      <span className={`px-2.5 py-1 rounded-full text-xs font-semibold border ${colors[report.quality]}`}>
        {report.quality.toUpperCase()}
      </span>
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in">
      <div className="relative w-full max-w-lg bg-card border border-border rounded-2xl shadow-2xl p-6 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-border">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-primary/10 border border-primary/20 text-primary">
              <Mic className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-foreground">Kiểm tra & Cân chỉnh Micro</h3>
              <p className="text-xs text-muted-foreground">Đảm bảo giọng nói rõ ràng và đạt chuẩn âm lượng</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Content */}
        <div className="py-5 space-y-4">
          <div className="p-3.5 rounded-xl bg-background/60 border border-border text-center">
            <p className="text-xs text-muted-foreground mb-1">Mẫu câu thử giọng:</p>
            <p className="text-sm font-japanese font-semibold text-primary">
              「こんにちは、はじめまして。よろしくお願いします。」
            </p>
          </div>

          <div className="space-y-2">
            <AudioLevelMeter volume={volumeLevel} />
            <RecordingWaveform volume={volumeLevel} isRecording={isRecording} />
          </div>

          {/* Action Button */}
          <div className="flex justify-center pt-2">
            {isRecording ? (
              <Button
                variant="danger"
                size="lg"
                onClick={handleStopTest}
                className="w-full shadow-lg shadow-destructive/20"
              >
                Hoàn tất đọc mẫu (3s+)
              </Button>
            ) : (
              <Button
                variant="primary"
                size="lg"
                onClick={handleStartTest}
                disabled={isAnalyzing}
                className="w-full shadow-lg shadow-primary/20"
              >
                {isAnalyzing ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Đang phân tích âm thanh...
                  </>
                ) : (
                  <>
                    <Mic className="h-4 w-4 mr-2" />
                    Bắt đầu thu thử âm thanh
                  </>
                )}
              </Button>
            )}
          </div>

          {/* Quality Report Results */}
          {report && (
            <div className="p-4 rounded-xl bg-background border border-border space-y-3 animate-in slide-in-from-bottom-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-foreground">Kết quả đánh giá</span>
                {getStatusBadge()}
              </div>

              <p className="text-xs text-foreground leading-relaxed">
                {report.recommendation}
              </p>

              <div className="grid grid-cols-3 gap-2 pt-2 border-t border-border/80 text-center">
                <div className="p-2 rounded-lg bg-card border border-border/50">
                  <div className="text-[10px] text-muted-foreground">Âm lượng (Volume)</div>
                  <div className="text-xs font-mono font-bold text-foreground">{report.volume_db} dB</div>
                </div>
                <div className="p-2 rounded-lg bg-card border border-border/50">
                  <div className="text-[10px] text-muted-foreground">Độ ồn nền (Noise)</div>
                  <div className="text-xs font-mono font-bold text-foreground">{report.noise_level_db} dB</div>
                </div>
                <div className="p-2 rounded-lg bg-card border border-border/50">
                  <div className="text-[10px] text-muted-foreground">Tỷ lệ SNR</div>
                  <div className="text-xs font-mono font-bold text-emerald-400">{report.snr_db ?? 0} dB</div>
                </div>
              </div>

              {report.warnings.length > 0 && (
                <div className="space-y-1 pt-1">
                  {report.warnings.map((w, idx) => (
                    <div key={idx} className="flex items-center gap-1.5 text-[11px] text-amber-400 font-medium">
                      <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
                      <span>{w}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end pt-3 border-t border-border">
          <Button variant="secondary" onClick={onClose} size="sm">
            Đóng
          </Button>
        </div>
      </div>
    </div>
  );
}
