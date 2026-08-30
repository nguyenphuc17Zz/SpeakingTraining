"use client";

import React, { useState, useMemo } from "react";
import { Modal } from "@/components/ui/modal";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Compass,
  Check,
  RotateCcw,
  Sparkles,
  Building2,
  Briefcase,
  AlertTriangle,
  Users,
  UtensilsCrossed,
  Search,
} from "lucide-react";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

export interface ContextCategoryOption {
  id: string;
  nameVi: string;
  nameJa: string;
  icon: any;
  badgeVariant: "sakura" | "matcha" | "fuji" | "kintsugi" | "sumi";
  colorClass: string;
  descVi: string;
  sampleTags: string[];
}

export const CONTEXT_CATEGORIES: ContextCategoryOption[] = [
  {
    id: "workplace",
    nameVi: "Công Sở & Báo Cáo Hou-Ren-So",
    nameJa: "職場・報連相",
    icon: Building2,
    badgeVariant: "sakura",
    colorClass: "text-rose-600 dark:text-rose-400 bg-rose-500/10 border-rose-500/30",
    descVi: "Sếp giao việc, báo cáo tiến độ 80%, xin phép về sớm, nhờ đồng nghiệp giúp...",
    sampleTags: ["Sếp giao việc", "Báo cáo tiến độ", "Xin về sớm", "Nhờ đồng nghiệp", "Bàn giao việc"],
  },
  {
    id: "business_client",
    nameVi: "Khách Hàng & Đàm Phán Thương Mại",
    nameJa: "顧客対応・ビジネス",
    icon: Briefcase,
    badgeVariant: "matcha",
    colorClass: "text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 border-emerald-500/30",
    descVi: "Tiếp đón khách hàng, hẹn lịch họp 14h, trao đổi danh thiếp, chào tiễn đối tác...",
    sampleTags: ["Tiếp khách", "Hẹn lịch họp", "Trao đổi danh thiếp", "Báo vắng mặt", "Gửi báo giá"],
  },
  {
    id: "apology_emergency",
    nameVi: "Trễ Tàu, Xin Lỗi & Xử Lý Sự Cố",
    nameJa: "遅延・お詫び・トラブル",
    icon: AlertTriangle,
    badgeVariant: "fuji",
    colorClass: "text-amber-600 dark:text-amber-400 bg-amber-500/10 border-amber-500/30",
    descVi: "Báo trễ tàu tín hiệu, thành thật xin lỗi sửa báo giá, sự cố đăng nhập máy tính...",
    sampleTags: ["Trễ tàu 15p", "Sửa báo giá", "Lỗi đăng nhập", "Tra cứu đơn hàng", "Xin lỗi chân thành"],
  },
  {
    id: "social_casual",
    nameVi: "Bạn Bè & Giao Tiếp Đời Thường",
    nameJa: "日常会話・友人関係",
    icon: Users,
    badgeVariant: "kintsugi",
    colorClass: "text-indigo-600 dark:text-indigo-400 bg-indigo-500/10 border-indigo-500/30",
    descVi: "Rủ đi quán nhậu, từ chối khéo vì có hẹn trước, cảm ơn lời khen phát âm, sinh nhật...",
    sampleTags: ["Rủ nhậu tối", "Từ chối khéo", "Cảm ơn lời khen", "Sinh nhật bạn", "Leo núi cuối tuần"],
  },
  {
    id: "service_dining",
    nameVi: "Nhà Hàng, Mua Sắm & Dịch Vụ",
    nameJa: "飲食店・ショッピング・接客",
    icon: UtensilsCrossed,
    badgeVariant: "sumi",
    colorClass: "text-teal-600 dark:text-teal-400 bg-teal-500/10 border-teal-500/30",
    descVi: "Báo bàn 2 người không hút thuốc, thử áo sơ mi size L, gọi mì Ramen, trả thẻ tín dụng...",
    sampleTags: ["Bàn 2 người", "Thử áo size L", "Gọi món Ramen", "Trả thẻ tín dụng", "Xin hóa đơn"],
  },
];

interface Props {
  isOpen: boolean;
  onClose: () => void;
  selectedCategories: string[];
  onChange: (categories: string[]) => void;
  customKeywords?: string;
  onChangeCustomKeywords?: (keywords: string) => void;
}

export function ContextFilterModal({
  isOpen,
  onClose,
  selectedCategories,
  onChange,
  customKeywords = "",
  onChangeCustomKeywords,
}: Props) {
  const [tempSelected, setTempSelected] = useState<string[]>(selectedCategories);
  const [search, setSearch] = useState("");

  // Sync state on open
  React.useEffect(() => {
    setTempSelected(selectedCategories);
  }, [selectedCategories, isOpen]);

  const isAllSelected = tempSelected.length === 0 || tempSelected.includes("all");

  const filteredCategories = useMemo(() => {
    if (!search.trim()) return CONTEXT_CATEGORIES;
    const q = search.toLowerCase();
    return CONTEXT_CATEGORIES.filter(
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
      setTempSelected([id]);
      return;
    }

    if (tempSelected.includes(id)) {
      const next = tempSelected.filter((c) => c !== id);
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
      title="Bối Cảnh Giao Tiếp • 状況選択"
      description="Tùy chỉnh các bối cảnh và vai vế giao tiếp mục tiêu hoặc tự do nhập từ khóa tình huống để AI tạo bài tập."
      className="max-w-2xl"
    >
      <div className="space-y-4 pt-1 pb-2">

        {/* Quick Search Bar */}
        <div className="relative">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Tìm kiếm bối cảnh (ví dụ: Sếp, trễ tàu, khách hàng, nhà hàng...)"
            className="w-full pl-10 pr-4 py-2.5 rounded-2xl bg-card border border-border text-xs md:text-sm text-foreground placeholder:text-muted-foreground focus:outline-hidden focus:ring-2 focus:ring-primary/30"
          />
        </div>

        {/* Top Hero Option: Random Across All Scenarios + Custom Keyword Box */}
        <div
          className={cn(
            "p-4 md:p-5 rounded-3xl border transition-all relative overflow-hidden washi-texture space-y-3",
            isAllSelected
              ? "border-primary bg-primary/10 ring-2 ring-primary/30 shadow-md shadow-primary/10"
              : "border-border/80 bg-card hover:border-primary/40 hover:bg-card/90"
          )}
        >
          <div
            onClick={handleSelectAll}
            className="flex items-center justify-between gap-3 cursor-pointer group"
          >
            <div className="flex items-center gap-3.5">
              <div
                className={cn(
                  "h-11 w-11 rounded-2xl flex items-center justify-center border shrink-0 transition-transform group-hover:scale-105",
                  isAllSelected
                    ? "bg-primary text-primary-foreground border-primary"
                    : "bg-primary/10 text-primary border-primary/20"
                )}
              >
                <Compass className="h-6 w-6 animate-spin-slow" />
              </div>
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <span className="font-black text-sm md:text-base text-foreground font-jp">
                    🎲 Ngẫu Nhiên Toàn Diện (60+ Tình Huống)
                  </span>
                  <Badge variant="sakura" size="sm">
                    Khuyên Dùng
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground">
                  Xáo trộn liên tục mọi tình huống từ công sở, đối tác, xin lỗi khẩn đến giao tiếp bạn bè và nhà hàng
                </p>
              </div>
            </div>

            <div
              className={cn(
                "h-6 w-6 rounded-full border-2 flex items-center justify-center shrink-0 transition-all",
                isAllSelected
                  ? "border-primary bg-primary text-primary-foreground shadow-xs"
                  : "border-muted-foreground/30 bg-background"
              )}
            >
              {isAllSelected && <Check className="h-3.5 w-3.5 stroke-[3]" />}
            </div>
          </div>

          {/* Custom Keyword Input Field */}
          <div className="pt-3 border-t border-border/60 space-y-2">
            <div className="flex items-center justify-between gap-2">
              <label className="text-[11px] font-bold text-foreground flex items-center gap-1.5">
                <Sparkles className="h-3.5 w-3.5 text-amber-500" />
                <span>Nhập từ khóa / tình huống tùy thích (Để trống = Ngẫu nhiên 100%):</span>
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
                placeholder="Ví dụ: sếp mắng, trễ tàu tuyết rơi, từ chối nhậu, đòi nợ, xin nghỉ việc..."
                className="w-full px-3.5 py-2.5 rounded-xl bg-card border border-border text-xs text-foreground placeholder:text-muted-foreground/60 focus:outline-hidden focus:ring-1 focus:ring-primary font-medium shadow-2xs"
              />
            </div>

            {/* Quick Suggestion Chips */}
            <div className="flex flex-wrap items-center gap-1.5 pt-1">
              <span className="text-[10px] font-bold text-muted-foreground">Gợi ý nhanh:</span>
              {[
                "👔 Sếp giao việc gấp",
                "🚨 Trễ tàu tín hiệu",
                "🤝 Đàm phán báo giá",
                "🍻 Từ chối đi nhậu",
                "🏪 Mua sắm thử áo",
                "🙇 Thành thật xin lỗi",
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

        {/* Specific Category Grid */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs font-bold text-muted-foreground px-1">
            <span>Hoặc chọn từng nhóm chuyên sâu:</span>
            {!isAllSelected && (
              <span className="text-primary">Đã chọn: {tempSelected.length} nhóm</span>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-[360px] overflow-y-auto pr-1">
            {filteredCategories.map((cat) => {
              const isSelected = !isAllSelected && tempSelected.includes(cat.id);
              const Icon = cat.icon;

              return (
                <div
                  key={cat.id}
                  onClick={() => handleToggle(cat.id)}
                  className={cn(
                    "p-3.5 rounded-2xl border transition-all cursor-pointer flex flex-col justify-between space-y-2.5 washi-texture group relative",
                    isSelected
                      ? "border-primary bg-primary/10 ring-2 ring-primary/25 shadow-xs"
                      : "border-border/80 bg-card hover:border-primary/40 hover:bg-card/90"
                  )}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2.5">
                      <div
                        className={cn(
                          "h-9 w-9 rounded-xl border flex items-center justify-center shrink-0 transition-transform group-hover:scale-105",
                          cat.colorClass
                        )}
                      >
                        <Icon className="h-4 w-4" />
                      </div>
                      <div className="space-y-0.5">
                        <div className="flex items-center gap-1.5">
                          <span className="font-black text-xs md:text-sm text-foreground font-jp leading-tight">
                            {cat.nameVi}
                          </span>
                        </div>
                        <span className="text-[10px] font-mono font-bold text-muted-foreground">
                          {cat.nameJa}
                        </span>
                      </div>
                    </div>

                    <div
                      className={cn(
                        "h-5 w-5 rounded-full border-2 flex items-center justify-center shrink-0 transition-all mt-0.5",
                        isSelected
                          ? "border-primary bg-primary text-primary-foreground shadow-2xs"
                          : "border-muted-foreground/30 bg-background"
                      )}
                    >
                      {isSelected && <Check className="h-3 w-3 stroke-[3]" />}
                    </div>
                  </div>

                  <p className="text-[11px] text-muted-foreground leading-snug line-clamp-2">
                    {cat.descVi}
                  </p>

                  {/* Sample Tags Preview */}
                  <div className="flex flex-wrap gap-1 pt-1 border-t border-border/40">
                    {cat.sampleTags.slice(0, 3).map((tag, idx) => (
                      <span
                        key={idx}
                        className="px-1.5 py-0.5 rounded-md bg-muted/60 text-[10px] font-medium text-foreground/80 font-jp"
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

        {/* Action Buttons Strip */}
        <div className="flex items-center justify-between gap-3 pt-3 border-t border-border">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={handleClear}
            className="text-xs font-bold text-muted-foreground gap-1.5"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            <span>Mặc định (Tất cả)</span>
          </Button>

          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onClose}
              className="text-xs font-bold"
            >
              Hủy
            </Button>
            <Button
              type="button"
              variant="akane"
              size="sm"
              onClick={handleSave}
              className="text-xs font-bold gap-1.5 px-4"
            >
              <Sparkles className="h-3.5 w-3.5" />
              <span>Áp Dụng ({isAllSelected ? "Tất cả" : `${tempSelected.length} nhóm`})</span>
            </Button>
          </div>
        </div>
      </div>
    </Modal>
  );
}
