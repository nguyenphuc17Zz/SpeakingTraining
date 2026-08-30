"use client";

import React, { useState, useMemo } from "react";
import { Modal } from "@/components/ui/modal";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Check,
  Search,
  MessageSquare,
  Briefcase,
  Coffee,
  Plane,
  HeartHandshake,
  AlertCircle,
  Shuffle,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { soundFX } from "@/lib/sound-fx";

export interface QnaTopicOption {
  id: string;
  nameVi: string;
  nameJa: string;
  descVi: string;
  icon: any;
  color: string;
  badgeVariant: "sakura" | "kintsugi" | "fuji" | "matcha" | "sumi" | "default";
}

export const QNA_TOPIC_OPTIONS: QnaTopicOption[] = [
  {
    id: "daily",
    nameVi: "Đời Sống & Thói Quen Hàng Ngày",
    nameJa: "日常生活・習慣",
    descVi: "Thức dậy, ăn uống, thời tiết, sở thích, ngày nghỉ, thói quen sinh hoạt.",
    icon: Coffee,
    color: "border-amber-500/40 bg-amber-500/10 text-amber-600 dark:text-amber-400",
    badgeVariant: "kintsugi",
  },
  {
    id: "interview",
    nameVi: "Phỏng Vấn Xin Việc & Sự Nghiệp",
    nameJa: "面接・キャリア目標",
    descVi: "Điểm mạnh, điểm yếu, mục tiêu 5 năm, thử thách lớn nhất, triết lý làm việc.",
    icon: Briefcase,
    color: "border-rose-500/40 bg-rose-500/10 text-rose-600 dark:text-rose-400",
    badgeVariant: "sakura",
  },
  {
    id: "workplace",
    nameVi: "Công Sở, Đồng Nghiệp & Horenso",
    nameJa: "職場・同僚・報連相",
    descVi: "Quan hệ đồng nghiệp, họp hành, deadline, xử lý sự cố, làm việc từ xa.",
    icon: Briefcase,
    color: "border-indigo-500/40 bg-indigo-500/10 text-indigo-600 dark:text-indigo-400",
    badgeVariant: "fuji",
  },
  {
    id: "social",
    nameVi: "Bạn Bè, Sở Thích & Giao Lưu",
    nameJa: "友人・趣味・交流",
    descVi: "Rủ rê đi chơi, âm nhạc, phim ảnh, anime, món ăn Việt Nam yêu thích.",
    icon: HeartHandshake,
    color: "border-emerald-500/40 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
    badgeVariant: "matcha",
  },
  {
    id: "travel",
    nameVi: "Du Lịch, Ẩm Thực & Dịch Vụ",
    nameJa: "旅行・グルメ・サービス",
    descVi: "Điểm đến mơ ước, suối nước nóng Onsen, khách sạn, món ăn Nhật Bản.",
    icon: Plane,
    color: "border-sky-500/40 bg-sky-500/10 text-sky-600 dark:text-sky-400",
    badgeVariant: "fuji",
  },
  {
    id: "emergency",
    nameVi: "Tình Huống Bất Ngờ & Ý Kiến Nhanh",
    nameJa: "仮定・とっさの意見",
    descVi: "Nếu trúng 100 triệu Yên, nếu có ngày nghỉ đột xuất, kẹt thang máy, quên tài liệu.",
    icon: AlertCircle,
    color: "border-purple-500/40 bg-purple-500/10 text-purple-600 dark:text-purple-400",
    badgeVariant: "sakura",
  },
];

export const QUICK_KEYWORD_SUGGESTIONS = [
  "Trí tuệ nhân tạo AI",
  "Đàm phán lương bổng",
  "Văn hóa Anime & Manga",
  "Hẹn hò & Tỏ tình",
  "Xử lý sự cố khẩn cấp",
  "Du lịch tự túc Nhật Bản",
  "Tâm lý & Giải tỏa stress",
];

interface Props {
  open: boolean;
  onClose: () => void;
  selectedTopics: string[];
  onChangeSelectedTopics: (topics: string[]) => void;
  customKeywords?: string;
  onChangeCustomKeywords?: (keywords: string) => void;
}

export function QnaTopicFilterModal({
  open,
  onClose,
  selectedTopics,
  onChangeSelectedTopics,
  customKeywords = "",
  onChangeCustomKeywords,
}: Props) {
  const [searchQuery, setSearchQuery] = useState("");

  const isRandomMode = selectedTopics.length === 0;

  const handleSelectRandomMode = () => {
    soundFX.playFurin();
    onChangeSelectedTopics([]);
  };

  const handleToggleTopic = (topicId: string) => {
    soundFX.playFurin();
    // Clear custom keywords if switching to fixed categories
    if (onChangeCustomKeywords && customKeywords) {
      onChangeCustomKeywords("");
    }

    if (isRandomMode) {
      // Switch from Random to this specific topic
      onChangeSelectedTopics([topicId]);
      return;
    }
    if (selectedTopics.includes(topicId)) {
      const next = selectedTopics.filter((t) => t !== topicId);
      onChangeSelectedTopics(next);
    } else {
      onChangeSelectedTopics([...selectedTopics, topicId]);
    }
  };

  const handleSelectAllSpecific = () => {
    soundFX.playFurin();
    if (onChangeCustomKeywords && customKeywords) {
      onChangeCustomKeywords("");
    }
    onChangeSelectedTopics(QNA_TOPIC_OPTIONS.map((t) => t.id));
  };

  const filteredTopics = useMemo(() => {
    if (!searchQuery.trim()) return QNA_TOPIC_OPTIONS;
    const q = searchQuery.toLowerCase().trim();
    return QNA_TOPIC_OPTIONS.filter(
      (t) =>
        t.nameVi.toLowerCase().includes(q) ||
        t.nameJa.toLowerCase().includes(q) ||
        t.descVi.toLowerCase().includes(q)
    );
  }, [searchQuery]);

  const handleSelectPreset = (preset: "all" | "career" | "life" | "emergency") => {
    soundFX.playFurin();
    if (onChangeCustomKeywords && customKeywords) {
      onChangeCustomKeywords("");
    }
    if (preset === "all") {
      onChangeSelectedTopics(QNA_TOPIC_OPTIONS.map((t) => t.id));
    } else if (preset === "career") {
      onChangeSelectedTopics(["interview", "workplace"]);
    } else if (preset === "life") {
      onChangeSelectedTopics(["daily", "social", "travel"]);
    } else if (preset === "emergency") {
      onChangeSelectedTopics(["emergency"]);
    }
  };

  return (
    <Modal
      isOpen={open}
      onClose={onClose}
      title="🎯 THIẾT LẬP CHỦ ĐỀ HỎI - ĐÁP (SPEED Q&A TOPIC)"
      description="Chọn luyện tập tự do không giới hạn chủ đề hoặc khoanh vùng chuyên đề bạn muốn rèn luyện."
      className="max-w-3xl"
    >
      <div className="space-y-4 max-h-[72vh] overflow-y-auto pr-1">
        {/* ============================================================ */}
        {/* OPTION 1: NGẪU NHIÊN VÔ TẬN & TỰ DO NHẬP CHỦ ĐỀ / TỪ KHÓA */}
        {/* ============================================================ */}
        <div
          className={cn(
            "p-4 rounded-2xl border-2 text-left transition-all relative overflow-hidden shadow-2xs washi-texture space-y-3",
            isRandomMode
              ? "border-primary bg-primary/10 ring-1 ring-primary/30"
              : "border-border/80 bg-card hover:border-primary/40 opacity-85 hover:opacity-100"
          )}
        >
          <div
            onClick={handleSelectRandomMode}
            className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 cursor-pointer"
          >
            <div className="flex items-start gap-3 min-w-0">
              <div
                className={cn(
                  "h-10 w-10 rounded-xl border flex items-center justify-center shrink-0 shadow-2xs",
                  isRandomMode
                    ? "bg-primary text-primary-foreground border-primary"
                    : "bg-muted text-muted-foreground border-border"
                )}
              >
                <Shuffle className="h-5 w-5" />
              </div>

              <div className="space-y-0.5 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-black text-xs sm:text-sm text-foreground">
                    🎲 Ngẫu Nhiên Vô Tận (Tự Do Mọi Đề Tài)
                  </span>
                  <Badge variant="matcha" size="sm" className="font-bold text-[9px] px-1.5 py-0">
                    Khuyên dùng
                  </Badge>
                </div>
                <p className="text-[11px] text-muted-foreground leading-snug">
                  Tự do phản xạ bất kỳ chủ đề nào trên đời (đời sống, khoa học, triết lý, công nghệ, giả định bất ngờ...).
                </p>
              </div>
            </div>

            <div
              className={cn(
                "h-5 w-5 rounded-full border-2 flex items-center justify-center shrink-0 transition-all self-end sm:self-center",
                isRandomMode
                  ? "border-primary bg-primary text-primary-foreground shadow-xs"
                  : "border-muted-foreground/30 bg-background"
              )}
            >
              {isRandomMode && <Check className="h-3 w-3 stroke-[3]" />}
            </div>
          </div>

          {/* Custom Keyword Input Field */}
          <div className="pt-2 border-t border-border/60 space-y-1.5">
            <div className="flex items-center justify-between gap-2">
              <label className="text-[10px] font-bold text-foreground flex items-center gap-1">
                <Sparkles className="h-3 w-3 text-amber-500" />
                <span>Nhập từ khóa tùy thích (Để trống = Ngẫu nhiên 100%):</span>
              </label>
              {customKeywords && (
                <button
                  type="button"
                  onClick={() => onChangeCustomKeywords?.("")}
                  className="text-[10px] font-bold text-muted-foreground hover:text-rose-500 transition-colors"
                >
                  ✕ Xóa
                </button>
              )}
            </div>

            <div className="relative">
              <input
                type="text"
                value={customKeywords}
                onChange={(e) => {
                  if (selectedTopics.length > 0) {
                    onChangeSelectedTopics([]); // Switch to custom mode
                  }
                  onChangeCustomKeywords?.(e.target.value);
                }}
                placeholder="Ví dụ: AI, đàm phán lương bổng, đi bar, chia tay, động đất..."
                className="w-full px-3 py-1.5 rounded-xl bg-card border border-border text-xs text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-1 focus:ring-primary font-medium"
              />
            </div>
          </div>
        </div>

        {/* ============================================================ */}
        {/* OPTION 2: KHOANH VÙNG THEO CHUYÊN ĐỀ CỐ ĐỊNH */}
        {/* ============================================================ */}
        <div className="space-y-2.5">
          <div className="flex items-center justify-between gap-2 px-1 flex-wrap">
            <div className="flex items-center gap-1.5">
              <span className="text-[11px] font-bold uppercase tracking-wider text-foreground">
                Chọn nhanh theo nhóm chuyên đề:
              </span>
            </div>

            {/* 1-Click Fast Presets Bar */}
            <div className="flex items-center gap-1 flex-wrap">
              <button
                type="button"
                onClick={() => handleSelectPreset("all")}
                className="text-[10px] font-bold text-primary px-2 py-0.5 rounded-md bg-primary/10 hover:bg-primary/20 transition-colors"
              >
                ✨ Tất cả 6 chủ đề
              </button>
              <button
                type="button"
                onClick={() => handleSelectPreset("career")}
                className="text-[10px] font-bold text-indigo-700 dark:text-indigo-300 px-2 py-0.5 rounded-md bg-indigo-500/10 hover:bg-indigo-500/20 transition-colors"
              >
                💼 Công Sở & Phỏng Vấn
              </button>
              <button
                type="button"
                onClick={() => handleSelectPreset("life")}
                className="text-[10px] font-bold text-emerald-700 dark:text-emerald-300 px-2 py-0.5 rounded-md bg-emerald-500/10 hover:bg-emerald-500/20 transition-colors"
              >
                ☕ Đời Sống & Du Lịch
              </button>
              <button
                type="button"
                onClick={() => handleSelectPreset("emergency")}
                className="text-[10px] font-bold text-purple-700 dark:text-purple-300 px-2 py-0.5 rounded-md bg-purple-500/10 hover:bg-purple-500/20 transition-colors"
              >
                ⚡ Khẩn Cấp
              </button>
              {!isRandomMode && (
                <button
                  type="button"
                  onClick={handleSelectRandomMode}
                  className="text-[10px] font-bold text-muted-foreground hover:text-foreground px-2 py-0.5 rounded-md bg-muted"
                >
                  ✕ Về ngẫu nhiên
                </button>
              )}
            </div>
          </div>

          {/* Search Bar for specific topics */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Tìm nhanh chuyên đề (phỏng vấn, công sở, du lịch, đời sống)..."
              className="w-full pl-8 pr-3 py-1.5 rounded-xl bg-card border border-border text-xs text-foreground placeholder:text-muted-foreground/70 focus:outline-none focus:ring-1 focus:ring-primary font-medium"
            />
          </div>

          {/* Grid of Specific Topics */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {filteredTopics.map((topic) => {
              const isChecked = selectedTopics.includes(topic.id);
              const Icon = topic.icon;

              return (
                <div
                  key={topic.id}
                  onClick={() => handleToggleTopic(topic.id)}
                  className={cn(
                    "p-3.5 rounded-2xl border text-left transition-all flex items-start justify-between gap-3 cursor-pointer shadow-2xs",
                    isChecked
                      ? "bg-card border-primary/50 ring-1 ring-primary/30 shadow-xs"
                      : "bg-muted/20 border-border/60 opacity-75 hover:opacity-100 hover:bg-muted/30"
                  )}
                >
                  <div className="flex items-start gap-3 min-w-0">
                    <div
                      className={cn(
                        "h-9 w-9 rounded-xl border flex items-center justify-center shrink-0 shadow-2xs",
                        topic.color
                      )}
                    >
                      <Icon className="h-4 w-4" />
                    </div>
                    <div className="space-y-0.5 min-w-0">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="font-black text-xs text-foreground">{topic.nameVi}</span>
                        <Badge variant={topic.badgeVariant} size="sm">
                          {topic.nameJa}
                        </Badge>
                      </div>
                      <p className="text-[11px] text-muted-foreground leading-snug line-clamp-2">
                        {topic.descVi}
                      </p>
                    </div>
                  </div>

                  <div
                    className={cn(
                      "h-5 w-5 rounded-md border flex items-center justify-center shrink-0 transition-colors mt-0.5",
                      isChecked
                        ? "bg-primary border-primary text-primary-foreground"
                        : "border-muted-foreground/40 bg-card"
                    )}
                  >
                    {isChecked && <Check className="h-3.5 w-3.5 stroke-[3]" />}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* ============================================================ */}
        {/* MODAL ACTION BAR */}
        {/* ============================================================ */}
        <div className="flex items-center justify-between pt-3 border-t border-border">
          <div className="text-xs text-muted-foreground font-semibold flex items-center gap-2">
            <span>Trạng thái:</span>
            {customKeywords.trim() ? (
              <Badge variant="sakura" size="sm" className="font-bold">
                💡 Từ khóa: &quot;{customKeywords.trim()}&quot;
              </Badge>
            ) : isRandomMode ? (
              <Badge variant="matcha" size="sm" className="font-bold">
                🎲 Ngẫu Nhiên Vô Tận
              </Badge>
            ) : (
              <Badge variant="sakura" size="sm" className="font-bold">
                🎯 Lọc {selectedTopics.length} chuyên đề
              </Badge>
            )}
          </div>

          <Button
            variant="akane"
            size="sm"
            onClick={() => {
              soundFX.playSuikinkutsu();
              onClose();
            }}
            className="font-bold text-xs px-5 shadow-sm"
          >
            <span>Áp dụng cấu hình</span>
          </Button>
        </div>
      </div>
    </Modal>
  );
}
