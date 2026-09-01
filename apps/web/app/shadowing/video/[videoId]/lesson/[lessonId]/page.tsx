"use client";

import React, { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  CheckCircle2,
  ChevronRight,
  Sparkles,
  Trophy,
  Play,
  RotateCcw,
  Zap,
  Award,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { HeadphoneRecommendation } from "@/features/shadowing/HeadphoneRecommendation";
import { SegmentDetailPanel } from "@/features/shadowing/SegmentDetailPanel";
import { ShadowingControls } from "@/features/shadowing/ShadowingControls";
import { ShadowingScoreDisplay } from "@/features/shadowing/ShadowingScoreDisplay";
import { YoutubePlayer, YoutubePlayerRef } from "@/features/shadowing/YoutubePlayer";
import { useShadowing } from "@/hooks/use-shadowing";
import { PracticeAttemptFeedback } from "@/types/shadowing";

export default function ShadowingLessonPage() {
  const params = useParams();
  const router = useRouter();
  const videoId = params.videoId as string;
  const lessonId = params.lessonId as string;
  const playerRef = useRef<YoutubePlayerRef | null>(null);

  const {
    video,
    isLoading,
    error,
    currentPlaybackTime,
    setCurrentPlaybackTime,
    selectedSegment,
    setSelectedSegment,
    playbackSpeed,
    setPlaybackSpeed,
    shadowingMode,
    setShadowingMode,
    isLooping,
    toggleLoop,
    startRecording,
    stopRecording,
    submitTextShadowing,
    isRecording,
    isEvaluating,
    lastFeedback,
  } = useShadowing(videoId);

  const [currentIndex, setCurrentIndex] = useState(0);
  const [completedScores, setCompletedScores] = useState<Record<string, number>>({});
  const [isLessonCompleted, setIsLessonCompleted] = useState(false);

  const lessonSegments = (video?.recommended_segments && video.recommended_segments.length > 0)
    ? video.segments.filter((s) => video.recommended_segments.some((r) => r.segment_id === s.id))
    : video?.segments.slice(0, 5) || [];

  const currentSegment = lessonSegments[currentIndex] || selectedSegment;

  useEffect(() => {
    if (currentSegment) {
      setSelectedSegment(currentSegment);
      playerRef.current?.seekTo(currentSegment.start_time);
    }
  }, [currentIndex, currentSegment?.id]);

  useEffect(() => {
    if (lastFeedback && currentSegment) {
      setCompletedScores((prev) => ({
        ...prev,
        [currentSegment.id]: Math.round(lastFeedback.score),
      }));
    }
  }, [lastFeedback, currentSegment?.id]);

  const handleNext = () => {
    if (currentIndex < lessonSegments.length - 1) {
      setCurrentIndex((prev) => prev + 1);
    } else {
      setIsLessonCompleted(true);
    }
  };

  const handlePlayCurrent = () => {
    if (currentSegment) {
      playerRef.current?.seekTo(currentSegment.start_time);
      playerRef.current?.play();
    }
  };

  if (isLoading || !video) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <div className="w-10 h-10 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
        <p className="text-xs text-muted-foreground font-medium">Đang chuẩn bị bài học Shadowing...</p>
      </div>
    );
  }

  const loopRange = isLooping && currentSegment
    ? { start: currentSegment.start_time, end: currentSegment.end_time }
    : null;

  const avgScore =
    Object.values(completedScores).length > 0
      ? Math.round(
          Object.values(completedScores).reduce((a, b) => a + b, 0) /
            Object.values(completedScores).length
        )
      : 0;

  return (
    <div className="max-w-6xl mx-auto p-4 md:p-8 space-y-6">
      {/* Lesson Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-border">
        <div className="space-y-1">
          <Link
            href={`/shadowing/video/${video.video_id}`}
            className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Quay lại phòng luyện tự do</span>
          </Link>
          <h1 className="text-lg md:text-2xl font-bold text-foreground">
            Bài luyện Shadowing tập trung — {video.title}
          </h1>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-muted-foreground">
            Tiến độ: {Object.keys(completedScores).length} / {lessonSegments.length} câu
          </span>
        </div>
      </div>

      <HeadphoneRecommendation />

      {isLessonCompleted ? (
        /* Celebration / Completion Screen */
        <div className="p-8 rounded-3xl bg-card/90 border border-border backdrop-blur-xl text-center space-y-6 max-w-xl mx-auto animate-in zoom-in-95">
          <div className="inline-flex p-4 rounded-3xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <Trophy className="h-10 w-10 animate-bounce" />
          </div>

          <div className="space-y-2">
            <h2 className="text-xl font-bold text-foreground">
              Hoàn thành xuất sắc bài luyện! (完了)
            </h2>
            <p className="text-xs text-muted-foreground max-w-md mx-auto">
              Bạn đã luyện tập trọn vẹn các câu thoại trọng tâm của video. Điểm phát âm và từ vựng đã được đồng bộ vào Mastery Engine.
            </p>
          </div>

          <div className="p-4 rounded-2xl bg-background/80 border border-border inline-flex items-center gap-6">
            <div className="text-center">
              <span className="text-[10px] text-muted-foreground uppercase font-semibold">Điểm TB</span>
              <p className="text-2xl font-extrabold font-mono text-primary">{avgScore}</p>
            </div>
            <div className="h-8 w-px bg-muted" />
            <div className="text-center">
              <span className="text-[10px] text-muted-foreground uppercase font-semibold">Số câu</span>
              <p className="text-2xl font-extrabold font-mono text-indigo-400">{lessonSegments.length}</p>
            </div>
          </div>

          <div className="flex items-center justify-center gap-3 pt-2">
            <Button
              variant="outline"
              size="md"
              onClick={() => {
                setIsLessonCompleted(false);
                setCurrentIndex(0);
              }}
            >
              <RotateCcw className="h-4 w-4 mr-1.5" />
              <span>Luyện lại</span>
            </Button>
            <Link href={`/shadowing/video/${video.video_id}`}>
              <Button variant="primary" size="md">
                <span>Trở về Video Studio</span>
                <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            </Link>
          </div>
        </div>
      ) : (
        /* Active Lesson Workspace */
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Player & Controls (7 cols) */}
          <div className="lg:col-span-7 space-y-4">
            {/* Step indicator */}
            <div className="flex items-center justify-between p-3 rounded-xl bg-card/60 border border-border text-xs">
              <span className="font-semibold text-primary">
                Câu {currentIndex + 1} / {lessonSegments.length}
              </span>
              <div className="flex items-center gap-1.5">
                {lessonSegments.map((s, idx) => (
                  <div
                    key={s.id || idx}
                    className={`w-3 h-3 rounded-full transition ${
                      completedScores[s.id]
                        ? "bg-emerald-500"
                        : idx === currentIndex
                        ? "bg-primary ring-2 ring-primary/30"
                        : "bg-muted"
                    }`}
                  />
                ))}
              </div>
            </div>

            <YoutubePlayer
              ref={playerRef}
              videoId={video.video_id}
              onTimeUpdate={setCurrentPlaybackTime}
              loopRange={loopRange}
              playbackSpeed={playbackSpeed}
            />

            <ShadowingControls
              segment={currentSegment}
              playbackSpeed={playbackSpeed}
              onSpeedChange={(s) => {
                setPlaybackSpeed(s);
                playerRef.current?.setSpeed(s);
              }}
              shadowingMode={shadowingMode}
              onModeChange={setShadowingMode}
              isLooping={isLooping}
              onToggleLoop={toggleLoop}
              onPlaySegment={handlePlayCurrent}
              onStartRecording={() => {
                playerRef.current?.pause();
                startRecording();
              }}
              onStopRecording={stopRecording}
              isRecording={isRecording}
              isEvaluating={isEvaluating}
              onSubmitTextPractice={submitTextShadowing}
            />

            {lastFeedback && (
              <div className="space-y-3">
                <ShadowingScoreDisplay
                  feedback={lastFeedback}
                  onRetry={handlePlayCurrent}
                />

                <div className="flex justify-end">
                  <Button
                    variant="primary"
                    size="md"
                    onClick={handleNext}
                    className="bg-emerald-600 hover:bg-emerald-700 text-xs"
                  >
                    <span>
                      {currentIndex < lessonSegments.length - 1
                        ? "Câu tiếp theo"
                        : "Hoàn tất bài học"}
                    </span>
                    <ChevronRight className="h-4 w-4 ml-1" />
                  </Button>
                </div>
              </div>
            )}
          </div>

          {/* Right Column: Segment Linguistic Details (5 cols) */}
          <div className="lg:col-span-5 h-[600px]">
            <SegmentDetailPanel segment={currentSegment} />
          </div>
        </div>
      )}
    </div>
  );
}
