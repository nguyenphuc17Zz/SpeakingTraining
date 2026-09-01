"use client";

import React, { useState, useEffect, useMemo, useRef, useCallback } from "react";
import { ZenLoadingState } from "@/components/ui/zen-loading-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import {
  Zap,
  Mic,
  Clock,
  Settings2,
  Play,
  RotateCcw,
  Trophy,
  Shuffle,
  HelpCircle,
  Keyboard,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  Volume2,
  Flame,
  Sparkles,
  ArrowRight,
  Headphones,
  Sliders,
  CheckCircle2,
  XCircle,
  Radio,
  Check,
  MessageSquare,
  Repeat,
  Compass,
  Star,
  Activity,
  BookText,
  Crown,
} from "lucide-react";
import { useReflexSession } from "@/features/reflex/hooks/useReflexSession";
import { ReflexTimer } from "@/features/reflex/components/ReflexTimer";
import { ReflexPromptCard } from "@/features/reflex/components/ReflexPromptCard";
import { ReflexResultCard } from "@/features/reflex/components/ReflexResultCard";
import { ReflexSessionSummary } from "@/features/reflex/components/ReflexSessionSummary";
import { ConjugationFilterModal } from "@/features/reflex/components/ConjugationFilterModal";
import { QnaTopicFilterModal } from "@/features/reflex/components/QnaTopicFilterModal";
import { TransformationFilterModal } from "@/features/reflex/components/TransformationFilterModal";
import { ContextFilterModal } from "@/features/reflex/components/ContextFilterModal";
import { VocabFilterModal } from "@/features/reflex/components/VocabFilterModal";
import { KeigoFilterModal } from "@/features/reflex/components/KeigoFilterModal";
import { GlobalKeybindingsModal } from "@/components/layout/global-keybindings-modal";
import { CoachQuickActions, CoachPanel } from "@/features/coach";
import { usePathname } from "next/navigation";
import { useCoachCore } from "@/features/coach/hooks/useCoachCore";
import { CoachInsightCard } from "@/features/coach/components/CoachInsightCard";
import { useCoachProactive } from "@/features/coach/hooks/useCoachProactive";
import { useSystemKeybindings, formatKeyDisplay } from "@/hooks/use-system-keybindings";
import { speakJapaneseText, stopWebSpeech } from "@/features/speaking/services/web-speech";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";
import { ZenUnifiedInputBar } from "@/components/ui/zen-unified-input-bar";

const DEDICATED_MODES = [
  {
    id: "reflex_conjugation",
    title: "Conjugation Blitz",
    titleJa: "活用",
    icon: Zap,
    badgeVariant: "sakura" as const,
    iconColor: "text-rose-500 bg-rose-500/10 border-rose-500/20",
    accentColor: "text-rose-600 dark:text-rose-400",
    desc: "Chia thể động từ & tính từ phản xạ siêu tốc",
    source: "食べる",
    target: "食べさせる (Sai khiến)",
  },
  {
    id: "reflex_qna",
    title: "Speed Q&A",
    titleJa: "速答",
    icon: MessageSquare,
    badgeVariant: "matcha" as const,
    iconColor: "text-emerald-500 bg-emerald-500/10 border-emerald-500/20",
    accentColor: "text-emerald-600 dark:text-emerald-400",
    desc: "Hỏi - đáp tức thì câu hỏi thường ngày & công việc",
    source: "週末は何を？",
    target: "映画を見ました",
  },
  {
    id: "reflex_transformation",
    title: "Transformation",
    titleJa: "文型変換",
    icon: Repeat,
    badgeVariant: "fuji" as const,
    iconColor: "text-indigo-500 bg-indigo-500/10 border-indigo-500/20",
    accentColor: "text-indigo-600 dark:text-indigo-400",
    desc: "Đổi ngữ pháp: Lịch sự ↔ Thân mật, Phủ định, Quá khứ",
    source: "行きます",
    target: "行く (Thân mật)",
  },
  {
    id: "reflex_context",
    title: "Contextual Reaction",
    titleJa: "状況対応",
    icon: Compass,
    badgeVariant: "kintsugi" as const,
    iconColor: "text-amber-500 bg-amber-500/10 border-amber-500/20",
    accentColor: "text-amber-600 dark:text-amber-400",
    desc: "Phản xạ giao tiếp đúng vai vế và văn hóa ứng xử",
    source: "Đến muộn do trễ tàu",
    target: "大変申し訳ありません",
  },
  {
    id: "reflex_vocabulary",
    title: "Vocabulary Blitz",
    titleJa: "語彙",
    icon: BookText,
    badgeVariant: "fuji" as const,
    iconColor: "text-violet-500 bg-violet-500/10 border-violet-500/20",
    accentColor: "text-violet-600 dark:text-violet-400",
    desc: "Nhớ nghĩa từ vựng JLPT N5-N1 theo phản xạ siêu tốc",
    source: "諦める",
    target: "bỏ cuộc 🇯🇵→🇻🇳",
  },
  {
    id: "reflex_keigo_vocab",
    title: "Keigo Word Blitz",
    titleJa: "敬語単語",
    icon: Crown,
    badgeVariant: "kintsugi" as const,
    iconColor: "text-amber-500 bg-amber-500/10 border-amber-500/20",
    accentColor: "text-amber-600 dark:text-amber-400",
    desc: "Phản xạ nhanh Tôn kính ngữ, Khiêm nhường ngữ & Từ thương mại",
    source: "食べる",
    target: "召し上がる 👑",
  },
];

const PRESSURE_LEVELS = [
  { id: "infinite", label: "Infinite", labelJa: "無制限", icon: "♾️", ms: 0, desc: "∞ • Không giới hạn thời gian phản xạ" },
  { id: "relaxed", label: "Relaxed", labelJa: "ゆっくり", icon: "🐢", ms: 6000, desc: "6.0s • Thong thả, tập trung độ chuẩn xác" },
  { id: "normal", label: "Normal", labelJa: "普通", icon: "🚶", ms: 4000, desc: "4.0s • Cân bằng, nhịp nói tự nhiên" },
  { id: "fast", label: "Fast", labelJa: "速め", icon: "🏃", ms: 3000, desc: "3.0s • Tăng tốc, phản xạ dứt khoát" },
  { id: "reflex", label: "Reflex", labelJa: "瞬発", icon: "⚡", ms: 2500, desc: "2.5s • Thực chiến, nhịp người bản xứ" },
  { id: "extreme", label: "Extreme", labelJa: "超速", icon: "🔥", ms: 1800, desc: "1.8s • Cực hạn, phản xạ chớp mắt" },
] as const;

const DURATION_OPTIONS = [0, 3, 5, 10, 20] as const;

export default function ReflexPage() {
  const [subMode, setSubMode] = useState("mixed");
  const [pressure, setPressure] = useState<"infinite" | "relaxed" | "normal" | "fast" | "reflex" | "extreme">("normal");
  const [subtitleMode, setSubtitleMode] = useState<"hidden" | "japanese" | "japanese_reading" | "vietnamese">("japanese");
  const [startTrigger, setStartTrigger] = useState<"manual" | "auto">("manual");
  const [transcriptInput, setTranscriptInput] = useState("");
  const [showTextInput, setShowTextInput] = useState(false);
  const [showSummary, setShowSummary] = useState(false);
  const [duration, setDuration] = useState<0 | 3 | 5 | 10 | 20>(5);
  const [sessionRemainingSec, setSessionRemainingSec] = useState(duration * 60);
  const [sessionElapsedSec, setSessionElapsedSec] = useState(0);
  const [autoNext, setAutoNext] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const [selectedForms, setSelectedForms] = useState<string[]>([]);
  const [showFormFilterModal, setShowFormFilterModal] = useState(false);
  const [selectedQnaTopics, setSelectedQnaTopics] = useState<string[]>([]);
  const [showQnaTopicFilterModal, setShowQnaTopicFilterModal] = useState(false);
  const [customKeywords, setCustomKeywords] = useState<string>("");
  const [selectedTransformCategories, setSelectedTransformCategories] = useState<string[]>([]);
  const [showTransformFilterModal, setShowTransformFilterModal] = useState(false);
  const [customTransformKeywords, setCustomTransformKeywords] = useState<string>("");
  const [selectedContextCategories, setSelectedContextCategories] = useState<string[]>([]);
  const [showContextFilterModal, setShowContextFilterModal] = useState(false);
  const [customContextKeywords, setCustomContextKeywords] = useState<string>("");
  const [selectedVocabCategories, setSelectedVocabCategories] = useState<string[]>([]);
  const [showVocabFilterModal, setShowVocabFilterModal] = useState(false);
  const [customVocabKeywords, setCustomVocabKeywords] = useState<string>("");
  const [selectedKeigoCategories, setSelectedKeigoCategories] = useState<string[]>([]);
  const [showKeigoFilterModal, setShowKeigoFilterModal] = useState(false);
  const [customKeigoKeywords, setCustomKeigoKeywords] = useState<string>("");
  const [isReflexAdvancedOpen, setIsReflexAdvancedOpen] = useState(false);

  const sessionEndTimestampRef = useRef<number | null>(null);
  const sessionPausedRemainingMsRef = useRef<number>(duration * 60 * 1000);
  const isSettingsLoadedRef = useRef(false);

  // 1. Load saved user preferences from localStorage on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem("speaking_training_reflex_settings_v1");
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.subMode && typeof parsed.subMode === "string") {
          setSubMode(parsed.subMode);
        }
        if (parsed.pressure && typeof parsed.pressure === "string") {
          setPressure(parsed.pressure);
        }
        if (parsed.duration !== undefined && [0, 3, 5, 10, 20].includes(parsed.duration)) {
          setDuration(parsed.duration);
        }
        if (parsed.subtitleMode && typeof parsed.subtitleMode === "string") {
          setSubtitleMode(parsed.subtitleMode);
        }
        if (parsed.startTrigger && typeof parsed.startTrigger === "string") {
          setStartTrigger(parsed.startTrigger);
        }
        if (parsed.autoNext !== undefined && typeof parsed.autoNext === "boolean") {
          setAutoNext(parsed.autoNext);
        }
      }

      const savedForms = localStorage.getItem("speaking_training_reflex_selected_forms");
      if (savedForms) {
        const parsedForms = JSON.parse(savedForms);
        if (Array.isArray(parsedForms)) {
          setSelectedForms(parsedForms);
        }
      }

      const savedQna = localStorage.getItem("speaking_training_reflex_selected_qna_topics");
      if (savedQna) {
        const parsedQna = JSON.parse(savedQna);
        if (Array.isArray(parsedQna)) {
          setSelectedQnaTopics(parsedQna);
        }
      }

      const savedKeywords = localStorage.getItem("speaking_training_reflex_qna_custom_keywords");
      if (savedKeywords) {
        setCustomKeywords(savedKeywords);
      }

      const savedTransform = localStorage.getItem("speaking_training_reflex_selected_transform_categories");
      if (savedTransform) {
        const parsedTransform = JSON.parse(savedTransform);
        if (Array.isArray(parsedTransform)) {
          setSelectedTransformCategories(parsedTransform);
        }
      }

      const savedTransformKeywords = localStorage.getItem("speaking_training_reflex_transform_custom_keywords");
      if (savedTransformKeywords) {
        setCustomTransformKeywords(savedTransformKeywords);
      }

      const savedContext = localStorage.getItem("speaking_training_reflex_selected_context_categories");
      if (savedContext) {
        const parsedContext = JSON.parse(savedContext);
        if (Array.isArray(parsedContext)) {
          setSelectedContextCategories(parsedContext);
        }
      }

      const savedContextKeywords = localStorage.getItem("speaking_training_reflex_context_custom_keywords");
      if (savedContextKeywords) {
        setCustomContextKeywords(savedContextKeywords);
      }

      const savedVocab = localStorage.getItem("speaking_training_reflex_selected_vocab_categories");
      if (savedVocab) {
        const parsedVocab = JSON.parse(savedVocab);
        if (Array.isArray(parsedVocab)) {
          setSelectedVocabCategories(parsedVocab);
        }
      }

      const savedVocabKeywords = localStorage.getItem("speaking_training_reflex_vocab_custom_keywords");
      if (savedVocabKeywords) {
        setCustomVocabKeywords(savedVocabKeywords);
      }

      const savedKeigo = localStorage.getItem("speaking_training_reflex_selected_keigo_categories");
      if (savedKeigo) {
        const parsedKeigo = JSON.parse(savedKeigo);
        if (Array.isArray(parsedKeigo)) {
          setSelectedKeigoCategories(parsedKeigo);
        }
      }

      const savedKeigoKeywords = localStorage.getItem("speaking_training_reflex_keigo_custom_keywords");
      if (savedKeigoKeywords) {
        setCustomKeigoKeywords(savedKeigoKeywords);
      }
    } catch (e) {
      console.warn("[ReflexPage] Failed to load saved settings:", e);
    } finally {
      isSettingsLoadedRef.current = true;
    }
  }, []);

  const handleSelectedFormsChange = (forms: string[]) => {
    setSelectedForms(forms);
    try {
      localStorage.setItem("speaking_training_reflex_selected_forms", JSON.stringify(forms));
    } catch (e) {}
  };

  const handleSelectedQnaTopicsChange = (topics: string[]) => {
    setSelectedQnaTopics(topics);
    try {
      localStorage.setItem("speaking_training_reflex_selected_qna_topics", JSON.stringify(topics));
    } catch (e) {}
  };

  const handleCustomKeywordsChange = (val: string) => {
    setCustomKeywords(val);
    try {
      localStorage.setItem("speaking_training_reflex_qna_custom_keywords", val);
    } catch (e) {}
  };

  const handleSelectedTransformCategoriesChange = (cats: string[]) => {
    setSelectedTransformCategories(cats);
    try {
      localStorage.setItem("speaking_training_reflex_selected_transform_categories", JSON.stringify(cats));
    } catch (e) {}
  };

  const handleCustomTransformKeywordsChange = (val: string) => {
    setCustomTransformKeywords(val);
    try {
      localStorage.setItem("speaking_training_reflex_transform_custom_keywords", val);
    } catch (e) {}
  };

  const handleSelectedContextCategoriesChange = (cats: string[]) => {
    setSelectedContextCategories(cats);
    try {
      localStorage.setItem("speaking_training_reflex_selected_context_categories", JSON.stringify(cats));
    } catch (e) {}
  };

  const handleCustomContextKeywordsChange = (val: string) => {
    setCustomContextKeywords(val);
    try {
      localStorage.setItem("speaking_training_reflex_context_custom_keywords", val);
    } catch (e) {}
  };

  const handleSelectedVocabCategoriesChange = (cats: string[]) => {
    setSelectedVocabCategories(cats);
    try {
      localStorage.setItem("speaking_training_reflex_selected_vocab_categories", JSON.stringify(cats));
    } catch (e) {}
  };

  const handleCustomVocabKeywordsChange = (val: string) => {
    setCustomVocabKeywords(val);
    try {
      localStorage.setItem("speaking_training_reflex_vocab_custom_keywords", val);
    } catch (e) {}
  };

  const handleSelectedKeigoCategoriesChange = (cats: string[]) => {
    setSelectedKeigoCategories(cats);
    try {
      localStorage.setItem("speaking_training_reflex_selected_keigo_categories", JSON.stringify(cats));
    } catch (e) {}
  };

  const handleCustomKeigoKeywordsChange = (val: string) => {
    setCustomKeigoKeywords(val);
    try {
      localStorage.setItem("speaking_training_reflex_keigo_custom_keywords", val);
    } catch (e) {}
  };

  const conjugationTarget = useMemo(() => {
    if (selectedForms.length === 0) return undefined;
    return selectedForms.join(",");
  }, [selectedForms]);

  const qnaTopic = useMemo(() => {
    if (customKeywords && customKeywords.trim()) {
      return customKeywords.trim();
    }
    if (selectedQnaTopics.length === 0) return undefined;
    return selectedQnaTopics.join(",");
  }, [customKeywords, selectedQnaTopics]);

  const transformationCategory = useMemo(() => {
    if (customTransformKeywords && customTransformKeywords.trim()) {
      return customTransformKeywords.trim();
    }
    if (selectedTransformCategories.length === 0) return undefined;
    return selectedTransformCategories.join(",");
  }, [customTransformKeywords, selectedTransformCategories]);

  const contextCategory = useMemo(() => {
    if (customContextKeywords && customContextKeywords.trim()) {
      return customContextKeywords.trim();
    }
    if (selectedContextCategories.length === 0) return undefined;
    return selectedContextCategories.join(",");
  }, [customContextKeywords, selectedContextCategories]);

  const vocabCategory = useMemo(() => {
    if (customVocabKeywords && customVocabKeywords.trim()) {
      return customVocabKeywords.trim();
    }
    if (selectedVocabCategories.length === 0) return undefined;
    return selectedVocabCategories.join(",");
  }, [customVocabKeywords, selectedVocabCategories]);

  const keigoCategory = useMemo(() => {
    if (customKeigoKeywords && customKeigoKeywords.trim()) {
      return customKeigoKeywords.trim();
    }
    if (selectedKeigoCategories.length === 0) return undefined;
    return selectedKeigoCategories.join(",");
  }, [customKeigoKeywords, selectedKeigoCategories]);

  // 2. Persist preferences whenever any setting changes
  useEffect(() => {
    if (!isSettingsLoadedRef.current) return;
    try {
      const settings = {
        subMode,
        pressure,
        duration,
        subtitleMode,
        startTrigger,
        autoNext,
      };
      localStorage.setItem("speaking_training_reflex_settings_v1", JSON.stringify(settings));
    } catch (e) {
      console.warn("[ReflexPage] Failed to save settings:", e);
    }
  }, [subMode, pressure, duration, subtitleMode, startTrigger, autoNext]);

  const { matchesAction, keybindings } = useSystemKeybindings();

  const session = useReflexSession({
    subMode,
    pressureLevel: pressure as any,
    autoNext,
    startTrigger,
    conjugationTarget,
    qnaTopic,
    transformationCategory,
    contextCategory,
    vocabCategory,
    keigoCategory,
  });

  // Sync duration selection in lobby
  useEffect(() => {
    if (session.phase === "idle" || session.phase === "summary" || showSummary) {
      setSessionRemainingSec(duration === 0 ? 0 : duration * 60);
      setSessionElapsedSec(0);
      sessionEndTimestampRef.current = null;
      sessionPausedRemainingMsRef.current = duration * 60 * 1000;
    }
  }, [duration, session.phase, showSummary]);

  // Robust session duration countdown / elapsed tracking
  useEffect(() => {
    const isSessionActive = session.phase !== "idle" && session.phase !== "summary" && !showSummary;
    if (!isSessionActive) return;

    // Endless mode (∞ Vô hạn): Count elapsed time upwards
    if (duration === 0) {
      if (session.isPaused) return;
      const interval = setInterval(() => {
        setSessionElapsedSec((s) => s + 1);
      }, 1000);
      return () => clearInterval(interval);
    }

    // Fixed duration countdown
    if (session.isPaused) {
      if (sessionEndTimestampRef.current !== null) {
        const remaining = Math.max(0, sessionEndTimestampRef.current - Date.now());
        sessionPausedRemainingMsRef.current = remaining;
        sessionEndTimestampRef.current = null;
      }
      return;
    }

    if (sessionEndTimestampRef.current === null) {
      sessionEndTimestampRef.current = Date.now() + sessionPausedRemainingMsRef.current;
    }

    const interval = setInterval(() => {
      if (sessionEndTimestampRef.current === null) return;
      const remainingMs = sessionEndTimestampRef.current - Date.now();
      const remainingSec = Math.max(0, Math.ceil(remainingMs / 1000));
      setSessionRemainingSec(remainingSec);

      if (remainingSec <= 0) {
        clearInterval(interval);
        sessionEndTimestampRef.current = null;
        setShowSummary(true);
        session.setPhase("summary" as any);
      }
    }, 500);

    return () => clearInterval(interval);
  }, [duration, session.phase, session.isPaused, showSummary, session.setPhase]);

  const timerMs = PRESSURE_LEVELS.find((p) => p.id === pressure)?.ms ?? 4000;
  const activeExercise = session.exercise;
  const pathname = usePathname();
  const { insights, dismiss } = useCoachProactive();
  const [coachOpen, setCoachOpen] = useState(false);
  const coach = useCoachCore();

  const handleCoachSelect = (prompt: string) => {
    setCoachOpen(true);
    setTimeout(() => coach.ask(prompt, { route: pathname || "/reflex", exerciseId: (activeExercise as any)?.id }), 300);
  };

  const playedPromptExerciseIdRef = useRef<string | null>(null);

  const playPromptAudio = useCallback(
    (autoTransition = false) => {
      if (!activeExercise) return;
      const rc = activeExercise.extra_metadata?.reflex_config || {};
      const text =
        rc.prompt ||
        (activeExercise.exercise_type === "reflex_conjugation" && rc.verb
          ? rc.verb
          : activeExercise.scenario || activeExercise.title);
      if (text) {
        speakJapaneseText(text, {
          rate: 1.0,
          onEnd: () => {
            if (autoTransition) {
              session.onPromptAudioFinished();
            }
          },
          onError: () => {
            if (autoTransition) {
              session.onPromptAudioFinished();
            }
          },
        });
      } else if (autoTransition) {
        session.onPromptAudioFinished();
      }
    },
    [activeExercise, session.onPromptAudioFinished]
  );

  // Auto-play prompt audio in prompt_playing phase and transition after audio ends
  useEffect(() => {
    if (session.phase === "prompt_playing" && activeExercise?.id) {
      if (playedPromptExerciseIdRef.current !== activeExercise.id) {
        playedPromptExerciseIdRef.current = activeExercise.id;
        playPromptAudio(true);
      }
    } else if (session.phase === "idle" || session.phase === "summary") {
      playedPromptExerciseIdRef.current = null;
      stopWebSpeech();
    }
  }, [session.phase, activeExercise?.id, playPromptAudio]);

  // Guaranteed audio and mic release on component unmount
  useEffect(() => {
    return () => {
      stopWebSpeech();
      session.recorder.releaseMicrophone();
      session.speech.stopListening();
    };
  }, []);

  const handleDirectSubmit = async () => {
    const text =
      transcriptInput.trim() ||
      session.speech.transcript.trim() ||
      session.speech.interimTranscript.trim();
    if (!text) return;
    setTranscriptInput("");
    await session.submitWithTranscript(text);
  };

  // Calculate current consecutive correct streak
  const currentStreak = useMemo(() => {
    let streak = 0;
    for (let i = session.results.length - 1; i >= 0; i--) {
      if (session.results[i].success) streak++;
      else break;
    }
    return streak;
  }, [session.results]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName?.toLowerCase();
      if (tag === "textarea" || tag === "input") {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          if (session.phase === "waiting_for_speech" || session.phase === "recording" || session.phase === "result") {
            handleDirectSubmit();
          }
        }
        return;
      }

      // Handle Result Phase Keybindings
      if (session.phase === "result") {
        // Next Question: Space, Enter, N, ArrowRight, reflexSubmitOrNext, reflexSkip, drillSubmitOrNext, drillSkip
        if (
          matchesAction(e, "reflexSubmitOrNext") ||
          matchesAction(e, "reflexSkip") ||
          matchesAction(e, "drillSubmitOrNext") ||
          matchesAction(e, "drillSkip") ||
          e.code === "Space" ||
          e.key === "Enter" ||
          e.key === "ArrowRight"
        ) {
          e.preventDefault();
          stopWebSpeech();
          session.startNext();
          return;
        }

        // Retry Question: R, reflexRetry, drillRetry
        if (matchesAction(e, "reflexRetry") || matchesAction(e, "drillRetry")) {
          e.preventDefault();
          stopWebSpeech();
          session.retry();
          return;
        }

        // Replay Answer Audio: A, reflexReplayModel, drillReplayAudio
        if (matchesAction(e, "reflexReplayModel") || matchesAction(e, "drillReplayAudio")) {
          e.preventDefault();
          const res = session.result;
          const rc = (activeExercise as any)?.extra_metadata?.reflex_config || {};
          const answerText =
            res?.canonicalAnswer ||
            (activeExercise as any)?.canonical ||
            rc.canonical ||
            rc.expected ||
            rc.target ||
            (activeExercise as any)?.target_patterns?.[0] ||
            "";
          if (answerText) {
            stopWebSpeech();
            speakJapaneseText(answerText);
          }
          return;
        }
      }

      if (matchesAction(e, "reflexToggleHelp") || matchesAction(e, "drillToggleHelp") || matchesAction(e, "openKeybindingsModal")) {
        e.preventDefault();
        setShowHelp((v) => !v);
        return;
      }

      if (matchesAction(e, "reflexPauseOrResume") || matchesAction(e, "drillPauseOrResume")) {
        e.preventDefault();
        session.togglePause();
        return;
      }

      if (matchesAction(e, "reflexListenPrompt") || matchesAction(e, "drillReplayAudio")) {
        e.preventDefault();
        playPromptAudio(false);
        return;
      }

      if (matchesAction(e, "reflexStartVoice") || matchesAction(e, "drillStartQuestion")) {
        e.preventDefault();
        stopWebSpeech();
        session.startQuestionNow();
        return;
      }

      if (matchesAction(e, "reflexSubmitOrNext") || matchesAction(e, "drillSubmitOrNext")) {
        e.preventDefault();
        if (session.phase === "waiting_for_speech" || session.phase === "recording") {
          handleDirectSubmit();
        }
        return;
      }

      if (e.key === "Escape") {
        if (session.phase !== "idle") {
          stopWebSpeech();
          session.recorder.releaseMicrophone();
          session.speech.stopListening();
          session.setPhase("idle" as any);
          setShowSummary(false);
        } else {
          setShowHelp(false);
        }
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [session.phase, transcriptInput, matchesAction]);

  // ==========================================
  // RENDER 1: LOBBY / SETUP SCREEN
  // ==========================================
  if (session.phase === "idle" && !showSummary) {
    const isMixedSelected = subMode === "mixed";

    return (
      <div className="space-y-4 animate-in fade-in duration-300 max-w-5xl mx-auto pb-8">
        {/* Proactive Coach Insight Banner */}
        {insights.slice(0, 1).map((ins, idx) => (
          <CoachInsightCard
            key={idx}
            insight={ins}
            onDismiss={() => dismiss(ins.insight_type)}
            onAction={() => handleCoachSelect(`Luyện ${ins.recommended_action || "reflex"} cho tui`)}
          />
        ))}

        {/* Hero Header */}
        <div className="relative overflow-hidden rounded-2xl border border-border bg-card p-4 sm:p-5 washi-texture shadow-2xs">
          <div className="absolute -top-12 -right-12 h-40 w-40 rounded-full bg-enso-gradient opacity-30 pointer-events-none" />
          <div className="relative flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <span className="h-9 w-9 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary shrink-0 shadow-2xs">
                <Zap className="h-5 w-5" />
              </span>
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <h1 className="text-xl sm:text-2xl font-black font-jp tracking-tight text-foreground">
                    瞬発力スピーキング
                  </h1>
                  <Badge variant="sakura" size="sm" className="font-bold text-[10px]">
                    Mode 3
                  </Badge>
                </div>
                <p className="text-[11px] text-muted-foreground">
                  Speed Reflex Speaking — Phản xạ câu nói tiếng Nhật dưới áp lực thời gian
                </p>
              </div>
            </div>

            <Button
              variant="outline"
              size="sm"
              className="gap-1 rounded-xl border-border h-8 px-2.5 text-xs font-bold shadow-2xs hover:border-primary/40 shrink-0"
              onClick={() => setShowHelp(true)}
            >
              <Keyboard className="h-3.5 w-3.5 text-primary" />
              <span>Phím tắt ({formatKeyDisplay(keybindings.drillToggleHelp)})</span>
            </Button>
          </div>
        </div>

        {/* 2-Column Cockpit Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 items-start">
          {/* Left 2 Cols: Mode Selection */}
          <div className="lg:col-span-2 space-y-2.5">
            <div className="flex items-center justify-between px-1">
              <h2 className="text-xs font-bold text-foreground flex items-center gap-1.5">
                <span>1. Chọn Dạng Bài Phản Xạ:</span>
              </h2>
              <span className="text-[10px] font-medium text-muted-foreground">6 Dạng bài thực chiến</span>
            </div>

            {/* TOP HERO CARD: Mixed Adaptive */}
            <button
              type="button"
              onClick={() => {
                soundFX.playFurin();
                setSubMode("mixed");
              }}
              className={cn(
                "w-full text-left rounded-2xl border p-3.5 transition-all duration-200 relative overflow-hidden group shadow-2xs washi-texture",
                isMixedSelected
                  ? "border-primary bg-primary/10 ring-1 ring-primary/30 shadow-xs"
                  : "border-border/80 bg-card hover:border-primary/40"
              )}
            >
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2.5 min-w-0">
                  <div className="h-8 w-8 rounded-xl bg-primary/15 border border-primary/25 flex items-center justify-center text-primary shrink-0 shadow-2xs">
                    <Shuffle className="h-4 w-4" />
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs font-bold text-foreground font-jp">
                        Mixed Adaptive (Tổng Hợp)
                      </span>
                      <Badge variant="kintsugi" size="sm" className="text-[9px] px-1.5 py-0">混合</Badge>
                    </div>
                    <p className="text-[10px] text-muted-foreground truncate">
                      Tự động phân tích điểm yếu & luân phiên 6 dạng bài để tối đa phản xạ
                    </p>
                  </div>
                </div>

                <div
                  className={cn(
                    "h-5 w-5 rounded-full border-2 flex items-center justify-center shrink-0 transition-all",
                    isMixedSelected ? "border-primary bg-primary text-primary-foreground shadow-xs" : "border-muted-foreground/30 bg-background"
                  )}
                >
                  {isMixedSelected && <Check className="h-3 w-3 stroke-[3]" />}
                </div>
              </div>
            </button>

            {/* 6 DEDICATED FOCUS MODES (2-Col Grid) */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {DEDICATED_MODES.map((m) => {
                const isSelected = subMode === m.id;
                const Icon = m.icon;

                return (
                  <div
                    key={m.id}
                    onClick={() => {
                      soundFX.playFurin();
                      setSubMode(m.id);
                    }}
                    className={cn(
                      "text-left rounded-2xl border p-3 transition-all duration-150 relative overflow-hidden group shadow-2xs washi-texture flex flex-col justify-between space-y-2 cursor-pointer",
                      isSelected
                        ? "border-primary bg-primary/10 ring-1 ring-primary/30 shadow-xs"
                        : "border-border/80 bg-card hover:border-primary/40"
                    )}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2 min-w-0">
                        <div className={cn("h-7 w-7 rounded-lg border flex items-center justify-center shrink-0 text-xs", m.iconColor)}>
                          <Icon className="h-3.5 w-3.5" />
                        </div>
                        <div className="min-w-0">
                          <div className="flex items-center gap-1">
                            <span className="text-xs font-bold text-foreground font-jp truncate">{m.title}</span>
                            <Badge variant={m.badgeVariant} size="sm" className="text-[9px] px-1 py-0 shrink-0">{m.titleJa}</Badge>
                          </div>
                          <p className="text-[10px] text-muted-foreground truncate">{m.desc}</p>
                        </div>
                      </div>

                      <div
                        className={cn(
                          "h-4 w-4 rounded-full border flex items-center justify-center shrink-0 transition-all mt-0.5",
                          isSelected ? "border-primary bg-primary text-primary-foreground" : "border-muted-foreground/30 bg-background"
                        )}
                      >
                        {isSelected && <Check className="h-2.5 w-2.5 stroke-[3]" />}
                      </div>
                    </div>

                    <div className="p-1.5 px-2.5 rounded-xl bg-muted/40 border border-border/60 text-[10px] flex items-center justify-between gap-1 font-medium">
                      <span className="text-foreground/80 font-mono truncate">{m.source}</span>
                      <ArrowRight className="h-3 w-3 text-muted-foreground shrink-0" />
                      <span className={cn("font-bold truncate", m.accentColor)}>{m.target}</span>
                    </div>

                    {/* Filter Action Pill */}
                    {m.id === "reflex_conjugation" && (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          soundFX.playFurin();
                          setShowFormFilterModal(true);
                        }}
                        className="w-full py-1 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 text-[10px] font-bold text-rose-700 dark:text-rose-300 flex items-center justify-center gap-1 transition-colors"
                      >
                        <Sliders className="h-3 w-3 text-rose-500" />
                        <span>{selectedForms.length === 0 ? "Tất cả 50 thể (Toàn diện)" : `${selectedForms.length} thể đã lọc`}</span>
                      </button>
                    )}

                    {m.id === "reflex_qna" && (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          soundFX.playFurin();
                          setShowQnaTopicFilterModal(true);
                        }}
                        className="w-full py-1 rounded-xl bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/20 text-[10px] font-bold text-emerald-700 dark:text-emerald-300 flex items-center justify-center gap-1 transition-colors"
                      >
                        <MessageSquare className="h-3 w-3 text-emerald-500" />
                        <span>{customKeywords.trim() ? `"${customKeywords.trim()}"` : selectedQnaTopics.length === 0 ? "Ngẫu nhiên mọi chủ đề" : `${selectedQnaTopics.length} chủ đề đã lọc`}</span>
                      </button>
                    )}

                    {m.id === "reflex_transformation" && (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          soundFX.playFurin();
                          setShowTransformFilterModal(true);
                        }}
                        className="w-full py-1 rounded-xl bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/20 text-[10px] font-bold text-indigo-700 dark:text-indigo-300 flex items-center justify-center gap-1 transition-colors"
                      >
                        <Repeat className="h-3 w-3 text-indigo-500" />
                        <span>{selectedTransformCategories.length === 0 ? "Ngẫu nhiên 75+ dạng ngữ pháp" : `${selectedTransformCategories.length} nhóm đã lọc`}</span>
                      </button>
                    )}

                    {m.id === "reflex_context" && (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          soundFX.playFurin();
                          setShowContextFilterModal(true);
                        }}
                        className="w-full py-1 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/20 text-[10px] font-bold text-amber-700 dark:text-amber-300 flex items-center justify-center gap-1 transition-colors"
                      >
                        <Compass className="h-3 w-3 text-amber-500" />
                        <span>{selectedContextCategories.length === 0 ? "Ngẫu nhiên 60+ tình huống" : `${selectedContextCategories.length} nhóm đã lọc`}</span>
                      </button>
                    )}

                    {m.id === "reflex_vocabulary" && (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          soundFX.playFurin();
                          setShowVocabFilterModal(true);
                        }}
                        className="w-full py-1 rounded-xl bg-violet-500/10 hover:bg-violet-500/20 border border-violet-500/20 text-[10px] font-bold text-violet-700 dark:text-violet-300 flex items-center justify-center gap-1 transition-colors"
                      >
                        <BookText className="h-3 w-3 text-violet-500" />
                        <span>{selectedVocabCategories.length === 0 ? "Ngẫu nhiên 500+ từ vựng" : `${selectedVocabCategories.length} nhóm đã lọc`}</span>
                      </button>
                    )}

                    {m.id === "reflex_keigo_vocab" && (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          soundFX.playFurin();
                          setShowKeigoFilterModal(true);
                        }}
                        className="w-full py-1 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/20 text-[10px] font-bold text-amber-700 dark:text-amber-300 flex items-center justify-center gap-1 transition-colors"
                      >
                        <Crown className="h-3 w-3 text-amber-500" />
                        <span>{selectedKeigoCategories.length === 0 ? "Ngẫu nhiên 80+ cặp kính ngữ" : `${selectedKeigoCategories.length} nhóm đã lọc`}</span>
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right 1 Col: Session Configuration Cockpit */}
          <div className="space-y-3 p-3.5 rounded-2xl border border-border bg-card shadow-2xs washi-texture">
            {/* Pressure Selector */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-xs font-bold">
                <label className="text-muted-foreground flex items-center gap-1">
                  <Clock className="h-3.5 w-3.5 text-primary" />
                  <span>Áp Lực Thời Gian:</span>
                </label>
                <span className="text-primary font-mono text-[11px] font-bold">
                  {timerMs > 0 ? `${timerMs / 1000}s / câu` : "∞ Vô hạn"}
                </span>
              </div>
              <div className="flex items-center gap-1 p-0.5 rounded-xl bg-muted/50 border border-border">
                {PRESSURE_LEVELS.map((p) => (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => {
                      soundFX.playFurin();
                      setPressure(p.id as any);
                    }}
                    className={cn(
                      "flex-1 py-1 rounded-lg text-[10px] font-bold transition-all text-center",
                      pressure === p.id
                        ? "bg-card text-foreground border border-border shadow-2xs"
                        : "text-muted-foreground hover:text-foreground"
                    )}
                    title={p.desc}
                  >
                    {p.id === "infinite" ? "∞" : `${p.ms / 1000}s`}
                  </button>
                ))}
              </div>
            </div>

            {/* Duration Selector */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-xs font-bold">
                <span className="text-muted-foreground">Thời Lượng Phiên:</span>
                <span className="text-primary font-mono text-[11px]">{duration === 0 ? "∞ Vô hạn" : `${duration} phút`}</span>
              </div>
              <div className="flex items-center gap-1 p-0.5 rounded-xl bg-muted/50 border border-border">
                {DURATION_OPTIONS.map((d) => (
                  <button
                    key={d}
                    type="button"
                    onClick={() => setDuration(d)}
                    className={cn(
                      "flex-1 py-1 rounded-lg text-[10px] font-bold transition-all text-center",
                      duration === d
                        ? "bg-card text-foreground border border-border shadow-2xs"
                        : "text-muted-foreground hover:text-foreground"
                    )}
                  >
                    {d === 0 ? "∞" : `${d}m`}
                  </button>
                ))}
              </div>
            </div>

            {/* Progressive Disclosure: Subtitles, Start Trigger & Auto Next */}
            <div className="border border-border/80 rounded-xl bg-muted/20 overflow-hidden">
              <button
                type="button"
                onClick={() => setIsReflexAdvancedOpen((v) => !v)}
                className="w-full px-2.5 py-1.5 flex items-center justify-between text-[11px] font-bold text-muted-foreground hover:text-foreground transition-colors"
              >
                <span>Phụ đề & Chế độ xuất phát</span>
                <span className="text-[10px] text-primary">{isReflexAdvancedOpen ? "▲" : "▼"}</span>
              </button>

              {isReflexAdvancedOpen && (
                <div className="p-2.5 pt-1 space-y-2 border-t border-border/60 animate-in fade-in duration-150">
                  {/* Subtitle Mode */}
                  <div className="space-y-1">
                    <span className="text-[10px] font-bold text-muted-foreground">Hiển thị đề bài:</span>
                    <div className="grid grid-cols-3 gap-1 text-[10px]">
                      {[
                        { id: "japanese", label: "🇯🇵 Nhật" },
                        { id: "vietnamese", label: "🇻🇳 Dịch" },
                        { id: "hidden", label: "🎧 Ẩn" },
                      ].map((opt) => (
                        <button
                          key={opt.id}
                          type="button"
                          onClick={() => setSubtitleMode(opt.id as any)}
                          className={cn(
                            "py-1 rounded-lg font-bold border transition-all text-center",
                            subtitleMode === opt.id
                              ? "bg-primary text-primary-foreground border-primary"
                              : "bg-card border-border hover:bg-muted text-foreground"
                          )}
                        >
                          {opt.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Start Trigger Mode */}
                  <div className="space-y-1 pt-1 border-t border-border/40">
                    <span className="text-[10px] font-bold text-muted-foreground">Chế độ xuất phát:</span>
                    <div className="grid grid-cols-2 gap-1 text-[10px]">
                      <button
                        type="button"
                        onClick={() => setStartTrigger("manual")}
                        className={cn(
                          "py-1 rounded-lg font-bold border transition-all text-center",
                          startTrigger === "manual" ? "bg-primary text-primary-foreground border-primary" : "bg-card border-border text-muted-foreground"
                        )}
                      >
                        🎯 Chủ động
                      </button>
                      <button
                        type="button"
                        onClick={() => setStartTrigger("auto")}
                        className={cn(
                          "py-1 rounded-lg font-bold border transition-all text-center",
                          startTrigger === "auto" ? "bg-amber-500 text-white border-amber-500" : "bg-card border-border text-muted-foreground"
                        )}
                      >
                        ⚡ Tự động
                      </button>
                    </div>
                  </div>

                  {/* Auto-Next */}
                  <div className="pt-1 border-t border-border/40 flex items-center justify-between text-[11px]">
                    <span className="font-bold text-muted-foreground">Tự chuyển câu:</span>
                    <button
                      type="button"
                      onClick={() => setAutoNext((v) => !v)}
                      className={cn(
                        "px-2 py-0.5 rounded-full text-[10px] font-bold border transition-all",
                        autoNext ? "bg-emerald-600 text-white border-emerald-600" : "bg-muted border-border text-muted-foreground"
                      )}
                    >
                      {autoNext ? "BẬT" : "TẮT"}
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Big CTA Start Button */}
            <Button
              variant="akane"
              size="lg"
              className="w-full font-bold text-xs rounded-xl h-10 shadow-md hover:shadow-lg transition-all gap-2"
              onClick={() => {
                soundFX.playTaiko();
                session.startSession();
              }}
            >
              <Play className="h-3.5 w-3.5 fill-current" />
              <span>Bắt Đầu Phản Xạ ({duration === 0 ? "Vô Hạn" : `${duration}p`})</span>
            </Button>
          </div>
        </div>

        {/* Conjugation Form Filter Modal */}
        <ConjugationFilterModal
          open={showFormFilterModal}
          onClose={() => setShowFormFilterModal(false)}
          selectedForms={selectedForms}
          onChangeSelectedForms={handleSelectedFormsChange}
        />

        {/* Q&A Topic Filter Modal */}
        <QnaTopicFilterModal
          open={showQnaTopicFilterModal}
          onClose={() => setShowQnaTopicFilterModal(false)}
          selectedTopics={selectedQnaTopics}
          onChangeSelectedTopics={handleSelectedQnaTopicsChange}
          customKeywords={customKeywords}
          onChangeCustomKeywords={handleCustomKeywordsChange}
        />

        {/* Transformation Category Filter Modal */}
        <TransformationFilterModal
          isOpen={showTransformFilterModal}
          onClose={() => setShowTransformFilterModal(false)}
          selectedCategories={selectedTransformCategories}
          onChange={handleSelectedTransformCategoriesChange}
          customKeywords={customTransformKeywords}
          onChangeCustomKeywords={handleCustomTransformKeywordsChange}
        />

        {/* Context Category Filter Modal */}
        <ContextFilterModal
          isOpen={showContextFilterModal}
          onClose={() => setShowContextFilterModal(false)}
          selectedCategories={selectedContextCategories}
          onChange={handleSelectedContextCategoriesChange}
          customKeywords={customContextKeywords}
          onChangeCustomKeywords={handleCustomContextKeywordsChange}
        />

        {/* Vocab Category Filter Modal */}
        <VocabFilterModal
          isOpen={showVocabFilterModal}
          onClose={() => setShowVocabFilterModal(false)}
          selectedCategories={selectedVocabCategories}
          onChange={handleSelectedVocabCategoriesChange}
          customKeywords={customVocabKeywords}
          onChangeCustomKeywords={handleCustomVocabKeywordsChange}
        />

        {/* Keigo Filter Modal */}
        <KeigoFilterModal
          isOpen={showKeigoFilterModal}
          onClose={() => setShowKeigoFilterModal(false)}
          selectedCategories={selectedKeigoCategories}
          onChange={handleSelectedKeigoCategoriesChange}
          customKeywords={customKeigoKeywords}
          onChangeCustomKeywords={handleCustomKeigoKeywordsChange}
        />

        {/* Global Keybindings Modal */}
        <GlobalKeybindingsModal
          isOpen={showHelp}
          onClose={() => setShowHelp(false)}
        />
      </div>
    );
  }

  // ==========================================
  // RENDER 2: ACTIVE ZEN REFLEX ARENA (NO-SCROLL VIEWPORT FIT)
  // ==========================================
  const isWaiting = session.phase === "waiting_for_speech";
  const isRecording = session.phase === "recording";
  const isEvaluating = session.phase === "evaluating" || session.phase === "loading";
  const isPromptPlaying = session.phase === "prompt_playing";
  const isReady = session.phase === "ready";
  const isResult = session.phase === "result";

  return (
    <div className="max-w-4xl mx-auto h-[calc(100vh-5.5rem)] flex flex-col justify-between animate-in fade-in duration-200 px-2 sm:px-4 overflow-hidden">
      {/* 1. Top HUD Bar */}
      <div className="p-3 px-4 rounded-2xl border border-border bg-card shadow-xs flex items-center justify-between gap-3 washi-texture shrink-0">
        <div className="flex items-center gap-2">
          <Badge variant="kintsugi" size="sm" className="font-bold">
            Câu {session.stats.total + (isResult ? 0 : 1)}
          </Badge>
          <span className="text-xs font-bold text-foreground hidden sm:inline font-jp">
            {subMode === "mixed" ? "Mixed Adaptive" : DEDICATED_MODES.find((m) => m.id === subMode)?.title}
          </span>
          <span className="text-xs font-mono text-muted-foreground">• {pressure} ({timerMs / 1000}s)</span>
        </div>

        <div className="flex items-center gap-2.5">
          {/* Live Session Countdown Clock / Elapsed Clock */}
          <div
            className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-primary/10 border border-primary/25 text-primary text-xs font-mono font-bold shadow-2xs"
            title={duration === 0 ? "Chế độ luyện tập không giới hạn thời gian (Endless)" : `Thời lượng phiên: ${duration} phút`}
          >
            <Clock className="h-3.5 w-3.5" />
            <span>
              {duration === 0 ? (
                `Phiên: ${Math.floor(sessionElapsedSec / 60).toString().padStart(2, "0")}:${(sessionElapsedSec % 60).toString().padStart(2, "0")} / ∞`
              ) : (
                `Phiên: ${Math.floor(sessionRemainingSec / 60).toString().padStart(2, "0")}:${(sessionRemainingSec % 60).toString().padStart(2, "0")} / ${duration}m`
              )}
            </span>
          </div>

          {/* Quick Subtitle Mode Segmented Switcher */}
          <div className="hidden sm:flex items-center rounded-xl bg-muted/60 p-0.5 border border-border text-[11px] font-bold">
            <button
              type="button"
              onClick={() => {
                soundFX.playFurin();
                setSubtitleMode("japanese");
              }}
              className={cn(
                "px-2 py-0.5 rounded-lg transition-all",
                subtitleMode === "japanese"
                  ? "bg-card text-foreground shadow-2xs font-extrabold"
                  : "text-muted-foreground hover:text-foreground"
              )}
              title="Chỉ hiển thị tiếng Nhật"
            >
              🇯🇵 Nhật
            </button>
            <button
              type="button"
              onClick={() => {
                soundFX.playFurin();
                setSubtitleMode("vietnamese");
              }}
              className={cn(
                "px-2 py-0.5 rounded-lg transition-all",
                subtitleMode === "vietnamese"
                  ? "bg-card text-primary shadow-2xs font-extrabold"
                  : "text-muted-foreground hover:text-foreground"
              )}
              title="Tiếng Nhật kèm dịch nghĩa tiếng Việt"
            >
              🇻🇳 Dịch
            </button>
            <button
              type="button"
              onClick={() => {
                soundFX.playFurin();
                setSubtitleMode("hidden");
              }}
              className={cn(
                "px-2 py-0.5 rounded-lg transition-all",
                subtitleMode === "hidden"
                  ? "bg-card text-rose-500 shadow-2xs font-extrabold"
                  : "text-muted-foreground hover:text-foreground"
              )}
              title="Ẩn phụ đề (Audio-Only)"
            >
              🎧 Ẩn
            </button>
          </div>

          {currentStreak > 1 && (
            <div className="flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-600 dark:text-amber-400 text-xs font-bold animate-pulse">
              <Flame className="h-3.5 w-3.5 fill-current" />
              <span>{currentStreak} Streak</span>
            </div>
          )}

          {session.stats.avgLatency > 0 && (
            <div className="hidden md:flex items-center gap-1 text-xs font-mono font-bold text-muted-foreground">
              <Zap className="h-3 w-3 text-amber-500" />
              <span>TB: {Math.round(session.stats.avgLatency)}ms</span>
            </div>
          )}

          {/* HUD Start Trigger Mode Switcher */}
          <button
            type="button"
            onClick={() => setStartTrigger((v) => (v === "manual" ? "auto" : "manual"))}
            className={cn(
              "hidden sm:inline-flex items-center gap-1 px-2.5 py-1 rounded-xl text-[11px] font-bold border transition-all",
              startTrigger === "manual"
                ? "bg-primary/15 text-primary border-primary/30 shadow-2xs"
                : "bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30"
            )}
            title={startTrigger === "manual" ? "Chế độ Chủ động: Bấm Space/Nút khi sẵn sàng (Click để chuyển Tự động)" : "Chế độ Tự động: Đếm giờ ngay sau đề bài (Click để chuyển Chủ động)"}
          >
            <span>{startTrigger === "manual" ? "🎯 Chủ động" : "⚡ Tự động"}</span>
          </button>

          {/* HUD Auto-Next Switcher */}
          <button
            type="button"
            onClick={() => setAutoNext((v) => !v)}
            className={cn(
              "hidden sm:inline-flex items-center gap-1 px-2.5 py-1 rounded-xl text-[11px] font-bold border transition-all",
              autoNext
                ? "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30 shadow-2xs"
                : "bg-muted text-muted-foreground border-border hover:text-foreground"
            )}
            title={autoNext ? "Tự động chuyển câu (Bấm để tắt)" : "Chuyển câu thủ công (Bấm để bật)"}
          >
            <span>Auto</span>
            <span className="font-mono text-[10px] font-black">{autoNext ? "ON" : "OFF"}</span>
          </button>

          {/* HUD Conjugation Form Filter */}
          {(subMode === "reflex_conjugation" || (activeExercise as any)?.exercise_type === "reflex_conjugation") && (
            <button
              type="button"
              onClick={() => {
                soundFX.playFurin();
                setShowFormFilterModal(true);
              }}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-xl text-[11px] font-bold border border-rose-500/30 bg-rose-500/10 text-rose-700 dark:text-rose-300 hover:bg-rose-500/20 transition-all cursor-pointer shadow-2xs"
              title="Bấm để đổi bộ lọc thể chia động từ mục tiêu"
            >
              <Sliders className="h-3 w-3 text-rose-500" />
              <span>{selectedForms.length === 0 ? "50 Thể" : `${selectedForms.length} Thể`}</span>
            </button>
          )}

          {/* HUD Q&A Topic Filter */}
          {(subMode === "reflex_qna" || (activeExercise as any)?.exercise_type === "reflex_qna") && (
            <button
              type="button"
              onClick={() => {
                soundFX.playFurin();
                setShowQnaTopicFilterModal(true);
              }}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-xl text-[11px] font-bold border border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-500/20 transition-all cursor-pointer shadow-2xs"
              title="Bấm để đổi chủ đề câu hỏi Speed Q&A"
            >
              <MessageSquare className="h-3 w-3 text-emerald-500" />
              <span>
                {customKeywords.trim()
                  ? `💡 "${customKeywords.trim()}"`
                  : selectedQnaTopics.length === 0
                  ? "Ngẫu nhiên vô tận"
                  : `${selectedQnaTopics.length} Chủ đề`}
              </span>
            </button>
          )}

          {/* HUD Transformation Category Filter */}
          {(subMode === "reflex_transformation" || (activeExercise as any)?.exercise_type === "reflex_transformation") && (
            <button
              type="button"
              onClick={() => {
                soundFX.playFurin();
                setShowTransformFilterModal(true);
              }}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-xl text-[11px] font-bold border border-indigo-500/30 bg-indigo-500/10 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-500/20 transition-all cursor-pointer shadow-2xs"
              title="Bấm để đổi nhóm cấu trúc biến đổi câu mục tiêu"
            >
              <Repeat className="h-3 w-3 text-indigo-500" />
              <span>
                {selectedTransformCategories.length === 0
                  ? "Ngẫu nhiên 75+ dạng"
                  : `${selectedTransformCategories.length} Nhóm ngữ pháp`}
              </span>
            </button>
          )}

          {/* HUD Context Category Filter */}
          {(subMode === "reflex_context" || (activeExercise as any)?.exercise_type === "reflex_context") && (
            <button
              type="button"
              onClick={() => {
                soundFX.playFurin();
                setShowContextFilterModal(true);
              }}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-xl text-[11px] font-bold border border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-300 hover:bg-amber-500/20 transition-all cursor-pointer shadow-2xs"
              title="Bấm để đổi nhóm bối cảnh giao tiếp mục tiêu"
            >
              <Compass className="h-3 w-3 text-amber-500" />
              <span>
                {selectedContextCategories.length === 0
                  ? "Ngẫu nhiên 60+ tình huống"
                  : `${selectedContextCategories.length} Nhóm bối cảnh`}
              </span>
            </button>
          )}

          {/* HUD Vocabulary Category Filter */}
          {(subMode === "reflex_vocabulary" || (activeExercise as any)?.exercise_type === "reflex_vocabulary") && (
            <button
              type="button"
              onClick={() => {
                soundFX.playFurin();
                setShowVocabFilterModal(true);
              }}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-xl text-[11px] font-bold border border-violet-500/30 bg-violet-500/10 text-violet-700 dark:text-violet-300 hover:bg-violet-500/20 transition-all cursor-pointer shadow-2xs"
              title="Bấm để đổi nhóm từ vựng mục tiêu"
            >
              <BookText className="h-3 w-3 text-violet-500" />
              <span>
                {customVocabKeywords.trim()
                  ? `Từ khóa: "${customVocabKeywords.trim()}"`
                  : selectedVocabCategories.length === 0
                  ? "Ngẫu nhiên 500+ từ"
                  : `${selectedVocabCategories.length} Nhóm từ`}
              </span>
            </button>
          )}

          {/* HUD Keigo Category Filter */}
          {(subMode === "reflex_keigo_vocab" || (activeExercise as any)?.exercise_type === "reflex_keigo_vocab") && (
            <button
              type="button"
              onClick={() => {
                soundFX.playFurin();
                setShowKeigoFilterModal(true);
              }}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-xl text-[11px] font-bold border border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-300 hover:bg-amber-500/20 transition-all cursor-pointer shadow-2xs"
              title="Bấm để đổi chuyên đề kính ngữ mục tiêu"
            >
              <Crown className="h-3 w-3 text-amber-500" />
              <span>
                {customKeigoKeywords.trim()
                  ? `Kính ngữ: "${customKeigoKeywords.trim()}"`
                  : selectedKeigoCategories.length === 0
                  ? "Ngẫu nhiên 80+ cặp"
                  : `${selectedKeigoCategories.length} Nhóm kính ngữ`}
              </span>
            </button>
          )}
        </div>

        <div className="flex items-center gap-1.5">
          <Button
            variant="ghost"
            size="sm"
            className="h-8 px-2 text-xs rounded-xl"
            onClick={() => setShowHelp(true)}
            title="Trợ giúp phím tắt (?)"
          >
            <HelpCircle className="h-4 w-4" />
          </Button>

          <Button
            variant="outline"
            size="sm"
            className="h-8 px-2.5 text-xs rounded-xl border-border"
            onClick={() => {
              stopWebSpeech();
              session.recorder.releaseMicrophone();
              session.speech.stopListening();
              setShowSummary(true);
              session.setPhase("summary" as any);
            }}
          >
            Tổng kết
          </Button>

          <Button
            variant="ghost"
            size="sm"
            className="h-8 px-2 text-xs rounded-xl text-muted-foreground hover:text-foreground"
            onClick={() => {
              stopWebSpeech();
              session.recorder.releaseMicrophone();
              session.speech.stopListening();
              session.setPhase("idle" as any);
              setShowSummary(false);
            }}
            title="Thoát phòng (Esc)"
          >
            Thoát
          </Button>
        </div>
      </div>

      {/* 2. Main Center Stage (Flex-1, Fits viewport) */}
      <div className="flex-1 flex flex-col justify-center py-2 md:py-3 space-y-3 min-h-0">
        {showSummary ? (
          <div className="overflow-y-auto max-h-full">
            <ReflexSessionSummary
              results={session.results as any}
              onRestart={() => {
                setShowSummary(false);
                session.startSession();
              }}
              onToPlan={() => (window.location.href = "/learning")}
            />
          </div>
        ) : session.phase === "loading" || (!activeExercise && !isResult) ? (
          <div className="py-6 animate-in fade-in duration-150">
            <ZenLoadingState
              variant="studio"
              title="AI Đang Chuẩn Bị Câu Hỏi Phản Xạ..."
              ja="瞬発設問生成中..."
              description="AI đang tinh chỉnh câu hỏi ngữ pháp, từ vựng và bối cảnh phù hợp với tốc độ phản xạ của bạn..."
            />
          </div>
        ) : isResult && session.result ? (
          /* Result Card Stage */
          <div className="animate-in fade-in zoom-in-95 duration-200">
            <ReflexResultCard
              key={`${session.result.exerciseId || (activeExercise as any)?.id || "res"}_${session.stats.total}`}
              result={session.result}
              exercise={activeExercise as any}
              onNext={() => session.startNext()}
              onRetry={() => session.retry()}
              onSlowMode={() => setPressure("relaxed")}
              onCancelAutoNext={session.cancelAutoNext}
            />
          </div>
        ) : (
          /* Active Question Stage */
          <div className="space-y-3 flex flex-col justify-center">
            {session.error && (
              <div className="p-3 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-600 dark:text-rose-400 text-xs font-bold flex items-center justify-between gap-2 animate-in fade-in duration-200">
                <span>⚠️ {session.error}</span>
                <Button
                  size="sm"
                  variant="outline"
                  className="h-7 text-xs border-rose-500/40 hover:bg-rose-500/10"
                  onClick={() => session.setError(null)}
                >
                  Đóng
                </Button>
              </div>
            )}

            {/* Prompt Card */}
            <ReflexPromptCard
              exercise={activeExercise as any}
              subtitleMode={subtitleMode}
              phase={session.phase}
              onPlayAudio={playPromptAudio}
            />

            {/* Live Web Speech Recognition Box & Countdown Timer */}
            <div className="p-4 md:p-5 rounded-3xl border border-border bg-card washi-texture shadow-sm flex flex-col items-center justify-center space-y-3">
              {/* Dynamic Countdown Ring */}
              <ReflexTimer
                remainingMs={session.timer.remainingMs}
                timerLimitMs={session.timer.totalLimitMs || timerMs}
                progress={session.timer.progress}
                state={session.timer.state}
                isActive={session.timer.isActive}
                isPaused={session.isPaused}
              />

              {/* Status Message */}
              <div className="text-center space-y-1">
                {session.isPaused ? (
                  <div className="flex items-center justify-center gap-2 text-sm md:text-base font-black text-amber-600 dark:text-amber-400 animate-pulse">
                    <Clock className="h-4 w-4" />
                    <span>⏸️ ĐANG TẠM DỪNG SUY NGHĨ — Bấm Tiếp Tục khi đã sẵn sàng!</span>
                  </div>
                ) : isPromptPlaying ? (
                  <div className="flex items-center justify-center gap-2 text-xs md:text-sm font-bold text-primary animate-pulse">
                    <Volume2 className="h-4 w-4" />
                    <span>🔊 Đang đọc câu hỏi đề bài... (Bấm [Space] để trả lời ngay)</span>
                  </div>
                ) : isReady ? (
                  <div className="flex flex-col items-center justify-center gap-1 animate-in fade-in zoom-in-95 duration-200">
                    <div className="flex items-center gap-2 text-sm md:text-base font-black text-primary animate-pulse">
                      <Sparkles className="h-4 w-4" />
                      <span>🎯 ĐÃ SẴN SÀNG! Hãy suy nghĩ câu trả lời và bắt đầu khi sẵn sàng</span>
                    </div>
                    <span className="text-[11px] text-muted-foreground font-medium">
                      Bấm phím <kbd className="px-1.5 py-0.5 rounded bg-muted border font-bold text-foreground">{formatKeyDisplay(keybindings.reflexStartVoice || keybindings.drillStartQuestion)}</kbd> hoặc click nút bên dưới để bật mic & tính giờ
                    </span>
                  </div>
                ) : isWaiting ? (
                  <div className="flex items-center justify-center gap-2 text-sm md:text-base font-black text-amber-600 dark:text-amber-400 animate-bounce">
                    <Zap className="h-4 w-4" />
                    <span>NÓI NGAY! Hãy bật câu trả lời bằng tiếng Nhật tức thì!</span>
                  </div>
                ) : isRecording ? (
                  <div className="flex items-center justify-center gap-2 text-sm md:text-base font-black text-rose-600 dark:text-rose-400">
                    <Activity className="h-4 w-4 animate-spin" />
                    <span>Đang ghi nhận giọng nói tiếng Nhật của bạn...</span>
                  </div>
                ) : isEvaluating ? (
                  <ZenLoadingState
                    variant="inline"
                    title="Đang phân tích phản xạ 7 chiều & chấm điểm..."
                    ja="反射速度・文法分析中..."
                  />
                ) : null}
              </div>

              {/* Quick Action Buttons (Start / Pause / Resume) */}
              <div className="flex items-center gap-2 pt-0.5">
                {isReady && (
                  <Button
                    size="lg"
                    variant="akane"
                    className="font-black text-sm md:text-base h-11 px-6 rounded-2xl shadow-md hover:shadow-lg transition-all gap-2 animate-bounce ring-2 ring-primary/30"
                    onClick={() => {
                      session.startQuestionNow();
                    }}
                  >
                    <Mic className="h-5 w-5" />
                    <span>🎙️ Bắt Đầu Nói ({formatKeyDisplay(keybindings.drillStartQuestion)})</span>
                  </Button>
                )}

                {isPromptPlaying && (
                  <Button
                    size="sm"
                    variant="outline"
                    className="font-bold text-xs h-8 px-4 rounded-xl shadow-xs gap-1.5 border-primary/40 text-primary hover:bg-primary/10"
                    onClick={() => {
                      stopWebSpeech();
                      session.startQuestionNow();
                    }}
                  >
                    <Play className="h-3.5 w-3.5 fill-current" />
                    <span>Bắt Đầu Trả Lời Ngay ({formatKeyDisplay(keybindings.drillStartQuestion)})</span>
                  </Button>
                )}

                {session.isPaused ? (
                  <Button
                    size="sm"
                    variant="kintsugi"
                    className="font-bold text-xs h-8 px-4 rounded-xl shadow-xs gap-1.5 animate-pulse"
                    onClick={() => session.togglePause()}
                  >
                    <Play className="h-3.5 w-3.5 fill-current" />
                    <span>Tiếp Tục Suy Nghĩ ({formatKeyDisplay(keybindings.drillPauseOrResume)})</span>
                  </Button>
                ) : (isWaiting || isRecording) ? (
                  <Button
                    size="sm"
                    variant="outline"
                    className="font-bold text-xs h-8 px-3 rounded-xl border-amber-500/40 text-amber-600 dark:text-amber-400 hover:bg-amber-500/10 gap-1.5"
                    onClick={() => session.togglePause()}
                    title="Tạm dừng đồng hồ để suy nghĩ"
                  >
                    <Clock className="h-3.5 w-3.5 text-amber-500" />
                    <span>Tạm Dừng Suy Nghĩ ({formatKeyDisplay(keybindings.drillPauseOrResume)})</span>
                  </Button>
                ) : null}
              </div>

              {/* LIVE SPEECH PREVIEW BUBBLE (Streaming Real-Time Audio Waves + Text) */}
              {(isWaiting || isRecording || session.speech.interimTranscript || session.speech.transcript) && (
                <div className="w-full max-w-xl mx-auto p-2.5 px-4 rounded-2xl bg-primary/5 border border-primary/25 shadow-xs flex items-center justify-between gap-3 animate-in fade-in zoom-in-95 duration-200">
                  <div className="flex items-center gap-2.5 min-w-0">
                    {/* Real-time Dynamic Sound Wave Bars */}
                    <div className="flex items-center gap-0.5 shrink-0 h-5 px-1.5 py-0.5 bg-primary/10 rounded-lg">
                      {[0.7, 1.2, 0.6, 1.4, 0.9].map((scale, i) => {
                        const height = Math.max(4, Math.min(18, ((session.volumeLevel || 0.05) * 50 * scale) + 4));
                        return (
                          <span
                            key={i}
                            className="w-1 bg-primary rounded-full transition-all duration-75"
                            style={{ height: `${height}px` }}
                          />
                        );
                      })}
                    </div>

                    <div className="flex flex-col min-w-0">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-primary/80 flex items-center gap-1.5">
                        <span>🎙️ Live Speech Preview</span>
                        {session.speech.interimTranscript && (
                          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-ping" />
                        )}
                      </span>
                      <span className="text-xs md:text-sm font-bold font-jp text-foreground truncate">
                        “{session.speech.interimTranscript || session.speech.transcript || "Đang lắng nghe âm thanh tiếng Nhật..."}”
                      </span>
                    </div>
                  </div>

                  <Badge variant="outline" size="sm" className="text-[10px] font-mono border-primary/30 text-primary shrink-0 hidden sm:inline-flex">
                    Google Web Speech
                  </Badge>
                </div>
              )}

              {/* UNIFIED VOICE & KEYBOARD REFLEX INPUT BAR */}
              <div className="w-full max-w-xl mx-auto space-y-1">
                <ZenUnifiedInputBar
                  value={transcriptInput || session.speech.transcript || session.speech.interimTranscript}
                  onChange={setTranscriptInput}
                  onSubmit={() => handleDirectSubmit()}
                  placeholder={
                    session.isPaused
                      ? "Đang tạm dừng — Bấm [P] để tiếp tục..."
                      : isWaiting
                      ? "Nói vào mic hoặc gõ câu trả lời tiếng Nhật (Enter)..."
                      : activeExercise?.exercise_type === "reflex_conjugation"
                      ? "Gõ câu chia thể (ví dụ: 書かせられた)..."
                      : "Gõ câu phản xạ tiếng Nhật..."
                  }
                  submitButtonText="Nộp"
                  isEvaluating={isEvaluating}
                  hintText={isRecording ? "Đang thu âm mic hoặc gõ phím" : "Chế độ văn phòng: Gõ phím & Enter để nộp bài"}
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 3. Bottom Minimal Shortcuts Strip */}
      <div className="shrink-0 py-1 border-t border-border/50 flex flex-wrap items-center justify-between gap-2 text-[11px] text-muted-foreground">
        <div className="flex items-center gap-3">
          <span><kbd className="px-1 py-0.5 rounded bg-muted border font-bold">{formatKeyDisplay(keybindings.reflexStartVoice)} / {formatKeyDisplay(keybindings.reflexSubmitOrNext)}</kbd> Bắt đầu / Câu tiếp</span>
          <span><kbd className="px-1 py-0.5 rounded bg-muted border font-bold">{formatKeyDisplay(keybindings.reflexRetry)}</kbd> Làm lại</span>
          <span><kbd className="px-1 py-0.5 rounded bg-muted border font-bold">{formatKeyDisplay(keybindings.reflexReplayModel)}</kbd> Nghe lại mẫu</span>
          <span><kbd className="px-1 py-0.5 rounded bg-muted border font-bold">{formatKeyDisplay(keybindings.reflexPauseOrResume)}</kbd> Tạm dừng</span>
        </div>
        <div className="flex items-center gap-2">
          <span><kbd className="px-1 py-0.5 rounded bg-muted border font-bold">{formatKeyDisplay(keybindings.reflexToggleHelp)}</kbd> Phím tắt</span>
          <span><kbd className="px-1 py-0.5 rounded bg-muted border font-bold">Esc</kbd> Thoát</span>
        </div>
      </div>

      {/* Conjugation Form Filter Modal */}
      <ConjugationFilterModal
        open={showFormFilterModal}
        onClose={() => setShowFormFilterModal(false)}
        selectedForms={selectedForms}
        onChangeSelectedForms={handleSelectedFormsChange}
      />

      {/* Q&A Topic Filter Modal */}
      <QnaTopicFilterModal
        open={showQnaTopicFilterModal}
        onClose={() => setShowQnaTopicFilterModal(false)}
        selectedTopics={selectedQnaTopics}
        onChangeSelectedTopics={handleSelectedQnaTopicsChange}
        customKeywords={customKeywords}
        onChangeCustomKeywords={handleCustomKeywordsChange}
      />

      {/* Transformation Category Filter Modal */}
      <TransformationFilterModal
        isOpen={showTransformFilterModal}
        onClose={() => setShowTransformFilterModal(false)}
        selectedCategories={selectedTransformCategories}
        onChange={handleSelectedTransformCategoriesChange}
        customKeywords={customTransformKeywords}
        onChangeCustomKeywords={handleCustomTransformKeywordsChange}
      />

      {/* Context Category Filter Modal */}
      <ContextFilterModal
        isOpen={showContextFilterModal}
        onClose={() => setShowContextFilterModal(false)}
        selectedCategories={selectedContextCategories}
        onChange={handleSelectedContextCategoriesChange}
        customKeywords={customContextKeywords}
        onChangeCustomKeywords={handleCustomContextKeywordsChange}
      />

      {/* Vocab Category Filter Modal */}
      <VocabFilterModal
        isOpen={showVocabFilterModal}
        onClose={() => setShowVocabFilterModal(false)}
        selectedCategories={selectedVocabCategories}
        onChange={handleSelectedVocabCategoriesChange}
        customKeywords={customVocabKeywords}
        onChangeCustomKeywords={handleCustomVocabKeywordsChange}
      />

      {/* Keigo Filter Modal */}
      <KeigoFilterModal
        isOpen={showKeigoFilterModal}
        onClose={() => setShowKeigoFilterModal(false)}
        selectedCategories={selectedKeigoCategories}
        onChange={handleSelectedKeigoCategoriesChange}
        customKeywords={customKeigoKeywords}
        onChangeCustomKeywords={handleCustomKeigoKeywordsChange}
      />

      {/* Global Keybindings Modal */}
      <GlobalKeybindingsModal
        isOpen={showHelp}
        onClose={() => setShowHelp(false)}
      />

      {/* Floating AI Coach Button */}
      <CoachPanel
        open={coachOpen}
        onClose={() => setCoachOpen(false)}
        route={pathname || "/reflex"}
        exerciseId={(activeExercise as any)?.id}
      />
      <button
        onClick={() => setCoachOpen(true)}
        className="fixed bottom-20 right-4 z-30 md:bottom-5 px-3 py-2 rounded-2xl bg-card border border-border shadow-xl text-xs font-bold flex items-center gap-1.5 hover:border-primary/40 transition-all"
      >
        <span className="h-5 w-5 rounded-lg bg-primary text-primary-foreground flex items-center justify-center font-bold text-xs">
          🤖
        </span>
        <span>AI Coach</span>
      </button>
    </div>
  );
}
