"use client";

import React, { useState, useMemo } from "react";
import {
  X,
  Search,
  Check,
  RotateCcw,
  Sparkles,
  Zap,
  Activity,
  Heart,
  Smile,
  MessageSquare,
  Briefcase,
  ShoppingBag,
  Layers,
  HelpCircle,
} from "lucide-react";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

export interface VocabCategory {
  id: string;
  name: string;
  nameJa: string;
  badge: string;
  desc: string;
  color: string;
  icon: any;
  examples: Array<{ ja: string; reading: string; vi: string; collocation?: string }>;
}

export const VOCAB_CATEGORIES: VocabCategory[] = [
  {
    id: "action_verbs",
    name: "Động Từ Hành Động & Đời Sống",
    nameJa: "行動・生活動詞",
    badge: "Thực Chiến",
    desc: "Các động từ chỉ hành động thường gặp: liên lạc, từ chối, dọn dẹp, nhờ vả, chuyển tàu, giao nhận...",
    color: "from-rose-500/20 via-rose-500/10 to-transparent border-rose-500/30 text-rose-600 dark:text-rose-400",
    icon: Activity,
    examples: [
      { ja: "連絡する", reading: "れんらくする", vi: "liên lạc", collocation: "連絡を取る (giữ liên lạc)" },
      { ja: "諦める", reading: "あきらめる", vi: "bỏ cuộc", collocation: "夢を諦めない (ko từ bỏ ước mơ)" },
      { ja: "断る", reading: "ことわる", vi: "từ chối", collocation: "誘いを断る (từ chối lời mời)" },
      { ja: "片付ける", reading: "かたづける", vi: "dọn dẹp", collocation: "部屋を片付ける (dọn phòng)" },
    ],
  },
  {
    id: "emotions_adj",
    name: "Tính Từ & Cảm Xúc, Đánh Giá",
    nameJa: "感情・評価形容詞",
    badge: "Biểu Cảm",
    desc: "Tính từ đắt giá diễn đạt tâm trạng, cảm xúc, đánh giá: nhớ nhung, tiếc nuối, phiền phức, đáng ngờ, tươi mới...",
    color: "from-pink-500/20 via-pink-500/10 to-transparent border-pink-500/30 text-pink-600 dark:text-pink-400",
    icon: Heart,
    examples: [
      { ja: "懐かしい", reading: "なつかしい", vi: "nhớ nhung / hoài niệm", collocation: "懐かしい思い出 (kỷ niệm xưa)" },
      { ja: "悔しい", reading: "くやしい", vi: "tiếc nuối / cay cú", collocation: "悔しい思いをする (thấy cay cú)" },
      { ja: "面倒くさい", reading: "めんどうくさい", vi: "phiền phức / ngại làm", collocation: "手続きが面倒くさい (thủ tục phiền)" },
      { ja: "怪しい", reading: "あやしい", vi: "khả nghi / đáng ngờ", collocation: "怪しい人物 (người khả nghi)" },
    ],
  },
  {
    id: "adverbs_mimetic",
    name: "Phó Từ & Từ Tượng Thanh / Tượng Hình",
    nameJa: "オノマトペ・副詞",
    badge: "Văn Nói Bản Xứ",
    desc: "Các từ tượng thanh, tượng hình và phó từ tự nhiên: lưu loát, sát nút, lỡ đãng, sảng khoái, cất công, quả nhiên...",
    color: "from-amber-500/20 via-amber-500/10 to-transparent border-amber-500/30 text-amber-600 dark:text-amber-400",
    icon: MessageSquare,
    examples: [
      { ja: "ぺらぺら", reading: "ぺらぺら", vi: "lưu loát / trôi chảy", collocation: "日本語がぺらぺら (bắn tiếng Nhật)" },
      { ja: "ぎりぎり", reading: "ぎりぎり", vi: "sát nút / suýt soát", collocation: "ぎりぎり間に合う (kịp sát nút)" },
      { ja: "うっかり", reading: "うっかり", vi: "lỡ đễnh / bất cẩn", collocation: "うっかり忘れる (lỡ quên bẵng)" },
      { ja: "すっきり", reading: "すっきり", vi: "sảng khoái / nhẹ nhõm", collocation: "気分がすっきり (thấy sảng khoái)" },
    ],
  },
  {
    id: "workplace_biz",
    name: "Công Sở, Thương Mại & Hou-Ren-So",
    nameJa: "ビジネス・報連相",
    badge: "Doanh Nghiệp",
    desc: "Từ vựng then chốt trong văn phòng Nhật: tài liệu, hạn giao việc, phụ trách, xem xét, báo giá, hợp đồng...",
    color: "from-indigo-500/20 via-indigo-500/10 to-transparent border-indigo-500/30 text-indigo-600 dark:text-indigo-400",
    icon: Briefcase,
    examples: [
      { ja: "書類", reading: "しょるい", vi: "tài liệu / hồ sơ", collocation: "書類を提出する (nộp tài liệu)" },
      { ja: "納期", reading: "のうき", vi: "hạn giao hàng / deadline", collocation: "納期を守る (đảm bảo đúng hạn)" },
      { ja: "担当", reading: "たんとう", vi: "phụ trách / đảm nhiệm", collocation: "案件を担当する (phụ trách việc)" },
      { ja: "見積もり", reading: "みつもり", vi: "bản báo giá", collocation: "見積もりを出す (lập báo giá)" },
    ],
  },
  {
    id: "daily_life",
    name: "Sinh Hoạt, Mua Sắm & Dịch Vụ",
    nameJa: "日常生活・接客",
    badge: "Đời Thường",
    desc: "Từ vựng thiết yếu khi đi nhà hàng, siêu thị, du lịch, đi tàu: tính tiền, giảm giá, đặt bàn, hóa đơn, chuyến tàu cuối...",
    color: "from-emerald-500/20 via-emerald-500/10 to-transparent border-emerald-500/30 text-emerald-600 dark:text-emerald-400",
    icon: ShoppingBag,
    examples: [
      { ja: "お会計", reading: "おかいけい", vi: "thanh toán / tính tiền", collocation: "お会計をお願いする (gọi tính tiền)" },
      { ja: "割引", reading: "わりびき", vi: "giảm giá / chiết khấu", collocation: "割引クーポン (mã giảm giá)" },
      { ja: "領収書", reading: "りょうしゅうしょ", vi: "hóa đơn đỏ", collocation: "領収書をもらう (xin hóa đơn đỏ)" },
      { ja: "終電", reading: "しゅうでん", vi: "chuyến tàu cuối", collocation: "終電を逃す (lỡ chuyến tàu cuối)" },
    ],
  },
];

const SUGGESTION_CHIPS = [
  "🍜 Ẩm thực & Món ăn",
  "💻 Công nghệ & IT",
  "✈️ Du lịch & Sân bay",
  "👔 Phỏng vấn & Xin việc",
  "🍻 Quán nhậu & Bạn bè",
  "🛍️ Mua sắm & Thời trang",
];

interface VocabFilterModalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedCategories: string[];
  onChange: (categories: string[]) => void;
  customKeywords?: string;
  onChangeCustomKeywords?: (val: string) => void;
}

export function VocabFilterModal({
  isOpen,
  onClose,
  selectedCategories,
  onChange,
  customKeywords = "",
  onChangeCustomKeywords,
}: VocabFilterModalProps) {
  const [searchQuery, setSearchQuery] = useState("");

  if (!isOpen) return null;

  const isAll = selectedCategories.length === 0;

  const filteredCategories = VOCAB_CATEGORIES.filter((cat) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      cat.name.toLowerCase().includes(q) ||
      cat.nameJa.toLowerCase().includes(q) ||
      cat.desc.toLowerCase().includes(q) ||
      cat.badge.toLowerCase().includes(q) ||
      cat.examples.some((ex) => ex.ja.includes(q) || ex.vi.toLowerCase().includes(q))
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
            <div className="p-2.5 rounded-2xl bg-violet-500/10 border border-violet-500/20 text-violet-600 dark:text-violet-400">
              <Layers className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-black text-foreground tracking-tight">
                  Tùy Chọn Nhóm Từ Vựng Phản Xạ
                </h3>
                <span className="text-xs font-bold font-jp px-2 py-0.5 rounded-full bg-violet-500/10 text-violet-600 dark:text-violet-400 border border-violet-500/20">
                  語彙カテゴリ
                </span>
              </div>
              <p className="text-xs text-muted-foreground font-medium">
                Xáo trộn ngẫu nhiên tự nhiên • 100% phản xạ bật tiếng Nhật kèm cụm Collocation thực chiến
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
              placeholder="Tìm kiếm nhóm từ vựng, ví dụ..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 rounded-xl bg-background border border-border/60 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-violet-500/40"
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
                  ? "bg-violet-500 text-white border-violet-500 shadow-xs"
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
                ? "bg-gradient-to-br from-violet-500/20 via-violet-500/10 to-transparent border-violet-500/50 shadow-md ring-2 ring-violet-500/20"
                : "bg-muted/20 border-border/60 hover:border-violet-500/30 hover:bg-muted/30"
            )}
          >
            <div className="flex items-start justify-between gap-3 mb-2">
              <div className="flex items-center gap-2.5">
                <div
                  className={cn(
                    "p-2 rounded-xl border shrink-0",
                    isAll
                      ? "bg-violet-500 text-white border-violet-400"
                      : "bg-muted text-muted-foreground border-border"
                  )}
                >
                  <Sparkles className="h-4 w-4" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-extrabold text-sm text-foreground">
                      Ngẫu Nhiên Toàn Diện (500+ Từ Vựng Đa Dạng)
                    </span>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-violet-500/10 text-violet-600 dark:text-violet-400 border border-violet-500/20 font-jp">
                      全語彙ランダム
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Hệ thống sẽ xáo trộn tự nhiên từ vựng thuộc mọi thể loại hoặc sinh theo từ khóa bạn nhập.
                  </p>
                </div>
              </div>
              {isAll && (
                <div className="p-1 rounded-full bg-violet-500 text-white shadow-xs shrink-0">
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
                  💡 Nhập từ khóa chủ đề (Tùy chọn):
                </span>
                <span className="text-[10px] text-muted-foreground">
                  (Ví dụ: "ẩm thực", "công nghệ", "cảm xúc", "công sở"...)
                </span>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  placeholder="Gõ từ khóa muốn luyện từ vựng... (Để trống để ngẫu nhiên 100%)"
                  value={customKeywords}
                  onChange={(e) => onChangeCustomKeywords?.(e.target.value)}
                  className="flex-1 px-3 py-1.5 rounded-xl bg-background/80 border border-border/80 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-violet-500/40"
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
                          ? "bg-violet-500 text-white border-violet-500 shadow-2xs"
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
              Hoặc Chọn Theo Nhóm Từ Vựng Thực Chiến
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

                  {/* Examples & Collocations */}
                  <div className="mt-3 pt-2.5 border-t border-border/40 flex flex-wrap gap-1.5">
                    {cat.examples.map((ex, idx) => (
                      <div
                        key={idx}
                        className="px-2 py-0.5 rounded-lg bg-background/80 border border-border/60 text-[10px] flex items-center gap-1 font-medium shadow-2xs"
                      >
                        <span className="font-bold font-jp text-primary">{ex.ja}</span>
                        <span className="text-muted-foreground font-jp">({ex.reading})</span>
                        <span className="text-muted-foreground">• {ex.vi}</span>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>

          {filteredCategories.length === 0 && (
            <div className="py-12 text-center text-muted-foreground space-y-2">
              <p className="text-sm font-semibold">Không tìm thấy nhóm từ vựng phù hợp với "{searchQuery}"</p>
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
                <span className="font-semibold text-violet-600 dark:text-violet-400">
                  💡 Đang lọc từ vựng theo từ khóa: <strong className="font-black">"{customKeywords.trim()}"</strong>
                </span>
              ) : (
                <span className="font-semibold text-violet-600 dark:text-violet-400">
                  🎯 Đang chọn: <strong className="font-black">Ngẫu nhiên toàn diện (500+ từ)</strong>
                </span>
              )
            ) : (
              <span>
                Đã chọn: <strong className="font-bold text-foreground">{selectedCategories.length}</strong> nhóm từ vựng
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
