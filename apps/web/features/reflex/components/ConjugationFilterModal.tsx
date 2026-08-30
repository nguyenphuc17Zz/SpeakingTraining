"use client";

import React, { useState, useMemo } from "react";
import { Modal } from "@/components/ui/modal";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Check,
  CheckCircle2,
  Filter,
  Layers,
  Sparkles,
  Zap,
  RotateCcw,
  Search,
  SlidersHorizontal,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { soundFX } from "@/lib/sound-fx";

export interface FormOption {
  id: string;
  labelJa: string;
  nameVi: string;
  suffix: string;
  group: string;
  groupNameVi: string;
}

export const CONJUGATION_PRESETS: {
  id: string;
  label: string;
  icon: string;
  color: string;
  forms: string[];
}[] = [
  {
    id: "all",
    label: "🌟 Tất cả 50 thể (Toàn diện)",
    icon: "🌟",
    color: "border-primary/40 bg-primary/10 text-primary",
    forms: [], // Empty means all in backend
  },
  {
    id: "core",
    label: "🔰 11 Thể Cốt Lõi (N5 - N4)",
    icon: "🔰",
    color: "border-emerald-500/40 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
    forms: [
      "nai", "ta", "te", "potential", "passive", "causative",
      "causative_passive", "volitional", "ba", "tara", "imperative",
    ],
  },
  {
    id: "colloquial",
    label: "🗣️ 11 Thể Khẩu Ngữ & Viết Tắt (Slang)",
    icon: "🗣️",
    color: "border-amber-500/40 bg-amber-500/10 text-amber-600 dark:text-amber-400",
    forms: [
      "nakya", "chau", "chatta", "toku", "toita", "teru",
      "tenai", "teta", "cha_dame", "cha_ikenai", "naito",
    ],
  },
  {
    id: "passive_causative",
    label: "🛡️ 6 Thể Bị Động & Sai Khiến",
    icon: "🛡️",
    color: "border-indigo-500/40 bg-indigo-500/10 text-indigo-600 dark:text-indigo-400",
    forms: [
      "passive", "causative", "causative_passive",
      "passive_past", "causative_past", "causative_passive_past",
    ],
  },
  {
    id: "desire",
    label: "❤️ 5 Thể Mong Muốn (Tai / Tagaru)",
    icon: "❤️",
    color: "border-rose-500/40 bg-rose-500/10 text-rose-600 dark:text-rose-400",
    forms: ["tai", "takunai", "takatta", "takunakatta", "tagaru"],
  },
  {
    id: "conditionals",
    label: "🌿 6 Thể Điều Kiện (Ba/Tara/Nara/To)",
    icon: "🌿",
    color: "border-teal-500/40 bg-teal-500/10 text-teal-600 dark:text-teal-400",
    forms: ["ba", "tara", "nakereba", "nakattara", "to_conditional", "nara"],
  },
  {
    id: "state_prep",
    label: "⏳ 6 Thể Trạng Thái & Chuẩn Bị",
    icon: "⏳",
    color: "border-sky-500/40 bg-sky-500/10 text-sky-600 dark:text-sky-400",
    forms: ["te_iru", "te_inai", "te_ita", "te_oku", "te_shimau", "te_miru"],
  },
  {
    id: "difficulty",
    label: "⚖️ 3 Thể Dễ / Khó (Yasui / Nikui)",
    icon: "⚖️",
    color: "border-purple-500/40 bg-purple-500/10 text-purple-600 dark:text-purple-400",
    forms: ["yasui", "nikui", "zurai"],
  },
  {
    id: "potential_all",
    label: "⚡ 4 Thể Khả Năng Toàn Diện",
    icon: "⚡",
    color: "border-cyan-500/40 bg-cyan-500/10 text-cyan-600 dark:text-cyan-400",
    forms: ["potential", "potential_negative", "potential_past", "potential_negative_past"],
  },
];

export const ALL_CONJUGATION_FORMS: FormOption[] = [
  // 1. Core Forms
  { id: "nai", labelJa: "ない形", nameVi: "Phủ định", suffix: "〜ない", group: "core", groupNameVi: "1. Thể Cốt Lõi (N5-N4)" },
  { id: "ta", labelJa: "た形", nameVi: "Quá khứ", suffix: "〜た / 〜だ", group: "core", groupNameVi: "1. Thể Cốt Lõi (N5-N4)" },
  { id: "te", labelJa: "て形", nameVi: "Thể Te", suffix: "〜て / 〜で", group: "core", groupNameVi: "1. Thể Cốt Lõi (N5-N4)" },
  { id: "potential", labelJa: "可能形", nameVi: "Khả năng", suffix: "〜れる / 〜える", group: "core", groupNameVi: "1. Thể Cốt Lõi (N5-N4)" },
  { id: "passive", labelJa: "受身形", nameVi: "Bị động", suffix: "〜られる / 〜れる", group: "core", groupNameVi: "1. Thể Cốt Lõi (N5-N4)" },
  { id: "causative", labelJa: "使役形", nameVi: "Sai khiến", suffix: "〜させる / 〜せる", group: "core", groupNameVi: "1. Thể Cốt Lõi (N5-N4)" },
  { id: "causative_passive", labelJa: "使役受身形", nameVi: "Bị sai khiến", suffix: "〜させられる", group: "core", groupNameVi: "1. Thể Cốt Lõi (N5-N4)" },
  { id: "volitional", labelJa: "意向形", nameVi: "Ý chí / Rủ rê", suffix: "〜よう / 〜おう", group: "core", groupNameVi: "1. Thể Cốt Lõi (N5-N4)" },
  { id: "ba", labelJa: "ば形", nameVi: "Điều kiện Ba", suffix: "〜えば / 〜れば", group: "core", groupNameVi: "1. Thể Cốt Lõi (N5-N4)" },
  { id: "tara", labelJa: "たら形", nameVi: "Điều kiện Tara", suffix: "〜たら / 〜だら", group: "core", groupNameVi: "1. Thể Cốt Lõi (N5-N4)" },
  { id: "imperative", labelJa: "命令形", nameVi: "Mệnh lệnh", suffix: "〜え / 〜ろ", group: "core", groupNameVi: "1. Thể Cốt Lõi (N5-N4)" },

  // 2. Desire
  { id: "tai", labelJa: "たい形", nameVi: "Muốn làm", suffix: "〜たい", group: "desire", groupNameVi: "2. Mong Muốn & Nguyện Vọng" },
  { id: "takunai", labelJa: "たくない形", nameVi: "Không muốn làm", suffix: "〜たくない", group: "desire", groupNameVi: "2. Mong Muốn & Nguyện Vọng" },
  { id: "takatta", labelJa: "たかった形", nameVi: "Đã từng muốn làm", suffix: "〜たかった", group: "desire", groupNameVi: "2. Mong Muốn & Nguyện Vọng" },
  { id: "takunakatta", labelJa: "たくなかった形", nameVi: "Đã không muốn làm", suffix: "〜たくなかった", group: "desire", groupNameVi: "2. Mong Muốn & Nguyện Vọng" },
  { id: "tagaru", labelJa: "たがる形", nameVi: "Người thứ 3 muốn", suffix: "〜たがる", group: "desire", groupNameVi: "2. Mong Muốn & Nguyện Vọng" },

  // 3. Prohibitive & Request
  { id: "prohibitive", labelJa: "禁止形", nameVi: "Cấm chỉ (Không được!)", suffix: "〜な", group: "requests", groupNameVi: "3. Cấm Chỉ & Sai Bảo" },
  { id: "naide", labelJa: "ないで形", nameVi: "Xin đừng...", suffix: "〜ないで", group: "requests", groupNameVi: "3. Cấm Chỉ & Sai Bảo" },
  { id: "nasai", labelJa: "なさい形", nameVi: "Hãy làm đi (Cấp trên)", suffix: "〜なさい", group: "requests", groupNameVi: "3. Cấm Chỉ & Sai Bảo" },

  // 4. State & Prep
  { id: "te_iru", labelJa: "ている形", nameVi: "Đang làm / Trạng thái", suffix: "〜ている", group: "state", groupNameVi: "4. Trạng Thái & Chuẩn Bị" },
  { id: "te_inai", labelJa: "ていない形", nameVi: "Chưa / Không đang làm", suffix: "〜ていない", group: "state", groupNameVi: "4. Trạng Thái & Chuẩn Bị" },
  { id: "te_ita", labelJa: "ていた形", nameVi: "Đã đang làm (Quá khứ)", suffix: "〜ていた", group: "state", groupNameVi: "4. Trạng Thái & Chuẩn Bị" },
  { id: "te_oku", labelJa: "ておく形", nameVi: "Làm sẵn / Chuẩn bị trước", suffix: "〜ておく", group: "state", groupNameVi: "4. Trạng Thái & Chuẩn Bị" },
  { id: "te_shimau", labelJa: "てしまう形", nameVi: "Lỡ làm / Hoàn thành hết", suffix: "〜てしまう", group: "state", groupNameVi: "4. Trạng Thái & Chuẩn Bị" },
  { id: "te_miru", labelJa: "てみる形", nameVi: "Làm thử xem sao", suffix: "〜てみる", group: "state", groupNameVi: "4. Trạng Thái & Chuẩn Bị" },

  // 5. Ease & Difficulty
  { id: "yasui", labelJa: "やすい形", nameVi: "Dễ làm / Dễ xảy ra", suffix: "〜やすい", group: "difficulty", groupNameVi: "5. Mức Độ Dễ & Khó" },
  { id: "nikui", labelJa: "にくい形", nameVi: "Khó làm (Khách quan)", suffix: "〜にくい", group: "difficulty", groupNameVi: "5. Mức Độ Dễ & Khó" },
  { id: "zurai", labelJa: "づらい形", nameVi: "Khó chịu / Ngại ngần", suffix: "〜づらい", group: "difficulty", groupNameVi: "5. Mức Độ Dễ & Khó" },

  // 6. Past & Combined
  { id: "nakatta", labelJa: "なかった形", nameVi: "Quá khứ phủ định", suffix: "〜なかった", group: "combined", groupNameVi: "6. Quá Khứ & Kết Hợp" },
  { id: "passive_past", labelJa: "受身過去形", nameVi: "Đã bị / Đã được", suffix: "〜られた", group: "combined", groupNameVi: "6. Quá Khứ & Kết Hợp" },
  { id: "causative_past", labelJa: "使役過去形", nameVi: "Đã bắt / Đã cho phép", suffix: "〜させた", group: "combined", groupNameVi: "6. Quá Khứ & Kết Hợp" },
  { id: "causative_passive_past", labelJa: "使役受身過去", nameVi: "Đã bị ép buộc làm", suffix: "〜させられた", group: "combined", groupNameVi: "6. Quá Khứ & Kết Hợp" },
  { id: "potential_negative", labelJa: "可能否定形", nameVi: "Không thể làm", suffix: "〜られない", group: "combined", groupNameVi: "6. Quá Khứ & Kết Hợp" },
  { id: "potential_past", labelJa: "可能過去形", nameVi: "Đã có thể làm", suffix: "〜られた", group: "combined", groupNameVi: "6. Quá Khứ & Kết Hợp" },
  { id: "potential_negative_past", labelJa: "可能否定過去", nameVi: "Đã không thể làm", suffix: "〜られなかった", group: "combined", groupNameVi: "6. Quá Khứ & Kết Hợp" },

  // 7. Conditionals
  { id: "nakereba", labelJa: "なければ形", nameVi: "Nếu không làm (Ba)", suffix: "〜なければ", group: "conditionals", groupNameVi: "7. Thể Điều Kiện (Nếu...)" },
  { id: "nakattara", labelJa: "なかったら形", nameVi: "Nếu đã không làm (Tara)", suffix: "〜なかったら", group: "conditionals", groupNameVi: "7. Thể Điều Kiện (Nếu...)" },
  { id: "to_conditional", labelJa: "と条件形", nameVi: "Cứ hễ làm là...", suffix: "〜と", group: "conditionals", groupNameVi: "7. Thể Điều Kiện (Nếu...)" },
  { id: "nara", labelJa: "なら形", nameVi: "Nếu là chuyện đó (Nara)", suffix: "〜なら", group: "conditionals", groupNameVi: "7. Thể Điều Kiện (Nếu...)" },

  // 8. Colloquial Slang
  { id: "nakya", labelJa: "なきゃ形", nameVi: "Phải làm (Khẩu ngữ)", suffix: "〜なきゃ", group: "colloquial", groupNameVi: "8. Khẩu Ngữ & Rút Gọn Thực Chiến" },
  { id: "chau", labelJa: "ちゃう形", nameVi: "Lỡ làm mất rồi", suffix: "〜ちゃう / 〜じゃう", group: "colloquial", groupNameVi: "8. Khẩu Ngữ & Rút Gọn Thực Chiến" },
  { id: "chatta", labelJa: "ちゃった形", nameVi: "Đã lỡ làm mất rồi", suffix: "〜ちゃった / 〜じゃった", group: "colloquial", groupNameVi: "8. Khẩu Ngữ & Rút Gọn Thực Chiến" },
  { id: "toku", labelJa: "とく形", nameVi: "Làm sẵn (Khẩu ngữ)", suffix: "〜とく / 〜どく", group: "colloquial", groupNameVi: "8. Khẩu Ngữ & Rút Gọn Thực Chiến" },
  { id: "toita", labelJa: "といた形", nameVi: "Đã làm sẵn rồi", suffix: "〜といた / 〜どいた", group: "colloquial", groupNameVi: "8. Khẩu Ngữ & Rút Gọn Thực Chiến" },
  { id: "teru", labelJa: "てる形", nameVi: "Đang làm (Rút gọn)", suffix: "〜てる / 〜でる", group: "colloquial", groupNameVi: "8. Khẩu Ngữ & Rút Gọn Thực Chiến" },
  { id: "tenai", labelJa: "てない形", nameVi: "Chưa làm (Rút gọn)", suffix: "〜てない / 〜でない", group: "colloquial", groupNameVi: "8. Khẩu Ngữ & Rút Gọn Thực Chiến" },
  { id: "teta", labelJa: "てた形", nameVi: "Đã đang làm (Rút gọn)", suffix: "〜てた / 〜деた", group: "colloquial", groupNameVi: "8. Khẩu Ngữ & Rút Gọn Thực Chiến" },
  { id: "cha_dame", labelJa: "ちゃだめ形", nameVi: "Không được làm đâu", suffix: "〜ちゃだめ / 〜じゃだめ", group: "colloquial", groupNameVi: "8. Khẩu Ngữ & Rút Gọn Thực Chiến" },
  { id: "cha_ikenai", labelJa: "ちゃいけない形", nameVi: "Không được làm nhé", suffix: "〜ちゃいけない / 〜じゃいけない", group: "colloquial", groupNameVi: "8. Khẩu Ngữ & Rút Gọn Thực Chiến" },
  { id: "naito", labelJa: "ないと形", nameVi: "Không làm là không xong", suffix: "〜ないと", group: "colloquial", groupNameVi: "8. Khẩu Ngữ & Rút Gọn Thực Chiến" },
];

interface Props {
  open: boolean;
  onClose: () => void;
  selectedForms: string[];
  onChangeSelectedForms: (forms: string[]) => void;
}

export function ConjugationFilterModal({
  open,
  onClose,
  selectedForms,
  onChangeSelectedForms,
}: Props) {
  const [searchQuery, setSearchQuery] = useState("");

  const isAll = selectedForms.length === 0;

  const handleSelectPreset = (presetId: string) => {
    soundFX.playFurin();
    const preset = CONJUGATION_PRESETS.find((p) => p.id === presetId);
    if (!preset) return;
    onChangeSelectedForms(preset.forms);
  };

  const handleToggleForm = (id: string) => {
    soundFX.playFurin();
    if (isAll) {
      // If was All, clicking one toggles to only that one
      onChangeSelectedForms([id]);
      return;
    }
    if (selectedForms.includes(id)) {
      const next = selectedForms.filter((f) => f !== id);
      onChangeSelectedForms(next);
    } else {
      onChangeSelectedForms([...selectedForms, id]);
    }
  };

  const handleSelectAll = () => {
    soundFX.playFurin();
    onChangeSelectedForms([]);
  };

  const filteredForms = useMemo(() => {
    if (!searchQuery.trim()) return ALL_CONJUGATION_FORMS;
    const q = searchQuery.toLowerCase().trim();
    return ALL_CONJUGATION_FORMS.filter(
      (f) =>
        f.id.toLowerCase().includes(q) ||
        f.labelJa.toLowerCase().includes(q) ||
        f.nameVi.toLowerCase().includes(q) ||
        f.suffix.toLowerCase().includes(q) ||
        f.groupNameVi.toLowerCase().includes(q)
    );
  }, [searchQuery]);

  // Group filtered forms
  const groupedForms = useMemo(() => {
    const map = new Map<string, FormOption[]>();
    for (const f of filteredForms) {
      if (!map.has(f.groupNameVi)) {
        map.set(f.groupNameVi, []);
      }
      map.get(f.groupNameVi)!.push(f);
    }
    return Array.from(map.entries());
  }, [filteredForms]);

  const activeCount = isAll ? ALL_CONJUGATION_FORMS.length : selectedForms.length;

  return (
    <Modal
      isOpen={open}
      onClose={onClose}
      title="🎯 BỘ LỌC THỂ CHIA ĐỘNG TỪ (CONJUGATION TARGET FILTER)"
      description="Chọn nhóm thể hoặc tích chọn các thể cụ thể để tập trung luyện phản xạ đúng mục tiêu."
      className="max-w-4xl"
    >
      <div className="space-y-5 max-h-[72vh] overflow-y-auto pr-1">
        {/* Active Status Banner */}
        <div className="p-3.5 rounded-2xl bg-muted/40 border border-border flex flex-wrap items-center justify-between gap-2.5">
          <div className="flex items-center gap-2">
            <Badge variant="sakura" size="md" className="font-bold flex items-center gap-1">
              <Zap className="h-3.5 w-3.5" />
              <span>
                Đang kích hoạt: {activeCount} / {ALL_CONJUGATION_FORMS.length} thể
              </span>
            </Badge>
            <span className="text-xs text-muted-foreground">
              {isAll ? "(Luyện tập toàn diện 50 thể)" : "(Lọc theo danh sách tự chọn)"}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleSelectAll}
              className={cn("text-xs font-bold gap-1 h-7 px-2.5", isAll && "border-primary text-primary")}
            >
              <CheckCircle2 className="h-3.5 w-3.5" />
              <span>Chọn tất cả (50)</span>
            </Button>
          </div>
        </div>

        {/* 1. Quick Preset Buttons */}
        <div className="space-y-2">
          <div className="text-xs font-bold text-muted-foreground flex items-center gap-1.5">
            <SlidersHorizontal className="h-3.5 w-3.5 text-primary" />
            <span>Chọn nhanh theo Nhóm thể (Presets):</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {CONJUGATION_PRESETS.map((preset) => {
              const isSelected =
                preset.id === "all"
                  ? isAll
                  : !isAll &&
                    preset.forms.length === selectedForms.length &&
                    preset.forms.every((f) => selectedForms.includes(f));

              return (
                <button
                  key={preset.id}
                  onClick={() => handleSelectPreset(preset.id)}
                  className={cn(
                    "p-2.5 rounded-xl border text-left text-xs font-bold transition-all flex items-center justify-between gap-2 cursor-pointer",
                    isSelected
                      ? preset.color + " shadow-xs ring-1 ring-primary/40 font-black"
                      : "bg-card border-border/80 text-foreground hover:bg-muted/60"
                  )}
                >
                  <span className="truncate">{preset.label}</span>
                  {isSelected && <Check className="h-3.5 w-3.5 shrink-0" />}
                </button>
              );
            })}
          </div>
        </div>

        {/* Search Input Bar */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Tìm kiếm thể (ví dụ: bị động, tai, chau, ba, tara)..."
            className="w-full pl-9 pr-3 py-2 rounded-xl bg-card border border-border text-xs text-foreground placeholder:text-muted-foreground/70 focus:outline-none focus:ring-1 focus:ring-primary font-medium"
          />
        </div>

        {/* 2. Detailed Form Checkboxes by Group */}
        <div className="space-y-4 pt-1">
          {groupedForms.map(([groupName, forms]) => {
            const allInGroupSelected = forms.every((f) => isAll || selectedForms.includes(f.id));

            return (
              <div
                key={groupName}
                className="p-3.5 rounded-2xl border border-border/70 bg-card/60 space-y-2.5"
              >
                {/* Group Header */}
                <div className="flex items-center justify-between border-b border-border/40 pb-2">
                  <span className="font-black text-xs text-foreground font-jp flex items-center gap-1.5">
                    <span>{groupName}</span>
                    <span className="text-[10px] text-muted-foreground font-normal">
                      ({forms.length} thể)
                    </span>
                  </span>

                  <button
                    onClick={() => {
                      soundFX.playFurin();
                      const groupIds = forms.map((f) => f.id);
                      if (allInGroupSelected && !isAll) {
                        // Deselect group
                        onChangeSelectedForms(selectedForms.filter((id) => !groupIds.includes(id)));
                      } else {
                        // Select all in group
                        const base = isAll ? [] : selectedForms;
                        const merged = Array.from(new Set([...base, ...groupIds]));
                        onChangeSelectedForms(merged);
                      }
                    }}
                    className="text-[11px] font-bold text-primary hover:underline cursor-pointer"
                  >
                    {allInGroupSelected && !isAll ? "Bỏ chọn nhóm" : "Chọn nhóm này"}
                  </button>
                </div>

                {/* Grid of Form Pills */}
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
                  {forms.map((form) => {
                    const isChecked = isAll || selectedForms.includes(form.id);

                    return (
                      <button
                        key={form.id}
                        type="button"
                        onClick={() => handleToggleForm(form.id)}
                        className={cn(
                          "p-2 rounded-xl border text-left transition-all flex items-center justify-between gap-2 text-xs cursor-pointer",
                          isChecked
                            ? "bg-rose-500/10 border-rose-500/30 text-rose-950 dark:text-rose-100 font-bold"
                            : "bg-muted/20 border-border/60 text-muted-foreground hover:bg-muted/40"
                        )}
                      >
                        <div className="min-w-0">
                          <div className="flex items-center gap-1 font-jp">
                            <span className="font-black text-foreground">{form.labelJa}</span>
                            <span className="text-[10px] text-muted-foreground font-normal truncate">
                              ({form.nameVi})
                            </span>
                          </div>
                          <div className="text-[10px] text-rose-600 dark:text-rose-400 font-mono">
                            {form.suffix}
                          </div>
                        </div>

                        <div
                          className={cn(
                            "h-4 w-4 rounded-md border flex items-center justify-center shrink-0 transition-colors",
                            isChecked
                              ? "bg-rose-500 border-rose-600 text-white"
                              : "border-muted-foreground/40 bg-card"
                          )}
                        >
                          {isChecked && <Check className="h-3 w-3" />}
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>

        {/* Modal Action Bar */}
        <div className="flex items-center justify-between pt-3 border-t border-border">
          <div className="text-xs text-muted-foreground font-semibold">
            Đang áp dụng: <strong className="text-foreground">{activeCount} thể</strong>
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
            <span>Áp dụng bộ lọc</span>
          </Button>
        </div>
      </div>
    </Modal>
  );
}
