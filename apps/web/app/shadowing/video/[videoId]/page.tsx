"use client";

import React, { useRef, useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Youtube,
  Sparkles,
  BookOpen,
  Clock,
  Zap,
  Play,
  RotateCcw,
  Headphones,
  Award,
  Layers,
  Repeat,
  Volume2,
  Languages,
  AlertCircle,
  X,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { HeadphoneRecommendation } from "@/features/shadowing/HeadphoneRecommendation";
import { RecommendedClipsPanel } from "@/features/shadowing/RecommendedClipsPanel";
import { SegmentDetailPanel } from "@/features/shadowing/SegmentDetailPanel";
import { ShadowingControls } from "@/features/shadowing/ShadowingControls";
import { ABLoopControls } from "@/features/shadowing/ABLoopControls";
import { LiveSpeechPreviewCard } from "@/features/shadowing/LiveSpeechPreviewCard";
import { ShadowingScoreDisplay } from "@/features/shadowing/ShadowingScoreDisplay";
import { TranscriptPanel } from "@/features/shadowing/TranscriptPanel";
import { ThemeToggle } from "@/components/theme-toggle";
import { YoutubePlayer, YoutubePlayerRef } from "@/features/shadowing/YoutubePlayer";
import { FuriganaRubyText } from "@/components/japanese/FuriganaRubyText";
import { useShadowing } from "@/hooks/use-shadowing";
import { useFuriganaSettings } from "@/hooks/use-furigana-settings";
import { useShadowingKeybindings } from "@/hooks/use-shadowing-keybindings";
import { shadowingApi } from "@/services/shadowing-api";
import { soundFX } from "@/lib/sound-fx";
import { ShadowingCandidate, TranscriptSegment } from "@/types/shadowing";
import { cn } from "@/lib/utils";

export default function ShadowingVideoStudioPage() {
  const params = useParams();
  const router = useRouter();
  const videoId = params.videoId as string;
  const playerRef = useRef<YoutubePlayerRef | null>(null);

  const { furiganaClass, furiganaStyle } = useFuriganaSettings();

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
    practiceStep,
    pauseAtTime,
    setPauseAtTime,
    startGuidedPractice,
    handlePauseAtTimeReached,
    cancelPractice,
    loopRange,
    loopGap,
    setLoopGap,
    toggleLoop,
    setMarkerA,
    setMarkerB,
    adjustMarkerA,
    adjustMarkerB,
    setExactLoopRange,
    expandLoopToNextSegment,
    expandLoopToPrevSegment,
    selectAndLoopSegment,
    loopCurrentSegment,
    clearLoop,
    selectNextSegment,
    selectPrevSegment,
    startRecording,
    stopRecording,
    isRecording,
    isEvaluating,
    lastFeedback,
    evaluationError,
    clearEvaluationError,
    volumeLevel,
    liveTranscript,
    interimTranscript,
  } = useShadowing(videoId);

  const [isCreatingLesson, setIsCreatingLesson] = useState(false);
  const [activeTab, setActiveTab] = useState<"transcript" | "analysis">("transcript");

  const { keybindings, matchesAction } = useShadowingKeybindings();

  const handleTriggerPractice = useCallback(() => {
    if (isRecording) {
      soundFX.playTaiko();
      stopRecording();
      return;
    }

    soundFX.playTaiko();
    if (shadowingMode === "repeat") {
      if (practiceStep === "prompting") {
        // Step 2: User is ready to speak. Start recording ONLY; ensure video is strictly paused!
        playerRef.current?.pause();
        startRecording();
      } else {
        // Step 1: Listen to reference sentence.
        startGuidedPractice(playerRef.current || undefined);
      }
    } else if (shadowingMode === "listen_shadow") {
      startGuidedPractice(playerRef.current || undefined);
    } else {
      // Direct recording mode: strictly pause video and record voice cleanly!
      playerRef.current?.pause();
      startRecording();
    }
  }, [
    isRecording,
    stopRecording,
    shadowingMode,
    practiceStep,
    startRecording,
    startGuidedPractice,
  ]);

  const handlePlaySegment = useCallback(() => {
    if (selectedSegment) {
      setPauseAtTime(selectedSegment.end_time);
      playerRef.current?.seekTo(selectedSegment.start_time);
      playerRef.current?.play();
    }
  }, [selectedSegment, setPauseAtTime]);

  const handleSelectSegmentWithAutoPause = useCallback((segment: TranscriptSegment) => {
    setSelectedSegment(segment);
    if (shadowingMode === "repeat" || shadowingMode === "listen_shadow") {
      setPauseAtTime(segment.end_time);
      playerRef.current?.seekTo(segment.start_time);
      playerRef.current?.play();
    } else {
      playerRef.current?.seekTo(segment.start_time);
    }
  }, [setSelectedSegment, shadowingMode, setPauseAtTime]);

  const handlePauseReached = useCallback(() => {
    handlePauseAtTimeReached(playerRef.current || undefined);
  }, [handlePauseAtTimeReached]);

  const handleCancelPractice = useCallback(() => {
    cancelPractice(playerRef.current || undefined);
  }, [cancelPractice]);

  const handleRetryPractice = useCallback(() => {
    if (shadowingMode === "shadow") {
      playerRef.current?.pause();
      startRecording();
    } else {
      startGuidedPractice(playerRef.current || undefined);
    }
  }, [shadowingMode, startRecording, startGuidedPractice]);

  const recommendedSegmentIds = React.useMemo(() => {
    return new Set((video?.recommended_segments || []).map((r) => r.segment_id));
  }, [video?.recommended_segments]);

  const hasMultipleSpeakers = React.useMemo(() => {
    const set = new Set((video?.segments || []).map((s) => s.speaker_id).filter(Boolean));
    return set.size > 1;
  }, [video?.segments]);

  // Keyboard Shortcuts for Shadowing
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName?.toLowerCase();
      if (tag === "input" || tag === "textarea") return;

      if (matchesAction(e, "toggleLoop")) {
        e.preventDefault();
        toggleLoop();
      } else if (matchesAction(e, "markerA")) {
        e.preventDefault();
        setMarkerA();
      } else if (matchesAction(e, "markerB")) {
        e.preventDefault();
        setMarkerB();
      } else if (matchesAction(e, "replay")) {
        e.preventDefault();
        handlePlaySegment();
      } else if (matchesAction(e, "nextSegment")) {
        e.preventDefault();
        soundFX.playFurin();
        selectNextSegment();
      } else if (matchesAction(e, "prevSegment")) {
        e.preventDefault();
        soundFX.playFurin();
        selectPrevSegment();
      } else if (matchesAction(e, "toggleMic")) {
        e.preventDefault();
        handleTriggerPractice();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [
    matchesAction,
    toggleLoop,
    setMarkerA,
    setMarkerB,
    handlePlaySegment,
    selectNextSegment,
    selectPrevSegment,
    handleTriggerPractice,
  ]);

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[65vh] space-y-4">
        <div className="relative w-12 h-12 flex items-center justify-center">
          <div className="absolute inset-0 rounded-full border-4 border-primary/20 border-t-primary animate-spin" />
        </div>
        <p className="text-sm font-bold text-foreground font-sans">
          Đang chuẩn bị phòng luyện Shadowing...
        </p>
        <p className="text-xs text-muted-foreground">Đang tải phụ đề và đồng bộ audio</p>
      </div>
    );
  }

  if (error || !video) {
    return (
      <div className="max-w-xl mx-auto p-8 text-center space-y-4">
        <div className="p-4 rounded-2xl bg-rose-950/40 border border-rose-500/40 text-rose-200 text-sm font-medium">
          {error || "Video không tồn tại hoặc đã bị xóa."}
        </div>
        <Link href="/shadowing">
          <Button variant="outline" size="sm" className="rounded-xl">
            <ArrowLeft className="h-4 w-4 mr-2" />
            <span>Quay lại thư viện Shadowing</span>
          </Button>
        </Link>
      </div>
    );
  }

  const handleSeek = (seconds: number) => {
    playerRef.current?.seekTo(seconds);
  };

  const handleSelectCandidate = (cand: ShadowingCandidate) => {
    const matched = video.segments.find((s) => s.id === cand.segment_id);
    if (matched) {
      handleSelectSegmentWithAutoPause(matched);
    }
  };

  const handleCreateLesson = async (minutes: number) => {
    soundFX.playTaiko();
    setIsCreatingLesson(true);
    try {
      const lesson = await shadowingApi.createLesson(video.id, minutes, "quick_shadow");
      router.push(`/shadowing/video/${video.video_id}/lesson/${lesson.id}`);
    } catch (e) {
      console.error("Lesson creation error:", e);
    } finally {
      setIsCreatingLesson(false);
    }
  };

  const handleAddToLearning = async (key: string, title: string, itemType: string) => {
    try {
      console.log(`[Shadowing] Added ${key} (${itemType}) to learning roadmap`);
    } catch (e) {
      console.warn("Add to learning warning:", e);
    }
  };

  return (
    <div className="max-w-[1700px] mx-auto p-3 sm:p-6 space-y-6 animate-in fade-in duration-200">
      {/* Top Bar: Navigation & Video Info */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-border/80">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2.5">
            <Link
              href="/shadowing"
              className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition font-semibold"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Thư viện Shadowing</span>
            </Link>
            <span className="text-border">•</span>
            <Badge variant="jlpt" size="sm" className="font-bold">
              JLPT {video.overall_difficulty.toUpperCase()}
            </Badge>
            <span className="text-border">•</span>
            <span className="text-xs text-muted-foreground font-mono">
              {Math.floor((video.duration_seconds || 0) / 60)}:{((video.duration_seconds || 0) % 60).toString().padStart(2, "0")}
            </span>
          </div>

          <h1 className="text-xl sm:text-2xl font-black text-foreground font-sans tracking-tight">
            {video.title}
          </h1>
        </div>

        {/* Quick Lesson Generators & Theme Toggle */}
        <div className="flex items-center gap-2 shrink-0">
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleCreateLesson(5)}
            disabled={isCreatingLesson}
            className="text-xs sm:text-sm font-bold h-9 px-3.5 rounded-xl bg-card border-border hover:border-primary/50 shadow-sm gap-1.5"
          >
            <Zap className="h-4 w-4 text-primary" />
            <span>5 phút</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => handleCreateLesson(10)}
            disabled={isCreatingLesson}
            className="text-xs sm:text-sm font-bold h-9 px-3.5 rounded-xl bg-card border-border hover:border-accent/50 shadow-sm gap-1.5"
          >
            <Zap className="h-4 w-4 text-accent" />
            <span>10 phút</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => handleCreateLesson(20)}
            disabled={isCreatingLesson}
            className="text-xs sm:text-sm font-bold h-9 px-3.5 rounded-xl bg-card border-border hover:border-aizome-500/50 shadow-sm gap-1.5"
          >
            <Zap className="h-4 w-4 text-aizome-400" />
            <span>20 phút</span>
          </Button>

          <ThemeToggle />
        </div>
      </div>

      {/* Headphone Recommendation Notice */}
      <HeadphoneRecommendation />

      {/* Main Studio Workspace: 2-Column Responsive Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: YouTube Player + Controls + Feedback (6 cols) */}
        <div className="lg:col-span-6 space-y-5">
          {/* YouTube Video Player */}
          <div className="rounded-2xl overflow-hidden shadow-sumi-lg border border-border/90 bg-card">
            <YoutubePlayer
              ref={playerRef}
              videoId={video.video_id}
              onTimeUpdate={setCurrentPlaybackTime}
              loopRange={loopRange}
              loopGap={loopGap}
              pauseAtTime={pauseAtTime}
              onPauseAtTimeReached={handlePauseReached}
              playbackSpeed={playbackSpeed}
            />
          </div>

          {/* Active Sentence Focus Card (Hero Focus) */}
          {selectedSegment && (
            <div
              onClick={() => {
                soundFX.playFurin();
                handlePlaySegment();
              }}
              className="cursor-pointer p-4 sm:p-5 rounded-2xl bg-card/95 border border-primary/40 washi-texture shadow-sumi-md space-y-2 ring-1 ring-primary/20 hover:border-primary transition-all animate-in fade-in"
              title="Bấm để nghe câu này"
            >
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span className="flex items-center gap-1.5 font-mono font-bold text-primary">
                  <Play className="h-3.5 w-3.5 fill-current" />
                  <span>Câu đang chọn luyện</span>
                </span>
                <span className="font-mono">
                  {hasMultipleSpeakers && `${selectedSegment.speaker_id || "Speaker"} • `}
                  {(selectedSegment.end_time - selectedSegment.start_time).toFixed(1)}s
                </span>
              </div>

              <div className="py-1">
                <FuriganaRubyText
                  text={selectedSegment.normalized_text}
                  reading={selectedSegment.reading}
                  ruby={selectedSegment.ruby}
                  vocabulary={selectedSegment.vocabulary}
                  displayMode="kanji_reading"
                  fontSize="large"
                  furiganaStyle={furiganaStyle}
                />
              </div>
            </div>
          )}

          {/* Interactive Shadowing Controls Dock */}
          <ShadowingControls
            segment={selectedSegment}
            playbackSpeed={playbackSpeed}
            onSpeedChange={(s) => {
              setPlaybackSpeed(s);
              playerRef.current?.setSpeed(s);
            }}
            shadowingMode={shadowingMode}
            onModeChange={setShadowingMode}
            isLooping={isLooping}
            onToggleLoop={toggleLoop}
            onPlaySegment={handlePlaySegment}
            onStartRecording={handleTriggerPractice}
            onStopRecording={stopRecording}
            onCancelPractice={handleCancelPractice}
            isRecording={isRecording}
            isEvaluating={isEvaluating}
            practiceStep={practiceStep}
            keybindings={keybindings}
          />

          {/* Backend / Evaluation Error Banner */}
          {evaluationError && (
            <div className="p-4 rounded-2xl bg-destructive/15 border border-destructive/30 text-destructive text-xs sm:text-sm flex items-start justify-between gap-3 shadow-md animate-in fade-in">
              <div className="flex items-start gap-2.5">
                <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <p className="font-bold">Lỗi chấm điểm từ Backend / Whisper</p>
                  <p className="text-foreground/90 text-xs font-mono bg-background/50 p-2 rounded-lg border border-border/60">
                    {evaluationError}
                  </p>
                </div>
              </div>
              <button
                onClick={clearEvaluationError}
                className="p-1.5 rounded-lg hover:bg-destructive/20 transition-colors text-foreground"
                title="Đóng thông báo"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          )}

          {/* Realtime Live Speech Recognition Preview Card */}
          <LiveSpeechPreviewCard
            isRecording={isRecording}
            volumeLevel={volumeLevel}
            liveTranscript={liveTranscript}
            interimTranscript={interimTranscript}
            targetText={selectedSegment?.normalized_text}
          />

          {/* Dedicated A-B Loop Studio Controls (Visual Dual Scrubber & Stepper) - Only visible when isLooping is true */}
          {isLooping && (
            <div className="animate-in fade-in slide-in-from-top-2 duration-200">
              <ABLoopControls
                currentPlaybackTime={currentPlaybackTime}
                selectedSegment={selectedSegment}
                videoDuration={video.duration_seconds || 600}
                isLooping={isLooping}
                loopRange={loopRange}
                loopGap={loopGap}
                onToggleLoop={toggleLoop}
                onSetMarkerA={setMarkerA}
                onSetMarkerB={setMarkerB}
                onAdjustMarkerA={adjustMarkerA}
                onAdjustMarkerB={adjustMarkerB}
                onSetExactLoopRange={setExactLoopRange}
                onExpandToNext={expandLoopToNextSegment}
                onExpandToPrev={expandLoopToPrevSegment}
                onLoopCurrentSegment={loopCurrentSegment}
                onClearLoop={clearLoop}
                onSetLoopGap={setLoopGap}
                onSeek={handleSeek}
              />
            </div>
          )}

          {/* Pronunciation Feedback Display */}
          {lastFeedback && (
            <ShadowingScoreDisplay
              feedback={lastFeedback}
              targetSentence={selectedSegment?.normalized_text}
              onRetry={handleRetryPractice}
              onNext={selectNextSegment}
            />
          )}
        </div>

        {/* Right Column: Transcript & Linguistic Intelligence (6 cols) */}
        <div className="lg:col-span-6 space-y-4 flex flex-col h-[650px] lg:h-[750px] max-h-[85vh] overflow-hidden">
          {/* Mobile/Tablet Tab Switcher */}
          <div className="flex lg:hidden items-center p-1 rounded-2xl bg-card border border-border shrink-0">
            <button
              onClick={() => setActiveTab("transcript")}
              className={cn(
                "flex-1 py-2 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5",
                activeTab === "transcript"
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              <BookOpen className="h-4 w-4" />
              <span>Phụ đề Transcript</span>
            </button>
            <button
              onClick={() => setActiveTab("analysis")}
              className={cn(
                "flex-1 py-2 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5",
                activeTab === "analysis"
                  ? "bg-aizome-600 text-white shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              <Layers className="h-4 w-4" />
              <span>Từ vựng & Ngữ pháp</span>
            </button>
          </div>

          {/* Desktop Dual Split / Mobile Tab Views */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 flex-1 min-h-0 h-full overflow-hidden">
            {/* Transcript Panel */}
            <div className={cn("h-full max-h-full flex flex-col min-h-0 overflow-hidden", activeTab !== "transcript" && "hidden lg:flex")}>
              <TranscriptPanel
                segments={video.segments}
                currentPlaybackTime={currentPlaybackTime}
                selectedSegmentId={selectedSegment?.id}
                recommendedSegmentIds={recommendedSegmentIds}
                isLooping={isLooping}
                loopRange={loopRange}
                onSelectSegment={handleSelectSegmentWithAutoPause}
                onLoopSegment={selectAndLoopSegment}
                onSeek={handleSeek}
              />
            </div>

            {/* Linguistic Details Panel */}
            <div className={cn("h-full max-h-full flex flex-col min-h-0 overflow-hidden", activeTab !== "analysis" && "hidden lg:flex")}>
              <SegmentDetailPanel
                segment={selectedSegment}
                onAddToLearning={handleAddToLearning}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Bottom: Recommended Clips Panel */}
      {video.recommended_segments && video.recommended_segments.length > 0 && (
        <div className="pt-6 border-t border-border/80">
          <RecommendedClipsPanel
            candidates={video.recommended_segments}
            onSelectCandidate={handleSelectCandidate}
          />
        </div>
      )}
    </div>
  );
}
