"use client";

import React, { useState, useEffect, useRef } from "react";
import { Persona } from "@/types/persona";
import { SessionMode, VADSensitivity, VoiceSettingsConfig } from "../types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Mic,
  Sparkles,
  Volume2,
  VolumeX,
  Cpu,
  Play,
  Square,
  CheckCircle2,
  AlertCircle,
  Radio,
  Check,
  Search,
  Settings2,
  Headphones,
  Globe,
  Zap,
} from "lucide-react";
import { settingsApi } from "@/services/settings-api";
import { cn } from "@/lib/utils";
import { aiApi } from "@/services/ai-api";
import { providersApi } from "@/services/providers-api";
import { audioApi } from "@/features/audio/services/audio-api";
import { STTModelInfo, VoiceProfile } from "@/types/audio";
import { ModelMetadata, ProviderDetail } from "@/types/provider";
import {
  VOICEVOX_FALLBACK_CATALOG,
  getVoiceCharacterMeta,
} from "@/features/audio/services/voice-meta";
import {
  isWebSpeechSupported,
  speakJapaneseText,
  stopWebSpeech,
} from "../services/web-speech";
import {
  getSavedLobbyPreferences,
  saveLobbyPreferences,
} from "../services/lobby-preferences";
import { soundFX } from "@/lib/sound-fx";

interface SessionLobbyProps {
  persona: Persona;
  volumeLevel: number;
  isInitializing: boolean;
  onStartSession: (mode: SessionMode, config: Partial<VoiceSettingsConfig>) => void;
  onClose: () => void;
}

type LobbyTab = "mode_ai" | "stt_mic" | "voicevox";
type TTSEngineMode = "voicevox" | "web_speech" | "none";

export function SessionLobby({
  persona,
  volumeLevel,
  isInitializing,
  onStartSession,
  onClose,
}: SessionLobbyProps) {
  // Read saved user preferences from previous sessions
  const initialPrefs = useRef(getSavedLobbyPreferences()).current;

  const [activeTab, setActiveTab] = useState<LobbyTab>("mode_ai");
  const [mode, setMode] = useState<SessionMode>(initialPrefs.mode);
  const [isAdvancedOpen, setIsAdvancedOpen] = useState(false);

  // AI Provider & Model States
  const [aiProvider, setAiProvider] = useState(initialPrefs.ai_provider);
  const [aiModel, setAiModel] = useState(initialPrefs.ai_model);
  const [providers, setProviders] = useState<ProviderDetail[]>([]);
  const [availableModels, setAvailableModels] = useState<ModelMetadata[]>([]);

  // STT Whisper Models
  const [sttModel, setSttModel] = useState(initialPrefs.stt_model);
  const [sttModelsList, setSttModelsList] = useState<STTModelInfo[]>([]);

  // TTS & VOICEVOX States
  const [ttsEnabled, setTtsEnabled] = useState(initialPrefs.tts_enabled);
  const [ttsEngine, setTtsEngine] = useState<TTSEngineMode>(initialPrefs.tts_engine);
  const [voicevoxOnline, setVoicevoxOnline] = useState<boolean | null>(null);
  const [ttsVoice, setTtsVoice] = useState(initialPrefs.tts_voice);
  const [voicesList, setVoicesList] = useState<VoiceProfile[]>(VOICEVOX_FALLBACK_CATALOG);
  const [voiceSearch, setVoiceSearch] = useState("");
  const [voiceFilter, setVoiceFilter] = useState<"all" | "female" | "male" | "anime" | "calm">("all");
  const [previewingVoiceId, setPreviewingVoiceId] = useState<string | null>(null);

  // VAD & End of Speech States
  const [autoEndOfSpeech, setAutoEndOfSpeech] = useState(initialPrefs.auto_end_of_speech);
  const [vadSensitivity, setVadSensitivity] = useState<VADSensitivity>(initialPrefs.vad_sensitivity);

  // Mic Test & Playback States
  const [isTestRecording, setIsTestRecording] = useState(false);
  const [testRecordDuration, setTestRecordDuration] = useState(0);
  const [testAudioUrl, setTestAudioUrl] = useState<string | null>(null);
  const [isPlayingTestAudio, setIsPlayingTestAudio] = useState(false);
  const [testPeakVolume, setTestPeakVolume] = useState(0);
  const testRecorderRef = useRef<MediaRecorder | null>(null);
  const testStreamRef = useRef<MediaStream | null>(null);
  const testChunksRef = useRef<Blob[]>([]);
  const testTimerRef = useRef<NodeJS.Timeout | null>(null);
  const testAudioElementRef = useRef<HTMLAudioElement | null>(null);

  // Persisting Handlers
  const handleModeChange = (newMode: SessionMode) => {
    setMode(newMode);
    saveLobbyPreferences({ mode: newMode });
  };

  const handleAiProviderChange = (newProvider: string) => {
    setAiProvider(newProvider);
    saveLobbyPreferences({ ai_provider: newProvider });
  };

  const handleAiModelChange = (newModel: string) => {
    setAiModel(newModel);
    saveLobbyPreferences({ ai_model: newModel });
  };

  const handleSttModelChange = (newModel: string) => {
    setSttModel(newModel);
    saveLobbyPreferences({ stt_model: newModel });
  };

  const handleTtsEngineChange = (newEngine: TTSEngineMode) => {
    setTtsEngine(newEngine);
    const enabled = newEngine !== "none";
    setTtsEnabled(enabled);
    saveLobbyPreferences({ tts_engine: newEngine, tts_enabled: enabled });
  };

  const handleTtsEnabledToggle = (enabled: boolean) => {
    setTtsEnabled(enabled);
    const engine: TTSEngineMode = enabled ? (ttsEngine === "none" ? "voicevox" : ttsEngine) : "none";
    setTtsEngine(engine);
    saveLobbyPreferences({ tts_enabled: enabled, tts_engine: engine });
  };

  const handleTtsVoiceChange = (newVoice: string) => {
    setTtsVoice(newVoice);
    saveLobbyPreferences({ tts_voice: newVoice });
  };

  const handleAutoVADToggle = (enabled: boolean) => {
    setAutoEndOfSpeech(enabled);
    saveLobbyPreferences({ auto_end_of_speech: enabled });
  };

  const handleVadSensitivityChange = (sens: VADSensitivity) => {
    setVadSensitivity(sens);
    saveLobbyPreferences({ vad_sensitivity: sens });
  };

  // Load User System Settings & Catalogs on mount
  useEffect(() => {
    let isMounted = true;

    async function loadLobbyConfigs() {
      try {
        const [
          userSettings,
          audioSettings,
          providersData,
          sttData,
          voicesData,
          healthData,
        ] = await Promise.all([
          settingsApi.getSettings().catch(() => null),
          audioApi.getSettings().catch(() => null),
          providersApi.listProviders().catch(() => []),
          audioApi.listSTTModels().catch(() => []),
          audioApi.getVoices("voicevox").catch(() => []),
          audioApi.getProvidersHealth().catch(() => []),
        ]);

        if (!isMounted) return;

        if (providersData && providersData.length > 0) {
          setProviders(providersData);
        }

        if (healthData && healthData.length > 0) {
          const vv = healthData.find((h) => h.provider_id === "voicevox");
          if (vv) {
            setVoicevoxOnline(vv.is_available);
          }
        }

        if (sttData && sttData.length > 0) {
          setSttModelsList(sttData);
          // If no previous model saved, pick active/recommended
          if (initialPrefs.stt_model === "base") {
            const activeSTT = sttData.find((m) => m.is_active);
            if (activeSTT) {
              setSttModel(activeSTT.id);
            }
          }
        }

        // Merge API voices with full catalog so no voices are missing
        if (voicesData && voicesData.length > 6) {
          setVoicesList(voicesData);
        } else if (voicesData && voicesData.length > 0) {
          const ids = new Set(voicesData.map((v) => v.voice_id || v.id));
          const rest = VOICEVOX_FALLBACK_CATALOG.filter((v) => !ids.has(v.voice_id || v.id));
          setVoicesList([...voicesData, ...rest]);
        } else {
          setVoicesList(VOICEVOX_FALLBACK_CATALOG);
        }

        // Apply Defaults from Settings if user hasn't customized in localStorage
        if (userSettings && initialPrefs.ai_provider === "auto") {
          if (userSettings.default_ai_provider) {
            setAiProvider(userSettings.default_ai_provider);
          }
          if (userSettings.default_ai_model) {
            setAiModel(userSettings.default_ai_model);
          }
        }

        if (audioSettings && initialPrefs.tts_voice === "1") {
          if (audioSettings.default_voice_profile_id) {
            setTtsVoice(audioSettings.default_voice_profile_id);
          }
        }
      } catch (err) {
        console.warn("[SessionLobby] Failed to preload settings:", err);
      }
    }

    loadLobbyConfigs();

    return () => {
      isMounted = false;
      stopTestRecording();
      stopWebSpeech();
      if (testAudioElementRef.current) {
        testAudioElementRef.current.pause();
      }
    };
  }, []);

  // Update models list when AI provider changes
  useEffect(() => {
    let isMounted = true;
    if (aiProvider === "auto") {
      setAvailableModels([]);
      return;
    }

    aiApi
      .listModels(aiProvider)
      .then((models) => {
        if (isMounted) {
          setAvailableModels(models);
          if (models.length > 0) {
            const hasCurrent = models.some((m) => m.id === aiModel);
            if (!hasCurrent) {
              setAiModel(models[0].id);
              saveLobbyPreferences({ ai_model: models[0].id });
            }
          }
        }
      })
      .catch(() => {
        if (isMounted) setAvailableModels([]);
      });

    return () => {
      isMounted = false;
    };
  }, [aiProvider]);

  // Track Peak Volume during test recording
  useEffect(() => {
    if (isTestRecording && volumeLevel > testPeakVolume) {
      setTestPeakVolume(volumeLevel);
    }
  }, [isTestRecording, volumeLevel, testPeakVolume]);

  // Voice Preview
  const handlePreviewVoice = async (voiceId: string) => {
    if (previewingVoiceId) return;

    if (ttsEngine === "web_speech") {
      setPreviewingVoiceId("web_speech");
      speakJapaneseText("こんにちは！一緒に日本語で楽しく話しましょう。", {
        onEnd: () => setPreviewingVoiceId(null),
        onError: () => setPreviewingVoiceId(null),
      });
      return;
    }

    setPreviewingVoiceId(voiceId);
    try {
      const sample = "こんにちは！一緒に日本語で楽しく話しましょう。";
      const res = await audioApi.previewVoice(sample, voiceId, "voicevox");
      if (res.audio_base64) {
        const audio = new Audio(`data:audio/wav;base64,${res.audio_base64}`);
        audio.onended = () => setPreviewingVoiceId(null);
        audio.onerror = () => setPreviewingVoiceId(null);
        await audio.play();
      } else {
        setPreviewingVoiceId(null);
      }
    } catch (e: any) {
      console.warn("VOICEVOX preview offline/failed:", e);
      setPreviewingVoiceId(null);
    }
  };

  // Mic Testing Functions
  const startTestRecording = async () => {
    try {
      if (testAudioElementRef.current) {
        testAudioElementRef.current.pause();
        setIsPlayingTestAudio(false);
      }
      setTestAudioUrl(null);
      testChunksRef.current = [];
      setTestRecordDuration(0);
      setTestPeakVolume(0);

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      testStreamRef.current = stream;
      const recorder = new MediaRecorder(stream);
      testRecorderRef.current = recorder;

      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          testChunksRef.current.push(e.data);
        }
      };

      recorder.onstop = () => {
        const blob = new Blob(testChunksRef.current, { type: "audio/webm" });
        const url = URL.createObjectURL(blob);
        setTestAudioUrl(url);
        stream.getTracks().forEach((t) => {
          try {
            t.stop();
          } catch {}
        });
        testStreamRef.current = null;
      };

      recorder.start(100);
      setIsTestRecording(true);

      // Auto countdown 5s max
      let sec = 0;
      testTimerRef.current = setInterval(() => {
        sec += 1;
        setTestRecordDuration(sec);
        if (sec >= 5) {
          stopTestRecording();
        }
      }, 1000);
    } catch (err) {
      console.error("Mic test access failed:", err);
    }
  };

  const stopTestRecording = () => {
    if (testTimerRef.current) {
      clearInterval(testTimerRef.current);
      testTimerRef.current = null;
    }
    if (testStreamRef.current) {
      testStreamRef.current.getTracks().forEach((t) => {
        try {
          t.stop();
        } catch {}
      });
      testStreamRef.current = null;
    }
    if (testRecorderRef.current && testRecorderRef.current.state !== "inactive") {
      try {
        testRecorderRef.current.stop();
      } catch {}
    }
    setIsTestRecording(false);
  };

  const playTestAudio = () => {
    if (!testAudioUrl) return;
    if (testAudioElementRef.current) {
      testAudioElementRef.current.pause();
    }
    const audio = new Audio(testAudioUrl);
    testAudioElementRef.current = audio;
    setIsPlayingTestAudio(true);
    audio.onended = () => setIsPlayingTestAudio(false);
    audio.onerror = () => setIsPlayingTestAudio(false);
    audio.play();
  };

  const handleStart = () => {
    const isTtsOff = !ttsEnabled || ttsEngine === "none";
    const selectedProvider = isTtsOff
      ? "none"
      : ttsEngine === "web_speech"
      ? "web_speech"
      : "voicevox";

    // 1. Persist full configuration in localStorage for instant recall next time
    saveLobbyPreferences({
      mode,
      ai_provider: aiProvider,
      ai_model: aiModel,
      stt_model: sttModel,
      tts_engine: isTtsOff ? "none" : ttsEngine,
      tts_enabled: !isTtsOff,
      tts_voice: ttsVoice,
      auto_end_of_speech: autoEndOfSpeech,
      vad_sensitivity: vadSensitivity,
    });

    // 2. Background sync with backend user settings
    if (aiProvider !== "auto") {
      settingsApi
        .updateSettings({
          default_ai_provider: aiProvider,
          default_ai_model: aiModel !== "auto" ? aiModel : undefined,
        })
        .catch(() => {});
    }

    onStartSession(mode, {
      ai_provider: aiProvider,
      ai_model: aiModel,
      stt_model: sttModel,
      tts_provider: selectedProvider,
      tts_voice: ttsVoice,
      tts_enabled: !isTtsOff,
      tts_engine: isTtsOff ? "none" : ttsEngine,
      auto_end_of_speech: autoEndOfSpeech,
      vad_sensitivity: vadSensitivity,
    });
  };

  // Filter voices list
  const filteredVoices = voicesList.filter((v) => {
    const meta = getVoiceCharacterMeta(v);
    if (voiceFilter === "female" && meta.gender !== "female") return false;
    if (voiceFilter === "male" && meta.gender !== "male") return false;
    if (voiceFilter === "anime" && meta.gender !== "mascot" && meta.vibe !== "energetic" && meta.vibe !== "cute") return false;
    if (voiceFilter === "calm" && meta.vibe !== "calm" && meta.vibe !== "gentle" && meta.vibe !== "deep") return false;

    if (!voiceSearch.trim()) return true;
    const q = voiceSearch.toLowerCase();
    return (
      (v.name || "").toLowerCase().includes(q) ||
      (v.style || "").toLowerCase().includes(q) ||
      meta.genderLabel.toLowerCase().includes(q) ||
      meta.vibeLabel.toLowerCase().includes(q)
    );
  });

  const selectedVoiceObj = voicesList.find((v) => (v.voice_id || v.id) === ttsVoice) || voicesList[0];

  return (
    <div className="flex flex-col space-y-4 max-h-full">
      {/* Persona Header Card */}
      <div className="p-3.5 rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900 to-slate-950 border border-border space-y-2.5 shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 min-w-0">
            <div className="h-11 w-11 rounded-2xl bg-gradient-to-tr from-primary via-akane-600 to-indigo-600 flex items-center justify-center text-primary-foreground font-extrabold text-base shadow-md shrink-0">
              {persona.name.charAt(0)}
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h3 className="text-sm font-bold text-foreground truncate">{persona.name}</h3>
                <Badge variant="jlpt" size="sm">
                  {persona.difficulty}
                </Badge>
                {persona.is_system && (
                  <Badge variant="fuji" size="sm" className="text-[10px] py-0 px-1.5 h-4">
                    Mẫu
                  </Badge>
                )}
              </div>
              <p className="text-xs text-primary font-medium truncate">{persona.role}</p>
            </div>
          </div>

          <div className="text-right hidden sm:block text-[11px] text-muted-foreground">
            <span className="text-foreground font-medium">{persona.speaking_style}</span>
          </div>
        </div>

        <p className="text-xs text-muted-foreground leading-relaxed line-clamp-2">{persona.description}</p>
      </div>

      {/* 1-Click Quick Presets Bar */}
      {/* Core Mode Selection (2 Clean Cards) */}
      <div className="space-y-2">
        <label className="text-xs font-bold text-foreground flex items-center justify-between">
          <span>1. Chọn Chế Độ Luyện Tập:</span>
          <span className="text-[10px] text-muted-foreground font-normal">Tự động cấu hình chuẩn theo nhân vật</span>
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          <button
            type="button"
            onClick={() => {
              soundFX.playFurin();
              handleModeChange("conversation");
            }}
            className={cn(
              "p-3 rounded-2xl border text-left transition-all relative",
              mode === "conversation"
                ? "bg-primary/10 border-primary shadow-xs ring-1 ring-primary/30"
                : "bg-card border-border hover:border-primary/40 text-muted-foreground"
            )}
          >
            <div className="flex items-center gap-2">
              <span className="text-base">🗣️</span>
              <span className={cn("text-xs font-bold", mode === "conversation" ? "text-primary" : "text-foreground")}>
                Hội Thoại Tự Nhiên
              </span>
            </div>
            <p className="text-[11px] text-muted-foreground mt-1 leading-snug">
              Đàm thoại trôi chảy, phản xạ nhanh như trò chuyện với người bản xứ.
            </p>
          </button>

          <button
            type="button"
            onClick={() => {
              soundFX.playFurin();
              handleModeChange("coaching");
            }}
            className={cn(
              "p-3 rounded-2xl border text-left transition-all relative",
              mode === "coaching"
                ? "bg-amber-500/10 border-amber-500 shadow-xs ring-1 ring-amber-500/30"
                : "bg-card border-border hover:border-amber-500/40 text-muted-foreground"
            )}
          >
            <div className="flex items-center gap-2">
              <Sparkles className={cn("h-4 w-4", mode === "coaching" ? "text-amber-500" : "text-muted-foreground")} />
              <span className={cn("text-xs font-bold", mode === "coaching" ? "text-amber-700 dark:text-amber-300" : "text-foreground")}>
                Có Giảng Viên Hướng Dẫn (Coaching)
              </span>
            </div>
            <p className="text-[11px] text-muted-foreground mt-1 leading-snug">
              AI gợi ý mẫu câu, sửa lỗi ngữ pháp & phát âm sau mỗi lượt nói.
            </p>
          </button>
        </div>
      </div>

      {/* Voice & Sound Quick Bar */}
      <div className="p-3 rounded-2xl bg-card border border-border flex flex-wrap items-center justify-between gap-2.5">
        <div className="flex items-center gap-2 min-w-0">
          <div className="h-8 w-8 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary text-xs font-bold shrink-0">
            {ttsEngine === "none" || !ttsEnabled ? "🔇" : ttsEngine === "web_speech" ? "🌐" : "🔊"}
          </div>
          <div className="min-w-0">
            <div className="text-[11px] font-bold text-foreground truncate flex items-center gap-1.5">
              <span>Giọng đọc NPC:</span>
              <span className="text-primary font-jp">
                {!ttsEnabled || ttsEngine === "none"
                  ? "Tắt âm thanh"
                  : ttsEngine === "web_speech"
                  ? "Giọng WebSpeech Trình Duyệt"
                  : selectedVoiceObj?.name || "VOICEVOX"}
              </span>
            </div>
            <div className="text-[10px] text-muted-foreground truncate">
              {!ttsEnabled || ttsEngine === "none" ? "Chỉ hiển thị phụ đề văn bản" : "Giọng phát âm chuẩn Tokyo"}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-1.5 shrink-0 ml-auto">
          {ttsEnabled && ttsEngine !== "none" && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePreviewVoice(ttsVoice)}
              isLoading={previewingVoiceId === ttsVoice || previewingVoiceId === "web_speech"}
              className="h-7 text-[11px] font-bold gap-1 px-2.5 rounded-lg"
            >
              <Play className="h-3 w-3 fill-current" />
              <span>Nghe thử</span>
            </Button>
          )}

          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleTtsEnabledToggle(!ttsEnabled)}
            className="h-7 text-[11px] font-bold text-muted-foreground hover:text-foreground px-2 rounded-lg"
          >
            {ttsEnabled ? "Tắt tiếng" : "Bật tiếng"}
          </Button>
        </div>
      </div>

      {/* Progressive Disclosure: Advanced Settings Accordion */}
      <div className="border border-border/80 rounded-2xl bg-muted/20 overflow-hidden">
        <button
          type="button"
          onClick={() => setIsAdvancedOpen((v) => !v)}
          className="w-full px-3.5 py-2.5 flex items-center justify-between text-xs font-bold text-muted-foreground hover:text-foreground hover:bg-muted/40 transition-colors"
        >
          <span className="flex items-center gap-1.5">
            <Settings2 className="h-3.5 w-3.5 text-primary" />
            <span>⚙️ Cài đặt kỹ thuật chuyên sâu (AI Provider, Whisper STT, Đổi giọng, Test mic)</span>
          </span>
          <span className="text-[10px] font-semibold text-primary">
            {isAdvancedOpen ? "Thu gọn ▲" : "Mở rộng ▼"}
          </span>
        </button>

        {isAdvancedOpen && (
          <div className="p-3.5 pt-1 space-y-3 border-t border-border/60 animate-in fade-in duration-200">
            {/* Advanced Navigation Tabs */}
            <div className="flex items-center gap-1.5 p-1 rounded-xl bg-muted/60 border border-border overflow-x-auto">
              <button
                type="button"
                onClick={() => setActiveTab("mode_ai")}
                className={cn(
                  "flex-1 min-w-[120px] px-2.5 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-1",
                  activeTab === "mode_ai" ? "bg-card text-foreground shadow-2xs border border-border" : "text-muted-foreground hover:text-foreground"
                )}
              >
                <Cpu className="h-3.5 w-3.5 text-primary" />
                <span>AI Model</span>
              </button>

              <button
                type="button"
                onClick={() => setActiveTab("stt_mic")}
                className={cn(
                  "flex-1 min-w-[120px] px-2.5 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-1",
                  activeTab === "stt_mic" ? "bg-card text-foreground shadow-2xs border border-border" : "text-muted-foreground hover:text-foreground"
                )}
              >
                <Mic className="h-3.5 w-3.5 text-emerald-500" />
                <span>STT & Test Mic</span>
              </button>

              <button
                type="button"
                onClick={() => setActiveTab("voicevox")}
                className={cn(
                  "flex-1 min-w-[120px] px-2.5 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-1",
                  activeTab === "voicevox" ? "bg-card text-foreground shadow-2xs border border-border" : "text-muted-foreground hover:text-foreground"
                )}
              >
                <Headphones className="h-3.5 w-3.5 text-indigo-500" />
                <span>Danh Sách Giọng</span>
              </button>
            </div>

      {/* Tab 1: Conversation Mode & AI Provider Configuration */}
      {activeTab === "mode_ai" && (
        <div className="space-y-4 animate-in fade-in duration-150">
          {/* Mode Selection */}
          <div className="space-y-2">
            <label className="text-xs font-bold text-foreground">Chế độ hội thoại (練習モード)</label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              <button
                type="button"
                onClick={() => handleModeChange("conversation")}
                className={`p-3 rounded-xl border text-left transition-all ${
                  mode === "conversation"
                    ? "bg-primary/10 border-primary/50 shadow-sm shadow-primary/10"
                    : "bg-card/60 border-border hover:border-border text-muted-foreground"
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className="text-sm">🗣️</span>
                  <span
                    className={`text-xs font-bold ${
                      mode === "conversation" ? "text-primary" : "text-foreground"
                    }`}
                  >
                    Hội thoại tự nhiên
                  </span>
                </div>
                <p className="text-[11px] text-muted-foreground mt-1">
                  Đắm chìm đàm thoại tự nhiên, không bị ngắt quãng mid-dialogue.
                </p>
              </button>

              <button
                type="button"
                onClick={() => handleModeChange("coaching")}
                className={`p-3 rounded-xl border text-left transition-all ${
                  mode === "coaching"
                    ? "bg-aizome-500/10 border-aizome-500/50 shadow-sm shadow-aizome-500/10"
                    : "bg-card/60 border-border hover:border-border text-muted-foreground"
                }`}
              >
                <div className="flex items-center gap-2">
                  <Sparkles
                    className={`h-4 w-4 ${mode === "coaching" ? "text-aizome-400" : "text-muted-foreground"}`}
                  />
                  <span
                    className={`text-xs font-bold ${
                      mode === "coaching" ? "text-aizome-300" : "text-foreground"
                    }`}
                  >
                    Có AI Coach hướng dẫn
                  </span>
                </div>
                <p className="text-[11px] text-muted-foreground mt-1">
                  Gợi ý từ vựng, sửa nhẹ ngữ pháp và hỗ trợ phản xạ sau mỗi câu nói.
                </p>
              </button>
            </div>
          </div>

          {/* AI Provider & Model (Synced with Settings) */}
          <div className="p-3.5 rounded-2xl bg-card border border-border space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-foreground flex items-center gap-1.5">
                <Cpu className="h-3.5 w-3.5 text-primary" /> AI Provider & Model (Đồng bộ & Tự lưu)
              </label>
              <Badge variant="fuji" size="sm">
                {aiProvider === "auto" ? "Tự động hệ thống" : aiProvider.toUpperCase()}
              </Badge>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <span className="text-[11px] text-muted-foreground block mb-1 font-medium">Provider</span>
                <select
                  value={aiProvider}
                  onChange={(e) => handleAiProviderChange(e.target.value)}
                  className="w-full px-2.5 py-2 rounded-lg bg-background border border-border text-foreground text-xs focus:outline-none focus:border-primary"
                >
                  <option value="auto">🌟 Tự động (Theo cài đặt hệ thống: Gemini / Groq)</option>
                  {providers.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.display_name || p.id} {p.is_configured ? "✓ (Đã có Key)" : "⚠️ (Chưa có Key)"}
                    </option>
                  ))}
                  {!providers.some((p) => p.id === "gemini") && <option value="gemini">Google Gemini</option>}
                  {!providers.some((p) => p.id === "groq") && <option value="groq">Groq LPU (Ultra Fast)</option>}
                </select>
              </div>

              <div>
                <span className="text-[11px] text-muted-foreground block mb-1 font-medium">Model</span>
                {aiProvider === "auto" ? (
                  <div className="px-2.5 py-2 rounded-lg bg-background/60 border border-dashed border-border text-muted-foreground text-xs flex items-center justify-between">
                    <span>Tự động tối ưu theo từng lượt</span>
                    <Sparkles className="h-3 w-3 text-primary" />
                  </div>
                ) : (
                  <select
                    value={aiModel}
                    onChange={(e) => handleAiModelChange(e.target.value)}
                    className="w-full px-2.5 py-2 rounded-lg bg-background border border-border text-foreground text-xs focus:outline-none focus:border-primary"
                  >
                    {availableModels.length > 0 ? (
                      availableModels.map((m) => (
                        <option key={m.id} value={m.id}>
                          {m.display_name || m.id}
                        </option>
                      ))
                    ) : (
                      <>
                        <option value="gemini-1.5-flash">Gemini 1.5 Flash (Khuyên dùng)</option>
                        <option value="gemini-2.0-flash">Gemini 2.0 Flash</option>
                        <option value="llama-3.3-70b-versatile">Llama 3.3 70B (Groq)</option>
                      </>
                    )}
                  </select>
                )}
              </div>
            </div>
          </div>

          {/* End of Speech / VAD Toggle */}
          <div className="p-3.5 rounded-2xl bg-card border border-border space-y-2.5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-foreground flex items-center gap-1.5">
                <Radio className="h-3.5 w-3.5 text-primary" /> Kết thúc câu nói (End of Speech) & VAD
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <span className="text-[11px] text-muted-foreground font-medium">
                  {autoEndOfSpeech ? "Tự động ngắt khi dứt câu" : "Thủ công (Push-to-Talk)"}
                </span>
                <input
                  type="checkbox"
                  checked={autoEndOfSpeech}
                  onChange={(e) => handleAutoVADToggle(e.target.checked)}
                  className="h-4 w-4 accent-primary rounded cursor-pointer"
                />
              </label>
            </div>

            {autoEndOfSpeech ? (
              <div className="p-2.5 rounded-xl bg-primary/5 border border-primary/15 space-y-1.5">
                <span className="text-[11px] font-semibold text-foreground">Độ nhạy ngắt câu:</span>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { id: "high", label: "⚡ Nhạy (0.7s)", desc: "Ngắt nhanh dứt khoát" },
                    { id: "medium", label: "⚖️ Cân bằng (1.0s)", desc: "Tiêu chuẩn tự nhiên" },
                    { id: "low", label: "⏳ Chậm rãi (1.4s)", desc: "Cho phép ngập ngừng" },
                  ].map((sens) => (
                    <button
                      key={sens.id}
                      type="button"
                      onClick={() => handleVadSensitivityChange(sens.id as VADSensitivity)}
                      className={`p-2 rounded-lg border text-left transition-colors ${
                        vadSensitivity === sens.id
                          ? "bg-primary text-primary-foreground border-primary shadow-sm"
                          : "bg-background text-muted-foreground border-border hover:text-foreground"
                      }`}
                    >
                      <span className="block text-[11px] font-bold">{sens.label}</span>
                      <span className="text-[10px] opacity-80">{sens.desc}</span>
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-[11px] text-amber-600 dark:text-amber-400 flex items-start gap-2">
                <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                <span>
                  <strong>Chế độ thủ công:</strong> Bạn có thể dừng lại suy nghĩ bao lâu tùy ý mà không sợ bị ngắt câu. Khi nói xong hãy bấm nút <em>"Hoàn thành & Gửi"</em> trong phòng nói.
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 2: STT Faster-Whisper & Mic Quick Test */}
      {activeTab === "stt_mic" && (
        <div className="space-y-4 animate-in fade-in duration-150">
          {/* Faster-Whisper Model List (All 6 models) */}
          <div className="p-3.5 rounded-2xl bg-card border border-border space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-foreground flex items-center gap-1.5">
                <Mic className="h-3.5 w-3.5 text-primary" /> Faster-Whisper STT (Toàn bộ 6 Model nhận diện)
              </label>
              <span className="text-[11px] text-muted-foreground">
                {sttModelsList.length > 0 ? `${sttModelsList.length} models` : "6 models có sẵn"}
              </span>
            </div>

            <div className="space-y-2">
              <select
                value={sttModel}
                onChange={(e) => handleSttModelChange(e.target.value)}
                className="w-full px-3 py-2.5 rounded-xl bg-background border border-border text-foreground text-xs focus:outline-none focus:border-primary font-medium shadow-sm"
              >
                <optgroup label="✨ Khuyên Dùng (Nhanh & Chuẩn Nhất)">
                  <option value="web_speech">
                    🌐 Google Web Speech (Trình duyệt) — Chuẩn xác 100%, 0ms, Siêu nhẹ máy ★ Khuyên dùng
                  </option>
                </optgroup>

                <optgroup label="🤖 Faster-Whisper (AI Chạy Offline Trên Máy)">
                  {sttModelsList.length > 0 ? (
                    sttModelsList.map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.name} ({m.size_display}) — {m.accuracy_rating} {m.is_downloaded ? "✓ Đã tải" : "⬇ Chưa tải"}
                      </option>
                    ))
                  ) : (
                    <>
                      <option value="tiny">Whisper Tiny (~75 MB) — Siêu nhanh (N5 / CPU thấp)</option>
                      <option value="base">Whisper Base (~145 MB) — Chuẩn cân bằng (N5–N3)</option>
                      <option value="small">Whisper Small (~460 MB) — Bắt trợ từ và phát âm chi tiết</option>
                      <option value="medium">Whisper Medium (~1.5 GB) — Hội thoại tự nhiên N2–N1</option>
                      <option value="turbo">Whisper Large-v3 Turbo (~1.6 GB) — Tốc độ cao 8x (Khuyên dùng GPU)</option>
                      <option value="large-v3">Whisper Large-v3 (~3.1 GB) — Đỉnh cao SOTA</option>
                    </>
                  )}
                </optgroup>
              </select>
              <p className="text-[11px] text-muted-foreground">
                💡 <strong>Google Web Speech</strong> nhận diện tức thì theo thời gian thực và cực chuẩn tiếng Nhật. Model bạn chọn sẽ được lưu tự động cho mọi phiên sau.
              </p>
            </div>
          </div>

          {/* Interactive Mic Test & Playback */}
          <div className="p-3.5 rounded-2xl bg-card border border-border space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="h-7 w-7 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                  <Mic className="h-3.5 w-3.5" />
                </span>
                <div>
                  <h4 className="text-xs font-bold text-foreground">Kiểm tra Micro & Nghe lại giọng mình</h4>
                  <p className="text-[11px] text-muted-foreground">Thử thu âm 3-5 giây để kiểm tra độ rõ ràng và âm lượng trước khi bắt đầu</p>
                </div>
              </div>

              {/* Volume Meter */}
              <div className="flex gap-0.5 items-end h-4 w-14 bg-muted rounded p-0.5">
                {[0.1, 0.25, 0.4, 0.6, 0.8, 1.0].map((step, idx) => (
                  <div
                    key={idx}
                    className={`flex-1 rounded-sm transition-all duration-75 ${
                      volumeLevel >= step
                        ? idx > 4
                          ? "bg-red-500 h-full"
                          : idx > 2
                          ? "bg-amber-400 h-full"
                          : "bg-emerald-400 h-full"
                        : "bg-muted-foreground/20 h-1"
                    }`}
                  />
                ))}
              </div>
            </div>

            {/* Controls */}
            <div className="flex items-center gap-2 pt-1 flex-wrap">
              {!isTestRecording ? (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={startTestRecording}
                  className="text-xs border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/10"
                >
                  <Mic className="h-3.5 w-3.5 mr-1" />
                  Thu âm thử (3-5s)
                </Button>
              ) : (
                <Button
                  variant="danger"
                  size="sm"
                  onClick={stopTestRecording}
                  className="text-xs animate-pulse"
                >
                  <Square className="h-3.5 w-3.5 mr-1 fill-current" />
                  Dừng thu ({testRecordDuration}s / 5s)
                </Button>
              )}

              {testAudioUrl && (
                <Button
                  variant="akane"
                  size="sm"
                  onClick={playTestAudio}
                  isLoading={isPlayingTestAudio}
                  className="text-xs"
                >
                  <Play className="h-3.5 w-3.5 mr-1 fill-current" />
                  Nghe lại giọng mình
                </Button>
              )}

              {testAudioUrl && (
                <span className="text-[11px] text-muted-foreground flex items-center gap-1">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                  {testPeakVolume > 0.05 ? "Âm lượng tốt, thu âm rõ ràng" : "Âm lượng hơi nhỏ, thử nói to hơn"}
                </span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Speech Synthesis & VOICEVOX ON/OFF Controls */}
      {activeTab === "voicevox" && (
        <div className="space-y-3.5 animate-in fade-in duration-150">
          {/* Master Voice Playback Mode Picker */}
          <div className="p-3 rounded-2xl bg-card border border-border space-y-2.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Volume2 className="h-4 w-4 text-primary" />
                <span className="text-xs font-bold text-foreground">Chế độ phát giọng nói AI</span>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-[11px] text-muted-foreground font-medium">
                  {ttsEnabled ? "Đang bật phát âm" : "Đã tắt (Chỉ xem chữ)"}
                </span>
                <input
                  type="checkbox"
                  checked={ttsEnabled}
                  onChange={(e) => handleTtsEnabledToggle(e.target.checked)}
                  className="h-4 w-4 accent-primary rounded cursor-pointer"
                />
              </div>
            </div>

            {/* 3 Mode Radio Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 pt-1">
              {/* Option 1: VOICEVOX */}
              <button
                type="button"
                onClick={() => handleTtsEngineChange("voicevox")}
                className={`p-2.5 rounded-xl border text-left transition-all ${
                  ttsEnabled && ttsEngine === "voicevox"
                    ? "bg-primary/10 border-primary ring-1 ring-primary/30"
                    : "bg-background/80 border-border text-muted-foreground hover:text-foreground"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5 font-bold text-xs text-foreground">
                    <Headphones className="h-3.5 w-3.5 text-indigo-400" />
                    <span>VOICEVOX</span>
                  </div>
                  {voicevoxOnline === true ? (
                    <span className="h-2 w-2 rounded-full bg-emerald-500" title="Engine Online" />
                  ) : (
                    <span className="h-2 w-2 rounded-full bg-slate-500" title="Engine Offline / App chưa mở" />
                  )}
                </div>
                <p className="text-[10px] text-muted-foreground mt-1 line-clamp-2">
                  46+ giọng Anime lồng tiếng (cần chạy VOICEVOX app).
                </p>
              </button>

              {/* Option 2: Web Speech API */}
              <button
                type="button"
                onClick={() => handleTtsEngineChange("web_speech")}
                className={`p-2.5 rounded-xl border text-left transition-all ${
                  ttsEnabled && ttsEngine === "web_speech"
                    ? "bg-sky-500/10 border-sky-500 ring-1 ring-sky-500/30 text-foreground"
                    : "bg-background/80 border-border text-muted-foreground hover:text-foreground"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5 font-bold text-xs text-foreground">
                    <Globe className="h-3.5 w-3.5 text-sky-400" />
                    <span>Trình duyệt (Web)</span>
                  </div>
                  <Badge variant="fuji" size="sm" className="text-[9px] py-0 px-1 h-3.5 bg-sky-500/20 text-sky-300">
                    0MB RAM
                  </Badge>
                </div>
                <p className="text-[10px] text-muted-foreground mt-1 line-clamp-2">
                  Giọng tiếng Nhật Windows / Browser, siêu nhẹ máy.
                </p>
              </button>

              {/* Option 3: Text Only */}
              <button
                type="button"
                onClick={() => handleTtsEngineChange("none")}
                className={`p-2.5 rounded-xl border text-left transition-all ${
                  !ttsEnabled || ttsEngine === "none"
                    ? "bg-amber-500/10 border-amber-500 ring-1 ring-amber-500/30 text-foreground"
                    : "bg-background/80 border-border text-muted-foreground hover:text-foreground"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5 font-bold text-xs text-foreground">
                    <VolumeX className="h-3.5 w-3.5 text-amber-400" />
                    <span>Tắt tiếng (Chỉ chữ)</span>
                  </div>
                  <Zap className="h-3 w-3 text-amber-400" />
                </div>
                <p className="text-[10px] text-muted-foreground mt-1 line-clamp-2">
                  Tiết kiệm 100% tài nguyên, đọc phụ đề văn bản.
                </p>
              </button>
            </div>
          </div>

          {/* Mode Dependent Body */}
          {(!ttsEnabled || ttsEngine === "none") && (
            <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-600 dark:text-amber-400 space-y-1.5">
              <div className="flex items-center gap-2 font-bold">
                <CheckCircle2 className="h-4 w-4" />
                <span>Chế độ Tiết kiệm RAM / Tối ưu phần cứng đang BẬT</span>
              </div>
              <p className="text-[11px] leading-relaxed text-amber-600/90 dark:text-amber-400/90">
                Bạn vẫn luyện nói qua Micro với mô hình Faster-Whisper. AI sẽ phản hồi ngay lập tức dưới dạng văn bản mà không gọi VOICEVOX, giúp máy tính hoạt động cực kỳ nhẹ và mát.
              </p>
            </div>
          )}

          {ttsEnabled && ttsEngine === "web_speech" && (
            <div className="p-3 rounded-xl bg-sky-500/10 border border-sky-500/20 text-xs text-sky-400 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 font-bold text-foreground">
                  <Globe className="h-4 w-4 text-sky-400" />
                  <span>Giọng đọc Trình duyệt Web Speech (ja-JP)</span>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePreviewVoice("web_speech")}
                  isLoading={previewingVoiceId === "web_speech"}
                  className="text-xs border-sky-500/30 text-sky-400 hover:bg-sky-500/10"
                >
                  <Play className="h-3 w-3 mr-1 fill-current" />
                  Nghe thử giọng Web
                </Button>
              </div>
              <p className="text-[11px] leading-relaxed text-muted-foreground">
                Tự động sử dụng giọng đọc tiếng Nhật tích hợp sẵn của Windows / Trình duyệt (Microsoft Haruka / Ayumi / Ichiro). Không yêu cầu cài đặt hay mở thêm bất kỳ phần mềm nào.
              </p>
            </div>
          )}

          {ttsEnabled && ttsEngine === "voicevox" && (
            <div className="space-y-3">
              {/* Engine Status Notice if Offline */}
              {voicevoxOnline === false && (
                <div className="p-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-xs text-muted-foreground flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-amber-400 shrink-0" />
                    <span>App VOICEVOX chưa mở trên máy (Port 50021).</span>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleTtsEngineChange("web_speech")}
                    className="text-[11px] h-7 px-2 border-sky-500/30 text-sky-400"
                  >
                    Dùng Web Speech thay thế
                  </Button>
                </div>
              )}

              {/* Search & Filter Bar */}
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <div className="relative flex-1">
                    <Search className="h-3.5 w-3.5 absolute left-2.5 top-2.5 text-muted-foreground" />
                    <input
                      type="text"
                      placeholder="Tìm nhân vật / phong cách (VD: Zundamon, Metan, Tsundere, Normal...)"
                      value={voiceSearch}
                      onChange={(e) => setVoiceSearch(e.target.value)}
                      className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-background border border-border text-foreground text-xs focus:outline-none focus:border-primary"
                    />
                  </div>

                  {selectedVoiceObj && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handlePreviewVoice(ttsVoice)}
                      isLoading={previewingVoiceId === ttsVoice}
                      className="text-xs shrink-0"
                      title="Nghe thử giọng đang chọn"
                    >
                      <Play className="h-3 w-3 mr-1 fill-current" />
                      Nghe thử
                    </Button>
                  )}
                </div>

                {/* Filter Category Chips */}
                <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
                  {[
                    { id: "all", label: "Tất cả", count: voicesList.length },
                    { id: "female", label: "👩 Nữ", count: voicesList.filter((v) => getVoiceCharacterMeta(v).gender === "female").length },
                    { id: "male", label: "👨 Nam", count: voicesList.filter((v) => getVoiceCharacterMeta(v).gender === "male").length },
                    { id: "anime", label: "✨ Anime / Nhí nhảnh" },
                    { id: "calm", label: "🍵 Điềm tĩnh" },
                  ].map((f) => (
                    <button
                      key={f.id}
                      type="button"
                      onClick={() => setVoiceFilter(f.id as any)}
                      className={`px-2.5 py-1 rounded-lg text-xs font-semibold whitespace-nowrap transition-all border ${
                        voiceFilter === f.id
                          ? "bg-primary text-primary-foreground border-primary shadow-sm"
                          : "bg-background text-muted-foreground border-border hover:text-foreground"
                      }`}
                    >
                      {f.label} {f.count !== undefined ? `(${f.count})` : ""}
                    </button>
                  ))}
                </div>
              </div>

              {/* Voice Cards Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-48 overflow-y-auto pr-1 border border-border rounded-xl p-2 bg-background/50">
                {filteredVoices.map((v) => {
                  const vId = v.voice_id || v.id;
                  const isSelected = ttsVoice === vId;
                  const meta = getVoiceCharacterMeta(v);

                  return (
                    <div
                      key={vId}
                      onClick={() => handleTtsVoiceChange(vId)}
                      className={`p-2 rounded-xl border text-left cursor-pointer transition-all flex items-center justify-between gap-2 ${
                        isSelected
                          ? "bg-primary/10 border-primary shadow-sm ring-1 ring-primary/30"
                          : "bg-card hover:bg-muted/50 border-border"
                      }`}
                    >
                      <div className="flex items-center gap-2.5 min-w-0">
                        <div
                          className={`h-8 w-8 rounded-lg bg-gradient-to-tr ${meta.gradient} flex items-center justify-center text-white font-bold text-xs shadow-sm shrink-0`}
                        >
                          {meta.avatarLetter}
                        </div>
                        <div className="min-w-0">
                          <div className="flex items-center gap-1 truncate">
                            <span className="text-xs font-bold text-foreground truncate">{v.name}</span>
                            {isSelected && <Check className="h-3 w-3 text-primary shrink-0" />}
                          </div>
                          <span className="text-[10px] text-muted-foreground block truncate">
                            {meta.genderLabel} · {v.style || meta.vibeLabel}
                          </span>
                        </div>
                      </div>

                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          handlePreviewVoice(vId);
                        }}
                        isLoading={previewingVoiceId === vId}
                        className="h-7 w-7 p-0 shrink-0 text-muted-foreground hover:text-primary rounded-lg"
                        title="Nghe thử giọng này"
                      >
                        <Play className="h-3 w-3 fill-current" />
                      </Button>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
          </div>
        )}
      </div>

      {/* Sticky Bottom Action Buttons */}
      <div className="flex items-center justify-between gap-2 pt-3 border-t border-border mt-auto shrink-0">
        <div className="text-xs text-muted-foreground hidden sm:block">
          Âm thanh:{" "}
          <span className="font-semibold text-foreground">
            {!ttsEnabled || ttsEngine === "none"
              ? "Tắt tiếng (Chỉ hiện chữ)"
              : ttsEngine === "web_speech"
              ? "Trình duyệt (0MB RAM)"
              : selectedVoiceObj?.name || ttsVoice}
          </span>
        </div>

        <div className="flex items-center gap-2 ml-auto">
          <Button variant="outline" size="sm" onClick={onClose}>
            Hủy bỏ
          </Button>
          <Button
            variant="akane"
            size="md"
            onClick={handleStart}
            disabled={isInitializing}
            className="min-w-[180px]"
          >
            <Mic className="h-4 w-4 mr-1.5" />
            <span>Vào phòng luyện nói (会話開始)</span>
          </Button>
        </div>
      </div>
    </div>
  );
}
