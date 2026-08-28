"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Youtube,
  Sparkles,
  Play,
  Clock,
  BookOpen,
  ArrowRight,
  TrendingUp,
  Award,
  Layers,
  Plus,
  Compass,
  Trash2,
  AlertTriangle,
  X,
  RefreshCw,
  CheckCircle2,
  ExternalLink,
  Flame,
  Film,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { shadowingApi } from "@/services/shadowing-api";
import { ShadowingVideo } from "@/types/shadowing";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

function extractYoutubeId(url: string): string | null {
  if (!url) return null;
  const match = url.match(
    /(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=|shorts\/))([\w-]{11})/
  );
  return match ? match[1] : null;
}

const CURATED_SAMPLES = [
  {
    title: "Hội Thoại Quán Cà Phê Hàng Ngày",
    channel: "Japanese Everyday",
    url: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    level: "N4",
    badge: "Giao tiếp đời thường",
    duration: "3 phút",
  },
  {
    title: "Phỏng Vấn Xin Việc Tiếng Nhật (Keigo)",
    channel: "Business Nihongo",
    url: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    level: "N2",
    badge: "Kính ngữ công sở",
    duration: "4 phút",
  },
  {
    title: "Tin Tức Đời Sống & Văn Hóa Tokyo",
    channel: "NHK Easy Japanese",
    url: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    level: "N3",
    badge: "Phát âm chuẩn",
    duration: "2 phút",
  },
];

export default function ShadowingPage() {
  const router = useRouter();
  const [urlInput, setUrlInput] = useState("");
  const [videos, setVideos] = useState<ShadowingVideo[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Video deletion state
  const [videoToDelete, setVideoToDelete] = useState<ShadowingVideo | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    async function loadVideos() {
      try {
        const res = await shadowingApi.listVideos(20);
        setVideos(res.videos || []);
      } catch (e) {
        console.error("Failed to load shadowing videos:", e);
      } finally {
        setIsLoading(false);
      }
    }
    loadVideos();
  }, []);

  // Real-time duplicate check
  const extractedVideoId = extractYoutubeId(urlInput.trim());
  const existingVideo = extractedVideoId
    ? videos.find((v) => v.video_id === extractedVideoId || v.id === extractedVideoId)
    : null;

  const handleImportSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!urlInput.trim()) return;

    if (existingVideo) {
      soundFX.playTaiko();
      router.push(`/shadowing/video/${existingVideo.video_id || existingVideo.id}`);
      return;
    }

    soundFX.playFurin();
    router.push(`/shadowing/import?url=${encodeURIComponent(urlInput.trim())}`);
  };

  const handleSelectSample = (sampleUrl: string) => {
    setUrlInput(sampleUrl);
    soundFX.playFurin();
  };

  const handleConfirmDelete = async () => {
    if (!videoToDelete) return;
    try {
      setIsDeleting(true);
      const targetId = videoToDelete.video_id || videoToDelete.id;
      await shadowingApi.deleteVideo(targetId);
      soundFX.playTaiko();

      setVideos((prev) =>
        prev.filter((v) => v.id !== videoToDelete.id && v.video_id !== videoToDelete.video_id)
      );
      setVideoToDelete(null);
    } catch (err: any) {
      console.error("Failed to delete shadowing video:", err);
      alert(err.message || "Không thể xóa video. Vui lòng thử lại!");
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Hero / Import Section */}
      <div className="relative overflow-hidden rounded-[28px] border border-border/80 bg-card/95 washi-texture shadow-sumi-lg p-6 sm:p-10 space-y-6">
        <div className="absolute -top-24 -right-24 h-80 w-80 rounded-full bg-enso-gradient opacity-25 pointer-events-none" />
        <div className="absolute inset-0 shoji-grid opacity-[0.03] pointer-events-none" />

        <div className="relative max-w-3xl space-y-3">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-primary/15 border border-primary/30 text-primary text-xs sm:text-sm font-bold">
            <Youtube className="h-4 w-4" />
            <span>Luyện Nói Shadowing Qua Video YouTube</span>
          </div>

          <h1 className="text-2xl sm:text-4xl font-black tracking-tight text-foreground font-sans leading-tight">
            Biến mọi video YouTube thành <span className="text-primary">phòng luyện Shadowing</span>
          </h1>

          <p className="text-sm sm:text-base text-muted-foreground leading-relaxed">
            Dán đường dẫn YouTube để AI tự động trích xuất phụ đề, chia nhịp câu chuẩn, cung cấp phiên âm Furigana và chấm điểm phát âm tương tác thời gian thực.
          </p>
        </div>

        {/* Input Bar with Real-Time Existing Video Detection */}
        <div className="space-y-3 max-w-3xl">
          <form onSubmit={handleImportSubmit} className="relative flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <input
                type="url"
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
                placeholder="Dán link YouTube (ví dụ: https://www.youtube.com/watch?v=...)"
                className={cn(
                  "w-full h-12 px-4 rounded-2xl border bg-background text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 transition-all shadow-inner",
                  existingVideo
                    ? "border-emerald-500/60 focus:ring-emerald-500"
                    : "border-border/90 focus:ring-primary"
                )}
              />
            </div>

            {existingVideo ? (
              <Button
                type="submit"
                variant="primary"
                className="h-12 px-6 rounded-2xl font-bold text-sm shrink-0 bg-emerald-600 hover:bg-emerald-700 text-white shadow-md gap-2"
              >
                <Play className="h-4 w-4 fill-current" />
                <span>Mở Bài Học Ngay</span>
              </Button>
            ) : (
              <Button
                type="submit"
                variant="primary"
                disabled={!urlInput.trim()}
                className="h-12 px-6 rounded-2xl font-bold text-sm shrink-0 shadow-md gap-2"
              >
                <Plus className="h-4 w-4" />
                <span>Nhập Video & Phân Tích</span>
              </Button>
            )}
          </form>

          {/* Existing Video Notice */}
          {existingVideo && (
            <div className="flex items-center gap-2 p-3 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs sm:text-sm font-semibold animate-in fade-in">
              <CheckCircle2 className="h-4 w-4 shrink-0" />
              <span className="truncate">
                Video này đã có trong thư viện: <strong>{existingVideo.title}</strong>
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Imported Videos List */}
      <div className="space-y-5">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg sm:text-xl font-bold text-foreground font-sans">
              Video Của Bạn ({videos.length})
            </h2>
            <p className="text-xs sm:text-sm text-muted-foreground">
              Các bài luyện Shadowing đã được đồng bộ phụ đề và phân tích điểm luyện
            </p>
          </div>
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-72 rounded-2xl bg-card border border-border animate-pulse" />
            ))}
          </div>
        ) : videos.length === 0 ? (
          <div className="text-center py-16 px-4 rounded-3xl border border-dashed border-border/80 bg-card/40 space-y-3">
            <Youtube className="h-14 w-14 mx-auto text-muted-foreground/40" />
            <div className="space-y-1">
              <h3 className="text-base font-bold text-foreground font-sans">
                Chưa có video nào trong thư viện
              </h3>
              <p className="text-xs sm:text-sm text-muted-foreground max-w-md mx-auto">
                Dán đường dẫn YouTube ở khung bên trên để bắt đầu phân tích và luyện nói phản xạ.
              </p>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {videos.map((vid) => (
              <div
                key={vid.id}
                className="group relative rounded-2xl bg-card/95 border border-border/80 hover:border-primary/40 hover:shadow-sumi-md transition-all duration-200 overflow-hidden flex flex-col justify-between"
              >
                <Link href={`/shadowing/video/${vid.video_id}`} className="block">
                  <div>
                    <div className="relative aspect-video w-full bg-muted overflow-hidden">
                      {vid.thumbnail_url ? (
                        <img
                          src={vid.thumbnail_url}
                          alt={vid.title}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center bg-muted text-muted-foreground">
                          <Youtube className="h-12 w-12" />
                        </div>
                      )}

                      {/* Difficulty Badge */}
                      <div className="absolute top-3 right-3">
                        <Badge variant="jlpt" size="sm" className="font-bold shadow-md">
                          JLPT {vid.overall_difficulty.toUpperCase()}
                        </Badge>
                      </div>

                      {/* Delete Action Button on Thumbnail */}
                      <button
                        type="button"
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          soundFX.playFurin();
                          setVideoToDelete(vid);
                        }}
                        className="absolute top-3 left-3 h-8 w-8 rounded-xl bg-card/90 hover:bg-primary hover:text-primary-foreground border border-border/80 text-muted-foreground flex items-center justify-center transition-all opacity-90 sm:opacity-0 sm:group-hover:opacity-100 shadow-md"
                        title="Xóa video khỏi thư viện"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>

                    <div className="p-4 space-y-1.5">
                      <h3 className="text-sm sm:text-base font-bold text-foreground font-sans line-clamp-2 leading-snug group-hover:text-primary transition">
                        {vid.title}
                      </h3>
                      <p className="text-xs text-muted-foreground font-medium flex items-center gap-1.5">
                        <span>{vid.channel_name}</span>
                      </p>
                    </div>
                  </div>
                </Link>

                <div className="px-4 py-3 border-t border-border/70 flex items-center justify-between text-xs text-muted-foreground bg-card/40">
                  <span className="flex items-center gap-1 font-mono font-medium">
                    <Clock className="h-3.5 w-3.5" />
                    {Math.floor((vid.duration_seconds || 120) / 60)} phút
                  </span>
                  <Link
                    href={`/shadowing/video/${vid.video_id}`}
                    className="text-primary font-bold flex items-center gap-1 hover:underline"
                  >
                    <span>Luyện Shadowing</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      {videoToDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md animate-in fade-in duration-200">
          <div className="relative w-full max-w-md rounded-[28px] border-2 border-primary/40 bg-card/95 washi-texture shadow-sumi-lg p-6 overflow-hidden space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <span className="h-10 w-10 rounded-2xl bg-primary/15 border border-primary/30 flex items-center justify-center text-primary text-lg shadow-sm">
                  <Trash2 className="h-5 w-5" />
                </span>
                <div>
                  <h3 className="text-base font-bold text-foreground font-sans">
                    Xóa Video Shadowing?
                  </h3>
                  <p className="text-xs text-muted-foreground font-jp">動画の削除・確認</p>
                </div>
              </div>

              <button
                type="button"
                onClick={() => setVideoToDelete(null)}
                className="h-8 w-8 rounded-full bg-muted/80 hover:bg-muted flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="rounded-2xl bg-muted/40 border border-border/80 p-3.5 space-y-2">
              <p className="text-xs sm:text-sm text-foreground font-bold line-clamp-2">
                "{videoToDelete.title}"
              </p>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Video này cùng toàn bộ các câu thoại phụ đề đã trích xuất, phân đoạn nhịp câu và dữ liệu luyện tập liên quan sẽ bị xóa vĩnh viễn khỏi thư viện.
              </p>
            </div>

            <div className="flex items-center gap-2.5 pt-2">
              <Button
                variant="outline"
                size="md"
                onClick={() => setVideoToDelete(null)}
                disabled={isDeleting}
                className="flex-1 text-xs font-bold rounded-xl"
              >
                Hủy bỏ
              </Button>

              <Button
                variant="danger"
                size="md"
                onClick={handleConfirmDelete}
                disabled={isDeleting}
                className="flex-1 text-xs font-bold gap-1.5 rounded-xl shadow-md"
              >
                {isDeleting ? (
                  <>
                    <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                    <span>Đang xóa...</span>
                  </>
                ) : (
                  <>
                    <Trash2 className="h-3.5 w-3.5" />
                    <span>Xác nhận xóa</span>
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
