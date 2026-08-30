"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useAudioRecorder } from "@/features/audio/hooks/useAudioRecorder";
import { useLiveSpeechRecognition } from "@/hooks/use-live-speech-recognition";
import { shadowingApi } from "@/services/shadowing-api";
import {
  PracticeAttemptFeedback,
  ShadowingMode,
  ShadowingVideoDetail,
  TranscriptSegment,
} from "@/types/shadowing";

export function useShadowing(videoId: string) {
  const [video, setVideo] = useState<ShadowingVideoDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Playback & Segment State
  const [currentPlaybackTime, setCurrentPlaybackTime] = useState(0);
  const [selectedSegment, setSelectedSegment] = useState<TranscriptSegment | null>(null);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(() => {
    if (typeof window === "undefined") return 1.0;
    try {
      const saved = localStorage.getItem("speaking_shadowing_speed");
      return saved ? parseFloat(saved) || 1.0 : 1.0;
    } catch {
      return 1.0;
    }
  });

  const [shadowingMode, setShadowingMode] = useState<ShadowingMode>(() => {
    if (typeof window === "undefined") return "repeat";
    try {
      const saved = localStorage.getItem("speaking_shadowing_mode");
      return (saved as ShadowingMode) || "repeat";
    } catch {
      return "repeat";
    }
  });

  const [displaySubtitleMode, setDisplaySubtitleMode] = useState<
    "bilingual" | "japanese" | "japanese_reading" | "hidden"
  >(() => {
    if (typeof window === "undefined") return "bilingual";
    try {
      const saved = localStorage.getItem("speaking_shadowing_sub_mode");
      return (saved as any) || "bilingual";
    } catch {
      return "bilingual";
    }
  });

  const [isLooping, setIsLooping] = useState(false);
  const [loopRange, setLoopRange] = useState<{ start: number; end: number } | null>(null);
  const [loopGap, setLoopGap] = useState<number>(() => {
    if (typeof window === "undefined") return 0;
    try {
      const saved = localStorage.getItem("speaking_shadowing_loop_gap");
      return saved ? parseInt(saved, 10) || 0 : 0;
    } catch {
      return 0;
    }
  });

  // Auto-Pilot state
  const [autoPilot, setAutoPilot] = useState<boolean>(() => {
    if (typeof window === "undefined") return false;
    try {
      return localStorage.getItem("speaking_shadowing_autopilot") === "true";
    } catch {
      return false;
    }
  });

  // Bookmarked Segment IDs
  const [bookmarkedSegmentIds, setBookmarkedSegmentIds] = useState<Set<string>>(() => {
    if (typeof window === "undefined") return new Set();
    try {
      const saved = localStorage.getItem(`speaking_shadowing_bookmarks_${videoId}`);
      return saved ? new Set(JSON.parse(saved)) : new Set();
    } catch {
      return new Set();
    }
  });

  // Segment Highest Scores Map
  const [segmentScores, setSegmentScores] = useState<Record<string, number>>(() => {
    if (typeof window === "undefined") return {};
    try {
      const saved = localStorage.getItem(`speaking_shadowing_scores_${videoId}`);
      return saved ? JSON.parse(saved) : {};
    } catch {
      return {};
    }
  });

  // Persist preferences
  useEffect(() => {
    try {
      localStorage.setItem("speaking_shadowing_speed", String(playbackSpeed));
      localStorage.setItem("speaking_shadowing_mode", shadowingMode);
      localStorage.setItem("speaking_shadowing_sub_mode", displaySubtitleMode);
      localStorage.setItem("speaking_shadowing_loop_gap", String(loopGap));
      localStorage.setItem("speaking_shadowing_autopilot", String(autoPilot));
    } catch {}
  }, [playbackSpeed, shadowingMode, displaySubtitleMode, loopGap, autoPilot]);

  useEffect(() => {
    try {
      localStorage.setItem(
        `speaking_shadowing_bookmarks_${videoId}`,
        JSON.stringify(Array.from(bookmarkedSegmentIds))
      );
    } catch {}
  }, [bookmarkedSegmentIds, videoId]);

  useEffect(() => {
    try {
      localStorage.setItem(
        `speaking_shadowing_scores_${videoId}`,
        JSON.stringify(segmentScores)
      );
    } catch {}
  }, [segmentScores, videoId]);

  // Active Practice & Recording State
  const [practiceStep, setPracticeStep] = useState<
    "idle" | "listening" | "prompting" | "recording" | "evaluating"
  >("idle");
  const [pauseAtTime, setPauseAtTime] = useState<number | null>(null);
  const [currentExerciseId, setCurrentExerciseId] = useState<string | null>(null);
  const [currentAttemptId, setCurrentAttemptId] = useState<string | null>(null);
  const exerciseIdRef = useRef<string | null>(null);
  const attemptIdRef = useRef<string | null>(null);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [lastFeedback, setLastFeedback] = useState<PracticeAttemptFeedback | null>(null);
  const [evaluationError, setEvaluationError] = useState<string | null>(null);

  // Audio Recorders & Speech Recognition
  const audioRecorder = useAudioRecorder();
  const liveSpeech = useLiveSpeechRecognition("ja-JP");

  // Fetch video details
  const fetchVideo = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await shadowingApi.getVideo(videoId);
      setVideo(data);
      if (data.segments && data.segments.length > 0) {
        setSelectedSegment(data.segments[0]);
      }
    } catch (e: any) {
      setError(e.message || "Không thể tải thông tin video shadowing.");
    } finally {
      setIsLoading(false);
    }
  }, [videoId]);

  useEffect(() => {
    fetchVideo();
  }, [fetchVideo]);

  // Select segment
  const handleSelectSegment = (segment: TranscriptSegment) => {
    setSelectedSegment(segment);
    setLastFeedback(null);
    setEvaluationError(null);
    liveSpeech.resetTranscript();
  };

  // Toggle bookmark
  const toggleBookmark = (segmentId: string) => {
    setBookmarkedSegmentIds((prev) => {
      const next = new Set(prev);
      if (next.has(segmentId)) {
        next.delete(segmentId);
      } else {
        next.add(segmentId);
      }
      return next;
    });
  };

  // Complete release of microphone whenever shadowing is idle or on unmount
  useEffect(() => {
    if (practiceStep === "idle") {
      audioRecorder.releaseMicrophone();
      liveSpeech.stopListening();
    }
  }, [practiceStep]);

  useEffect(() => {
    return () => {
      audioRecorder.releaseMicrophone();
      liveSpeech.stopListening();
    };
  }, []);

  // When selectedSegment changes and isLooping is active, sync loopRange
  useEffect(() => {
    if (selectedSegment && isLooping && (!loopRange || loopRange.start === selectedSegment.start_time)) {
      setLoopRange({
        start: selectedSegment.start_time,
        end: selectedSegment.end_time,
      });
    }
  }, [selectedSegment, isLooping]);

  // Toggle Loop on Current Segment (1-Click Sentence Snapping)
  const loopCurrentSegment = () => {
    if (!selectedSegment) return;
    setLoopRange({
      start: selectedSegment.start_time,
      end: selectedSegment.end_time,
    });
    setIsLooping(true);
  };

  const handleToggleLoop = () => {
    if (isLooping) {
      setIsLooping(false);
      setLoopRange(null);
    } else {
      if (selectedSegment) {
        setLoopRange({
          start: selectedSegment.start_time,
          end: selectedSegment.end_time,
        });
        setIsLooping(true);
      }
    }
  };

  const clearLoop = () => {
    setIsLooping(false);
    setLoopRange(null);
  };

  // Select Next/Prev Segment
  const selectNextSegment = () => {
    if (!video?.segments || !selectedSegment) return;
    const currIdx = video.segments.findIndex((s) => s.id === selectedSegment.id);
    if (currIdx >= 0 && currIdx < video.segments.length - 1) {
      handleSelectSegment(video.segments[currIdx + 1]);
    }
  };

  const selectPrevSegment = () => {
    if (!video?.segments || !selectedSegment) return;
    const currIdx = video.segments.findIndex((s) => s.id === selectedSegment.id);
    if (currIdx > 0) {
      handleSelectSegment(video.segments[currIdx - 1]);
    }
  };

  // 4-Step Pedagogical Preset Flow
  const applyPedagogicalLevel = (level: 1 | 2 | 3 | 4) => {
    switch (level) {
      case 1: // Mumbling
        setPlaybackSpeed(0.8);
        setShadowingMode("repeat");
        setDisplaySubtitleMode("bilingual");
        break;
      case 2: // Sync Reading
        setPlaybackSpeed(1.0);
        setShadowingMode("repeat");
        setDisplaySubtitleMode("japanese_reading");
        break;
      case 3: // Blind Shadowing
        setPlaybackSpeed(1.0);
        setShadowingMode("repeat");
        setDisplaySubtitleMode("hidden");
        break;
      case 4: // Pro Impersonation
        setPlaybackSpeed(1.1);
        setShadowingMode("listen_shadow");
        setDisplaySubtitleMode("japanese");
        break;
    }
  };

  // Start Guided Practice depending on shadowingMode
  const startGuidedPractice = async (player?: {
    seekTo: (t: number) => void;
    play: () => void;
    pause: () => void;
  }) => {
    if (!selectedSegment) return;

    setLastFeedback(null);
    setEvaluationError(null);

    if (shadowingMode === "repeat") {
      setPracticeStep("listening");
      setPauseAtTime(selectedSegment.end_time);
      player?.seekTo(selectedSegment.start_time);
      player?.play();
    } else if (shadowingMode === "listen_shadow") {
      setPracticeStep("listening");
      setPauseAtTime(selectedSegment.end_time);
      player?.seekTo(selectedSegment.start_time);
      player?.play();
    } else {
      player?.pause();
      setPracticeStep("recording");
      await startRecording();
    }
  };

  // Called when video reaches pauseAtTime
  const handlePauseAtTimeReached = async (player?: {
    seekTo: (t: number) => void;
    play: () => void;
    pause: () => void;
  }) => {
    if (!selectedSegment) return;

    if (shadowingMode === "repeat") {
      setPauseAtTime(null);
      setPracticeStep("prompting");
    } else if (shadowingMode === "listen_shadow") {
      if (practiceStep === "listening") {
        setPauseAtTime(null);
        player?.pause();
        setPracticeStep("recording");
        await startRecording();
      } else if (practiceStep === "recording") {
        setPauseAtTime(null);
        await stopRecording();
      }
    }
  };

  const cancelPractice = (player?: { pause: () => void }) => {
    player?.pause();
    setPauseAtTime(null);
    setPracticeStep("idle");
    if (audioRecorder.isRecording) {
      audioRecorder.stopRecording();
    }
    liveSpeech.stopListening();
  };

  // Start Recording
  const startRecording = async () => {
    if (audioRecorder.isRecording) return;

    setLastFeedback(null);
    setEvaluationError(null);
    liveSpeech.resetTranscript();

    try {
      await audioRecorder.startRecording();
      liveSpeech.startListening();
      setPracticeStep("recording");

      if (selectedSegment) {
        const startRes = await shadowingApi.startPractice(selectedSegment.id, shadowingMode);
        exerciseIdRef.current = startRes.exercise_id;
        attemptIdRef.current = startRes.attempt_id;
        setCurrentExerciseId(startRes.exercise_id);
        setCurrentAttemptId(startRes.attempt_id);
      }
    } catch (err: any) {
      console.error("Microphone or API error:", err);
      setEvaluationError(
        err.message || "Không thể khởi động bài luyện. Vui lòng kiểm tra quyền Microphone hoặc kết nối backend!"
      );
      setPracticeStep("idle");
    }
  };

  // Stop Recording & Submit Evaluation
  const stopRecording = async () => {
    if (!audioRecorder.isRecording) return;

    liveSpeech.stopListening();
    setIsEvaluating(true);
    setPracticeStep("evaluating");
    setEvaluationError(null);

    try {
      const audioBlob = await audioRecorder.stopRecording();
      if (!audioBlob || audioBlob.size < 50) {
        setEvaluationError("Bản thu âm quá ngắn hoặc không có tín hiệu âm thanh.");
        setIsEvaluating(false);
        setPracticeStep("idle");
        return;
      }

      const userAudioUrl = typeof window !== "undefined" ? URL.createObjectURL(audioBlob) : undefined;
      const reader = new FileReader();

      reader.onerror = () => {
        setEvaluationError("Lỗi khi đọc file âm thanh từ bộ nhớ trình duyệt.");
        setIsEvaluating(false);
        setPracticeStep("idle");
      };

      reader.onloadend = async () => {
        try {
          const base64Audio = (reader.result as string)?.split(",")[1];

          if (selectedSegment && base64Audio) {
            let exId = exerciseIdRef.current || currentExerciseId;
            let attId = attemptIdRef.current || currentAttemptId;
            if (!exId || !attId) {
              const startRes = await shadowingApi.startPractice(selectedSegment.id, shadowingMode);
              exId = startRes.exercise_id;
              attId = startRes.attempt_id;
              exerciseIdRef.current = exId;
              attemptIdRef.current = attId;
              setCurrentExerciseId(exId);
              setCurrentAttemptId(attId);
            }

            const feedbackRes = await shadowingApi.completePractice(
              selectedSegment.id,
              exId,
              attId,
              base64Audio,
              shadowingMode,
              playbackSpeed,
              liveSpeech.fullTranscript || undefined
            );

            if (userAudioUrl) {
              feedbackRes.user_audio_url = userAudioUrl;
            }
            if (!feedbackRes.user_transcript && liveSpeech.fullTranscript) {
              feedbackRes.user_transcript = liveSpeech.fullTranscript;
            }

            setLastFeedback(feedbackRes);
            setEvaluationError(null);

            // Record score in local map
            if (feedbackRes.score !== undefined) {
              setSegmentScores((prev) => ({
                ...prev,
                [selectedSegment.id]: Math.max(prev[selectedSegment.id] || 0, Math.round(feedbackRes.score)),
              }));
            }

            // Reset attempt refs
            exerciseIdRef.current = null;
            attemptIdRef.current = null;
            setCurrentExerciseId(null);
            setCurrentAttemptId(null);
          }
        } catch (apiErr: any) {
          console.error("Evaluation API error:", apiErr);
          setEvaluationError(
            apiErr.message || "Không thể hoàn thành chấm điểm. Máy chủ Whisper hoặc Backend gặp lỗi!"
          );
        } finally {
          setIsEvaluating(false);
          setPracticeStep("idle");
        }
      };

      reader.readAsDataURL(audioBlob);
    } catch (err: any) {
      console.error("Evaluation recorder error:", err);
      setEvaluationError(err.message || "Lỗi xử lý file âm thanh thu âm.");
      setIsEvaluating(false);
      setPracticeStep("idle");
    }
  };

  return {
    video,
    isLoading,
    error,
    currentPlaybackTime,
    setCurrentPlaybackTime,
    selectedSegment,
    setSelectedSegment: handleSelectSegment,
    playbackSpeed,
    setPlaybackSpeed,
    shadowingMode,
    setShadowingMode,
    displaySubtitleMode,
    setDisplaySubtitleMode,
    practiceStep,
    pauseAtTime,
    setPauseAtTime,
    startGuidedPractice,
    handlePauseAtTimeReached,
    cancelPractice,
    isLooping,
    loopRange,
    loopGap,
    setLoopGap,
    toggleLoop: handleToggleLoop,
    loopCurrentSegment,
    clearLoop,
    selectNextSegment,
    selectPrevSegment,
    startRecording,
    stopRecording,
    isRecording: audioRecorder.isRecording,
    isEvaluating,
    lastFeedback,
    evaluationError,
    clearEvaluationError: () => setEvaluationError(null),
    volumeLevel: audioRecorder.volumeLevel,
    liveTranscript: liveSpeech.fullTranscript,
    interimTranscript: liveSpeech.interimTranscript,
    // Enhanced Features
    bookmarkedSegmentIds,
    toggleBookmark,
    segmentScores,
    autoPilot,
    setAutoPilot,
    applyPedagogicalLevel,
  };
}
