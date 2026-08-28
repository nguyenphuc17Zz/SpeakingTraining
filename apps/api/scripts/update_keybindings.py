import os

KEYBINDINGS_HOOK_CONTENT = """\"use client\";

import { useState, useEffect, useCallback } from "react";

export type KeybindingCategory = "shadowing" | "speaking" | "keigo" | "drills" | "system";

export interface SystemKeybindings {
  // 1. Shadowing Studio
  toggleMic: string;
  replay: string;
  nextSegment: string;
  prevSegment: string;
  toggleLoop: string;
  markerA: string;
  markerB: string;

  // 2. Speaking / Conversation
  speakingMic: string;
  speakingReplay: string;
  speakingHint: string;
  speakingSubtitle: string;
  speakingMute: string;
  speakingModeToggle: string;

  // 3. Keigo Studio (Mode 2)
  keigoSubmitOrNext: string;
  keigoListenPrompt: string;
  keigoRetry: string;
  keigoSkip: string;
  keigoOpenCheatsheet: string;
  keigoStartVoice: string;
  keigoToggleInputMode: string;

  // 4. Drills & Quick Practice (Reflex, Pitch, Situations, Speech)
  drillSubmitOrNext: string;
  drillReplayAudio: string;
  drillRetry: string;
  drillSkip: string;
  drillToggleHelp: string;
  drillPauseOrResume: string;
  drillStartQuestion: string;

  // 5. System & Navigation
  globalSearch: string;
  openCoach: string;
  openKeybindingsModal: string;
  openDojo: string;
  toggleTheme: string;
}

export type ShadowingKeybindings = SystemKeybindings;

export const DEFAULT_KEYBINDINGS: SystemKeybindings = {
  // Shadowing
  toggleMic: "q",
  replay: "c",
  nextSegment: "arrowright",
  prevSegment: "arrowleft",
  toggleLoop: "l",
  markerA: "[",
  markerB: "]",

  // Speaking
  speakingMic: "space",
  speakingReplay: "r",
  speakingHint: "h",
  speakingSubtitle: "s",
  speakingMute: "m",
  speakingModeToggle: "t",

  // Keigo
  keigoSubmitOrNext: "enter",
  keigoListenPrompt: "l",
  keigoRetry: "r",
  keigoSkip: "n",
  keigoOpenCheatsheet: "c",
  keigoStartVoice: "space",
  keigoToggleInputMode: "t",

  // Drills
  drillSubmitOrNext: "enter",
  drillReplayAudio: "space",
  drillRetry: "r",
  drillSkip: "n",
  drillToggleHelp: "?",
  drillPauseOrResume: "p",
  drillStartQuestion: "s",

  // System
  globalSearch: "k",
  openCoach: "j",
  openKeybindingsModal: "?",
  openDojo: "d",
  toggleTheme: "t",
};

export const ACTION_CATEGORIES: Record<keyof SystemKeybindings, KeybindingCategory> = {
  // Shadowing
  toggleMic: "shadowing",
  replay: "shadowing",
  nextSegment: "shadowing",
  prevSegment: "shadowing",
  toggleLoop: "shadowing",
  markerA: "shadowing",
  markerB: "shadowing",

  // Speaking
  speakingMic: "speaking",
  speakingReplay: "speaking",
  speakingHint: "speaking",
  speakingSubtitle: "speaking",
  speakingMute: "speaking",
  speakingModeToggle: "speaking",

  // Keigo
  keigoSubmitOrNext: "keigo",
  keigoListenPrompt: "keigo",
  keigoRetry: "keigo",
  keigoSkip: "keigo",
  keigoOpenCheatsheet: "keigo",
  keigoStartVoice: "keigo",
  keigoToggleInputMode: "keigo",

  // Drills
  drillSubmitOrNext: "drills",
  drillReplayAudio: "drills",
  drillRetry: "drills",
  drillSkip: "drills",
  drillToggleHelp: "drills",
  drillPauseOrResume: "drills",
  drillStartQuestion: "drills",

  // System
  globalSearch: "system",
  openCoach: "system",
  openKeybindingsModal: "system",
  openDojo: "system",
  toggleTheme: "system",
};

const STORAGE_KEY = "hanasu_system_keybindings_v3";

export function formatKeyDisplay(keyVal: string): string {
  if (!keyVal) return "";
  const lower = keyVal.toLowerCase();
  if (lower === "arrowright") return "→";
  if (lower === "arrowleft") return "←";
  if (lower === "arrowup") return "↑";
  if (lower === "arrowdown") return "↓";
  if (lower === "space" || lower === " ") return "Space";
  if (lower === "enter") return "Enter ↵";
  if (lower === "escape" || lower === "esc") return "Esc";
  return keyVal.toUpperCase();
}

export function isKeyMatch(e: KeyboardEvent, targetKey: string): boolean {
  if (!targetKey) return false;
  const pressed = e.key.toLowerCase();
  const code = e.code.toLowerCase();
  const target = targetKey.toLowerCase();

  if (target === "space") {
    return pressed === " " || code === "space";
  }
  if (target === "enter") {
    return pressed === "enter" || code === "enter" || code === "numpadenter";
  }
  if (target === "arrowright") {
    return pressed === "arrowright" || code === "arrowright";
  }
  if (target === "arrowleft") {
    return pressed === "arrowleft" || code === "arrowleft";
  }
  if (target === "arrowup") {
    return pressed === "arrowup" || code === "arrowup";
  }
  if (target === "arrowdown") {
    return pressed === "arrowdown" || code === "arrowdown";
  }
  if (target === "escape" || target === "esc") {
    return pressed === "escape" || code === "escape";
  }

  return pressed === target;
}

export function useSystemKeybindings() {
  const [keybindings, setKeybindings] = useState<SystemKeybindings>(DEFAULT_KEYBINDINGS);
  const [isLoaded, setIsLoaded] = useState(false);

  // Load from localStorage
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        setKeybindings({ ...DEFAULT_KEYBINDINGS, ...parsed });
      }
    } catch (e) {
      console.warn("Failed to load keybindings from localStorage:", e);
    } finally {
      setIsLoaded(true);
    }
  }, []);

  // Save single keybinding
  const updateKeybinding = useCallback((action: keyof SystemKeybindings, key: string) => {
    let normalized = key.toLowerCase();
    if (normalized === " ") normalized = "space";

    setKeybindings((prev) => {
      const updated = { ...prev, [action]: normalized };
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      } catch (e) {}
      return updated;
    });
  }, []);

  // Check if a key conflicts with other actions in the same category
  const getConflicts = useCallback(
    (action: keyof SystemKeybindings, candidateKey: string): (keyof SystemKeybindings)[] => {
      const category = ACTION_CATEGORIES[action];
      const normalizedCandidate = candidateKey.toLowerCase() === " " ? "space" : candidateKey.toLowerCase();
      const conflicts: (keyof SystemKeybindings)[] = [];

      (Object.keys(keybindings) as (keyof SystemKeybindings)[]).forEach((act) => {
        if (act !== action && ACTION_CATEGORIES[act] === category) {
          const currentKey = keybindings[act]?.toLowerCase();
          if (currentKey === normalizedCandidate) {
            conflicts.push(act);
          }
        }
      });

      return conflicts;
    },
    [keybindings]
  );

  // Reset by category or reset all
  const resetToDefaults = useCallback((category?: KeybindingCategory) => {
    setKeybindings((prev) => {
      if (!category) {
        try {
          localStorage.removeItem(STORAGE_KEY);
        } catch (e) {}
        return DEFAULT_KEYBINDINGS;
      }

      const updated = { ...prev };
      (Object.keys(DEFAULT_KEYBINDINGS) as (keyof SystemKeybindings)[]).forEach((act) => {
        if (ACTION_CATEGORIES[act] === category) {
          updated[act] = DEFAULT_KEYBINDINGS[act];
        }
      });

      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      } catch (e) {}
      return updated;
    });
  }, []);

  // Helper to match an action against a key event
  const matchesAction = useCallback(
    (e: KeyboardEvent, action: keyof SystemKeybindings): boolean => {
      const target = keybindings[action];
      return isKeyMatch(e, target);
    },
    [keybindings]
  );

  return {
    keybindings,
    updateKeybinding,
    resetToDefaults,
    getConflicts,
    matchesAction,
    isLoaded,
  };
}

// Backwards compatibility
export const useShadowingKeybindings = useSystemKeybindings;
"""

SETTINGS_SECTION_CONTENT = """\"use client\";

import React, { useState, useEffect, useMemo } from "react";
import {
  Keyboard,
  RotateCcw,
  Check,
  Search,
  Mic,
  Play,
  Repeat,
  MapPin,
  Sparkles,
  MessageSquare,
  Volume2,
  VolumeX,
  HelpCircle,
  Subtitles,
  Compass,
  Swords,
  SunMoon,
  Tv,
  Zap,
  AlertTriangle,
  Radio,
  Clock,
  ArrowRight,
  Shield,
  Crown,
  BookOpen,
  Edit3,
} from "lucide-react";
import {
  useSystemKeybindings,
  SystemKeybindings,
  KeybindingCategory,
  DEFAULT_KEYBINDINGS,
  ACTION_CATEGORIES,
  formatKeyDisplay,
} from "@/hooks/use-system-keybindings";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface ActionDefinition {
  key: keyof SystemKeybindings;
  label: string;
  category: KeybindingCategory;
  categoryLabel: string;
  description: string;
  icon: React.ReactNode;
}

export const ALL_ACTION_DEFINITIONS: ActionDefinition[] = [
  // 1. Shadowing
  {
    key: "toggleMic",
    label: "Bật / Tắt Thu Âm & Chấm Điểm",
    category: "shadowing",
    categoryLabel: "Phòng Shadowing",
    description: "Bắt đầu thu âm phát âm hoặc dừng & gửi chấm điểm AI tức thì",
    icon: <Mic className="h-4 w-4 text-rose-500" />,
  },
  {
    key: "replay",
    label: "Phát Lại Câu Đang Chọn",
    category: "shadowing",
    categoryLabel: "Phòng Shadowing",
    description: "Tua về đầu câu, phát đúng 1 câu và tự động dừng ở cuối câu",
    icon: <Play className="h-4 w-4 text-primary" />,
  },
  {
    key: "nextSegment",
    label: "Chuyển Sang Câu Kế Tiếp",
    category: "shadowing",
    categoryLabel: "Phòng Shadowing",
    description: "Chọn và chuyển sang câu tiếp theo trong bài học",
    icon: <Play className="h-4 w-4 text-emerald-500" />,
  },
  {
    key: "prevSegment",
    label: "Quay Lại Câu Trước Đó",
    category: "shadowing",
    categoryLabel: "Phòng Shadowing",
    description: "Chọn và chuyển về câu trước đó trong bài học",
    icon: <Play className="h-4 w-4 text-amber-500 rotate-180" />,
  },
  {
    key: "toggleLoop",
    label: "Bật / Tắt Bảng Lặp Đoạn A-B",
    category: "shadowing",
    categoryLabel: "Phòng Shadowing",
    description: "Mở hoặc đóng nhanh bảng căn chỉnh lặp đoạn A-B",
    icon: <Repeat className="h-4 w-4 text-cyan-500" />,
  },
  {
    key: "markerA",
    label: "Đặt Mốc Bắt Đầu (Mốc A)",
    category: "shadowing",
    categoryLabel: "Phòng Shadowing",
    description: "Gán thời điểm hiện tại làm mốc bắt đầu lặp A-B",
    icon: <MapPin className="h-4 w-4 text-emerald-500" />,
  },
  {
    key: "markerB",
    label: "Đặt Mốc Kết Thúc (Mốc B)",
    category: "shadowing",
    categoryLabel: "Phòng Shadowing",
    description: "Gán thời điểm hiện tại làm mốc kết thúc lặp A-B",
    icon: <MapPin className="h-4 w-4 text-amber-500" />,
  },

  // 2. Speaking / Conversation
  {
    key: "speakingMic",
    label: "Bật / Dừng Nói Chuyện Với AI",
    category: "speaking",
    categoryLabel: "Hội Thoại AI",
    description: "Kích hoạt micro nói chuyện hoặc gửi câu thoại cho trợ lý AI",
    icon: <Mic className="h-4 w-4 text-primary" />,
  },
  {
    key: "speakingReplay",
    label: "Nghe Lại Câu Thoại Của AI",
    category: "speaking",
    categoryLabel: "Hội Thoại AI",
    description: "Phát lại audio giọng đọc tiếng Nhật tự nhiên của nhân vật AI",
    icon: <Volume2 className="h-4 w-4 text-sky-500" />,
  },
  {
    key: "speakingHint",
    label: "Xem Gợi Ý Câu Trả Lời (Hint)",
    category: "speaking",
    categoryLabel: "Hội Thoại AI",
    description: "Mở bảng gợi ý mẫu câu đối thoại tự nhiên từ AI Coach",
    icon: <HelpCircle className="h-4 w-4 text-amber-500" />,
  },
  {
    key: "speakingSubtitle",
    label: "Bật / Tắt Phụ Đề Furigana",
    category: "speaking",
    categoryLabel: "Hội Thoại AI",
    description: "Ẩn hoặc hiện phụ đề tiếng Nhật và phiên âm Furigana",
    icon: <Subtitles className="h-4 w-4 text-purple-500" />,
  },
  {
    key: "speakingMute",
    label: "Bật / Tắt Tiếng Giọng Nói AI",
    category: "speaking",
    categoryLabel: "Hội Thoại AI",
    description: "Tắt tiếng hoặc bật lại âm thanh nhân vật AI đang nói",
    icon: <VolumeX className="h-4 w-4 text-rose-500" />,
  },
  {
    key: "speakingModeToggle",
    label: "Đổi Chế Độ Rảnh Tay / Thủ Công",
    category: "speaking",
    categoryLabel: "Hội Thoại AI",
    description: "Chuyển đổi giữa chế độ VAD tự động nghe và Push-to-Talk",
    icon: <Radio className="h-4 w-4 text-emerald-500" />,
  },

  // 3. Keigo Studio (Mode 2)
  {
    key: "keigoSubmitOrNext",
    label: "Nộp Bài / Chuyển Câu Kế Tiếp",
    category: "keigo",
    categoryLabel: "Phòng Kính Ngữ",
    description: "Nộp bài thu âm hoặc chuyển sang câu tình huống Kính ngữ tiếp theo",
    icon: <Check className="h-4 w-4 text-emerald-500" />,
  },
  {
    key: "keigoListenPrompt",
    label: "Nghe Lại Giọng Đọc Đề Bài TTS",
    category: "keigo",
    categoryLabel: "Phòng Kính Ngữ",
    description: "Phát âm lại câu tình huống tiếng Nhật chuẩn bản xứ của đề bài",
    icon: <Volume2 className="h-4 w-4 text-primary" />,
  },
  {
    key: "keigoRetry",
    label: "Thử Lại Câu Hiện Tại (Retry)",
    category: "keigo",
    categoryLabel: "Phòng Kính Ngữ",
    description: "Reset đồng hồ đếm ngược và thu âm lại câu kính ngữ vừa làm",
    icon: <RotateCcw className="h-4 w-4 text-amber-500" />,
  },
  {
    key: "keigoSkip",
    label: "Bỏ Qua Câu Này (Skip / Next)",
    category: "keigo",
    categoryLabel: "Phòng Kính Ngữ",
    description: "Bỏ qua câu tình huống khó và chuyển sang câu kế tiếp",
    icon: <ArrowRight className="h-4 w-4 text-sky-500" />,
  },
  {
    key: "keigoOpenCheatsheet",
    label: "Mở / Đóng Sổ Tay Kính Ngữ",
    category: "keigo",
    categoryLabel: "Phòng Kính Ngữ",
    description: "Tra cứu nhanh 25+ động từ bất quy tắc, Uchi/Soto & Nhị trùng kính ngữ",
    icon: <BookOpen className="h-4 w-4 text-amber-600 dark:text-amber-400" />,
  },
  {
    key: "keigoStartVoice",
    label: "Bắt Đầu Trả Lời / Kích Hoạt Mic",
    category: "keigo",
    categoryLabel: "Phòng Kính Ngữ",
    description: "Bật microphone thu âm giọng nói tiếng Nhật ở chế độ thủ công",
    icon: <Mic className="h-4 w-4 text-rose-500" />,
  },
  {
    key: "keigoToggleInputMode",
    label: "Đổi Giữa Giọng Nói & Gõ Phím",
    category: "keigo",
    categoryLabel: "Phòng Kính Ngữ",
    description: "Chuyển nhanh sang ô nhập liệu text khi ở môi trường yên tĩnh",
    icon: <Edit3 className="h-4 w-4 text-purple-500" />,
  },

  // 4. Drills & Quick Practice (Reflex, Pitch, Situations, Speech)
  {
    key: "drillSubmitOrNext",
    label: "Nộp Bài / Chuyển Câu Kế Tiếp",
    category: "drills",
    categoryLabel: "Luyện Tập Phản Xạ",
    description: "Gửi câu trả lời STT hoặc bấm tiếp tục khi xem xong kết quả",
    icon: <Check className="h-4 w-4 text-emerald-500" />,
  },
  {
    key: "drillReplayAudio",
    label: "Phát Lại Âm Thanh Đề Bài / Mẫu",
    category: "drills",
    categoryLabel: "Luyện Tập Phản Xạ",
    description: "Nghe lại audio đề bài phản xạ, kính ngữ hoặc cao độ",
    icon: <Play className="h-4 w-4 text-primary" />,
  },
  {
    key: "drillRetry",
    label: "Thử Lại Câu Hiện Tại (Retry)",
    category: "drills",
    categoryLabel: "Luyện Tập Phản Xạ",
    description: "Luyện lại ngay câu prompt vừa làm để cải thiện điểm số",
    icon: <RotateCcw className="h-4 w-4 text-amber-500" />,
  },
  {
    key: "drillSkip",
    label: "Bỏ Qua Câu Này (Skip / Next)",
    category: "drills",
    categoryLabel: "Luyện Tập Phản Xạ",
    description: "Bỏ qua prompt khó và chuyển sang câu bài tập tiếp theo",
    icon: <ArrowRight className="h-4 w-4 text-sky-500" />,
  },
  {
    key: "drillToggleHelp",
    label: "Bật / Tắt Bảng Phím Tắt Nhanh",
    category: "drills",
    categoryLabel: "Luyện Tập Phản Xạ",
    description: "Mở bảng tra cứu phím tắt nhanh trong khi đang làm bài",
    icon: <HelpCircle className="h-4 w-4 text-purple-500" />,
  },
  {
    key: "drillPauseOrResume",
    label: "Tạm Dừng / Tiếp Tục Suy Nghĩ (Pause Timer)",
    category: "drills",
    categoryLabel: "Luyện Tập Phản Xạ",
    description: "Đóng băng đồng hồ đếm ngược và tạm dừng micro để suy nghĩ kỹ",
    icon: <Clock className="h-4 w-4 text-amber-500" />,
  },
  {
    key: "drillStartQuestion",
    label: "Bắt Đầu Trả Lời Câu Hỏi (Start Prompt)",
    category: "drills",
    categoryLabel: "Luyện Tập Phản Xạ",
    description: "Kích hoạt đếm ngược và bật nhận diện giọng nói khi đã sẵn sàng",
    icon: <Zap className="h-4 w-4 text-primary" />,
  },

  // 5. System & Navigation
  {
    key: "globalSearch",
    label: "Tìm Kiếm Nhanh (Command Palette)",
    category: "system",
    categoryLabel: "Hệ Thống",
    description: "Mở thanh tìm kiếm bài học, tính năng và hỏi AI Coach",
    icon: <Search className="h-4 w-4 text-primary" />,
  },
  {
    key: "openCoach",
    label: "Mở Nhanh AI Coach Panel",
    category: "system",
    categoryLabel: "Hệ Thống",
    description: "Mở bảng trò chuyện và nhận gợi ý học tập từ AI Coach",
    icon: <Sparkles className="h-4 w-4 text-amber-500" />,
  },
  {
    key: "openKeybindingsModal",
    label: "Mở Tra Cứu Phím Tắt Toàn Cục",
    category: "system",
    categoryLabel: "Hệ Thống",
    description: "Mở nhanh bảng tra cứu và tùy biến phím tắt toàn hệ thống",
    icon: <Keyboard className="h-4 w-4 text-emerald-500" />,
  },
  {
    key: "openDojo",
    label: "Mở Nhanh Dojo & Nhiệm Vụ",
    category: "system",
    categoryLabel: "Hệ Thống",
    description: "Truy cập nhanh vào võ đường luyện tập & săn thành tựu",
    icon: <Swords className="h-4 w-4 text-rose-500" />,
  },
  {
    key: "toggleTheme",
    label: "Đổi Giao Diện Sáng / Tối",
    category: "system",
    categoryLabel: "Hệ Thống",
    description: "Chuyển đổi giữa chế độ màu Haru Washi và Dark Zen",
    icon: <SunMoon className="h-4 w-4 text-amber-500" />,
  },
];

type CategoryFilter = KeybindingCategory | "all";

export function KeybindingsSettingsSection() {
  const { keybindings, updateKeybinding, resetToDefaults, getConflicts } = useSystemKeybindings();
  const [selectedCategory, setSelectedCategory] = useState<CategoryFilter>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [listeningAction, setListeningAction] = useState<keyof SystemKeybindings | null>(null);
  const [conflictWarning, setConflictWarning] = useState<string | null>(null);

  // Key listening effect
  useEffect(() => {
    if (!listeningAction) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      e.preventDefault();
      e.stopPropagation();

      if (e.key === "Escape") {
        setListeningAction(null);
        setConflictWarning(null);
        return;
      }

      let captured = e.key.toLowerCase();
      if (captured === " ") captured = "space";

      // Check conflict
      const conflicts = getConflicts(listeningAction, captured);
      if (conflicts.length > 0) {
        const conflictNames = conflicts
          .map((c) => ALL_ACTION_DEFINITIONS.find((a) => a.key === c)?.label || c)
          .join(", ");
        setConflictWarning(`Phím "${formatKeyDisplay(captured)}" đã được dùng cho: ${conflictNames}. Bạn vẫn có thể gán hoặc chọn phím khác.`);
      } else {
        setConflictWarning(null);
      }

      soundFX.playFurin();
      updateKeybinding(listeningAction, captured);
      setListeningAction(null);
    };

    window.addEventListener("keydown", handleKeyDown, { capture: true });
    return () => window.removeEventListener("keydown", handleKeyDown, { capture: true });
  }, [listeningAction, updateKeybinding, getConflicts]);

  const filteredActions = useMemo(() => {
    return ALL_ACTION_DEFINITIONS.filter((item) => {
      const matchCategory = selectedCategory === "all" || item.category === selectedCategory;
      const q = searchQuery.toLowerCase().trim();
      const matchSearch =
        !q ||
        item.label.toLowerCase().includes(q) ||
        item.description.toLowerCase().includes(q) ||
        (keybindings[item.key] || "").toLowerCase().includes(q) ||
        formatKeyDisplay(keybindings[item.key] || "").toLowerCase().includes(q);
      return matchCategory && matchSearch;
    });
  }, [selectedCategory, searchQuery, keybindings]);

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="p-5 rounded-2xl bg-card border border-border washi-texture shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <h3 className="text-base font-bold text-foreground flex items-center gap-2">
              <Keyboard className="h-5 w-5 text-primary" />
              <span>Tùy biến phím tắt toàn hệ thống</span>
            </h3>
            <p className="text-xs text-muted-foreground">
              Bấm vào bất kỳ phím nào bên dưới để gán phím mới. Nhấn <kbd className="px-1.5 py-0.5 rounded bg-muted border font-mono text-[10px] font-bold">Esc</kbd> để hủy gán.
            </p>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {selectedCategory !== "all" && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  soundFX.playFurin();
                  resetToDefaults(selectedCategory);
                }}
                className="text-xs text-muted-foreground hover:text-foreground gap-1.5"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                <span>Mặc định tab này</span>
              </Button>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                soundFX.playTaiko();
                resetToDefaults();
              }}
              className="text-xs text-muted-foreground hover:text-destructive gap-1.5"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              <span>Khôi phục tất cả</span>
            </Button>
          </div>
        </div>

        {/* Search and Category Filter Tabs */}
        <div className="flex flex-col sm:flex-row gap-3 pt-2">
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Tìm kiếm thao tác hoặc phím tắt..."
              className="w-full bg-background border border-border rounded-xl pl-10 pr-4 py-2 text-xs focus:outline-none focus:border-primary placeholder:text-muted-foreground"
            />
          </div>

          <div className="flex items-center p-1 rounded-xl bg-muted/60 border border-border/80 overflow-x-auto scrollbar-thin">
            {[
              { id: "all", label: "Tất cả" },
              { id: "shadowing", label: "Shadowing" },
              { id: "speaking", label: "Hội thoại AI" },
              { id: "keigo", label: "Kính ngữ (Keigo)" },
              { id: "drills", label: "Luyện phản xạ" },
              { id: "system", label: "Hệ thống" },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => {
                  soundFX.playFurin();
                  setSelectedCategory(tab.id as CategoryFilter);
                }}
                className={cn(
                  "px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all",
                  selectedCategory === tab.id
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Listening State Banner */}
      {listeningAction && (
        <div className="p-4 rounded-xl bg-primary/10 border-2 border-primary/40 flex items-center justify-between gap-3 animate-pulse shadow-sm">
          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-primary animate-ping" />
            <span className="text-xs font-bold text-primary">
              Đang lắng nghe phím mới cho:{" "}
              <span className="underline">{ALL_ACTION_DEFINITIONS.find((a) => a.key === listeningAction)?.label}</span>
            </span>
          </div>
          <span className="text-[11px] text-muted-foreground">Nhấn phím bất kỳ trên bàn phím (hoặc Esc để hủy)</span>
        </div>
      )}

      {/* Conflict Warning */}
      {conflictWarning && (
        <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-xs text-foreground/90 flex items-start gap-2 animate-in fade-in">
          <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
          <div className="flex-1">
            <div className="font-bold text-amber-700 dark:text-amber-300">Cảnh báo trùng phím</div>
            <div className="text-[11px] text-muted-foreground mt-0.5">{conflictWarning}</div>
          </div>
          <button
            onClick={() => setConflictWarning(null)}
            className="text-muted-foreground hover:text-foreground text-xs"
          >
            ✕
          </button>
        </div>
      )}

      {/* Keybindings Grid / Table */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {filteredActions.map((action) => {
          const rawKey = keybindings[action.key] || "";
          const isListening = listeningAction === action.key;

          return (
            <div
              key={action.key}
              className={cn(
                "p-3.5 rounded-xl border transition-all flex items-center justify-between gap-3 bg-card shadow-2xs hover:border-primary/40",
                isListening && "border-primary ring-2 ring-primary/20 bg-primary/5"
              )}
            >
              <div className="flex items-start gap-3 flex-1 min-w-0">
                <div className="p-2 rounded-lg bg-muted/60 border border-border/80 shrink-0">
                  {action.icon}
                </div>
                <div className="space-y-0.5 min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-foreground truncate">{action.label}</span>
                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-muted text-muted-foreground shrink-0">
                      {action.categoryLabel}
                    </span>
                  </div>
                  <p className="text-[11px] text-muted-foreground leading-snug line-clamp-1">
                    {action.description}
                  </p>
                </div>
              </div>

              {/* Action Key Button */}
              <button
                type="button"
                onClick={() => {
                  soundFX.playFurin();
                  setListeningAction(action.key);
                  setConflictWarning(null);
                }}
                className={cn(
                  "px-3 py-1.5 rounded-lg border font-mono text-xs font-bold transition-all shrink-0 min-w-[54px] text-center",
                  isListening
                    ? "bg-primary text-primary-foreground border-primary animate-bounce"
                    : "bg-muted/70 hover:bg-muted text-foreground border-border/80 hover:border-primary/50 shadow-2xs"
                )}
                title="Bấm để đổi phím"
              >
                {isListening ? "..." : formatKeyDisplay(rawKey)}
              </button>
            </div>
          );
        })}
      </div>

      {filteredActions.length === 0 && (
        <div className="p-8 text-center rounded-xl border border-dashed border-border bg-muted/20 text-muted-foreground text-xs space-y-1">
          <p className="font-bold">Không tìm thấy phím tắt phù hợp</p>
          <p>Thử tìm kiếm với từ khóa khác hoặc chuyển danh mục hiển thị.</p>
        </div>
      )}
    </div>
  );
}
"""

GLOBAL_MODAL_CONTENT = """\"use client\";

import React, { useState, useEffect } from "react";
import { Modal } from "@/components/ui/modal";
import { Button } from "@/components/ui/button";
import {
  RotateCcw,
  Keyboard,
  Check,
  Tv,
  MessageSquare,
  Zap,
  Crown,
  Settings,
} from "lucide-react";
import {
  SystemKeybindings,
  KeybindingCategory,
  useSystemKeybindings,
  formatKeyDisplay,
} from "@/hooks/use-system-keybindings";
import { ALL_ACTION_DEFINITIONS } from "@/components/settings/keybindings-settings-section";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

interface GlobalKeybindingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function GlobalKeybindingsModal({ isOpen, onClose }: GlobalKeybindingsModalProps) {
  const [activeTab, setActiveTab] = useState<KeybindingCategory>("keigo");
  const { keybindings, updateKeybinding, resetToDefaults } = useSystemKeybindings();
  const [listeningAction, setListeningAction] = useState<keyof SystemKeybindings | null>(null);

  // Capture pressed key when listening
  useEffect(() => {
    if (!listeningAction) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      e.preventDefault();
      e.stopPropagation();

      if (e.key === "Escape") {
        setListeningAction(null);
        return;
      }

      let capturedKey = e.key.toLowerCase();
      if (capturedKey === " ") capturedKey = "space";

      soundFX.playFurin();
      updateKeybinding(listeningAction, capturedKey);
      setListeningAction(null);
    };

    window.addEventListener("keydown", handleKeyDown, { capture: true });
    return () => window.removeEventListener("keydown", handleKeyDown, { capture: true });
  }, [listeningAction, updateKeybinding]);

  const filteredActions = ALL_ACTION_DEFINITIONS.filter((a) => a.category === activeTab);

  return (
    <Modal
      isOpen={isOpen}
      onClose={() => {
        setListeningAction(null);
        onClose();
      }}
      title="Cài Đặt & Tra Cứu Phím Tắt"
      description="Tùy chỉnh các phím tắt nhanh được phân loại theo từng phòng học & tính năng"
      className="max-w-xl"
    >
      <div className="space-y-4 pt-2">
        {/* Module Category Tabs */}
        <div className="flex items-center p-1 rounded-2xl bg-muted/70 border border-border overflow-x-auto scrollbar-thin">
          <button
            type="button"
            onClick={() => {
              soundFX.playFurin();
              setActiveTab("keigo");
            }}
            className={cn(
              "flex-1 py-2 px-2.5 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 whitespace-nowrap",
              activeTab === "keigo"
                ? "bg-primary text-primary-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            <Crown className="h-3.5 w-3.5" />
            <span>Kính Ngữ (Keigo)</span>
          </button>

          <button
            type="button"
            onClick={() => {
              soundFX.playFurin();
              setActiveTab("shadowing");
            }}
            className={cn(
              "flex-1 py-2 px-2.5 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 whitespace-nowrap",
              activeTab === "shadowing"
                ? "bg-primary text-primary-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            <Tv className="h-3.5 w-3.5" />
            <span>Shadowing</span>
          </button>

          <button
            type="button"
            onClick={() => {
              soundFX.playFurin();
              setActiveTab("speaking");
            }}
            className={cn(
              "flex-1 py-2 px-2.5 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 whitespace-nowrap",
              activeTab === "speaking"
                ? "bg-primary text-primary-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            <MessageSquare className="h-3.5 w-3.5" />
            <span>Hội Thoại AI</span>
          </button>

          <button
            type="button"
            onClick={() => {
              soundFX.playFurin();
              setActiveTab("drills");
            }}
            className={cn(
              "flex-1 py-2 px-2.5 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 whitespace-nowrap",
              activeTab === "drills"
                ? "bg-primary text-primary-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            <Zap className="h-3.5 w-3.5" />
            <span>Phản Xạ</span>
          </button>

          <button
            type="button"
            onClick={() => {
              soundFX.playFurin();
              setActiveTab("system");
            }}
            className={cn(
              "flex-1 py-2 px-2.5 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 whitespace-nowrap",
              activeTab === "system"
                ? "bg-primary text-primary-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            <Settings className="h-3.5 w-3.5" />
            <span>Hệ Thống</span>
          </button>
        </div>

        {/* Listening alert */}
        {listeningAction && (
          <div className="p-3 rounded-xl bg-primary/10 border border-primary/30 flex items-center justify-between text-xs text-primary font-bold animate-pulse">
            <span>Đang lắng nghe phím mới... Bấm phím bất kỳ trên bàn phím.</span>
            <span className="text-[10px] text-muted-foreground font-normal">Esc để hủy</span>
          </div>
        )}

        {/* Action list */}
        <div className="space-y-2 max-h-[340px] overflow-y-auto pr-1">
          {filteredActions.map((action) => {
            const currentKey = keybindings[action.key] || "";
            const isListening = listeningAction === action.key;

            return (
              <div
                key={action.key}
                className="p-3 rounded-xl border border-border/80 bg-card flex items-center justify-between gap-3 text-xs"
              >
                <div className="space-y-0.5">
                  <div className="font-bold text-foreground">{action.label}</div>
                  <div className="text-[11px] text-muted-foreground">{action.description}</div>
                </div>

                <button
                  type="button"
                  onClick={() => setListeningAction(action.key)}
                  className={cn(
                    "px-3 py-1.5 rounded-lg border font-mono text-xs font-bold transition-all shrink-0 min-w-[50px] text-center",
                    isListening
                      ? "bg-primary text-primary-foreground border-primary animate-bounce"
                      : "bg-muted hover:bg-muted/80 text-foreground border-border"
                  )}
                >
                  {isListening ? "..." : formatKeyDisplay(currentKey)}
                </button>
              </div>
            );
          })}
        </div>

        {/* Modal Footer */}
        <div className="pt-3 border-t border-border flex items-center justify-between">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              soundFX.playTaiko();
              resetToDefaults(activeTab);
            }}
            className="text-xs text-muted-foreground gap-1.5"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            <span>Mặc định tab này</span>
          </Button>

          <Button
            size="sm"
            onClick={() => {
              soundFX.playSuikinkutsu();
              onClose();
            }}
            className="text-xs font-bold gap-1.5"
          >
            <Check className="h-3.5 w-3.5" />
            <span>Hoàn Tất</span>
          </Button>
        </div>
      </div>
    </Modal>
  );
}
"""

PAGE_CONTENT = """\"use client\";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import {
  Crown,
  Mic,
  Clock,
  Play,
  RotateCcw,
  Sparkles,
  BookOpen,
  Edit3,
} from "lucide-react";
import { useKeigoSession } from "@/features/keigo/hooks/useKeigoSession";
import { ReflexTimer as KeigoTimer } from "@/features/reflex/components/ReflexTimer";
import { KeigoPromptCard } from "@/features/keigo/components/KeigoPromptCard";
import { KeigoResultCard } from "@/features/keigo/components/KeigoResultCard";
import { KeigoSessionSummary } from "@/features/keigo/components/KeigoSessionSummary";
import { KeigoCheatsheetModal } from "@/features/keigo/components/KeigoCheatsheetModal";
import { KeigoLobby, KEIGO_SUB_MODES, PRESSURE_LEVELS } from "@/features/keigo/components/KeigoLobby";
import { GlobalKeybindingsModal } from "@/components/layout/global-keybindings-modal";
import { CoachPanel } from "@/features/coach";
import { usePathname } from "next/navigation";
import { useCoachCore } from "@/features/coach/hooks/useCoachCore";
import { CoachInsightCard } from "@/features/coach/components/CoachInsightCard";
import { useCoachProactive } from "@/features/coach/hooks/useCoachProactive";
import { useSystemKeybindings, formatKeyDisplay } from "@/hooks/use-system-keybindings";
import { speakJapaneseText, stopWebSpeech } from "@/features/speaking/services/web-speech";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

export default function KeigoPage() {
  const [subMode, setSubMode] = useState("mixed");
  const [pressure, setPressure] = useState<"relaxed" | "normal" | "fast" | "reflex" | "extreme">("normal");
  const [subtitleMode, setSubtitleMode] = useState<"hidden" | "japanese" | "japanese_reading" | "vietnamese">("japanese");
  const [startTrigger, setStartTrigger] = useState<"manual" | "auto">("manual");
  const [transcriptInput, setTranscriptInput] = useState("");
  const [showTextInput, setShowTextInput] = useState(false);
  const [showSummary, setShowSummary] = useState(false);
  const [showCheatsheet, setShowCheatsheet] = useState(false);
  const [showKeybindingsModal, setShowKeybindingsModal] = useState(false);
  const [duration, setDuration] = useState<3 | 5 | 10 | 20>(5);
  const [sessionRemainingSec, setSessionRemainingSec] = useState(duration * 60);
  const [autoNext, setAutoNext] = useState(false);

  const sessionEndTimestampRef = useRef<number | null>(null);
  const sessionPausedRemainingMsRef = useRef<number>(duration * 60 * 1000);

  const { matchesAction, keybindings } = useSystemKeybindings();

  const session = useKeigoSession({
    subMode,
    pressureLevel: pressure as any,
    autoNext,
    startTrigger,
  });

  useEffect(() => {
    if (session.phase === "idle" || session.phase === "summary" || showSummary) {
      setSessionRemainingSec(duration * 60);
      sessionEndTimestampRef.current = null;
      sessionPausedRemainingMsRef.current = duration * 60 * 1000;
    }
  }, [duration, session.phase, showSummary]);

  useEffect(() => {
    const isSessionActive = session.phase !== "idle" && session.phase !== "summary" && !showSummary;
    if (!isSessionActive) return;

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
        soundFX.playVictory();
      }
    }, 500);

    return () => clearInterval(interval);
  }, [session.phase, session.isPaused, showSummary, session.setPhase]);

  const timerMs = PRESSURE_LEVELS.find((p) => p.id === pressure)?.ms ?? 5000;
  const activeExercise = session.exercise;
  const pathname = usePathname();
  const { insights, dismiss } = useCoachProactive();
  const [coachOpen, setCoachOpen] = useState(false);
  const coach = useCoachCore();

  const handleCoachSelect = (prompt: string) => {
    setCoachOpen(true);
    setTimeout(() => coach.ask(prompt, { route: pathname || "/keigo", exerciseId: (activeExercise as any)?.id }), 300);
  };

  const playedPromptExerciseIdRef = useRef<string | null>(null);

  const playPromptAudio = useCallback(
    (autoTransition = false) => {
      if (!activeExercise) return;
      const rc = activeExercise.extra_metadata?.keigo_config || {};
      const text = rc.prompt || activeExercise.prompt || activeExercise.scenario || activeExercise.title;
      if (text) {
        speakJapaneseText(text, {
          rate: 1.0,
          onEnd: () => {
            if (autoTransition) session.onPromptAudioFinished();
          },
          onError: () => {
            if (autoTransition) session.onPromptAudioFinished();
          },
        });
      } else if (autoTransition) {
        session.onPromptAudioFinished();
      }
    },
    [activeExercise, session.onPromptAudioFinished]
  );

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

  useEffect(() => {
    return () => {
      stopWebSpeech();
      session.recorder.releaseMicrophone();
      session.speech.stopListening();
    };
  }, []);

  useEffect(() => {
    if (session.phase === "result" && session.result) {
      if (session.result.isPerfect) {
        soundFX.playVictory();
      } else if (session.result.success) {
        soundFX.playSuikinkutsu();
      } else if (session.result.timedOut) {
        soundFX.playTaiko();
      }
    }
  }, [session.phase, session.result]);

  const handleDirectSubmit = async () => {
    const text = transcriptInput.trim() || session.speech.transcript.trim();
    if (!text) return;
    await session.submitWithTranscript(text);
    setTranscriptInput("");
  };

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName?.toLowerCase();
      if (tag === "textarea" || tag === "input") {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          handleDirectSubmit();
        }
        return;
      }

      if (matchesAction(e, "openKeybindingsModal") || matchesAction(e, "drillToggleHelp")) {
        e.preventDefault();
        setShowKeybindingsModal((v) => !v);
      } else if (matchesAction(e, "keigoOpenCheatsheet")) {
        e.preventDefault();
        setShowCheatsheet((v) => !v);
      } else if (matchesAction(e, "keigoToggleInputMode")) {
        e.preventDefault();
        setShowTextInput((v) => !v);
      } else if (matchesAction(e, "keigoRetry") && session.phase === "result") {
        e.preventDefault();
        soundFX.playSuikinkutsu();
        session.retry();
      } else if (matchesAction(e, "keigoSkip") && session.phase === "result") {
        e.preventDefault();
        soundFX.playSuikinkutsu();
        session.startNext();
      } else if (matchesAction(e, "keigoListenPrompt") && session.phase !== "idle") {
        e.preventDefault();
        playPromptAudio(false);
      } else if (e.key === "Escape") {
        if (showCheatsheet) {
          setShowCheatsheet(false);
        } else if (showKeybindingsModal) {
          setShowKeybindingsModal(false);
        } else if (session.phase !== "idle") {
          session.setPhase("idle" as any);
          setShowSummary(false);
          stopWebSpeech();
        }
      } else if (matchesAction(e, "keigoSubmitOrNext") || matchesAction(e, "drillSubmitOrNext")) {
        e.preventDefault();
        if (session.phase === "ready") {
          session.startVoiceRecording();
        } else if (session.phase === "waiting_for_speech" || session.phase === "recording") {
          handleDirectSubmit();
        } else if (session.phase === "result") {
          soundFX.playSuikinkutsu();
          session.startNext();
        }
      } else if (matchesAction(e, "keigoStartVoice")) {
        if (session.phase === "ready") {
          e.preventDefault();
          session.startVoiceRecording();
        }
      }
    };

    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [session.phase, transcriptInput, session.speech.transcript, showCheatsheet, showKeybindingsModal, matchesAction, playPromptAudio]);

  const formatSessionTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  if (showSummary || session.phase === "summary") {
    return (
      <div className="py-6 animate-in fade-in duration-300">
        <KeigoSessionSummary
          results={session.results}
          onRestart={() => {
            setShowSummary(false);
            soundFX.playSuikinkutsu();
            session.startSession();
          }}
          onToLobby={() => {
            setShowSummary(false);
            session.setPhase("idle" as any);
          }}
          onRetryWeak={() => {
            setShowSummary(false);
            soundFX.playSuikinkutsu();
            session.startSession();
          }}
        />
      </div>
    );
  }

  if (session.phase === "idle") {
    return (
      <div className="py-2">
        <KeigoLobby
          subMode={subMode}
          setSubMode={setSubMode}
          pressure={pressure}
          setPressure={setPressure}
          subtitleMode={subtitleMode}
          setSubtitleMode={setSubtitleMode}
          duration={duration}
          setDuration={setDuration}
          autoNext={autoNext}
          setAutoNext={setAutoNext}
          startTrigger={startTrigger}
          setStartTrigger={setStartTrigger}
          onStartSession={() => {
            soundFX.playKatana();
            session.startSession();
          }}
          onOpenCheatsheet={() => setShowCheatsheet(true)}
          onOpenHelp={() => setShowKeybindingsModal(true)}
          error={session.error}
        />

        <KeigoCheatsheetModal isOpen={showCheatsheet} onClose={() => setShowCheatsheet(false)} />
        <GlobalKeybindingsModal isOpen={showKeybindingsModal} onClose={() => setShowKeybindingsModal(false)} />
      </div>
    );
  }

  const isEvaluating = session.phase === "evaluating" || session.phase === "loading";
  const isRecordingOrWaiting = session.phase === "waiting_for_speech" || session.phase === "recording";
  const currentSubModeInfo = KEIGO_SUB_MODES.find((m) => m.id === subMode) || KEIGO_SUB_MODES[0];

  return (
    <div className="max-w-5xl mx-auto space-y-4 animate-in fade-in duration-300 pb-8">
      {/* Session Top Status Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 rounded-2xl bg-card border border-border/80 washi-texture shadow-xs">
        <div className="flex items-center gap-2">
          <Badge variant={currentSubModeInfo.badgeVariant} size="sm" className="font-bold">
            {currentSubModeInfo.ja} • {currentSubModeInfo.label}
          </Badge>
          <div className="hidden sm:flex items-center gap-2 text-xs font-semibold text-muted-foreground">
            <span>•</span>
            <span>Đúng: <strong className="text-emerald-600 dark:text-emerald-400">{session.stats.correct}</strong>/{session.stats.total}</span>
            <span>•</span>
            <span>TB: <strong className="text-foreground">{session.stats.avgLatency ? Math.round(session.stats.avgLatency) : "—"}ms</strong></span>
          </div>
        </div>

        <div className="flex items-center gap-3 ml-auto">
          <div
            className={cn(
              "flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-bold border shadow-2xs",
              sessionRemainingSec <= 30
                ? "bg-rose-500/10 text-rose-600 border-rose-500/30 animate-pulse"
                : "bg-muted/60 text-foreground border-border"
            )}
          >
            <Clock className="h-3.5 w-3.5 text-primary" />
            <span>{formatSessionTime(sessionRemainingSec)}</span>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowCheatsheet(true)}
            className="h-8 gap-1 text-xs font-bold border-amber-500/30 text-amber-700 dark:text-amber-300 hover:bg-amber-500/10"
            title="Mở Sổ tay Kính ngữ"
          >
            <BookOpen className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Sổ tay ({formatKeyDisplay(keybindings.keigoOpenCheatsheet)})</span>
          </Button>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              stopWebSpeech();
              session.setPhase("idle" as any);
              setShowSummary(false);
            }}
            className="h-8 text-xs font-bold text-muted-foreground hover:text-foreground"
          >
            Thoát (Esc)
          </Button>
        </div>
      </div>

      {/* Main Workout Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 items-start">
        {/* Left 2 Columns: Prompt & Result Arena */}
        <div className="lg:col-span-2 space-y-4">
          <KeigoPromptCard
            exercise={activeExercise}
            subtitleMode={subtitleMode}
            onPlayAudio={() => playPromptAudio(false)}
            phase={session.phase}
          />

          {isEvaluating && (
            <div className="p-5 rounded-3xl border border-primary/20 bg-primary/5 text-center space-y-2 animate-pulse washi-texture">
              <div className="flex items-center justify-center gap-2 font-bold text-sm text-primary">
                <Sparkles className="h-4 w-4 animate-spin" />
                <span>✨ Đang phân tích phản xạ & chuẩn mực Kính ngữ...</span>
              </div>
              <p className="text-xs text-muted-foreground">
                Kiểm tra hướng Tôn kính / Khiêm nhường, Uchi-Soto & Nhị trùng kính ngữ
              </p>
            </div>
          )}

          {session.phase === "result" && session.result && (
            <KeigoResultCard
              result={session.result}
              exercise={activeExercise}
              onNext={() => {
                soundFX.playSuikinkutsu();
                session.startNext();
              }}
              onRetry={() => {
                soundFX.playSuikinkutsu();
                session.retry();
              }}
              onAskCoach={handleCoachSelect}
              onCancelAutoNext={session.cancelAutoNext}
            />
          )}

          {session.phase === "ready" && (
            <div className="p-6 rounded-3xl border-2 border-primary/30 bg-card washi-texture text-center space-y-3 shadow-md">
              <div className="h-10 w-10 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center text-primary mx-auto">
                <Play className="h-5 w-5 fill-current ml-0.5" />
              </div>
              <div className="space-y-1">
                <h4 className="font-bold text-base text-foreground">Bạn đã sẵn sàng trả lời?</h4>
                <p className="text-xs text-muted-foreground">
                  Bấm nút bên dưới hoặc phím <kbd className="px-1.5 py-0.5 rounded bg-muted border text-[11px] font-mono font-bold">{formatKeyDisplay(keybindings.keigoStartVoice)}</kbd> để kích hoạt microphone và bắt đầu nói
                </p>
              </div>
              <Button
                variant="akane"
                size="lg"
                onClick={() => session.startVoiceRecording()}
                className="font-bold gap-2 text-sm shadow-md"
              >
                <Mic className="h-4 w-4" />
                <span>🎙️ Bắt Đầu Trả Lời</span>
              </Button>
            </div>
          )}
        </div>

        {/* Right 1 Column: Timer & Speech Controls */}
        <div className="space-y-4">
          <KeigoTimer
            remainingMs={session.timer.remainingMs}
            timerLimitMs={session.timer.isActive ? timerMs : activeExercise?.timerLimitMs ?? timerMs}
            progress={session.timer.progress}
            state={session.timer.state}
            isActive={session.timer.isActive}
          />

          <div className="p-4 rounded-3xl border border-border/80 bg-card shadow-xs washi-texture space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-foreground flex items-center gap-1.5">
                <Mic className="h-3.5 w-3.5 text-primary" />
                <span>Giọng Nói & Nhập Liệu</span>
              </span>
              <button
                onClick={() => setShowTextInput((v) => !v)}
                className="text-[11px] font-bold text-primary hover:underline flex items-center gap-1"
                title={`Đổi chế độ nhập (${formatKeyDisplay(keybindings.keigoToggleInputMode)})`}
              >
                <Edit3 className="h-3 w-3" />
                <span>{showTextInput ? "Dùng Mic" : "Gõ phím"}</span>
              </button>
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-[11px] text-muted-foreground">
                <span>Âm lượng mic:</span>
                <span className="font-bold font-mono">
                  {session.isUserSpeaking ? "Đang nói..." : `${Math.round(session.recorder.volumeLevel * 100)}%`}
                </span>
              </div>
              <div className="h-2 w-full bg-muted rounded-full overflow-hidden border border-border/60">
                <div
                  className={cn(
                    "h-full transition-all duration-75",
                    session.isUserSpeaking ? "bg-emerald-500" : "bg-primary"
                  )}
                  style={{ width: `${Math.min(100, Math.round(session.recorder.volumeLevel * 100))}%` }}
                />
              </div>
            </div>

            <div className="p-3 rounded-2xl bg-muted/40 border border-border/60 min-h-[58px] flex flex-col justify-center space-y-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
                Nhận diện trực tiếp (ja-JP):
              </span>
              <div className="text-xs font-bold font-jp text-foreground">
                {session.speech.transcript ? (
                  <span>“{session.speech.transcript}”</span>
                ) : isRecordingOrWaiting ? (
                  <span className="text-muted-foreground italic font-sans font-normal animate-pulse">
                    Đang lắng nghe giọng nói tiếng Nhật của bạn...
                  </span>
                ) : (
                  <span className="text-muted-foreground italic font-sans font-normal">Chờ kích hoạt mic</span>
                )}
              </div>
            </div>

            {showTextInput && (
              <div className="space-y-2 pt-1">
                <textarea
                  value={transcriptInput}
                  onChange={(e) => setTranscriptInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleDirectSubmit();
                    }
                  }}
                  placeholder="Nhập câu kính ngữ của bạn (VD: ご覧になります / 拝見いたします)..."
                  className="w-full rounded-xl border bg-background p-2.5 text-xs font-jp min-h-[64px] focus:border-primary focus:ring-1 focus:ring-primary/20"
                />
              </div>
            )}

            <div className="pt-1 flex gap-2">
              <Button
                size="sm"
                variant="akane"
                className="flex-1 font-bold text-xs"
                onClick={handleDirectSubmit}
                disabled={isEvaluating}
              >
                Gửi ({formatKeyDisplay(keybindings.keigoSubmitOrNext)})
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="font-bold text-xs"
                onClick={() => session.skip()}
                disabled={isEvaluating}
              >
                Bỏ qua ({formatKeyDisplay(keybindings.keigoSkip)})
              </Button>
            </div>
          </div>

          {insights.length > 0 && (
            <CoachInsightCard
              insight={insights[0]}
              onDismiss={() => dismiss(insights[0].id)}
              onAction={(ins) => handleCoachSelect(ins.recommended_action || ins.description)}
            />
          )}
        </div>
      </div>

      <KeigoCheatsheetModal isOpen={showCheatsheet} onClose={() => setShowCheatsheet(false)} />
      <GlobalKeybindingsModal isOpen={showKeybindingsModal} onClose={() => setShowKeybindingsModal(false)} />

      <CoachPanel open={coachOpen} onClose={() => setCoachOpen(false)} />
    </div>
  );
}
"""

FILES = {
    r"E:\SpeakingTraining\apps\web\hooks\use-system-keybindings.ts": KEYBINDINGS_HOOK_CONTENT,
    r"E:\SpeakingTraining\apps\web\components\settings\keybindings-settings-section.tsx": SETTINGS_SECTION_CONTENT,
    r"E:\SpeakingTraining\apps\web\components\layout\global-keybindings-modal.tsx": GLOBAL_MODAL_CONTENT,
    r"E:\SpeakingTraining\apps\web\app\keigo\page.tsx": PAGE_CONTENT,
}

for filepath, content in FILES.items():
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"Successfully wrote {os.path.basename(filepath)}")

print("Keybindings updated across all components!")
