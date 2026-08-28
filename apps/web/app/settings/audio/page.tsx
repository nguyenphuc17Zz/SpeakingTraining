"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Volume2,
  Mic,
  Sliders,
  Sparkles,
  CheckCircle,
  Activity,
  Zap,
  Save,
  Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { AudioSettings, PlaybackPreset } from "@/types/audio";
import { audioApi } from "@/features/audio/services/audio-api";
import { MicrophoneCalibrationModal } from "@/features/audio/components/MicrophoneCalibrationModal";

export default function AudioSettingsPage() {
  const [settings, setSettings] = useState<AudioSettings | null>(null);
  const [presets, setPresets] = useState<PlaybackPreset[]>([]);
  const [isCalibrating, setIsCalibrating] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([audioApi.getSettings(), audioApi.listPresets()])
      .then(([s, p]) => {
        setSettings(s);
        setPresets(p);
        setIsLoading(false);
      })
      .catch((e) => {
        console.warn("Failed to load audio settings:", e);
        setIsLoading(false);
      });
  }, []);

  const handleSave = async () => {
    if (!settings) return;
    setIsSaving(true);
    setSavedMessage(null);
    try {
      const updated = await audioApi.updateSettings(settings);
      setSettings(updated);
      setSavedMessage("Cấu hình Audio đã được lưu thành công!");
    } catch (e: any) {
      setSavedMessage(`Lỗi: ${e.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading || !settings) {
    return (
      <div className="flex items-center justify-center py-20 text-muted-foreground gap-2">
        <Loader2 className="h-5 w-5 animate-spin" />
        <span className="text-sm">Đang tải cài đặt âm thanh...</span>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-in fade-in duration-200">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-border">
        <div className="flex items-center gap-3">
          <Link
            href="/settings"
            className="p-2 rounded-xl bg-card border border-border text-muted-foreground hover:text-foreground hover:bg-muted"
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div>
            <h1 className="text-xl font-bold text-foreground flex items-center gap-2">
              <Sliders className="h-5 w-5 text-rose-400" />
              Cấu hình Âm thanh & Micro (Audio Platform)
            </h1>
            <p className="text-xs text-muted-foreground mt-0.5">
              Cân chỉnh micro thu âm, quản lý chế độ dự phòng TTS, và thiết lập phát âm thanh.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Link href="/settings">
            <Button variant="outline" size="sm" className="text-xs">
              <Volume2 className="h-3.5 w-3.5 mr-1.5 text-primary" />
              Studio Giọng Nói
            </Button>
          </Link>

          <Link href="/settings/audio/diagnostics">
            <Button variant="outline" size="sm" className="text-xs">
              <Activity className="h-3.5 w-3.5 mr-1.5 text-aizome-400" />
              Diagnostics
            </Button>
          </Link>

          <Button
            variant="primary"
            size="sm"
            onClick={handleSave}
            disabled={isSaving}
            className="text-xs"
          >
            {isSaving ? <Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" /> : <Save className="h-3.5 w-3.5 mr-1.5" />}
            Lưu thay đổi
          </Button>
        </div>
      </div>

      {savedMessage && (
        <div className="p-3 rounded-xl bg-aizome-500/10 border border-aizome-500/30 text-aizome-300 text-xs flex items-center gap-2">
          <CheckCircle className="h-4 w-4 shrink-0" />
          <span>{savedMessage}</span>
        </div>
      )}

      {/* Section 1: Microphone Calibration */}
      <div className="p-5 rounded-2xl bg-card/80 border border-border space-y-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-primary/10 border border-primary/20 text-primary">
              <Mic className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-foreground">Cân chỉnh Microphone Đầu Vào</h3>
              <p className="text-xs text-muted-foreground">
                Kiểm tra âm lượng, độ ồn và hiện tượng méo tiếng (clipping) trước khi luyện nói.
              </p>
            </div>
          </div>

          <Button
            variant="primary"
            size="sm"
            onClick={() => setIsCalibrating(true)}
            className="text-xs shadow-md shadow-primary/20"
          >
            <Mic className="h-3.5 w-3.5 mr-1.5" />
            Mở bộ cân chỉnh Micro
          </Button>
        </div>
      </div>

      {/* Section 2: Speech Engines & Fallback */}
      <div className="p-5 rounded-2xl bg-card/80 border border-border space-y-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-aizome-500/10 border border-aizome-500/20 text-aizome-400">
            <Zap className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-foreground">Engine Tổng hợp & Nhận diện Giọng nói</h3>
            <p className="text-xs text-muted-foreground">
              Cấu hình nhà cung cấp mặc định và cơ chế dự phòng (Fallback)
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
          {/* TTS Provider */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-foreground">TTS Engine mặc định</label>
            <select
              value={settings.default_tts_provider}
              onChange={(e) =>
                setSettings({ ...settings, default_tts_provider: e.target.value })
              }
              className="w-full px-3 py-2 bg-background border border-border rounded-xl text-xs text-foreground focus:outline-none focus:border-primary"
            >
              <option value="voicevox">VOICEVOX (Local / Self-hosted)</option>
            </select>
          </div>

          {/* STT Provider */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-foreground">STT Engine mặc định</label>
            <select
              value={settings.default_stt_provider}
              onChange={(e) =>
                setSettings({ ...settings, default_stt_provider: e.target.value })
              }
              className="w-full px-3 py-2 bg-background border border-border rounded-xl text-xs text-foreground focus:outline-none focus:border-primary"
            >
              <option value="faster_whisper">Faster-Whisper (Local CT2 / VAD)</option>
            </select>
          </div>
        </div>

        {/* Fallback Toggle */}
        <div className="p-3.5 rounded-xl bg-background border border-border/80 flex items-center justify-between">
          <div>
            <h4 className="text-xs font-semibold text-foreground">Tự động chuyển tiếp dự phòng (TTS Fallback)</h4>
            <p className="text-[11px] text-muted-foreground">
              Khi engine chính mất kết nối, tự động chuyển sang giọng mặc định để không làm gián đoạn hội thoại.
            </p>
          </div>
          <input
            type="checkbox"
            checked={settings.tts_fallback_enabled}
            onChange={(e) =>
              setSettings({ ...settings, tts_fallback_enabled: e.target.checked })
            }
            className="w-4 h-4 rounded text-primary focus:ring-primary accent-primary"
          />
        </div>

        {/* Auto Play Response */}
        <div className="p-3.5 rounded-xl bg-background border border-border/80 flex items-center justify-between">
          <div>
            <h4 className="text-xs font-semibold text-foreground">Tự động phát câu trả lời của AI</h4>
            <p className="text-[11px] text-muted-foreground">
              Phát âm thanh giọng nói của AI ngay sau khi hoàn tất lượt trả lời.
            </p>
          </div>
          <input
            type="checkbox"
            checked={settings.auto_play_ai_response}
            onChange={(e) =>
              setSettings({ ...settings, auto_play_ai_response: e.target.checked })
            }
            className="w-4 h-4 rounded text-primary focus:ring-primary accent-primary"
          />
        </div>
      </div>

      {/* Section 3: Playback Presets */}
      <div className="p-5 rounded-2xl bg-card/80 border border-border space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-foreground">Presets Tốc độ & Lặp lại Sẵn có</h3>
              <p className="text-xs text-muted-foreground">
                Các cấu hình phát âm mẫu cho Conversation, Pronunciation và Shadowing
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
          {presets.map((p) => (
            <div
              key={p.id}
              className="p-3.5 rounded-xl bg-background border border-border space-y-1.5"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-foreground">{p.name}</span>
                <span className="font-mono text-xs px-2 py-0.5 rounded bg-card border border-border text-rose-300">
                  {p.speed}x
                </span>
              </div>
              <p className="text-[11px] text-muted-foreground leading-relaxed">
                {p.description}
              </p>
              <div className="flex items-center gap-3 text-[10px] text-muted-foreground pt-1 font-mono">
                <span>Lặp: {p.loop_count} lần</span>
                <span>Nghỉ: {p.pause_after_ms}ms</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Calibration Modal */}
      <MicrophoneCalibrationModal
        isOpen={isCalibrating}
        onClose={() => setIsCalibrating(false)}
      />
    </div>
  );
}
