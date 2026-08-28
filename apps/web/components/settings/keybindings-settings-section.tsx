"use client";

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
  Music,
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

  // 4. Pitch Lab (Mode 3)
  {
    key: "pitchSubmitOrNext",
    label: "Nộp Bài / Chuyển Câu Kế Tiếp",
    category: "pitch",
    categoryLabel: "Phòng Cao Độ",
    description: "Nộp âm thanh thu âm hoặc chuyển sang bài tập cao độ tiếp theo",
    icon: <Check className="h-4 w-4 text-emerald-500" />,
  },
  {
    key: "pitchListenPrompt",
    label: "Nghe Lại Mẫu Phát Âm Chuẩn (TTS)",
    category: "pitch",
    categoryLabel: "Phòng Cao Độ",
    description: "Phát âm mẫu từ vựng tiếng Nhật chuẩn cao độ Tokyo",
    icon: <Volume2 className="h-4 w-4 text-primary" />,
  },
  {
    key: "pitchRetry",
    label: "Luyện Lại Câu Hiện Tại (Retry)",
    category: "pitch",
    categoryLabel: "Phòng Cao Độ",
    description: "Reset đồng hồ và thu âm lại từ vựng vừa phát âm",
    icon: <RotateCcw className="h-4 w-4 text-amber-500" />,
  },
  {
    key: "pitchSkip",
    label: "Bỏ Qua Câu Này (Skip / Next)",
    category: "pitch",
    categoryLabel: "Phòng Cao Độ",
    description: "Bỏ qua bài tập cao độ khó và chuyển sang câu kế tiếp",
    icon: <ArrowRight className="h-4 w-4 text-sky-500" />,
  },
  {
    key: "pitchOpenCheatsheet",
    label: "Mở / Đóng Sổ Tay Cao Độ & Phách",
    category: "pitch",
    categoryLabel: "Phòng Cao Độ",
    description: "Tra cứu 4 loại cao độ Tokyo, Cặp từ tối thiểu & Vô thanh hóa",
    icon: <BookOpen className="h-4 w-4 text-sky-600 dark:text-sky-400" />,
  },
  {
    key: "pitchStartVoice",
    label: "Bắt Đầu Nói / Kích Hoạt Mic",
    category: "pitch",
    categoryLabel: "Phòng Cao Độ",
    description: "Bật microphone thu âm phân tích đường cao độ F0",
    icon: <Mic className="h-4 w-4 text-rose-500" />,
  },
  {
    key: "pitchToggleInputMode",
    label: "Đổi Giữa Giọng Nói & Gõ Phím",
    category: "pitch",
    categoryLabel: "Phòng Cao Độ",
    description: "Chuyển đổi giữa chế độ phát âm giọng nói và nhập liệu text",
    icon: <Edit3 className="h-4 w-4 text-purple-500" />,
  },

  // 5. Situations Studio (Mode 4)
  {
    key: "situationsSubmitOrNext",
    label: "Nộp Câu Trả Lời / Chuyển Tình Huống Tiếp",
    category: "situations",
    categoryLabel: "Phòng Tình Huống",
    description: "Gửi câu đối đáp tiếng Nhật hoặc chuyển sang cảnh tình huống tiếp theo",
    icon: <Check className="h-4 w-4 text-emerald-500" />,
  },
  {
    key: "situationsListenPrompt",
    label: "Nghe Lại Lời Thoại Của NPC (TTS)",
    category: "situations",
    categoryLabel: "Phòng Tình Huống",
    description: "Phát lại câu thoại mở đầu và phản ứng của nhân vật NPC",
    icon: <Volume2 className="h-4 w-4 text-primary" />,
  },
  {
    key: "situationsRetry",
    label: "Thử Lại Tình Huống Này (Retry)",
    category: "situations",
    categoryLabel: "Phòng Tình Huống",
    description: "Reset thời gian và thử nói lại để cải thiện độ tự nhiên & hoàn thành mục tiêu",
    icon: <RotateCcw className="h-4 w-4 text-amber-500" />,
  },
  {
    key: "situationsSkip",
    label: "Bỏ Qua Tình Huống Này (Skip / Next)",
    category: "situations",
    categoryLabel: "Phòng Tình Huống",
    description: "Bỏ qua tình huống khó và chuyển sang cảnh đối thoại kế tiếp",
    icon: <ArrowRight className="h-4 w-4 text-sky-500" />,
  },
  {
    key: "situationsOpenCheatsheet",
    label: "Mở / Đóng Sổ Tay Mẫu Câu Thực Chiến",
    category: "situations",
    categoryLabel: "Phòng Tình Huống",
    description: "Tra cứu 100+ mẫu câu giao tiếp 6 bối cảnh (Izakaya, Konbini, Ga tàu, Bệnh viện...)",
    icon: <BookOpen className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />,
  },
  {
    key: "situationsStartVoice",
    label: "Bắt Đầu Đối Thoại / Kích Hoạt Mic",
    category: "situations",
    categoryLabel: "Phòng Tình Huống",
    description: "Bật microphone thu âm giọng nói tiếng Nhật ở chế độ thủ công",
    icon: <Mic className="h-4 w-4 text-rose-500" />,
  },
  {
    key: "situationsToggleInputMode",
    label: "Đổi Giữa Giọng Nói & Gõ Phím",
    category: "situations",
    categoryLabel: "Phòng Tình Huống",
    description: "Chuyển nhanh sang ô nhập liệu text khi ở môi trường yên tĩnh",
    icon: <Edit3 className="h-4 w-4 text-purple-500" />,
  },

  // 6. Drills & Quick Practice (Reflex, Pitch, Situations, Speech)
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

  // 7. System & Navigation
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
              { id: "pitch", label: "Cao độ (Pitch)" },
              { id: "situations", label: "Tình huống (Situations)" },
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
