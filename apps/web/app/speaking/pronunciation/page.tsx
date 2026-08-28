"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  PronunciationAttemptResponse,
  PronunciationPracticeTargetDTO,
} from "@/features/speaking/types/pronunciation";
import { pronunciationApi } from "@/features/speaking/services/pronunciation-api";
import { speechApi } from "@/features/speaking/services/speech-api";
import {
  PronunciationDashboard,
  AttemptComparisonStrip,
  AttemptSummary,
} from "@/features/speaking/components";
import {
  Mic,
  Square,
  Volume2,
  RotateCcw,
  Sparkles,
  Award,
  BookOpen,
  ArrowRight,
  Loader2,
  CheckCircle2,
  ChevronRight,
  History,
} from "lucide-react";

export default function PronunciationPracticePage() {
  // Target Selection State
  const [targets, setTargets] = useState<PronunciationPracticeTargetDTO[]>([]);
  const [selectedTarget, setSelectedTarget] = useState<PronunciationPracticeTargetDTO | null>(null);
  const [customText, setCustomText] = useState("");
  const [isCustomMode, setIsCustomMode] = useState(false);

  // Audio Recording State
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null);
  const [recordedAudioUrl, setRecordedAudioUrl] = useState<string | null>(null);

  // Reference Audio State
  const [isPlayingReference, setIsPlayingReference] = useState(false);
  const referenceAudioRef = useRef<HTMLAudioElement | null>(null);

  // Analysis State
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [currentAttempt, setCurrentAttempt] = useState<PronunciationAttemptResponse | null>(null);
  const [attemptHistory, setAttemptHistory] = useState<AttemptSummary[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Load Practice Targets
  useEffect(() => {
    async function loadTargets() {
      try {
        const data = await pronunciationApi.getTargets(8);
        setTargets(data);
        if (data.length > 0 && !selectedTarget) {
          setSelectedTarget(data[0]);
        }
      } catch (err) {
        console.error("Failed to load practice targets", err);
      }
    }
    loadTargets();
  }, []);

  const activeStreamRef = useRef<MediaStream | null>(null);

  // Cleanup object URLs and active mic stream on unmount
  useEffect(() => {
    return () => {
      if (recordedAudioUrl) {
        URL.revokeObjectURL(recordedAudioUrl);
      }
      if (activeStreamRef.current) {
        activeStreamRef.current.getTracks().forEach((track) => {
          try {
            track.stop();
          } catch {}
        });
        activeStreamRef.current = null;
      }
    };
  }, [recordedAudioUrl]);

  // Play Reference Audio via TTS
  const handlePlayReference = async () => {
    const textToSpeak = isCustomMode ? customText : selectedTarget?.target_text;
    if (!textToSpeak) return;

    try {
      setIsPlayingReference(true);
      const res = await speechApi.synthesize(textToSpeak, "1", 1.0, 0.0);
      if (res.audio_base64) {
        const audioUrl = `data:audio/wav;base64,${res.audio_base64}`;
        const audio = new Audio(audioUrl);
        referenceAudioRef.current = audio;

        audio.onended = () => {
          setIsPlayingReference(false);
        };
        audio.onerror = () => {
          setIsPlayingReference(false);
        };

        await audio.play();
      } else {
        setIsPlayingReference(false);
      }
    } catch (err) {
      console.error("Failed to synthesize reference speech", err);
      setIsPlayingReference(false);
    }
  };

  // Start Recording
  const startRecording = async () => {
    setErrorMessage(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      activeStreamRef.current = stream;
      const recorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
      const chunks: BlobPart[] = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunks.push(e.data);
        }
      };

      recorder.onstop = async () => {
        const webmBlob = new Blob(chunks, { type: "audio/webm" });
        // Convert to WAV/PCM audio blob for backend pipeline
        const wavBlob = await convertToWavBlob(webmBlob);
        setRecordedBlob(wavBlob);
        const url = URL.createObjectURL(wavBlob);
        setRecordedAudioUrl(url);

        // Stop all media tracks
        stream.getTracks().forEach((track) => {
          try {
            track.stop();
          } catch {}
        });
        activeStreamRef.current = null;

        // Automatically trigger analysis
        await handleAnalyze(wavBlob);
      };

      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
    } catch (err: any) {
      console.error("Failed to access microphone", err);
      setErrorMessage("Không thể kết nối với Micro. Vui lòng cấp quyền truy cập micro trên trình duyệt.");
    }
  };

  // Stop Recording
  const stopRecording = () => {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
      mediaRecorder.stop();
      setIsRecording(false);
    }
  };

  // Execute Analysis
  const handleAnalyze = async (blobToAnalyze: Blob) => {
    const targetText = isCustomMode ? customText.trim() : selectedTarget?.target_text;
    const expectedReading = isCustomMode ? undefined : selectedTarget?.target_reading;

    if (!targetText) {
      setErrorMessage("Vui lòng chọn hoặc nhập câu mục tiêu để luyện tập.");
      return;
    }

    setIsAnalyzing(true);
    setErrorMessage(null);

    try {
      const response = await pronunciationApi.analyze({
        audioBlob: blobToAnalyze,
        targetText: targetText,
        expectedReading: expectedReading,
        targetType: isCustomMode ? "custom" : (selectedTarget?.target_type as any) || "sentence",
        referenceType: "synthetic",
      });

      setCurrentAttempt(response);

      if (response.overall_score !== null && response.overall_score !== undefined) {
        const newSummary: AttemptSummary = {
          attemptNumber: attemptHistory.length + 1,
          overallScore: response.overall_score,
          moraScore: response.result?.mora_timing_score?.score,
          pitchScore: response.result?.pitch_score?.score,
          timestamp: new Date().toLocaleTimeString(),
        };
        setAttemptHistory((prev) => [...prev, newSummary]);
      }
    } catch (err: any) {
      console.error("Analysis failed", err);
      setErrorMessage(err.message || "Phân tích phát âm thất bại. Vui lòng thử lại.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Play User Audio
  const handlePlayUserAudio = () => {
    if (recordedAudioUrl) {
      const audio = new Audio(recordedAudioUrl);
      audio.play();
    }
  };

  // Reset for Retry Loop
  const handleRetry = () => {
    setCurrentAttempt(null);
    setRecordedBlob(null);
    if (recordedAudioUrl) {
      URL.revokeObjectURL(recordedAudioUrl);
      setRecordedAudioUrl(null);
    }
    setErrorMessage(null);
  };

  return (
    <div className="min-h-screen bg-background text-foreground py-10 px-4 sm:px-6 lg:px-8 font-sans">
      <div className="max-w-5xl mx-auto space-y-8">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-border pb-6">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-indigo-400 font-mono mb-1">
              <Sparkles className="w-4 h-4 text-indigo-400" />
              Japanese Pronunciation Engine
            </div>
            <h1 className="text-3xl font-extrabold text-white tracking-tight">
              Luyện phát âm & Cao độ chuẩn Nhật
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              Phân tích chuyên sâu 5 trụ cột âm thanh: Ngữ âm, Trường độ Mora, Pitch Accent, Nhịp điệu và Ngữ điệu.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                setIsCustomMode(!isCustomMode);
                handleRetry();
              }}
              className="px-4 py-2 rounded-xl text-xs font-medium border border-border bg-card hover:bg-muted text-foreground transition-all"
            >
              {isCustomMode ? "Chọn câu mẫu" : "Tự nhập câu tùy chỉnh"}
            </button>
          </div>
        </div>

        {/* Practice Target Selection Section */}
        {!isCustomMode ? (
          <div className="space-y-3">
            <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider font-mono">
              Chọn chủ đề & Thử thách phát âm
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {targets.map((t) => {
                const isSelected = selectedTarget?.id === t.id;
                return (
                  <button
                    key={t.id}
                    onClick={() => {
                      setSelectedTarget(t);
                      handleRetry();
                    }}
                    className={`text-left p-4 rounded-2xl border transition-all duration-200 ${
                      isSelected
                        ? "bg-indigo-600/20 border-indigo-400 shadow-lg shadow-indigo-500/20"
                        : "bg-card/60 border-border hover:border-border"
                    }`}
                  >
                    <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
                      <span className="capitalize px-2 py-0.5 rounded bg-muted border border-border font-mono text-[10px]">
                        {t.category.replace("_", " ")}
                      </span>
                      <span className="text-[10px] text-indigo-300 font-mono">
                        {t.difficulty}
                      </span>
                    </div>

                    <div className="text-lg font-bold text-foreground font-japanese mt-1">
                      {t.target_text}
                    </div>
                    <div className="text-xs text-muted-foreground font-japanese">
                      {t.target_reading}
                    </div>

                    {t.hint && (
                      <p className="text-[11px] text-muted-foreground mt-2 line-clamp-2 leading-relaxed">
                        {t.hint}
                      </p>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        ) : (
          <div className="p-5 rounded-2xl bg-card/80 border border-border space-y-3">
            <h3 className="text-xs font-semibold text-foreground uppercase tracking-wider font-mono">
              Nhập từ hoặc câu tiếng Nhật bất kỳ
            </h3>
            <input
              type="text"
              value={customText}
              onChange={(e) => setCustomText(e.target.value)}
              placeholder="Ví dụ: おばあさんは昨日映画を見ました。"
              className="w-full px-4 py-3 rounded-xl bg-background border border-border text-foreground font-japanese text-lg focus:outline-none focus:border-indigo-500 transition-all"
            />
          </div>
        )}

        {/* Practice Arena Card */}
        <div className="relative overflow-hidden p-8 rounded-3xl bg-gradient-to-br from-slate-900/90 via-slate-900 to-indigo-950/30 border border-border shadow-2xl backdrop-blur-2xl">
          <div className="flex flex-col items-center justify-center text-center space-y-6">
            {/* Active Target Japanese Display */}
            <div>
              <span className="text-xs font-mono uppercase tracking-widest text-indigo-400">
                Câu mục tiêu luyện tập
              </span>
              <h2 className="text-3xl sm:text-4xl font-extrabold text-white font-japanese tracking-normal mt-1">
                {isCustomMode ? customText || "（Chưa nhập câu）" : selectedTarget?.target_text}
              </h2>
              {!isCustomMode && selectedTarget?.target_reading && (
                <div className="text-base text-indigo-300 font-japanese mt-1 font-medium">
                  {selectedTarget.target_reading}
                </div>
              )}
            </div>

            {/* Audio Action Buttons */}
            <div className="flex items-center justify-center gap-4 flex-wrap">
              {/* Reference Audio Player Button */}
              <button
                onClick={handlePlayReference}
                disabled={isPlayingReference || isRecording}
                className="flex items-center gap-2 px-5 py-3 rounded-2xl bg-muted/80 hover:bg-slate-700 border border-border text-foreground font-medium text-sm transition-all shadow-md active:scale-95 disabled:opacity-50"
              >
                <Volume2
                  className={`w-4 h-4 ${
                    isPlayingReference ? "text-cyan-400 animate-bounce" : "text-muted-foreground"
                  }`}
                />
                <span>{isPlayingReference ? "Đang phát giọng mẫu..." : "Nghe giọng mẫu"}</span>
              </button>

              {/* Record Microphone Button */}
              {!isRecording ? (
                <button
                  onClick={startRecording}
                  disabled={isAnalyzing}
                  className="flex items-center gap-2 px-7 py-3 rounded-2xl bg-gradient-to-r from-primary via-primary/90 to-aizome-600 hover:opacity-95 text-primary-foreground font-semibold text-sm shadow-xl shadow-primary/25 transition-all active:scale-95 disabled:opacity-50"
                >
                  <Mic className="w-4 h-4" />
                  <span>Bắt đầu thu âm</span>
                </button>
              ) : (
                <button
                  onClick={stopRecording}
                  className="flex items-center gap-2 px-7 py-3 rounded-2xl bg-destructive hover:bg-destructive/90 text-destructive-foreground font-semibold text-sm shadow-xl shadow-destructive/25 transition-all animate-pulse active:scale-95"
                >
                  <Square className="w-4 h-4 fill-current" />
                  <span>Dừng & Phân tích</span>
                </button>
              )}

              {/* Retry button */}
              {currentAttempt && (
                <button
                  onClick={handleRetry}
                  className="flex items-center gap-2 px-4 py-3 rounded-2xl bg-muted/80 hover:bg-slate-700 border border-border text-foreground font-medium text-sm transition-all active:scale-95"
                >
                  <RotateCcw className="w-4 h-4" />
                  <span>Thử lại</span>
                </button>
              )}
            </div>

            {/* Error Banner */}
            {errorMessage && (
              <div className="p-3 rounded-xl bg-destructive/10 border border-destructive/30 text-destructive text-xs">
                {errorMessage}
              </div>
            )}

            {/* Analysis Loading Indicator */}
            {isAnalyzing && (
              <div className="flex items-center gap-3 text-indigo-300 text-sm font-medium animate-pulse py-2">
                <Loader2 className="w-5 h-5 animate-spin text-indigo-400" />
                <span>Đang phân tích âm học, nhịp Mora và F₀ Pitch Accent...</span>
              </div>
            )}
          </div>
        </div>

        {/* Attempt Progression History */}
        {attemptHistory.length > 1 && (
          <AttemptComparisonStrip attempts={attemptHistory} />
        )}

        {/* Analysis Results & Dashboard */}
        {currentAttempt?.result && (
          <div className="animate-in fade-in slide-in-from-bottom-3 duration-300">
            <PronunciationDashboard
              result={currentAttempt.result}
              onPlayReference={handlePlayReference}
              onPlayUserAudio={handlePlayUserAudio}
            />
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Converts audio/webm Blob to standard 16-bit PCM WAV Blob via browser AudioContext
 */
async function convertToWavBlob(blob: Blob): Promise<Blob> {
  const arrayBuffer = await blob.arrayBuffer();
  const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
  const audioBuffer = await audioCtx.decodeAudioData(arrayBuffer);

  // Encode to 16kHz mono WAV
  const targetSampleRate = 16000;
  const offlineCtx = new OfflineAudioContext(1, (audioBuffer.duration * targetSampleRate) | 0, targetSampleRate);
  const source = offlineCtx.createBufferSource();
  source.buffer = audioBuffer;
  source.connect(offlineCtx.destination);
  source.start();

  const renderedBuffer = await offlineCtx.startRendering();
  const pcmData = renderedBuffer.getChannelData(0);

  // Build WAV container
  const wavBuffer = new ArrayBuffer(44 + pcmData.length * 2);
  const view = new DataView(wavBuffer);

  const writeString = (offset: number, string: string) => {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  };

  writeString(0, "RIFF");
  view.setUint32(4, 36 + pcmData.length * 2, true);
  writeString(8, "WAVE");
  writeString(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true); // PCM
  view.setUint16(22, 1, true); // Mono
  view.setUint32(24, targetSampleRate, true);
  view.setUint32(28, targetSampleRate * 2, true);
  view.setUint16(32, 2, true); // block align
  view.setUint16(34, 16, true); // 16-bit
  writeString(36, "data");
  view.setUint32(40, pcmData.length * 2, true);

  // Write PCM samples
  let offset = 44;
  for (let i = 0; i < pcmData.length; i++, offset += 2) {
    const s = Math.max(-1, Math.min(1, pcmData[i]));
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
  }

  await audioCtx.close();
  return new Blob([wavBuffer], { type: "audio/wav" });
}
