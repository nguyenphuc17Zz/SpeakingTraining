"use client";

import React, { useState } from "react";
import {
  X,
  Search,
  Check,
  RotateCcw,
  Sparkles,
  Crown,
  UserCheck,
  Settings2,
  Briefcase,
  Layers,
} from "lucide-react";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

export interface KeigoCategory {
  id: string;
  name: string;
  nameJa: string;
  badge: string;
  desc: string;
  color: string;
  icon: any;
  examples: Array<{ source: string; target: string; reading: string; label: string }>;
}

export const KEIGO_CATEGORIES: KeigoCategory[] = [
  {
    id: "sonkeigo_irregular",
    name: "Tôn Kính Ngữ Bất Quy Tắc (Sonkeigo)",
    nameJa: "尊敬語・不規則動詞",
    badge: "Sếp / Khách",
    desc: "Nâng cao vị thế đối phương, khách hàng, cấp trên: ăn/uống (召し上がる), đi/đến (いらっしゃる), nói (おっしゃる), xem (ご覧になる)...",
    color: "from-amber-500/20 via-amber-500/10 to-transparent border-amber-500/30 text-amber-600 dark:text-amber-400",
    icon: Crown,
    examples: [
      { source: "食べる", target: "召し上がる", reading: "めしあがる", label: "ăn / uống" },
      { source: "行く/来る", target: "いらっしゃる", reading: "いらっしゃる", label: "đi / đến" },
      { source: "言う", target: "おっしゃる", reading: "おっしゃる", label: "nói" },
      { source: "見る", target: "ご覧になる", reading: "ごらんになる", label: "xem / nhìn" },
    ],
  },
  {
    id: "kenjougo_irregular",
    name: "Khiêm Nhường Ngữ Bất Quy Tắc (Kenjougo)",
    nameJa: "謙譲語・不規則動詞",
    badge: "Bản Thân / Bên Mình",
    desc: "Hạ mình khiêm tốn khi nói về hành động của bản thân hoặc công ty mình: ăn/nhận (いただく), đi/đến (参る/伺う), nói (申す), xem (拝見する)...",
    color: "from-indigo-500/20 via-indigo-500/10 to-transparent border-indigo-500/30 text-indigo-600 dark:text-indigo-400",
    icon: UserCheck,
    examples: [
      { source: "食べる/もらう", target: "いただく", reading: "いただく", label: "ăn / nhận" },
      { source: "行く/来る", target: "参る / 伺う", reading: "まいる / うかがう", label: "đi / đến" },
      { source: "言う", target: "申す / 申し上げる", reading: "もうす", label: "nói / tên là" },
      { source: "見る", target: "拝見する", reading: "はいけんする", label: "xem qua" },
    ],
  },
  {
    id: "rule_based",
    name: "Kính Ngữ Theo Quy Tắc (お〜になる / お〜いたす)",
    nameJa: "規則的敬語パターン",
    badge: "Quy Tắc",
    desc: "Biến đổi động từ thường theo khuôn mẫu: Tôn kính [お + V + になる] (chờ, mang) ↔ Khiêm nhường [お/ご + V + いたす] (liên lạc, hướng dẫn, giao hàng)...",
    color: "from-teal-500/20 via-teal-500/10 to-transparent border-teal-500/30 text-teal-600 dark:text-teal-400",
    icon: Settings2,
    examples: [
      { source: "待つ", target: "お待ちになる", reading: "おまちになる", label: "đợi (Tôn kính)" },
      { source: "連絡する", target: "ご連絡いたす", reading: "ごれんらくいたす", label: "liên lạc (Khiêm nhường)" },
      { source: "案内する", target: "ご案内いたす", reading: "ごあんないいたす", label: "dẫn đường (Khiêm nhường)" },
      { source: "持つ", target: "お持ちする", reading: "おもちする", label: "cầm giúp (Khiêm nhường)" },
    ],
  },
  {
    id: "business_words",
    name: "Đại Từ, Danh Từ & Từ Thương Mại",
    nameJa: "ビジネス敬語・名詞代名詞",
    badge: "Thương Mại",
    desc: "Từ xưng hô và thuật ngữ văn phòng chuẩn mực: người (方), ai (どなた), công ty mình (弊社), công ty khách (貴社/御社), hôm nay (本日), được (よろしい)...",
    color: "from-blue-500/20 via-blue-500/10 to-transparent border-blue-500/30 text-blue-600 dark:text-blue-400",
    icon: Briefcase,
    examples: [
      { source: "人", target: "方", reading: "かた", label: "người / vị" },
      { source: "会社 (mình)", target: "弊社", reading: "へいしゃ", label: "công ty chúng tôi" },
      { source: "会社 (khách)", target: "御社 / 貴社", reading: "おんしゃ", label: "quý công ty" },
      { source: "今日", target: "本日", reading: "ほんじつ", label: "hôm nay" },
    ],
  },
];

const SUGGESTION_CHIPS = [
  "🍽️ Ăn uống & Mời trà",
  "🚶 Đi lại & Thăm gặp",
  "📄 Xem tài liệu & Đề xuất",
  "🗣️ Nói chuyện & Giới thiệu",
  "🤝 Công ty mình vs Công ty khách",
  "🏢 Văn phòng & Hou-Ren-So",
];

interface KeigoFilterModalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedCategories: string[];
  onChange: (categories: string[]) => void;
  customKeywords?: string;
  onChangeCustomKeywords?: (val: string) => void;
}

export function KeigoFilterModal({
  isOpen,
  onClose,
  selectedCategories,
  onChange,
  customKeywords = "",
  onChangeCustomKeywords,
}: KeigoFilterModalProps) {
  const [searchQuery, setSearchQuery] = useState("");

  if (!isOpen) return null;

  const isAll = selectedCategories.length === 0;

  const filteredCategories = KEIGO_CATEGORIES.filter((cat) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      cat.name.toLowerCase().includes(q) ||
      cat.nameJa.toLowerCase().includes(q) ||
      cat.desc.toLowerCase().includes(q) ||
      cat.badge.toLowerCase().includes(q) ||
      cat.examples.some(
        (ex) =>
          ex.source.toLowerCase().includes(q) ||
          ex.target.toLowerCase().includes(q) ||
          ex.reading.toLowerCase().includes(q) ||
          ex.label.toLowerCase().includes(q)
      )
    );
  });

  const toggleCategory = (id: string) => {
    soundFX.playFurin();
    if (selectedCategories.includes(id)) {
      onChange(selectedCategories.filter((c) => c !== id));
    } else {
      onChange([...selectedCategories, id]);
    }
  };

  const handleSelectAll = () => {
    soundFX.playFurin();
    onChange([]);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-md animate-in fade-in duration-200">
      <div
        className="relative w-full max-w-4xl max-h-[90vh] flex flex-col rounded-3xl bg-card border border-border/80 shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border/60 bg-muted/20">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-600 dark:text-amber-400">
              <Crown className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-black text-foreground tracking-tight">
                  Tùy Chọn Chuyên Đề Kính Ngữ Phản Xạ
                </h3>
                <span className="text-xs font-bold font-jp px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
                  敬語カテゴリ
                </span>
              </div>
              <p className="text-xs text-muted-foreground font-medium">
                Tôn kính (Sonkei) ↔ Khiêm nhường (Kenjou) • Quy tắc お/ご〜いたす • Từ thương mại
              </p>
            </div>
          </div>
          <button
            onClick={() => {
              soundFX.playFurin();
              onClose();
            }}
            className="p-2 rounded-xl text-muted-foreground hover:text-foreground hover:bg-muted/60 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Search & Actions Bar */}
        <div className="px-6 py-3 border-b border-border/40 bg-muted/10 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="relative w-full sm:w-80">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Tìm kiếm dạng kính ngữ, từ gốc..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 rounded-xl bg-background border border-border/60 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-amber-500/40"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground text-xs"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            )}
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
            <button
              onClick={handleSelectAll}
              className={cn(
                "px-3 py-1.5 rounded-xl text-xs font-bold transition-all border flex items-center gap-1.5",
                isAll
                  ? "bg-amber-500 text-white border-amber-500 shadow-xs"
                  : "bg-background border-border/80 text-muted-foreground hover:text-foreground hover:bg-muted/40"
              )}
            >
              <Sparkles className="h-3.5 w-3.5" />
              Ngẫu nhiên toàn diện
            </button>
            {selectedCategories.length > 0 && (
              <button
                onClick={handleSelectAll}
                className="px-2.5 py-1.5 rounded-xl text-xs font-medium text-muted-foreground hover:text-foreground bg-muted/40 hover:bg-muted/80 transition-colors flex items-center gap-1"
                title="Bỏ chọn tất cả"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                Mặc định
              </button>
            )}
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4 max-h-[60vh]">
          {/* Top Hero: Random / Custom Keyword Generator */}
          <div
            onClick={handleSelectAll}
            className={cn(
              "p-4 rounded-2xl border transition-all cursor-pointer relative overflow-hidden",
              isAll
                ? "bg-gradient-to-br from-amber-500/20 via-amber-500/10 to-transparent border-amber-500/50 shadow-md ring-2 ring-amber-500/20"
                : "bg-muted/20 border-border/60 hover:border-amber-500/30 hover:bg-muted/30"
            )}
          >
            <div className="flex items-start justify-between gap-3 mb-2">
              <div className="flex items-center gap-2.5">
                <div
                  className={cn(
                    "p-2 rounded-xl border shrink-0",
                    isAll
                      ? "bg-amber-500 text-white border-amber-400"
                      : "bg-muted text-muted-foreground border-border"
                  )}
                >
                  <Sparkles className="h-4 w-4" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-extrabold text-sm text-foreground">
                      Ngẫu Nhiên Toàn Diện (80+ Cặp Kính Ngữ Thực Chiến)
                    </span>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20 font-jp">
                      全敬語ランダム
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Hệ thống sẽ xáo trộn ngẫu nhiên mọi dạng kính ngữ hoặc sinh theo từ khóa bạn nhập.
                  </p>
                </div>
              </div>
              {isAll && (
                <div className="p-1 rounded-full bg-amber-500 text-white shadow-xs shrink-0">
                  <Check className="h-3.5 w-3.5" />
                </div>
              )}
            </div>

            {/* Custom Keywords Input inside Random Option */}
            <div
              className="mt-3 pt-3 border-t border-border/40"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center gap-1.5 mb-1.5">
                <span className="text-[11px] font-bold text-foreground">
                  💡 Nhập từ khóa kính ngữ (Tùy chọn):
                </span>
                <span className="text-[10px] text-muted-foreground">
                  (Ví dụ: "ăn uống", "đi lại", "xem tài liệu", "xưng hô", "công sở"...)
                </span>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  placeholder="Gõ từ khóa kính ngữ muốn luyện... (Để trống để ngẫu nhiên 100%)"
                  value={customKeywords}
                  onChange={(e) => onChangeCustomKeywords?.(e.target.value)}
                  className="flex-1 px-3 py-1.5 rounded-xl bg-background/80 border border-border/80 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-amber-500/40"
                />
                {customKeywords && (
                  <button
                    type="button"
                    onClick={() => onChangeCustomKeywords?.("")}
                    className="px-2.5 py-1.5 rounded-xl bg-muted/60 hover:bg-muted text-[11px] font-semibold text-muted-foreground hover:text-foreground"
                  >
                    Xóa
                  </button>
                )}
              </div>

              {/* Quick suggestion chips */}
              <div className="flex items-center gap-1.5 mt-2 flex-wrap">
                <span className="text-[10px] text-muted-foreground font-semibold">Gợi ý nhanh:</span>
                {SUGGESTION_CHIPS.map((chip) => {
                  const keyword = chip.split(" ")[1] || chip;
                  const isActive = customKeywords.includes(keyword);
                  return (
                    <button
                      key={chip}
                      type="button"
                      onClick={() => {
                        soundFX.playFurin();
                        onChangeCustomKeywords?.(keyword);
                      }}
                      className={cn(
                        "text-[10px] font-bold px-2 py-0.5 rounded-lg border transition-all",
                        isActive
                          ? "bg-amber-500 text-white border-amber-500 shadow-2xs"
                          : "bg-muted/40 border-border/60 text-muted-foreground hover:text-foreground hover:bg-muted"
                      )}
                    >
                      {chip}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 pt-2">
            <span className="text-xs font-black uppercase tracking-wider text-muted-foreground">
              Hoặc Chọn Theo Chuyên Đề Kính Ngữ
            </span>
            <div className="flex-1 h-px bg-border/40" />
            <span className="text-[11px] font-semibold text-muted-foreground">
              {selectedCategories.length} đã chọn
            </span>
          </div>

          {/* Category Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
            {filteredCategories.map((cat) => {
              const isSelected = selectedCategories.includes(cat.id);
              const Icon = cat.icon;
              return (
                <div
                  key={cat.id}
                  onClick={() => toggleCategory(cat.id)}
                  className={cn(
                    "p-4 rounded-2xl border transition-all cursor-pointer flex flex-col justify-between group",
                    isSelected
                      ? `bg-gradient-to-br ${cat.color} shadow-sm ring-1.5 ring-primary/40`
                      : "bg-card border-border/60 hover:border-border hover:bg-muted/20"
                  )}
                >
                  <div>
                    <div className="flex items-start justify-between gap-2 mb-1.5">
                      <div className="flex items-center gap-2">
                        <div
                          className={cn(
                            "p-1.5 rounded-xl border shrink-0",
                            isSelected
                              ? "bg-background text-foreground border-border/80 shadow-2xs"
                              : "bg-muted text-muted-foreground border-border/40"
                          )}
                        >
                          <Icon className="h-4 w-4" />
                        </div>
                        <div>
                          <div className="flex items-center gap-1.5 flex-wrap">
                            <span className="font-extrabold text-xs text-foreground group-hover:text-primary transition-colors">
                              {cat.name}
                            </span>
                            <span className="text-[10px] font-bold font-jp text-muted-foreground">
                              {cat.nameJa}
                            </span>
                          </div>
                        </div>
                      </div>
                      <div
                        className={cn(
                          "w-5 h-5 rounded-lg border flex items-center justify-center transition-all shrink-0 mt-0.5",
                          isSelected
                            ? "bg-primary border-primary text-primary-foreground shadow-2xs"
                            : "border-border/80 bg-background/50 group-hover:border-primary/50"
                        )}
                      >
                        {isSelected && <Check className="h-3 w-3" />}
                      </div>
                    </div>

                    <p className="text-[11px] text-muted-foreground leading-relaxed line-clamp-2 mt-1">
                      {cat.desc}
                    </p>
                  </div>

                  {/* Examples */}
                  <div className="mt-3 pt-2.5 border-t border-border/40 flex flex-wrap gap-1.5">
                    {cat.examples.map((ex, idx) => (
                      <div
                        key={idx}
                        className="px-2 py-0.5 rounded-lg bg-background/80 border border-border/60 text-[10px] flex items-center gap-1 font-medium shadow-2xs"
                      >
                        <span className="text-muted-foreground">{ex.source} →</span>
                        <span className="font-bold font-jp text-primary">{ex.target}</span>
                        <span className="text-muted-foreground font-jp">({ex.reading})</span>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>

          {filteredCategories.length === 0 && (
            <div className="py-12 text-center text-muted-foreground space-y-2">
              <p className="text-sm font-semibold">Không tìm thấy chuyên đề kính ngữ phù hợp với "{searchQuery}"</p>
              <button
                onClick={() => setSearchQuery("")}
                className="text-xs text-primary font-bold hover:underline"
              >
                Xóa bộ lọc tìm kiếm
              </button>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-border/60 bg-muted/20">
          <div className="text-xs text-muted-foreground">
            {isAll ? (
              customKeywords.trim() ? (
                <span className="font-semibold text-amber-600 dark:text-amber-400">
                  💡 Đang lọc kính ngữ theo từ khóa: <strong className="font-black">"{customKeywords.trim()}"</strong>
                </span>
              ) : (
                <span className="font-semibold text-amber-600 dark:text-amber-400">
                  🎯 Đang chọn: <strong className="font-black">Ngẫu nhiên toàn diện (80+ cặp kính ngữ)</strong>
                </span>
              )
            ) : (
              <span>
                Đã chọn: <strong className="font-bold text-foreground">{selectedCategories.length}</strong> chuyên đề
              </span>
            )}
          </div>
          <button
            onClick={() => {
              soundFX.playFurin();
              onClose();
            }}
            className="px-6 py-2 rounded-2xl bg-primary text-primary-foreground font-bold text-xs shadow-md hover:bg-primary/90 hover:scale-[1.02] active:scale-[0.98] transition-all"
          >
            Áp Dụng & Luyện Tập
          </button>
        </div>
      </div>
    </div>
  );
}
