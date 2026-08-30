"use client";

import React, { useState, useMemo } from "react";
import { Modal } from "@/components/ui/modal";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Check,
  Search,
  MessageSquare,
  Shield,
  GitBranch,
  HeartHandshake,
  Zap,
  Crown,
  Shuffle,
  Sparkles,
  Layers,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { soundFX } from "@/lib/sound-fx";

export interface TransformationCategoryOption {
  id: string;
  nameVi: string;
  nameJa: string;
  descVi: string;
  sampleTags: string[];
  icon: any;
  color: string;
  badgeVariant: "sakura" | "kintsugi" | "fuji" | "matcha" | "sumi" | "default";
}

export const TRANSFORMATION_CATEGORY_OPTIONS: TransformationCategoryOption[] = [
  {
    id: "casual",
    nameVi: "Thể Ngắn & Khẩu Ngữ Rút Gọn",
    nameJa: "カジュアル・口語短縮",
    descVi: "Lịch sự ↔ Thể ngắn, văn nói rút gọn (〜ちゃう, 〜とく, 〜ちゃだめ, 〜なきゃ).",
    sampleTags: ["〜ちゃう", "〜とく", "〜ちゃだめ", "〜なきゃ", "〜ないと"],
    icon: MessageSquare,
    color: "border-amber-500/40 bg-amber-500/10 text-amber-600 dark:text-amber-400",
    badgeVariant: "kintsugi",
  },
  {
    id: "passive_causative",
    nameVi: "Bị Động & Sai Khiến (N4-N3)",
    nameJa: "受身・使役・使役受身",
    descVi: "Hoán đổi chủ ngữ - trợ từ: bị động (〜られる), bị động phiền toái, sai khiến (〜させる), bị ép làm (〜させられる).",
    sampleTags: ["受身形 〜られる", "迷惑受身", "使役 〜させる", "使役受身 〜させられる"],
    icon: Shield,
    color: "border-rose-500/40 bg-rose-500/10 text-rose-600 dark:text-rose-400",
    badgeVariant: "sakura",
  },
  {
    id: "conditional",
    nameVi: "4 Thể Điều Kiện (Ba / Tara / Nara / To)",
    nameJa: "仮定・条件表現 (ば・たら・なら・と)",
    descVi: "Chuyển đổi linh hoạt giữa các thể điều kiện giả định, tự nhiên, kinh nghiệm và khuyên nhủ.",
    sampleTags: ["〜たら", "〜ば", "〜なら", "〜と", "〜ても"],
    icon: GitBranch,
    color: "border-emerald-500/40 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
    badgeVariant: "matcha",
  },
  {
    id: "giving_receiving",
    nameVi: "Cho Nhận & Nhờ Vả Lịch Sự",
    nameJa: "授受表現・依頼表現",
    descVi: "Đổi góc nhìn hành động: 〜てくれる ↔ 〜てもらう, 〜ていただく, nhờ vả lịch sự.",
    sampleTags: ["〜てもらう", "〜てくれる", "〜ていただく", "〜てあげる"],
    icon: HeartHandshake,
    color: "border-sky-500/40 bg-sky-500/10 text-sky-600 dark:text-sky-400",
    badgeVariant: "fuji",
  },
  {
    id: "advanced_modals",
    nameVi: "Mẫu Câu N3 - N2 Nâng Cao",
    nameJa: "N3/N2重要文型・ニュアンス",
    descVi: "Khả năng, đạo đức/hoàn cảnh, phán đoán chắc chắn, khẩu ngữ phê bình.",
    sampleTags: ["〜わけにはいかない", "〜ざるを得ない", "〜に違いない", "〜っこない", "〜気味", "〜っぽい"],
    icon: Zap,
    color: "border-purple-500/40 bg-purple-500/10 text-purple-600 dark:text-purple-400",
    badgeVariant: "fuji",
  },
  {
    id: "keigo",
    nameVi: "Kính Ngữ & Lịch Sự Doanh Nghiệp",
    nameJa: "敬語・尊敬・謙譲変換",
    descVi: "Đổi câu thường sang Tôn kính ngữ (お〜になる, いらっしゃる) / Khiêm nhường ngữ (お〜する, 伺う, 拝見する).",
    sampleTags: ["お〜になる", "お〜する", "いらっしゃる", "伺う", "拝見する", "ご存知"],
    icon: Crown,
    color: "border-indigo-500/40 bg-indigo-500/10 text-indigo-600 dark:text-indigo-400",
    badgeVariant: "sakura",
  },
];

interface TransformationFilterModalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedCategories: string[];
  onChange: (categories: string[]) => void;
  customKeywords?: string;
  onChangeCustomKeywords?: (keywords: string) => void;
}

export const TransformationFilterModal: React.FC<TransformationFilterModalProps> = ({
  isOpen,
  onClose,
  selectedCategories,
  onChange,
  customKeywords = "",
  onChangeCustomKeywords,
}) => {
  const [search, setSearch] = useState("");
  const [tempSelected, setTempSelected] = useState<string[]>(selectedCategories);

  // Sync state on open
  React.useEffect(() => {
    if (isOpen) {
      setTempSelected(selectedCategories);
      setSearch("");
    }
  }, [isOpen, selectedCategories]);

  // Is unrestricted random mode active? (empty or explicitly includes 'all' or all items checked)
  const isAllSelected = tempSelected.length === 0 || tempSelected.includes("all");

  const filteredOptions = useMemo(() => {
    if (!search.trim()) return TRANSFORMATION_CATEGORY_OPTIONS;
    const q = search.toLowerCase();
    return TRANSFORMATION_CATEGORY_OPTIONS.filter(
      (opt) =>
        opt.nameVi.toLowerCase().includes(q) ||
        opt.nameJa.toLowerCase().includes(q) ||
        opt.descVi.toLowerCase().includes(q) ||
        opt.sampleTags.some((tag) => tag.toLowerCase().includes(q))
    );
  }, [search]);

  const handleToggle = (id: string) => {
    soundFX.playFurin();
    if (customKeywords) {
      onChangeCustomKeywords?.("");
    }
    if (isAllSelected) {
      // If was random, switch to specifically selecting just this item
      setTempSelected([id]);
      return;
    }

    if (tempSelected.includes(id)) {
      const next = tempSelected.filter((c) => c !== id);
      // If none selected, return to random all mode
      setTempSelected(next.length === 0 ? [] : next);
    } else {
      setTempSelected([...tempSelected.filter((c) => c !== "all"), id]);
    }
  };

  const handleSelectAll = () => {
    soundFX.playFurin();
    setTempSelected([]);
  };

  const handleClear = () => {
    soundFX.playFurin();
    setTempSelected([]);
    onChangeCustomKeywords?.("");
  };

  const handleSave = () => {
    soundFX.playTaiko();
    onChange(tempSelected.length === 0 ? [] : tempSelected);
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="🎯 Chuyên Đề Biến Đổi Ngữ Pháp"
      description="Chọn nhóm cấu trúc bạn muốn tập trung luyện phản xạ, hoặc tự do nhập từ khóa ngữ pháp để AI tạo bài tập."
      className="max-w-2xl"
    >
      <div className="space-y-4 pt-1 pb-2">
        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Tìm cấu trúc ngữ pháp (bị động, thể ngắn, điều kiện, kính ngữ...)..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 text-sm rounded-xl bg-card border border-border focus:outline-none focus:ring-2 focus:ring-primary/40 transition-all placeholder:text-muted-foreground/60"
          />
        </div>

        {/* HERO CARD: Ngẫu Nhiên Toàn Diện (Random Mode) + Custom Keyword Box */}
        {!search && (
          <div
            className={cn(
              "relative p-4 rounded-2xl border-2 transition-all overflow-hidden space-y-3",
              isAllSelected
                ? "bg-gradient-to-r from-primary/15 via-primary/10 to-indigo-500/15 border-primary shadow-md ring-2 ring-primary/20"
                : "bg-muted/40 border-border hover:border-primary/50 hover:bg-muted/60"
            )}
          >
            <div
              onClick={handleSelectAll}
              className="flex items-start justify-between gap-3 cursor-pointer"
            >
              <div className="flex items-center gap-3">
                <div
                  className={cn(
                    "p-2.5 rounded-xl border flex items-center justify-center transition-all",
                    isAllSelected
                      ? "bg-primary text-primary-foreground shadow-sm"
                      : "bg-background border-border text-muted-foreground"
                  )}
                >
                  <Shuffle className="h-5 w-5 animate-pulse" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-foreground">🎲 Ngẫu Nhiên Toàn Diện</span>
                    <Badge variant="sakura" className="text-[10px] uppercase font-mono font-bold">
                      75+ Dạng Câu
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Hệ thống sẽ bốc ngẫu nhiên không lặp lại từ tất cả các chuyên đề (Thể ngắn, Bị động, Điều kiện, Kính ngữ...).
                  </p>
                </div>
              </div>
              <div
                className={cn(
                  "w-5 h-5 rounded-full border flex items-center justify-center transition-all shrink-0 mt-1",
                  isAllSelected
                    ? "bg-primary border-primary text-primary-foreground"
                    : "border-muted-foreground/40 bg-background"
                )}
              >
                {isAllSelected && <Check className="h-3 w-3 stroke-[3]" />}
              </div>
            </div>

            {/* Custom Keyword Input Field */}
            <div className="pt-3 border-t border-border/60 space-y-2">
              <div className="flex items-center justify-between gap-2">
                <label className="text-[11px] font-bold text-foreground flex items-center gap-1.5">
                  <Sparkles className="h-3.5 w-3.5 text-amber-500" />
                  <span>Nhập từ khóa / cấu trúc ngữ pháp tùy thích (Để trống = Ngẫu nhiên 100%):</span>
                </label>
                {customKeywords && (
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onChangeCustomKeywords?.("");
                    }}
                    className="text-[10px] font-bold text-muted-foreground hover:text-rose-500 transition-colors"
                  >
                    ✕ Xóa từ khóa
                  </button>
                )}
              </div>

              <div className="relative">
                <input
                  type="text"
                  value={customKeywords || ""}
                  onChange={(e) => {
                    if (tempSelected.length > 0) {
                      setTempSelected([]); // Switch to custom mode
                    }
                    onChangeCustomKeywords?.(e.target.value);
                  }}
                  onClick={(e) => e.stopPropagation()}
                  placeholder="Ví dụ: bị động, sai khiến, thể ngắn 〜ちゃう, cho nhận, 〜わけにはいかない..."
                  className="w-full px-3.5 py-2.5 rounded-xl bg-card border border-border text-xs text-foreground placeholder:text-muted-foreground/60 focus:outline-hidden focus:ring-1 focus:ring-primary font-medium shadow-2xs"
                />
              </div>

              {/* Quick Suggestion Chips */}
              <div className="flex flex-wrap items-center gap-1.5 pt-1">
                <span className="text-[10px] font-bold text-muted-foreground">Gợi ý nhanh:</span>
                {[
                  "🛡️ Bị động 〜られる",
                  "⚡ Sai khiến 〜させる",
                  "🗣️ Khẩu ngữ 〜ちゃう",
                  "🤝 Cho nhận 〜てもらう",
                  "🌿 Điều kiện 〜たら",
                  "👑 Kính ngữ お〜になる",
                ].map((chip, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      soundFX.playFurin();
                      setTempSelected([]);
                      onChangeCustomKeywords?.(chip);
                    }}
                    className="px-2 py-0.5 rounded-lg text-[10px] font-medium bg-muted/80 hover:bg-primary/10 hover:text-primary border border-border/60 transition-all text-foreground/80 cursor-pointer"
                  >
                    {chip}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* List of Specific Categories */}
        <div className="space-y-2 max-h-[340px] overflow-y-auto pr-1">
          <div className="flex items-center justify-between px-1 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            <span>Hoặc chọn chuyên đề mục tiêu ({TRANSFORMATION_CATEGORY_OPTIONS.length}):</span>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={handleSelectAll}
                className="text-[11px] font-bold text-primary hover:underline"
              >
                Chọn tất cả
              </button>
              <span>•</span>
              <button
                type="button"
                onClick={handleClear}
                className="text-[11px] font-bold text-muted-foreground hover:text-foreground hover:underline"
              >
                Xóa lọc
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
            {filteredOptions.map((opt) => {
              const isSelected = !isAllSelected && tempSelected.includes(opt.id);
              const Icon = opt.icon;
              return (
                <div
                  key={opt.id}
                  onClick={() => handleToggle(opt.id)}
                  className={cn(
                    "relative p-3 rounded-2xl border transition-all cursor-pointer flex flex-col justify-between gap-2 select-none",
                    isSelected
                      ? "bg-primary/10 border-primary shadow-xs ring-1 ring-primary/20"
                      : "bg-card hover:bg-muted/40 border-border/80 hover:border-primary/40"
                  )}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2.5">
                      <div className={cn("p-2 rounded-xl border shrink-0", opt.color)}>
                        <Icon className="h-4 w-4" />
                      </div>
                      <div>
                        <div className="text-xs font-bold text-foreground leading-tight flex items-center gap-1.5 flex-wrap">
                          <span>{opt.nameVi}</span>
                        </div>
                        <span className="text-[10px] font-jp font-medium text-muted-foreground block mt-0.5">
                          {opt.nameJa}
                        </span>
                      </div>
                    </div>

                    <div
                      className={cn(
                        "w-4 h-4 rounded-md border flex items-center justify-center transition-all shrink-0 mt-0.5",
                        isSelected
                          ? "bg-primary border-primary text-primary-foreground"
                          : "border-muted-foreground/40 bg-background"
                      )}
                    >
                      {isSelected && <Check className="h-2.5 w-2.5 stroke-[3]" />}
                    </div>
                  </div>

                  <p className="text-[11px] text-muted-foreground/90 line-clamp-2 leading-relaxed">
                    {opt.descVi}
                  </p>

                  <div className="flex items-center gap-1 flex-wrap pt-0.5">
                    {opt.sampleTags.map((tag, tIdx) => (
                      <span
                        key={tIdx}
                        className="px-1.5 py-0.5 rounded-md bg-muted text-[10px] font-medium text-muted-foreground font-jp"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between pt-3 border-t border-border mt-3">
          <div className="text-xs text-muted-foreground font-medium flex items-center gap-1.5">
            <Layers className="h-3.5 w-3.5 text-primary" />
            <span>
              Đang chọn:{" "}
              <strong className="text-foreground">
                {isAllSelected
                  ? "Ngẫu Nhiên Toàn Diện (Tất Cả)"
                  : `${tempSelected.length} chuyên đề`}
              </strong>
            </span>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={onClose}>
              Hủy
            </Button>
            <Button variant="sakura" size="sm" onClick={handleSave} className="gap-1.5 font-bold">
              <Check className="h-4 w-4" />
              <span>Áp Dụng</span>
            </Button>
          </div>
        </div>
      </div>
    </Modal>
  );
};
