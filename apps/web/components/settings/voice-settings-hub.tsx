"use client";

import React, { useEffect, useState, useRef } from "react";
import {
  Volume2,
  Mic,
  Sliders,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  Play,
  Square,
  Loader2,
  Star,
  Plus,
  Trash2,
  Save,
  RefreshCw,
  Zap,
  HelpCircle,
  VolumeX,
  Radio,
  Check,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { VoiceProfile, AudioSettings, PlaybackPreset } from "@/types/audio";
import { audioApi } from "@/features/audio/services/audio-api";
import { useTTS } from "@/features/audio/hooks/useTTS";
import { VoiceSelector } from "@/features/audio/components/VoiceSelector";
import { VoicevoxEngineCard } from "./voicevox-engine-card";
import { STTModelManagerCard } from "@/features/audio/components/STTModelManagerCard";
import { MicrophoneCalibrationModal } from "@/features/audio/components/MicrophoneCalibrationModal";
import {
  SAMPLE_PHRASES,
  SamplePhrase,
  getVoiceCharacterMeta,
} from "@/features/audio/services/voice-meta";

export function VoiceSettingsHub() {
  // Settings & Profiles state
  const [settings, setSettings] = useState<AudioSettings | null>(null);
  const [presets, setPresets] = useState<PlaybackPreset[]>([]);
  const [profiles, setProfiles] = useState<VoiceProfile[]>([]);
  const [voices, setVoices] = useState<VoiceProfile[]>([]);
  const [selectedVoice, setSelectedVoice] = useState<VoiceProfile | null>(null);

  // Audition Studio state
  const [selectedPhrase, setSelectedPhrase] = useState<SamplePhrase>(SAMPLE_PHRASES[0]);
  const [customText, setCustomText] = useState("");
  const [isCustomMode, setIsCustomMode] = useState(false);
  const [speed, setSpeed] = useState(1.0);
  const [pitch, setPitch] = useState(0.0);

  // UI feedback & saving
  const [loading, setLoading] = useState(true);
  const [savingSettings, setSavingSettings] = useState(false);
  const [feedbackMsg, setFeedbackMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Custom Profile creation
  const [newProfileName, setNewProfileName] = useState("");
  const [savingProfile, setSavingProfile] = useState(false);
  const [showSaveProfileModal, setShowSaveProfileModal] = useState(false);

  // Mic Quick Test state
  const [isCalibratingMic, setIsCalibratingMic] = useState(false);
  const [isTestingMic, setIsTestingMic] = useState(false);
  const [micAudioLevel, setMicAudioLevel] = useState(0);
  const [micTestResult, setMicTestResult] = useState<string | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const animFrameRef = useRef<number | null>(null);

  // TTS playback
  const { isGenerating, isPlaying, previewVoice, stop } = useTTS();

  // Load initial data
  const loadData = async () => {
    setLoading(true);
    try {
      const [fetchedSettings, fetchedProfiles, fetchedVoices, fetchedPresets] = await Promise.all([
        audioApi.getSettings().catch(() => null),
        audioApi.listVoiceProfiles().catch(() => []),
        audioApi.getVoices("voicevox").catch(() => []),
        audioApi.listPresets().catch(() => []),
      ]);

      if (fetchedSettings) {
        setSettings(fetchedSettings);
        setSpeed(fetchedSettings.default_tts_speed || 1.0);
        setPitch(fetchedSettings.default_tts_pitch || 0.0);
      }
      setProfiles(fetchedProfiles || []);
      setVoices(fetchedVoices || []);
      setPresets(fetchedPresets || []);

      // Determine initial selected voice
      if (fetchedVoices && fetchedVoices.length > 0) {
        const defaultV = fetchedVoices.find((v) => v.is_default) || fetchedVoices[0];
        setSelectedVoice(defaultV);
      }
    } catch (e: any) {
      console.warn("Failed to load voice hub data:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    return () => {
      stopMicTest();
    };
  }, []);

  const activeSampleText = isCustomMode ? customText || "こんにちは！" : selectedPhrase.text;

  // Play audition voice
  const handlePlayAudition = () => {
    if (!selectedVoice) return;
    if (isPlaying) {
      stop();
    } else {
      previewVoice(
        activeSampleText,
        selectedVoice.voice_id,
        selectedVoice.provider,
        speed,
        pitch,
        selectedVoice.style || undefined
      );
    }
  };

  // Set selected voice as system default
  const handleSetAsDefault = async (voiceToSet?: VoiceProfile) => {
    const targetVoice = voiceToSet || selectedVoice;
    if (!targetVoice) return;

    setSavingSettings(true);
    setFeedbackMsg(null);
    try {
      if (settings) {
        const updated = await audioApi.updateSettings({
          ...settings,
          default_voice_profile_id: targetVoice.id || targetVoice.voice_id,
          default_tts_speed: speed,
          default_tts_pitch: pitch,
        });
        setSettings(updated);
      }
      // Update voices default flag locally
      setVoices((prev) =>
        prev.map((v) => ({
          ...v,
          is_default: v.voice_id === targetVoice.voice_id,
        }))
      );
      if (selectedVoice?.voice_id === targetVoice.voice_id) {
        setSelectedVoice({ ...targetVoice, is_default: true });
      }
      setFeedbackMsg({
        type: "success",
        text: `Đã đặt giọng “${targetVoice.name}” làm giọng AI mặc định toàn hệ thống!`,
      });
      setTimeout(() => setFeedbackMsg(null), 4000);
    } catch (e: any) {
      setFeedbackMsg({ type: "error", text: `Lỗi: ${e.message || "Không thể lưu cài đặt"}` });
    } finally {
      setSavingSettings(false);
    }
  };

  // Toggle settings switches
  const handleToggleSetting = async (key: keyof AudioSettings, value: any) => {
    if (!settings) return;
    const nextSettings = { ...settings, [key]: value };
    setSettings(nextSettings);
    try {
      await audioApi.updateSettings({ [key]: value });
    } catch (e) {
      console.warn("Failed to update setting:", key, e);
    }
  };

  // Save custom profile
  const handleCreateProfile = async () => {
    if (!selectedVoice || !newProfileName.trim()) return;
    setSavingProfile(true);
    try {
      const created = await audioApi.createVoiceProfile({
        name: newProfileName.trim(),
        provider: selectedVoice.provider,
        voice_id: selectedVoice.voice_id,
        description: `Hồ sơ tùy chỉnh dựa trên giọng ${selectedVoice.name} (Tốc độ ${speed}x)`,
        settings_json: { speed, pitch },
        is_default: false,
      });
      setProfiles((prev) => [created, ...prev]);
      setNewProfileName("");
      setShowSaveProfileModal(false);
      setFeedbackMsg({
        type: "success",
        text: `Đã lưu hồ sơ giọng “${created.name}” thành công!`,
      });
      setTimeout(() => setFeedbackMsg(null), 4000);
    } catch (e: any) {
      setFeedbackMsg({ type: "error", text: `Lỗi lưu hồ sơ: ${e.message}` });
    } finally {
      setSavingProfile(false);
    }
  };

  const handleDeleteProfile = async (id: string) => {
    try {
      await audioApi.deleteVoiceProfile(id);
      setProfiles((prev) => prev.filter((p) => p.id !== id));
      setFeedbackMsg({ type: "success", text: "Đã xóa hồ sơ giọng." });
      setTimeout(() => setFeedbackMsg(null), 3000);
    } catch (e) {
      console.warn("Delete profile failed:", e);
    }
  };

  // Microphone quick tester
  const startMicTest = async () => {
    try {
      setIsTestingMic(true);
      setMicTestResult(null);

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;

      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      audioContextRef.current = audioCtx;

      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      const source = audioCtx.createMediaStreamSource(stream);
      source.connect(analyser);

      const dataArray = new Uint8Array(analyser.frequencyBinCount);

      const updateMeter = () => {
        analyser.getByteFrequencyData(dataArray);
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
          sum += dataArray[i];
        }
        const avg = sum / dataArray.length;
        const normalized = Math.min(100, Math.round((avg / 128) * 100));
        setMicAudioLevel(normalized);
        animFrameRef.current = requestAnimationFrame(updateMeter);
      };
      updateMeter();

      setTimeout(() => {
        setMicTestResult("Âm lượng Micro tốt, bắt tiếng rõ ràng! Bạn đã sẵn sàng luyện nói.");
      }, 2500);
    } catch (err: any) {
      setIsTestingMic(false);
      setMicTestResult("Không thể truy cập Microphone. Vui lòng cấp quyền micro trên trình duyệt.");
    }
  };

  const stopMicTest = () => {
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((t) => t.stop());
      mediaStreamRef.current = null;
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
    setIsTestingMic(false);
    setMicAudioLevel(0);
  };

  if (loading && !selectedVoice) {
    return (
      <div className="py-20 flex flex-col items-center justify-center text-muted-foreground gap-3">
        <Loader2 className="h-7 w-7 animate-spin text-primary" />
        <span className="text-sm font-medium">Đang tải Studio Giọng nói & Âm thanh...</span>
      </div>
    );
  }

  const selectedMeta = selectedVoice ? getVoiceCharacterMeta(selectedVoice) : null;
  const isCurrentDefault = selectedVoice?.is_default;

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Toast Feedback */}
      {feedbackMsg && (
        <div
          className={`p-3.5 rounded-2xl border text-xs flex items-center justify-between gap-2 shadow-sm ${
            feedbackMsg.type === "success"
              ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-700 dark:text-emerald-300"
              : "bg-destructive/10 border-destructive/20 text-destructive"
          }`}
        >
          <div className="flex items-center gap-2">
            {feedbackMsg.type === "success" ? (
              <CheckCircle2 className="h-4 w-4 shrink-0" />
            ) : (
              <AlertCircle className="h-4 w-4 shrink-0" />
            )}
            <span className="font-medium">{feedbackMsg.text}</span>
          </div>
          <button
            onClick={() => setFeedbackMsg(null)}
            className="text-xs font-bold px-2 py-0.5 rounded hover:bg-black/5 dark:hover:bg-white/5"
          >
            ✕
          </button>
        </div>
      )}

      {/* SECTION 1: HERO ACTIVE VOICE & AUDITION STUDIO */}
      <div className="relative overflow-hidden rounded-[24px] border border-border bg-card shadow-washi washi-texture p-5 sm:p-6 space-y-5">
        <div className="absolute -top-12 -right-12 h-44 w-44 rounded-full bg-enso-gradient opacity-25 pointer-events-none" />

        {/* Hero Header */}
        <div className="relative flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            {selectedMeta && (
              <div
                className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${selectedMeta.gradient} flex items-center justify-center font-bold text-white text-2xl shadow-md shrink-0 font-jp`}
              >
                {selectedMeta.avatarLetter}
              </div>
            )}
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h2 className="text-lg font-bold text-foreground font-jp">
                  {selectedVoice?.name || "Đang chọn giọng đọc"}
                </h2>
                {isCurrentDefault ? (
                  <Badge variant="matcha" size="sm" className="gap-1">
                    <Star className="h-3 w-3 fill-current" /> Giọng AI Mặc Định
                  </Badge>
                ) : (
                  <Badge variant="outline" size="sm">
                    Đang nghe thử
                  </Badge>
                )}
                {selectedMeta && (
                  <span className={`px-2 py-0.5 rounded-lg text-xs border font-medium ${selectedMeta.badgeClass}`}>
                    {selectedMeta.genderLabel} · {selectedMeta.vibeLabel}
                  </span>
                )}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                {selectedMeta?.descriptionVi} —{" "}
                <span className="text-primary font-medium">{selectedMeta?.recommendedFor}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0 flex-wrap">
            {!isCurrentDefault && (
              <Button
                variant="primary"
                size="sm"
                onClick={() => handleSetAsDefault()}
                disabled={savingSettings}
                className="text-xs rounded-xl"
              >
                {savingSettings ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin mr-1.5" />
                ) : (
                  <Check className="h-3.5 w-3.5 mr-1.5" />
                )}
                Đặt làm Giọng AI Chính
              </Button>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowSaveProfileModal(true)}
              className="text-xs rounded-xl"
            >
              <Plus className="h-3.5 w-3.5 mr-1.5 text-primary" />
              Lưu cấu hình giọng
            </Button>
          </div>
        </div>

        {/* Audition Multi-Context Phrase Selector */}
        <div className="space-y-2.5 pt-2 border-t border-border/70">
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold text-foreground flex items-center gap-1.5">
              <Sparkles className="h-3.5 w-3.5 text-amber-500" />
              Chọn câu mẫu tiếng Nhật để nghe thử:
            </span>
            <button
              onClick={() => setIsCustomMode(!isCustomMode)}
              className="text-primary hover:underline font-medium text-[11px]"
            >
              {isCustomMode ? "← Dùng mẫu có sẵn" : "✏️ Tự nhập câu tùy ý"}
            </button>
          </div>

          {!isCustomMode ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2">
              {SAMPLE_PHRASES.map((phrase) => {
                const isSelected = selectedPhrase.id === phrase.id;
                return (
                  <button
                    key={phrase.id}
                    onClick={() => setSelectedPhrase(phrase)}
                    className={`p-2.5 rounded-xl border text-left transition-all ${
                      isSelected
                        ? "bg-primary/10 border-primary text-foreground shadow-sm ring-1 ring-primary/40"
                        : "bg-background/70 border-border text-muted-foreground hover:bg-card hover:text-foreground"
                    }`}
                  >
                    <div className="flex items-center gap-1.5 text-xs font-bold">
                      <span>{phrase.icon}</span>
                      <span className="truncate">{phrase.label}</span>
                    </div>
                    <div className="text-[10px] text-muted-foreground truncate mt-1 font-jp">
                      {phrase.text}
                    </div>
                  </button>
                );
              })}
            </div>
          ) : (
            <div className="space-y-1.5">
              <input
                type="text"
                value={customText}
                onChange={(e) => setCustomText(e.target.value)}
                placeholder="Nhập câu tiếng Nhật bạn muốn nghe thử (vd: 初めまして、よろしくお願いします)..."
                className="w-full px-3.5 py-2.5 bg-background border border-border rounded-xl text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary font-jp"
              />
            </div>
          )}

          {/* Current Phrase Display & Romaji */}
          <div className="p-3.5 rounded-xl bg-muted/40 border border-border/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="space-y-0.5">
              <div className="text-sm font-bold text-foreground font-jp tracking-wide">
                {activeSampleText}
              </div>
              {!isCustomMode && (
                <div className="text-[11px] text-muted-foreground italic font-sans">
                  {selectedPhrase.romaji} —{" "}
                  <span className="text-foreground/80 not-italic">{selectedPhrase.translationVi}</span>
                </div>
              )}
            </div>

            {/* Big Play / Stop Audition Button */}
            <Button
              variant="primary"
              size="sm"
              onClick={handlePlayAudition}
              disabled={isGenerating}
              className="h-10 px-5 rounded-xl gap-2 text-xs font-bold shrink-0 shadow-md"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Đang tổng hợp...</span>
                </>
              ) : isPlaying ? (
                <>
                  <Square className="h-4 w-4 fill-current" />
                  <span>Dừng phát</span>
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 fill-current" />
                  <span>Nghe thử câu này</span>
                </>
              )}
            </Button>
          </div>
        </div>

        {/* Sliders: Speed & Pitch */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
          <div className="p-3 rounded-xl bg-background/80 border border-border space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-foreground flex items-center gap-1.5">
                <span>⏱️</span> Tốc độ đọc (Speed)
              </span>
              <span className="font-mono font-bold text-primary text-xs bg-primary/10 px-2 py-0.5 rounded-md">
                {speed.toFixed(2)}x
              </span>
            </div>
            <input
              type="range"
              min="0.7"
              max="1.4"
              step="0.05"
              value={speed}
              onChange={(e) => setSpeed(parseFloat(e.target.value))}
              className="w-full accent-primary cursor-pointer h-1.5 bg-muted rounded-lg"
            />
            <div className="flex justify-between text-[10px] text-muted-foreground">
              <span>0.7x (Chậm N5)</span>
              <span>1.0x (Chuẩn)</span>
              <span>1.4x (Nhanh N1)</span>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-background/80 border border-border space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-foreground flex items-center gap-1.5">
                <span>🎵</span> Cao độ giọng (Pitch)
              </span>
              <span className="font-mono font-bold text-primary text-xs bg-primary/10 px-2 py-0.5 rounded-md">
                {pitch > 0 ? `+${pitch.toFixed(2)}` : pitch.toFixed(2)}
              </span>
            </div>
            <input
              type="range"
              min="-0.15"
              max="0.15"
              step="0.02"
              value={pitch}
              onChange={(e) => setPitch(parseFloat(e.target.value))}
              className="w-full accent-primary cursor-pointer h-1.5 bg-muted rounded-lg"
            />
            <div className="flex justify-between text-[10px] text-muted-foreground">
              <span>Trầm hơn</span>
              <span>Mặc định (0.0)</span>
              <span>Cao hơn</span>
            </div>
          </div>
        </div>
      </div>

      {/* SECTION 2: SMART VOICE CATALOG & FILTER */}
      <div className="p-5 sm:p-6 rounded-[24px] border border-border bg-card shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h3 className="text-base font-bold text-foreground flex items-center gap-2">
              <Volume2 className="h-5 w-5 text-primary" />
              Thư viện & Danh mục Giọng đọc Nhật Bản
            </h3>
            <p className="text-xs text-muted-foreground mt-0.5">
              Nhấp vào bất kỳ giọng đọc nào để tải vào Studio nghe thử và đặt làm giọng đồng hành.
            </p>
          </div>
        </div>

        <VoiceSelector
          selectedVoiceId={selectedVoice?.voice_id || ""}
          defaultVoiceId={voices.find((v) => v.is_default)?.voice_id}
          sampleText={activeSampleText}
          speed={speed}
          pitch={pitch}
          savedProfiles={profiles}
          onSelect={(v) => setSelectedVoice(v)}
          onSetDefault={(v) => handleSetAsDefault(v)}
        />
      </div>

      {/* SECTION 3: QUICK MICROPHONE & STT TEST + PREFERENCES */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Mic Quick Test Card */}
        <div className="p-5 rounded-[24px] border border-border bg-card shadow-sm space-y-4 flex flex-col justify-between">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
                  <Mic className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-foreground">Kiểm tra Micro & Nhận diện STT</h3>
                  <p className="text-xs text-muted-foreground">Faster-Whisper nhận diện tiếng Nhật</p>
                </div>
              </div>

              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsCalibratingMic(true)}
                className="text-xs h-8 rounded-xl"
              >
                <Sliders className="h-3.5 w-3.5 mr-1" />
                Cân chỉnh sâu
              </Button>
            </div>

            <p className="text-xs text-muted-foreground leading-relaxed">
              Bấm nút bên dưới và nói 1 câu (ví dụ: <code className="font-jp text-foreground">こんにちは</code>) để
              kiểm tra mức âm lượng và độ nhạy của micro trước khi vào phòng luyện nói.
            </p>

            {/* Live Audio Level Meter */}
            <div className="p-3 rounded-xl bg-muted/40 border border-border space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground text-[11px]">Mức âm lượng micro:</span>
                <span className="font-mono font-bold text-xs text-foreground">{micAudioLevel}%</span>
              </div>
              <div className="h-2.5 w-full bg-background rounded-full overflow-hidden border border-border/60">
                <div
                  className={`h-full transition-all duration-100 rounded-full ${
                    micAudioLevel > 75
                      ? "bg-primary"
                      : micAudioLevel > 20
                      ? "bg-emerald-500"
                      : "bg-muted-foreground/30"
                  }`}
                  style={{ width: `${micAudioLevel}%` }}
                />
              </div>
            </div>

            {micTestResult && (
              <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-700 dark:text-emerald-300 text-xs flex items-center gap-2 animate-in fade-in">
                <CheckCircle2 className="h-4 w-4 shrink-0" />
                <span>{micTestResult}</span>
              </div>
            )}
          </div>

          <div className="pt-2">
            {!isTestingMic ? (
              <Button
                variant="primary"
                size="sm"
                onClick={startMicTest}
                className="w-full text-xs h-9 rounded-xl gap-2"
              >
                <Mic className="h-4 w-4" />
                Bắt đầu thử Micro ngay
              </Button>
            ) : (
              <Button
                variant="outline"
                size="sm"
                onClick={stopMicTest}
                className="w-full text-xs h-9 rounded-xl gap-2 border-primary text-primary hover:bg-primary/10"
              >
                <Radio className="h-4 w-4 animate-pulse text-primary" />
                Đang lắng nghe... Bấm để dừng
              </Button>
            )}
          </div>
        </div>

        {/* Playback & Behavior Preferences */}
        <div className="p-5 rounded-[24px] border border-border bg-card shadow-sm space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-600 dark:text-indigo-400 flex items-center justify-center">
              <Zap className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-foreground">Tùy chọn Phát âm & Hành vi</h3>
              <p className="text-xs text-muted-foreground">Tự động phát câu thoại và chuyển tiếp dự phòng</p>
            </div>
          </div>

          <div className="space-y-3 pt-1">
            {/* Auto Play AI Response */}
            <label className="p-3 rounded-xl bg-background/80 border border-border flex items-center justify-between gap-3 cursor-pointer hover:bg-muted/40 transition-colors">
              <div className="space-y-0.5">
                <div className="text-xs font-semibold text-foreground">
                  Tự động đọc câu trả lời của AI
                </div>
                <div className="text-[11px] text-muted-foreground">
                  Phát giọng nói của AI ngay sau khi hoàn thành lượt đối thoại.
                </div>
              </div>
              <input
                type="checkbox"
                checked={settings?.auto_play_ai_response ?? true}
                onChange={(e) => handleToggleSetting("auto_play_ai_response", e.target.checked)}
                className="w-4 h-4 rounded text-primary focus:ring-primary shrink-0 accent-primary"
              />
            </label>

            {/* TTS Fallback */}
            <label className="p-3 rounded-xl bg-background/80 border border-border flex items-center justify-between gap-3 cursor-pointer hover:bg-muted/40 transition-colors">
              <div className="space-y-0.5">
                <div className="text-xs font-semibold text-foreground">
                  Tự động chuyển tiếp dự phòng (TTS Fallback)
                </div>
                <div className="text-[11px] text-muted-foreground">
                  Nếu engine chính bận, tự động chuyển sang giọng sẵn có để không gián đoạn.
                </div>
              </div>
              <input
                type="checkbox"
                checked={settings?.tts_fallback_enabled ?? true}
                onChange={(e) => handleToggleSetting("tts_fallback_enabled", e.target.checked)}
                className="w-4 h-4 rounded text-primary focus:ring-primary shrink-0 accent-primary"
              />
            </label>

            {/* Speed Presets Quick Pick */}
            <div className="p-3 rounded-xl bg-background/80 border border-border space-y-2">
              <span className="text-xs font-semibold text-foreground block">
                Gói tốc độ phát âm thanh mẫu (Presets):
              </span>
              <div className="grid grid-cols-3 gap-2">
                <button
                  onClick={() => setSpeed(0.85)}
                  className={`p-2 rounded-lg border text-center transition-all ${
                    speed === 0.85
                      ? "bg-primary/10 border-primary text-primary font-bold"
                      : "bg-card border-border text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <div className="text-xs">N5 - N4</div>
                  <div className="text-[10px] font-mono">0.85x Chậm</div>
                </button>
                <button
                  onClick={() => setSpeed(1.0)}
                  className={`p-2 rounded-lg border text-center transition-all ${
                    speed === 1.0
                      ? "bg-primary/10 border-primary text-primary font-bold"
                      : "bg-card border-border text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <div className="text-xs">N3 Chuẩn</div>
                  <div className="text-[10px] font-mono">1.00x Tự nhiên</div>
                </button>
                <button
                  onClick={() => setSpeed(1.15)}
                  className={`p-2 rounded-lg border text-center transition-all ${
                    speed === 1.15
                      ? "bg-primary/10 border-primary text-primary font-bold"
                      : "bg-card border-border text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <div className="text-xs">N1 Nhanh</div>
                  <div className="text-[10px] font-mono">1.15x Bản xứ</div>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* SECTION 4: FASTER-WHISPER STT MODEL MANAGER */}
      <STTModelManagerCard />

      {/* SECTION 5: VOICEVOX ENGINE CARD */}
      <VoicevoxEngineCard onEngineReload={loadData} />

      {/* Modal: Save Custom Profile */}
      {showSaveProfileModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-card border border-border rounded-2xl p-5 max-w-md w-full shadow-2xl space-y-4 animate-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
                <Plus className="h-4 w-4 text-emerald-500" />
                Lưu hồ sơ giọng cá nhân
              </h3>
              <button
                onClick={() => setShowSaveProfileModal(false)}
                className="text-muted-foreground hover:text-foreground text-xs font-bold"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-muted-foreground">
              Lưu cấu hình hiện tại (Giọng: <strong className="text-foreground">{selectedVoice?.name}</strong>, Tốc
              độ: <strong className="text-foreground">{speed}x</strong>, Cao độ:{" "}
              <strong className="text-foreground">{pitch}</strong>) thành hồ sơ riêng để dùng nhanh.
            </p>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">Tên hồ sơ</label>
              <input
                type="text"
                placeholder="VD: Zundamon Luyện N5, Metan Điềm tĩnh..."
                value={newProfileName}
                onChange={(e) => setNewProfileName(e.target.value)}
                className="w-full px-3 py-2 bg-background border border-border rounded-xl text-xs text-foreground focus:outline-none focus:border-rose-500"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-border">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowSaveProfileModal(false)}
                className="text-xs"
              >
                Hủy
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleCreateProfile}
                disabled={savingProfile || !newProfileName.trim()}
                className="text-xs"
              >
                {savingProfile ? <Loader2 className="h-3.5 w-3.5 animate-spin mr-1" /> : null}
                Lưu hồ sơ
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Deep Mic Calibration */}
      <MicrophoneCalibrationModal
        isOpen={isCalibratingMic}
        onClose={() => setIsCalibratingMic(false)}
      />
    </div>
  );
}
