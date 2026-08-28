"use client";

import React, { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Youtube, Sparkles, AlertCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ImportProgressTracker } from "@/features/shadowing/ImportProgressTracker";
import { shadowingApi } from "@/services/shadowing-api";
import { soundFX } from "@/lib/sound-fx";

function ShadowingImportContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialUrl = searchParams.get("url") || "";

  const [url, setUrl] = useState(initialUrl);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const hasTriggeredRef = React.useRef(false);

  useEffect(() => {
    if (initialUrl && !hasTriggeredRef.current && !activeJobId) {
      hasTriggeredRef.current = true;
      handleStartImport(initialUrl);
    }
  }, [initialUrl]);

  const handleStartImport = async (targetUrl: string) => {
    if (!targetUrl.trim()) return;
    setIsSubmitting(true);
    setError(null);

    try {
      // Automatically uses default settings STT model without asking user
      const res = await shadowingApi.importVideo(targetUrl.trim());

      if (res.is_existing && res.status === "ready") {
        soundFX.playTaiko();
        router.push(`/shadowing/video/${res.canonical_video_id || res.video_id}`);
      } else {
        setActiveJobId(res.job_id);
      }
    } catch (e: any) {
      setError(e.message || "Không thể khởi tạo import video. Vui lòng kiểm tra lại URL!");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleJobCompleted = (videoId: string) => {
    router.push(`/shadowing/video/${videoId}`);
  };

  return (
    <div className="max-w-4xl mx-auto p-4 sm:p-8 space-y-6 animate-in fade-in duration-200">
      {/* Back button */}
      <div>
        <Link
          href="/shadowing"
          className="inline-flex items-center gap-2 text-xs sm:text-sm font-semibold text-muted-foreground hover:text-foreground transition"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Quay lại thư viện Shadowing</span>
        </Link>
      </div>

      {/* Main Import / Progress Tracker */}
      {activeJobId ? (
        <ImportProgressTracker
          jobId={activeJobId}
          onCompleted={handleJobCompleted}
          onFailed={(err) => setError(err)}
        />
      ) : isSubmitting && !error ? (
        <div className="p-8 sm:p-12 rounded-[28px] bg-card/95 border border-border/80 washi-texture backdrop-blur-xl shadow-sumi-lg space-y-5 max-w-lg mx-auto text-center animate-in fade-in">
          <div className="relative mx-auto w-16 h-16 flex items-center justify-center">
            <div className="absolute inset-0 rounded-full bg-primary/20 animate-ping opacity-60" />
            <div className="relative p-4 rounded-2xl bg-primary/20 text-primary border border-primary/30 shadow-md">
              <Youtube className="h-8 w-8" />
            </div>
          </div>
          <div className="space-y-2">
            <h2 className="text-lg font-bold text-foreground font-sans">
              Đang chuẩn bị tiến trình phân tích...
            </h2>
            <p className="text-xs sm:text-sm text-muted-foreground font-mono truncate max-w-xs mx-auto">
              {url || initialUrl}
            </p>
          </div>
          <div className="flex items-center justify-center gap-2 text-xs sm:text-sm text-primary font-bold">
            <RefreshCw className="h-4 w-4 animate-spin" />
            <span>Kết nối máy chủ Whisper STT & Gemini AI</span>
          </div>
        </div>
      ) : (
        <div className="p-6 sm:p-10 rounded-[28px] bg-card/95 border border-border/80 washi-texture backdrop-blur-xl shadow-sumi-lg space-y-6 max-w-xl mx-auto">
          <div className="text-center space-y-2.5">
            <div className="inline-flex p-3.5 rounded-2xl bg-primary/15 text-primary border border-primary/25 shadow-sm">
              <Youtube className="h-8 w-8" />
            </div>
            <h1 className="text-xl sm:text-2xl font-black text-foreground font-sans">
              Nhập Video YouTube để Shadowing
            </h1>
            <p className="text-xs sm:text-sm text-muted-foreground max-w-md mx-auto leading-relaxed">
              Hệ thống sẽ tự động trích xuất phụ đề, phân đoạn nhịp câu và chấm điểm phát âm tương tác dựa trên cấu hình STT mặc định của bạn.
            </p>
          </div>

          {error && (
            <div className="p-4 rounded-2xl bg-rose-950/40 border border-rose-500/40 text-rose-200 text-xs sm:text-sm flex items-start gap-3 shadow-sm animate-in fade-in">
              <AlertCircle className="h-5 w-5 text-rose-400 shrink-0 mt-0.5" />
              <div className="flex-1 space-y-1">
                <p className="font-bold">Lỗi khởi tạo</p>
                <p className="text-rose-300/80 leading-relaxed">{error}</p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleStartImport(url || initialUrl)}
                  className="mt-2 h-8 text-xs font-bold border-rose-500/40 text-rose-200 hover:bg-rose-500/20 rounded-xl"
                >
                  <RefreshCw className="h-3.5 w-3.5 mr-1.5" /> Thử lại
                </Button>
              </div>
            </div>
          )}

          <div className="space-y-4">
            <div className="space-y-2">
              <label className="text-xs sm:text-sm font-bold text-foreground">
                Đường dẫn YouTube (URL)
              </label>
              <input
                type="text"
                placeholder="https://www.youtube.com/watch?v=..."
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="w-full h-12 px-4 rounded-2xl border border-border/90 bg-background text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>

            <Button
              variant="primary"
              size="lg"
              onClick={() => handleStartImport(url)}
              disabled={isSubmitting || !url.trim()}
              className="w-full h-12 text-sm font-bold shadow-md gap-2 rounded-2xl"
            >
              {isSubmitting ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  <span>Đang khởi tạo phân tích...</span>
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  <span>Bắt đầu phân tích & Nhập video</span>
                </>
              )}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function ShadowingImportPage() {
  return (
    <Suspense
      fallback={
        <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-3">
          <div className="w-8 h-8 border-3 border-primary/30 border-t-primary rounded-full animate-spin" />
          <p className="text-xs text-muted-foreground">Đang tải tiến trình phân tích...</p>
        </div>
      }
    >
      <ShadowingImportContent />
    </Suspense>
  );
}
