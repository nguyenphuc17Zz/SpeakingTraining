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
  const [playbackSpeed, setPlaybackSpeed] = useState(1.0);
  const [shadowingMode, setShadowingMode] = useState<ShadowingMode>("shadow");
  const [isLooping, setIsLooping] = useState(false);
  const [loopRange, setLoopRange] = useState<{ start: number; end: number } | null>(null);
  const [loopGap, setLoopGap] = useState<number>(0);

  // Active Practice & Recording State
  const [practiceStep, setPracticeStep] = useState<"idle" | "listening" | "prompting" | "recording" | "evaluating">("idle");
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

  // Set Marker A
  const setMarkerA = (time?: number) => {
    const t = Math.max(0, time !== undefined ? time : currentPlaybackTime);
    setLoopRange((prev) => {
      const end = prev && prev.end > t ? prev.end : Number((t + 3).toFixed(2));
      return { start: Number(t.toFixed(2)), end };
    });
    setIsLooping(true);
  };

  // Set Marker B
  const setMarkerB = (time?: number) => {
    const t = Math.max(0, time !== undefined ? time : currentPlaybackTime);
    setLoopRange((prev) => {
      const start = prev && prev.start < t ? prev.start : Math.max(0, Number((t - 3).toFixed(2)));
      return { start, end: Number(t.toFixed(2)) };
    });
    setIsLooping(true);
  };

  // Fine tune marker A (±0.5s)
  const adjustMarkerA = (delta: number) => {
    setLoopRange((prev) => {
      if (!prev) {
        const base = selectedSegment?.start_time || currentPlaybackTime;
        return { start: Math.max(0, Number((base + delta).toFixed(2))), end: selectedSegment?.end_time || base + 3 };
      }
      const newStart = Math.max(0, Math.min(prev.end - 0.2, Number((prev.start + delta).toFixed(2))));
      return { ...prev, start: newStart };
    });
    setIsLooping(true);
  };

  // Fine tune marker B (±0.5s)
  const adjustMarkerB = (delta: number) => {
    setLoopRange((prev) => {
      if (!prev) {
        const base = selectedSegment?.end_time || currentPlaybackTime + 3;
        return { start: selectedSegment?.start_time || 0, end: Math.max(0.5, Number((base + delta).toFixed(2))) };
      }
      const newEnd = Math.max(prev.start + 0.2, Number((prev.end + delta).toFixed(2)));
      return { ...prev, end: newEnd };
    });
    setIsLooping(true);
  };

  // Set exact custom range
  const setExactLoopRange = (start: number, end: number) => {
    setLoopRange({
      start: Number(start.toFixed(2)),
      end: Number(end.toFixed(2)),
    });
    setIsLooping(true);
  };

  // Expand loop to include the next segment
  const expandLoopToNextSegment = () => {
    if (!video?.segments || !selectedSegment) return;
    const currIdx = video.segments.findIndex((s) => s.id === selectedSegment.id);
    if (currIdx >= 0 && currIdx < video.segments.length - 1) {
      const nextSeg = video.segments[currIdx + 1];
      const start = loopRange ? loopRange.start : selectedSegment.start_time;
      setLoopRange({
        start,
        end: nextSeg.end_time,
      });
      setIsLooping(true);
    }
  };

  // Expand loop to include the previous segment
  const expandLoopToPrevSegment = () => {
    if (!video?.segments || !selectedSegment) return;
    const currIdx = video.segments.findIndex((s) => s.id === selectedSegment.id);
    if (currIdx > 0) {
      const prevSeg = video.segments[currIdx - 1];
      const end = loopRange ? loopRange.end : selectedSegment.end_time;
      setLoopRange({
        start: prevSeg.start_time,
        end,
      });
      setIsLooping(true);
    }
  };

  // Direct 1-click select and loop
  const selectAndLoopSegment = (segment: TranscriptSegment) => {
    setSelectedSegment(segment);
    setLoopRange({
      start: segment.start_time,
      end: segment.end_time,
    });
    setIsLooping(true);
  };

  // Loop current segment
  const loopCurrentSegment = () => {
    if (!selectedSegment) return;
    setLoopRange({
      start: selectedSegment.start_time,
      end: selectedSegment.end_time,
    });
    setIsLooping(true);
  };

  // Toggle A-B Loop
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
      }
      setIsLooping(true);
    }
  };

  // Clear loop
  const clearLoop = () => {
    setIsLooping(false);
    setLoopRange(null);
  };

  // Select next segment in timeline
  // Select next segment in timeline
  const selectNextSegment = () => {
    if (!video?.segments || !selectedSegment) return;
    const currIdx = video.segments.findIndex((s) => s.id === selectedSegment.id);
    if (currIdx >= 0 && currIdx + 1 < video.segments.length) {
      handleSelectSegment(video.segments[currIdx + 1]);
    }
  };

  // Select previous segment in timeline
  const selectPrevSegment = () => {
    if (!video?.segments || !selectedSegment) return;
    const currIdx = video.segments.findIndex((s) => s.id === selectedSegment.id);
    if (currIdx > 0) {
      handleSelectSegment(video.segments[currIdx - 1]);
    }
  };

  // Start Shadowing practice for current segment
  const startRecording = async () => {
    if (!selectedSegment) return;

    try {
      setLastFeedback(null);
      setEvaluationError(null);
      setIsEvaluating(false);
      exerciseIdRef.current = null;
      attemptIdRef.current = null;
      setCurrentExerciseId(null);
      setCurrentAttemptId(null);

      liveSpeech.resetTranscript();
      liveSpeech.startListening();
      await audioRecorder.startRecording();
      setPracticeStep("recording");

      // Start Exercise attempt on backend
      const startRes = await shadowingApi.startPractice(selectedSegment.id, shadowingMode);
      exerciseIdRef.current = startRes.exercise_id;
      attemptIdRef.current = startRes.attempt_id;
      setCurrentExerciseId(startRes.exercise_id);
      setCurrentAttemptId(startRes.attempt_id);
    } catch (err: any) {
      console.error("Microphone or API error:", err);
      setEvaluationError(err.message || "Không thể khởi động bài luyện. Vui lòng kiểm tra quyền Microphone hoặc kết nối backend!");
      setPracticeStep("idle");
    }
  };

  // Start Guided Practice depending on shadowingMode
  const startGuidedPractice = async (player?: { seekTo: (t: number) => void; play: () => void; pause: () => void }) => {
    if (!selectedSegment) return;

    setLastFeedback(null);
    setEvaluationError(null);

    if (shadowingMode === "repeat") {
      // Step 1: Listen to reference sentence. Video pauses at end_time.
      setPracticeStep("listening");
      setPauseAtTime(selectedSegment.end_time);
      player?.seekTo(selectedSegment.start_time);
      player?.play();
    } else if (shadowingMode === "listen_shadow") {
      // Round 1: Listen. Video pauses at end_time before user speaks.
      setPracticeStep("listening");
      setPauseAtTime(selectedSegment.end_time);
      player?.seekTo(selectedSegment.start_time);
      player?.play();
    } else {
      // Direct Recording: Strictly pause video so mic records only the user's voice cleanly!
      player?.pause();
      setPracticeStep("recording");
      await startRecording();
    }
  };

  // Called when video reaches pauseAtTime
  const handlePauseAtTimeReached = async (player?: { seekTo: (t: number) => void; play: () => void; pause: () => void }) => {
    if (!selectedSegment) return;

    if (shadowingMode === "repeat") {
      // Video is now paused in silence! Do NOT auto-activate microphone; wait for user to press Q or click to record.
      setPauseAtTime(null);
      setPracticeStep("prompting");
    } else if (shadowingMode === "listen_shadow") {
      if (practiceStep === "listening") {
        // Transition from Round 1 (Listen) to Round 2 (Record) - Keep video paused for clean mic recording
        setPauseAtTime(null);
        player?.pause();
        setPracticeStep("recording");
        await startRecording();
      } else if (practiceStep === "recording") {
        // Round 2 completed!
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
            // Always read the latest mutable ref values to avoid stale closures
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

            // Reset attempt refs so subsequent attempts are completely clean
            exerciseIdRef.current = null;
            attemptIdRef.current = null;
            setCurrentExerciseId(null);
            setCurrentAttemptId(null);
          }
        } catch (apiErr: any) {
          console.error("Evaluation API error:", apiErr);
          setEvaluationError(apiErr.message || "Không thể hoàn thành chấm điểm. Máy chủ Whisper hoặc Backend gặp lỗi!");
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
    isRecording: audioRecorder.isRecording,
    isEvaluating,
    lastFeedback,
    evaluationError,
    clearEvaluationError: () => setEvaluationError(null),
    volumeLevel: audioRecorder.volumeLevel,
    liveTranscript: liveSpeech.fullTranscript,
    interimTranscript: liveSpeech.interimTranscript,
  };
}
