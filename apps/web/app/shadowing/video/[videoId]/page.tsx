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
  Keyboard,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { KaraokeSubtitleBar } from "@/features/shadowing/KaraokeSubtitleBar";
import { ShadowingControls } from "@/features/shadowing/ShadowingControls";
import { LiveSpeechPreviewCard } from "@/features/shadowing/LiveSpeechPreviewCard";
import { ShadowingScoreDisplay } from "@/features/shadowing/ShadowingScoreDisplay";
import { TranscriptPanel } from "@/features/shadowing/TranscriptPanel";
import { YoutubePlayer, YoutubePlayerRef } from "@/features/shadowing/YoutubePlayer";
import { useShadowing } from "@/hooks/use-shadowing";
import { useFuriganaSettings } from "@/hooks/use-furigana-settings";
import { useShadowingKeybindings } from "@/hooks/use-shadowing-keybindings";
import { soundFX } from "@/lib/sound-fx";
import { TranscriptSegment } from "@/types/shadowing";
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
    displaySubtitleMode,
    setDisplaySubtitleMode,
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
    loopCurrentSegment,
    clearLoop,
    selectNextSegment,
    selectPrevSegment,
    startRecording,
    stopRecording,
    submitTextShadowing,
    isRecording,
    isEvaluating,
    lastFeedback,
    evaluationError,
    clearEvaluationError,
    volumeLevel,
    liveTranscript,
    interimTranscript,
    bookmarkedSegmentIds,
    toggleBookmark,
    segmentScores,
    autoPilot,
    setAutoPilot,
    applyPedagogicalLevel,
  } = useShadowing(videoId);

  const [showHelpModal, setShowHelpModal] = useState(false);

  const { keybindings, matchesAction } = useShadowingKeybindings();

  // Unified trigger practice callback
  const handleTriggerPractice = useCallback(() => {
    if (isRecording) {
      soundFX.playTaiko();
      stopRecording();
      return;
    }

    soundFX.playTaiko();
    if (shadowingMode === "repeat") {
      if (practiceStep === "prompting") {
        playerRef.current?.pause();
        startRecording();
      } else {
        startGuidedPractice(playerRef.current || undefined);
      }
    } else if (shadowingMode === "listen_shadow") {
      startGuidedPractice(playerRef.current || undefined);
    } else {
      playerRef.current?.pause();
      startRecording();
    }
  }, [isRecording, stopRecording, shadowingMode, practiceStep, startRecording, startGuidedPractice]);

  const handlePlaySegment = useCallback(() => {
    if (selectedSegment) {
      setPauseAtTime(selectedSegment.end_time);
      playerRef.current?.seekTo(selectedSegment.start_time);
      playerRef.current?.play();
    }
  }, [selectedSegment, setPauseAtTime]);

  const handleSelectSegmentWithAutoPause = useCallback(
    (segment: TranscriptSegment) => {
      setSelectedSegment(segment);
      if (shadowingMode === "repeat" || shadowingMode === "listen_shadow") {
        setPauseAtTime(segment.end_time);
        playerRef.current?.seekTo(segment.start_time);
        playerRef.current?.play();
      } else {
        playerRef.current?.seekTo(segment.start_time);
      }
    },
    [setSelectedSegment, shadowingMode, setPauseAtTime]
  );

  const handlePauseReached = useCallback(() => {
    handlePauseAtTimeReached(playerRef.current || undefined);
  }, [handlePauseAtTimeReached]);

  const handleRetryPractice = useCallback(() => {
    if (shadowingMode === "shadow") {
      playerRef.current?.pause();
      startRecording();
    } else {
      startGuidedPractice(playerRef.current || undefined);
    }
  }, [shadowingMode, startRecording, startGuidedPractice]);

  // Auto-Pilot Step-by-Step advancement
  useEffect(() => {
    if (autoPilot && lastFeedback && lastFeedback.score >= 80) {
      const timer = setTimeout(() => {
        soundFX.playTaiko();
        selectNextSegment();
      }, 3500);
      return () => clearTimeout(timer);
    }
  }, [autoPilot, lastFeedback, selectNextSegment]);

  // Keyboard Shortcuts for Shadowing
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName?.toLowerCase();
      if (tag === "input" || tag === "textarea") return;

      if (matchesAction(e, "toggleLoop")) {
        e.preventDefault();
        toggleLoop();
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
      } else if (matchesAction(e, "toggleMic") || e.code === "Space") {
        e.preventDefault();
        handleTriggerPractice();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [
    matchesAction,
    toggleLoop,
    handlePlaySegment,
    selectNextSegment,
    selectPrevSegment,
    handleTriggerPractice,
  ]);

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-3">
        <Sparkles className="h-8 w-8 text-primary animate-spin" />
        <p className="text-xs font-bold text-muted-foreground">Đang tải video và đồng bộ phụ đề...</p>
      </div>
    );
  }

  if (error || !video) {
    return (
      <div className="p-8 rounded-3xl border border-destructive/30 bg-destructive/5 text-center space-y-4 max-w-xl mx-auto mt-12">
        <AlertCircle className="h-10 w-10 text-destructive mx-auto" />
        <h2 className="text-base font-bold text-foreground">Không thể tải thông tin video</h2>
        <p className="text-xs text-muted-foreground">{error || "Video không tồn tại hoặc đã bị xóa."}</p>
        <Link href="/shadowing">
          <Button variant="outline" size="sm" className="rounded-xl">
            Quay lại danh sách video
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-3 animate-in fade-in duration-200 max-w-7xl mx-auto pb-6">
      {/* 1. Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 p-3 px-4 rounded-2xl border border-border bg-card washi-texture shadow-2xs">
        <div className="flex items-center gap-2.5 min-w-0">
          <Link
            href="/shadowing"
            className="p-1.5 rounded-xl hover:bg-muted text-muted-foreground hover:text-foreground transition-colors shrink-0"
            title="Quay lại thư viện video"
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>

          <div className="flex items-center gap-2 min-w-0">
            <span className="p-1.5 rounded-lg bg-rose-500/10 text-rose-500 shrink-0">
              <Youtube className="h-4 w-4" />
            </span>
            <div className="min-w-0">
              <h1 className="text-xs sm:text-sm font-bold text-foreground truncate font-jp">
                {video.title}
              </h1>
              <div className="text-[10px] text-muted-foreground truncate">
                {video.channel_name || "YouTube Shadowing"} • {video.segments?.length || 0} câu thoại
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <Badge variant="sakura" size="sm" className="font-bold text-[10px]">
            {video.overall_difficulty || "N3-N2"}
          </Badge>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowHelpModal(true)}
            className="h-8 px-2 text-xs rounded-xl border-border gap-1 text-muted-foreground hover:text-foreground"
            title="Phím tắt (?)"
          >
            <Keyboard className="h-3.5 w-3.5 text-primary" />
            <span className="hidden sm:inline">Phím tắt</span>
          </Button>
        </div>
      </div>

      {/* 2. Zero-Scroll Cinema Cockpit (2 Columns) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-3.5 items-start">
        {/* Left Column (7/12 - 58%): Video Player + Subtitle Bar + Live Speech */}
        <div className="lg:col-span-7 space-y-3">
          {/* YouTube Player Container (16:9 Aspect Ratio) */}
          <div className="relative aspect-video rounded-2xl overflow-hidden border border-border/80 bg-black shadow-sm">
            <YoutubePlayer
              ref={playerRef}
              videoId={video.video_id || videoId}
              onTimeUpdate={(t) => setCurrentPlaybackTime(t)}
              loopRange={loopRange}
              loopGap={loopGap}
              pauseAtTime={pauseAtTime}
              onPauseAtTimeReached={handlePauseReached}
              playbackSpeed={playbackSpeed}
              autoPlay={false}
            />
          </div>

          {/* Karaoke Subtitle Bar (Highlight + Furigana + Translation) */}
          <KaraokeSubtitleBar
            segment={selectedSegment}
            currentPlaybackTime={currentPlaybackTime}
            displayMode={displaySubtitleMode}
            onToggleDisplayMode={() =>
              setDisplaySubtitleMode((m) =>
                m === "bilingual" ? "japanese_reading" : m === "japanese_reading" ? "hidden" : "bilingual"
              )
            }
            isBookmarked={selectedSegment ? bookmarkedSegmentIds.has(selectedSegment.id) : false}
            onToggleBookmark={() => selectedSegment && toggleBookmark(selectedSegment.id)}
            onPlaySegment={handlePlaySegment}
            highestScore={selectedSegment ? segmentScores[selectedSegment.id] : undefined}
          />

          {/* Live Speech Recognition & Sóng âm Live */}
          {(isRecording || liveTranscript || interimTranscript) && (
            <LiveSpeechPreviewCard
              isRecording={isRecording}
              volumeLevel={volumeLevel}
              liveTranscript={liveTranscript}
              interimTranscript={interimTranscript}
            />
          )}

          {/* Evaluation Error Banner */}
          {evaluationError && (
            <div className="p-3 rounded-xl bg-destructive/10 border border-destructive/30 text-destructive text-xs font-bold flex items-center justify-between gap-2 animate-in fade-in">
              <span>⚠️ {evaluationError}</span>
              <button
                type="button"
                onClick={clearEvaluationError}
                className="p-1 hover:bg-destructive/20 rounded-lg text-xs"
              >
                ✕
              </button>
            </div>
          )}
        </div>

        {/* Right Column (5/12 - 42%): Playlist + Studio Controls + Score Display */}
        <div className="lg:col-span-5 space-y-3">
          {/* Studio Controls (Speed, 4-Step Flow, CTA Button, Autopilot) */}
          <ShadowingControls
            segment={selectedSegment}
            playbackSpeed={playbackSpeed}
            onSpeedChange={(s) => setPlaybackSpeed(s)}
            shadowingMode={shadowingMode}
            onModeChange={(m) => setShadowingMode(m)}
            isLooping={isLooping}
            onToggleLoop={toggleLoop}
            onPlaySegment={handlePlaySegment}
            onTriggerPractice={handleTriggerPractice}
            onCancelPractice={() => cancelPractice(playerRef.current || undefined)}
            isRecording={isRecording}
            isEvaluating={isEvaluating}
            practiceStep={practiceStep}
            keybindings={keybindings}
            autoPilot={autoPilot}
            onToggleAutoPilot={() => setAutoPilot((v) => !v)}
            onApplyPedagogicalLevel={applyPedagogicalLevel}
            onSubmitTextPractice={submitTextShadowing}
          />

          {/* Evaluation Result Card (Displays after speaking) */}
          {lastFeedback && (
            <ShadowingScoreDisplay
              feedback={lastFeedback}
              targetSentence={selectedSegment?.text}
              onRetry={handleRetryPractice}
              onNext={selectNextSegment}
              onPlayReference={handlePlaySegment}
            />
          )}

          {/* Playlist Panel (Tabs: All, Bookmarked, Weak) */}
          <TranscriptPanel
            segments={video.segments || []}
            currentPlaybackTime={currentPlaybackTime}
            selectedSegmentId={selectedSegment?.id}
            bookmarkedSegmentIds={bookmarkedSegmentIds}
            onToggleBookmark={toggleBookmark}
            segmentScores={segmentScores}
            onSelectSegment={handleSelectSegmentWithAutoPause}
            onSeek={(t) => playerRef.current?.seekTo(t)}
          />
        </div>
      </div>

      {/* Keyboard Shortcuts Modal */}
      {showHelpModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in">
          <div className="bg-card border border-border rounded-3xl p-5 sm:p-6 max-w-md w-full washi-texture shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-border/60 pb-3">
              <div className="flex items-center gap-2">
                <Keyboard className="h-5 w-5 text-primary" />
                <h3 className="text-sm font-bold text-foreground">Bảng Phím Tắt Shadowing Studio</h3>
              </div>
              <button
                type="button"
                onClick={() => setShowHelpModal(false)}
                className="p-1 rounded-lg hover:bg-muted text-muted-foreground"
              >
                ✕
              </button>
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between p-2 rounded-xl bg-muted/40 border border-border/60">
                <span className="text-muted-foreground">Bắt đầu thu âm / Dừng & chấm:</span>
                <kbd className="px-2 py-0.5 rounded bg-card border font-mono font-bold">Space</kbd> hoặc <kbd className="px-2 py-0.5 rounded bg-card border font-mono font-bold">Q</kbd>
              </div>
              <div className="flex items-center justify-between p-2 rounded-xl bg-muted/40 border border-border/60">
                <span className="text-muted-foreground">Phát lại câu mẫu:</span>
                <kbd className="px-2 py-0.5 rounded bg-card border font-mono font-bold">C</kbd>
              </div>
              <div className="flex items-center justify-between p-2 rounded-xl bg-muted/40 border border-border/60">
                <span className="text-muted-foreground">Bật / Tắt lặp lại câu này:</span>
                <kbd className="px-2 py-0.5 rounded bg-card border font-mono font-bold">L</kbd>
              </div>
              <div className="flex items-center justify-between p-2 rounded-xl bg-muted/40 border border-border/60">
                <span className="text-muted-foreground">Chuyển sang câu kế tiếp:</span>
                <kbd className="px-2 py-0.5 rounded bg-card border font-mono font-bold">J</kbd>
              </div>
              <div className="flex items-center justify-between p-2 rounded-xl bg-muted/40 border border-border/60">
                <span className="text-muted-foreground">Quay lại câu trước đó:</span>
                <kbd className="px-2 py-0.5 rounded bg-card border font-mono font-bold">K</kbd>
              </div>
            </div>

            <Button
              variant="akane"
              size="sm"
              onClick={() => setShowHelpModal(false)}
              className="w-full rounded-xl font-bold text-xs"
            >
              Đã Hiểu (Đóng)
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
