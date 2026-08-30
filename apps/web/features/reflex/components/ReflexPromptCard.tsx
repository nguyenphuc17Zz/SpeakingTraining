"use client";

import { UniversalFurigana } from "@/components/japanese/UniversalFurigana";

import React, { useState, useEffect } from "react";
import { Badge } from "@/components/ui/badge";
import { Volume2, Sparkles, ArrowRight, BookOpen, Headphones, HelpCircle, Crown, Zap, Repeat } from "lucide-react";
import type { ReflexExercise } from "../services/reflex-api";
import { translateJaToVi } from "../services/google-translate";
import { cn } from "@/lib/utils";

interface Props {
  exercise: ReflexExercise | null;
  subtitleMode?: "hidden" | "japanese" | "japanese_reading" | "vietnamese";
  onPlayAudio?: () => void;
  phase: string;
}

export interface ConjugationTargetDetail {
  shortName: string;
  formJa: string;
  meaning: string;
  suffixHint: string;
  fullLabel: string;
}

export const CONJUGATION_FORM_DETAILS: Record<string, ConjugationTargetDetail> = {
  // Core (12)
  nai: {
    shortName: "Thể Phủ định (〜ない)",
    formJa: "ない形",
    meaning: "Không làm / Chưa làm",
    suffixHint: "〜ない",
    fullLabel: "Thể Phủ định [〜ない] (Không làm...)",
  },
  negative: {
    shortName: "Thể Phủ định (〜ない)",
    formJa: "ない形",
    meaning: "Không làm / Chưa làm",
    suffixHint: "〜ない",
    fullLabel: "Thể Phủ định [〜ない] (Không làm...)",
  },
  nai_form: {
    shortName: "Thể Phủ định (〜ない)",
    formJa: "ない形",
    meaning: "Không làm / Chưa làm",
    suffixHint: "〜ない",
    fullLabel: "Thể Phủ định [〜ない] (Không làm...)",
  },
  te: {
    shortName: "Thể TE (〜て / 〜で)",
    formJa: "て形",
    meaning: "Nối câu, đang làm, yêu cầu nhẹ",
    suffixHint: "〜て / 〜で",
    fullLabel: "Thể TE [〜て / 〜で] (Nối câu / Đang làm...)",
  },
  te_form: {
    shortName: "Thể TE (〜て / 〜で)",
    formJa: "て形",
    meaning: "Nối câu, đang làm, yêu cầu nhẹ",
    suffixHint: "〜て / 〜で",
    fullLabel: "Thể TE [〜て / 〜で] (Nối câu / Đang làm...)",
  },
  ta: {
    shortName: "Thể Quá khứ (〜た / 〜だ)",
    formJa: "た形",
    meaning: "Đã làm",
    suffixHint: "〜た / 〜だ",
    fullLabel: "Thể Quá khứ [〜た / 〜だ] (Đã làm...)",
  },
  past: {
    shortName: "Thể Quá khứ (〜た / 〜だ)",
    formJa: "た形",
    meaning: "Đã làm",
    suffixHint: "〜た / 〜だ",
    fullLabel: "Thể Quá khứ [〜た / 〜だ] (Đã làm...)",
  },
  ta_form: {
    shortName: "Thể Quá khứ (〜た / 〜だ)",
    formJa: "た形",
    meaning: "Đã làm",
    suffixHint: "〜た / 〜だ",
    fullLabel: "Thể Quá khứ [〜た / 〜だ] (Đã làm...)",
  },
  potential: {
    shortName: "Thể Khả năng (〜れる / 〜える)",
    formJa: "可能形",
    meaning: "Có thể làm...",
    suffixHint: "〜れる / 〜える",
    fullLabel: "Thể Khả năng [〜れる / 〜える] (Có thể làm...)",
  },
  kanou: {
    shortName: "Thể Khả năng (〜れる / 〜える)",
    formJa: "可能形",
    meaning: "Có thể làm...",
    suffixHint: "〜れる / 〜える",
    fullLabel: "Thể Khả năng [〜れる / 〜える] (Có thể làm...)",
  },
  passive: {
    shortName: "Thể Bị động (〜られる / 〜れる)",
    formJa: "受身形",
    meaning: "Bị / Được làm...",
    suffixHint: "〜られる / 〜れる",
    fullLabel: "Thể Bị động [〜られる / 〜れる] (Bị / Được làm...)",
  },
  ukemi: {
    shortName: "Thể Bị động (〜られる / 〜れる)",
    formJa: "受身形",
    meaning: "Bị / Được làm...",
    suffixHint: "〜られる / 〜れる",
    fullLabel: "Thể Bị động [〜られる / 〜れる] (Bị / Được làm...)",
  },
  causative: {
    shortName: "Thể Sai khiến (〜させる / 〜せる)",
    formJa: "使役形",
    meaning: "Bắt / Cho phép làm...",
    suffixHint: "〜させる / 〜せる",
    fullLabel: "Thể Sai khiến [〜させる / 〜せる] (Bắt / Cho phép làm...)",
  },
  shieki: {
    shortName: "Thể Sai khiến (〜させる / 〜せる)",
    formJa: "使役形",
    meaning: "Bắt / Cho phép làm...",
    suffixHint: "〜させる / 〜せる",
    fullLabel: "Thể Sai khiến [〜させる / 〜せる] (Bắt / Cho phép làm...)",
  },
  causative_passive: {
    shortName: "Thể Bị động Sai khiến (〜させられる)",
    formJa: "使役受身形",
    meaning: "Bị bắt phải làm...",
    suffixHint: "〜させられる / 〜される",
    fullLabel: "Thể Bị động Sai khiến [〜させられる] (Bị bắt phải làm...)",
  },
  "causative-passive": {
    shortName: "Thể Bị động Sai khiến (〜させられる)",
    formJa: "使役受身形",
    meaning: "Bị bắt phải làm...",
    suffixHint: "〜させられる / 〜される",
    fullLabel: "Thể Bị động Sai khiến [〜させられる] (Bị bắt phải làm...)",
  },
  shieki_ukemi: {
    shortName: "Thể Bị động Sai khiến (〜させられる)",
    formJa: "使役受身形",
    meaning: "Bị bắt phải làm...",
    suffixHint: "〜させられる / 〜される",
    fullLabel: "Thể Bị động Sai khiến [〜させられる] (Bị bắt phải làm...)",
  },
  volitional: {
    shortName: "Thể Ý chí / Rủ rê (〜よう / 〜おう)",
    formJa: "意向形",
    meaning: "Hãy cùng làm / Dự định làm...",
    suffixHint: "〜よう / 〜おう",
    fullLabel: "Thể Ý chí / Rủ rê [〜よう / 〜おう] (Hãy cùng làm...)",
  },
  ikou: {
    shortName: "Thể Ý chí / Rủ rê (〜よう / 〜おう)",
    formJa: "意向形",
    meaning: "Hãy cùng làm / Dự định làm...",
    suffixHint: "〜よう / 〜おう",
    fullLabel: "Thể Ý chí / Rủ rê [〜よう / 〜おう] (Hãy cùng làm...)",
  },
  ba: {
    shortName: "Thể Điều kiện (〜ば)",
    formJa: "ば形",
    meaning: "Nếu làm...",
    suffixHint: "〜えば / 〜れば",
    fullLabel: "Thể Điều kiện BA [〜ば] (Nếu làm...)",
  },
  conditional: {
    shortName: "Thể Điều kiện (〜ば)",
    formJa: "ば形",
    meaning: "Nếu làm...",
    suffixHint: "〜えば / 〜れば",
    fullLabel: "Thể Điều kiện BA [〜ば] (Nếu làm...)",
  },
  tara: {
    shortName: "Thể Điều kiện (〜たら)",
    formJa: "たら形",
    meaning: "Nếu / Sau khi làm...",
    suffixHint: "〜たら / 〜だら",
    fullLabel: "Thể Điều kiện TARA [〜たら] (Nếu / Sau khi làm...)",
  },
  imperative: {
    shortName: "Thể Mệnh lệnh (〜ろ / 〜え)",
    formJa: "命令形",
    meaning: "Hãy làm! / Ra lệnh",
    suffixHint: "〜ろ / 〜え",
    fullLabel: "Thể Mệnh lệnh [〜ろ / 〜え] (Hãy làm!)",
  },
  meirei: {
    shortName: "Thể Mệnh lệnh (〜ろ / 〜え)",
    formJa: "命令形",
    meaning: "Hãy làm! / Ra lệnh",
    suffixHint: "〜ろ / 〜え",
    fullLabel: "Thể Mệnh lệnh [〜ろ / 〜え] (Hãy làm!)",
  },
  dictionary: {
    shortName: "Thể Từ điển (Nguyên mẫu)",
    formJa: "辞書形",
    meaning: "Nguyên mẫu",
    suffixHint: "〜る / 〜う",
    fullLabel: "Thể Từ điển [辞書形] (Nguyên mẫu)",
  },
  jisho: {
    shortName: "Thể Từ điển (Nguyên mẫu)",
    formJa: "辞書形",
    meaning: "Nguyên mẫu",
    suffixHint: "〜る / 〜う",
    fullLabel: "Thể Từ điển [辞書形] (Nguyên mẫu)",
  },

  // Group 2: Desire (5)
  tai: {
    shortName: "Thể Mong muốn (〜たい)",
    formJa: "たい形",
    meaning: "Muốn làm...",
    suffixHint: "〜たい",
    fullLabel: "Thể Mong muốn [〜たい] (Muốn làm...)",
  },
  takunai: {
    shortName: "Thể Không muốn (〜たくない)",
    formJa: "たくない形",
    meaning: "Không muốn làm...",
    suffixHint: "〜たくない",
    fullLabel: "Thể Không muốn [〜たくない] (Không muốn làm...)",
  },
  takatta: {
    shortName: "Thể Đã muốn (〜たかった)",
    formJa: "たかった形",
    meaning: "Đã từng muốn làm...",
    suffixHint: "〜たかった",
    fullLabel: "Thể Đã muốn [〜たかった] (Đã muốn làm...)",
  },
  takunakatta: {
    shortName: "Thể Đã không muốn (〜たくなかった)",
    formJa: "たくなかった形",
    meaning: "Đã không muốn làm...",
    suffixHint: "〜たくなかった",
    fullLabel: "Thể Đã không muốn [〜たくなかった] (Đã không muốn làm...)",
  },
  tagaru: {
    shortName: "Thể Người thứ 3 muốn (〜たがる)",
    formJa: "たがる形",
    meaning: "Người khác muốn làm...",
    suffixHint: "〜たがる",
    fullLabel: "Thể Người thứ 3 muốn [〜たがる] (Ai đó muốn làm...)",
  },

  // Group 3: Prohibition & Requests (3)
  prohibitive: {
    shortName: "Thể Cấm chỉ (〜な)",
    formJa: "禁止形",
    meaning: "Cấm làm!",
    suffixHint: "〜な",
    fullLabel: "Thể Cấm chỉ [〜な] (Cấm làm!)",
  },
  kinshi: {
    shortName: "Thể Cấm chỉ (〜な)",
    formJa: "禁止形",
    meaning: "Cấm làm!",
    suffixHint: "〜な",
    fullLabel: "Thể Cấm chỉ [〜な] (Cấm làm!)",
  },
  naide: {
    shortName: "Thể Xin đừng làm (〜ないで)",
    formJa: "ないで形",
    meaning: "Đừng làm...",
    suffixHint: "〜ないで",
    fullLabel: "Thể Xin đừng làm [〜ないで] (Đừng làm...)",
  },
  nasai: {
    shortName: "Thể Mệnh lệnh nhẹ (〜なさい)",
    formJa: "なさい形",
    meaning: "Hãy làm đi (người lớn dặn)",
    suffixHint: "〜なさい",
    fullLabel: "Thể Mệnh lệnh nhẹ [〜なさい] (Hãy làm đi...)",
  },

  // Group 4: State & Prep (6)
  te_iru: {
    shortName: "Thể Đang làm (〜ている)",
    formJa: "ている形",
    meaning: "Đang làm / Trạng thái",
    suffixHint: "〜ている",
    fullLabel: "Thể Đang làm [〜ている] (Tiếp diễn / Trạng thái)",
  },
  te_inai: {
    shortName: "Thể Chưa làm (〜ていない)",
    formJa: "ていない形",
    meaning: "Chưa làm / Không tiếp diễn",
    suffixHint: "〜ていない",
    fullLabel: "Thể Chưa làm [〜ていない] (Chưa làm / Không tiếp diễn)",
  },
  te_ita: {
    shortName: "Thể Quá khứ tiếp diễn (〜ていた)",
    formJa: "ていた形",
    meaning: "Lúc đó đã đang làm...",
    suffixHint: "〜ていた",
    fullLabel: "Thể Quá khứ tiếp diễn [〜ていた] (Đã đang làm...)",
  },
  te_oku: {
    shortName: "Thể Làm sẵn (〜ておく)",
    formJa: "ておく形",
    meaning: "Làm sẵn trước...",
    suffixHint: "〜ておく",
    fullLabel: "Thể Làm sẵn [〜ておく] (Chuẩn bị trước...)",
  },
  te_shimau: {
    shortName: "Thể Lỡ làm (〜てしまう)",
    formJa: "てしまう形",
    meaning: "Lỡ làm / Làm xong hết...",
    suffixHint: "〜てしまう",
    fullLabel: "Thể Lỡ làm [〜てしまう] (Lỡ làm / Xong xuôi...)",
  },
  te_miru: {
    shortName: "Thể Thử làm (〜てみる)",
    formJa: "てみる形",
    meaning: "Thử làm xem sao...",
    suffixHint: "〜てみる",
    fullLabel: "Thể Thử làm [〜てみる] (Thử làm...)",
  },

  // Group 5: Ease & Difficulty (3)
  yasui: {
    shortName: "Thể Dễ làm (〜やすい)",
    formJa: "やすい形",
    meaning: "Dễ làm / Thuận tiện...",
    suffixHint: "〜やすい",
    fullLabel: "Thể Dễ làm [〜やすい] (Dễ làm...)",
  },
  nikui: {
    shortName: "Thể Khó làm (〜にくい)",
    formJa: "にくい形",
    meaning: "Khó làm / Bất tiện...",
    suffixHint: "〜にくい",
    fullLabel: "Thể Khó làm [〜にくい] (Khó làm...)",
  },
  zurai: {
    shortName: "Thể Khó chịu khi làm (〜づらい)",
    formJa: "づらい形",
    meaning: "Khó chịu / Đau / Khó thao tác...",
    suffixHint: "〜づらい",
    fullLabel: "Thể Khó chịu [〜づらい] (Khó chịu khi làm...)",
  },

  // Group 6: Past & Combined (7)
  nakatta: {
    shortName: "Thể Quá khứ phủ định (〜なかった)",
    formJa: "なかった形",
    meaning: "Đã không làm...",
    suffixHint: "〜なかった",
    fullLabel: "Thể Quá khứ phủ định [〜なかった] (Đã không làm...)",
  },
  passive_past: {
    shortName: "Thể Bị động quá khứ (〜られた)",
    formJa: "受身・過去形",
    meaning: "Đã bị / Được làm...",
    suffixHint: "〜られた / 〜れた",
    fullLabel: "Thể Bị động quá khứ [受身・過去] (Đã bị/được làm...)",
  },
  causative_past: {
    shortName: "Thể Sai khiến quá khứ (〜させた)",
    formJa: "使役・過去形",
    meaning: "Đã bắt / Cho phép làm...",
    suffixHint: "〜させた / 〜せた",
    fullLabel: "Thể Sai khiến quá khứ [使役・過去] (Đã bắt/cho phép làm...)",
  },
  causative_passive_past: {
    shortName: "Thể Sai khiến bị động QK (〜させられた)",
    formJa: "使役受身・過去形",
    meaning: "Đã bị bắt phải làm...",
    suffixHint: "〜させられた / 〜された",
    fullLabel: "Thể Sai khiến bị động QK [使役受身・過去] (Đã bị bắt phải làm...)",
  },
  potential_negative: {
    shortName: "Thể Không thể (〜れない)",
    formJa: "可能・否定形",
    meaning: "Không thể làm...",
    suffixHint: "〜れない / 〜えない",
    fullLabel: "Thể Không thể [可能・否定] (Không thể làm...)",
  },
  potential_past: {
    shortName: "Thể Đã có thể (〜れた)",
    formJa: "可能・過去形",
    meaning: "Đã có thể làm...",
    suffixHint: "〜れた / 〜えた",
    fullLabel: "Thể Đã có thể [可能・過去] (Đã có thể làm...)",
  },
  potential_negative_past: {
    shortName: "Thể Đã không thể (〜れなかった)",
    formJa: "可能・過去否定形",
    meaning: "Đã không thể làm...",
    suffixHint: "〜れなかった / 〜えなかった",
    fullLabel: "Thể Đã không thể [可能・過去否定] (Đã không thể làm...)",
  },

  // Group 7: Conditionals (4)
  nakereba: {
    shortName: "Thể Nếu không làm (〜なければ)",
    formJa: "なければ形",
    meaning: "Nếu không làm...",
    suffixHint: "〜なければ",
    fullLabel: "Thể Nếu không [〜なければ] (Nếu không làm...)",
  },
  nakattara: {
    shortName: "Thể Nếu đã không làm (〜なかったら)",
    formJa: "なかったら形",
    meaning: "Nếu như đã không làm...",
    suffixHint: "〜なかったら",
    fullLabel: "Thể Nếu đã không [〜なかったら] (Nếu như không làm...)",
  },
  to_conditional: {
    shortName: "Thể Hễ mà (〜と)",
    formJa: "と形",
    meaning: "Hễ làm thì... (tự nhiên)",
    suffixHint: "〜と",
    fullLabel: "Thể Hễ mà [〜と] (Hễ làm thì...)",
  },
  to: {
    shortName: "Thể Hễ mà (〜と)",
    formJa: "と形",
    meaning: "Hễ làm thì... (tự nhiên)",
    suffixHint: "〜と",
    fullLabel: "Thể Hễ mà [〜と] (Hễ làm thì...)",
  },
  nara: {
    shortName: "Thể Nếu là (〜なら)",
    formJa: "なら形",
    meaning: "Nếu làm thì...",
    suffixHint: "〜なら",
    fullLabel: "Thể Nếu là [〜なら] (Nếu làm thì...)",
  },

  // Group 8: Colloquial Slang (11)
  nakya: {
    shortName: "Thể Phải làm rút gọn (〜なきゃ)",
    formJa: "なきゃ形",
    meaning: "Phải làm...",
    suffixHint: "〜なきゃ / 〜なくちゃ",
    fullLabel: "Thể Phải làm [〜なきゃ] (Phải làm...)",
  },
  chau: {
    shortName: "Thể Lỡ làm rút gọn (〜ちゃう)",
    formJa: "ちゃう形",
    meaning: "Lỡ làm / Xong mất...",
    suffixHint: "〜ちゃう / 〜じゃう",
    fullLabel: "Thể Lỡ làm [〜ちゃう] (Lỡ làm mất rồi...)",
  },
  chatta: {
    shortName: "Thể Đã lỡ làm rút gọn (〜ちゃった)",
    formJa: "ちゃった形",
    meaning: "Đã lỡ làm mất rồi...",
    suffixHint: "〜ちゃった / 〜じゃった",
    fullLabel: "Thể Đã lỡ làm [〜ちゃった] (Đã lỡ làm mất rồi...)",
  },
  toku: {
    shortName: "Thể Làm sẵn rút gọn (〜とく)",
    formJa: "とく形",
    meaning: "Làm sẵn trước...",
    suffixHint: "〜とく / 〜どく",
    fullLabel: "Thể Làm sẵn [〜とく] (Làm sẵn trước...)",
  },
  toita: {
    shortName: "Thể Đã làm sẵn rút gọn (〜といた)",
    formJa: "といた形",
    meaning: "Đã làm sẵn trước...",
    suffixHint: "〜といた / 〜どいた",
    fullLabel: "Thể Đã làm sẵn [〜といた] (Đã làm sẵn trước...)",
  },
  teru: {
    shortName: "Thể Đang làm rút gọn (〜てる)",
    formJa: "てる形",
    meaning: "Đang làm...",
    suffixHint: "〜てる / 〜でる",
    fullLabel: "Thể Đang làm [〜てる] (Đang làm...)",
  },
  tenai: {
    shortName: "Thể Chưa làm rút gọn (〜てない)",
    formJa: "てない形",
    meaning: "Chưa làm...",
    suffixHint: "〜てない / 〜でない",
    fullLabel: "Thể Chưa làm [〜てない] (Chưa làm...)",
  },
  teta: {
    shortName: "Thể Quá khứ rút gọn (〜てた)",
    formJa: "てた形",
    meaning: "Đã đang làm...",
    suffixHint: "〜てた / 〜でた",
    fullLabel: "Thể Quá khứ [〜てた] (Đã đang làm...)",
  },
  cha_dame: {
    shortName: "Thể Không được làm (〜ちゃだめ)",
    formJa: "ちゃだめ形",
    meaning: "Không được làm!",
    suffixHint: "〜ちゃだめ / 〜じゃだめ",
    fullLabel: "Thể Không được làm [〜ちゃだめ] (Cấm / Không được làm!)",
  },
  cha_ikenai: {
    shortName: "Thể Cấm làm (〜ちゃいけない)",
    formJa: "ちゃいけない形",
    meaning: "Không được làm!",
    suffixHint: "〜ちゃいけない / 〜じゃいけない",
    fullLabel: "Thể Cấm làm [〜ちゃいけない] (Không được phép làm!)",
  },
  naito: {
    shortName: "Thể Phải làm (〜ないと)",
    formJa: "ないと形",
    meaning: "Phải làm...",
    suffixHint: "〜ないと",
    fullLabel: "Thể Phải làm [〜ないと] (Phải làm...)",
  },
};

export function getConjugationTargetDetail(target: string): ConjugationTargetDetail | null {
  if (!target) return null;
  const t = target.trim().toLowerCase();
  return CONJUGATION_FORM_DETAILS[t] || null;
}

export function formatJapaneseConjugationTarget(target: string): string {
  if (!target) return "";
  const detail = getConjugationTargetDetail(target);
  if (detail) return detail.fullLabel;
  return target;
}

export function ReflexPromptCard({ exercise, subtitleMode = "japanese", onPlayAudio, phase }: Props) {
  const [liveTranslation, setLiveTranslation] = useState<string>("");

  const rc = exercise?.extra_metadata?.reflex_config || {};
  const prompt = rc.prompt || exercise?.scenario || exercise?.title || "";
  const isConjugation = exercise?.exercise_type === "reflex_conjugation";
  const isVocabulary = exercise?.exercise_type === "reflex_vocabulary";
  const isKeigoVocab = exercise?.exercise_type === "reflex_keigo_vocab";
  const verb = rc.verb;
  const rawTarget = rc.conjugation_target || rc.form || "";
  const target = formatJapaneseConjugationTarget(rawTarget);
  const targetDetail = getConjugationTargetDetail(rawTarget);
  const isPlaying = phase === "prompt_playing";

  // Keigo-specific data
  const keigoTargetType = rc.target_type || "sonkeigo";
  const keigoTargetLabel = rc.target_label_vi || "Kính ngữ";
  const keigoMeaning = rc.prompt_translation || rc.word_meaning_vi || "";
  const keigoReading = rc.prompt_reading || rc.word_reading || "";
  const keigoSubjectHint =
    rc.subject_hint_vi ||
    exercise?.subjectHintVi ||
    (keigoTargetType === "sonkeigo"
      ? "👑 Hành động của: SẾP / ĐỐI TÁC / KHÁCH HÀNG"
      : keigoTargetType === "kenjougo"
      ? "🙇 Hành động của: BẢN THÂN / CÔNG TY MÌNH"
      : "💼 Từ xưng hô & Giao tiếp công sở");
  const keigoFormula = rc.formula || exercise?.formula || "";

  // Vocabulary-specific data
  const vocabDirection: "ja_to_vi" | "vi_to_ja" = rc.direction || "ja_to_vi";
  const vocabWord = rc.prompt || "";
  const vocabReading = rc.word_reading || rc.prompt_reading || "";
  const vocabMeaning = rc.word_meaning_vi || rc.prompt_translation || "";
  const vocabWordType: string = rc.word_type || "noun";
  const vocabJlpt: string = rc.jlpt_level || "";

  const wordTypeLabel: Record<string, string> = {
    noun: "名 Danh từ",
    verb: "動 Động từ",
    adj_i: "形(い) Tính từ い",
    adj_na: "形(な) Tính từ な",
    adverb: "副 Trạng từ",
  };

  const staticTranslation =
    rc.translation ||
    rc.vietnamese ||
    (exercise?.scenario && exercise.scenario !== prompt ? exercise.scenario : null) ||
    exercise?.extra_metadata?.vietnamese_translation ||
    exercise?.extra_metadata?.translation ||
    null;

  const keyVocab: Array<{ ja: string; vi: string }> =
    exercise?.keyVocab ||
    rc.key_vocab ||
    rc.keyVocab ||
    (exercise as any)?.key_vocab ||
    (exercise as any)?.keyVocab ||
    [];
  const ideaSparks: string[] =
    exercise?.ideaSparks ||
    rc.idea_sparks ||
    rc.ideaSparks ||
    (exercise as any)?.idea_sparks ||
    (exercise as any)?.ideaSparks ||
    [];

  const isTransformation = exercise?.exercise_type === "reflex_transformation" || rc.sub_mode === "reflex_transformation";
  const transformTargetLabel = exercise?.targetLabel || rc.target_label || rc.targetLabel || exercise?.task || rc.task || "";
  const transformFormula = exercise?.formula || rc.formula || "";

  const isContext = exercise?.exercise_type === "reflex_context" || rc.sub_mode === "reflex_context";
  const contextRole = exercise?.role || rc.role || rc.relationship || exercise?.relationship || "Đối phương";
  const contextSpeakerJa = exercise?.speakerJa || rc.speaker_ja || prompt || "";
  const contextSpeakerVi = exercise?.speakerVi || rc.speaker_vi || rc.prompt_translation || "";
  const contextIntent = exercise?.intent || rc.intent || "";

  // Auto-translate using Google Translate Client Engine when in Vietnamese mode
  useEffect(() => {
    if (subtitleMode === "vietnamese" && exercise) {
      const textToTranslate = isConjugation ? (verb || prompt) : prompt;
      if (textToTranslate) {
        translateJaToVi(textToTranslate).then((res) => {
          if (res) setLiveTranslation(res);
        });
      }
    } else {
      setLiveTranslation("");
    }
  }, [subtitleMode, exercise, isConjugation, verb, prompt]);

  const displayTranslation = liveTranslation || staticTranslation;

  if (!exercise) {
    return (
      <div className="p-8 text-center rounded-3xl border border-dashed border-border bg-card/60 washi-texture flex flex-col items-center justify-center space-y-2">
        <div className="h-8 w-8 rounded-full border-2 border-primary/20 border-t-primary animate-spin" />
        <p className="text-xs font-bold text-muted-foreground">Đang chuẩn bị đề bài phản xạ...</p>
      </div>
    );
  }

  // Label formatting
  const subModeMap: Record<string, { label: string; ja: string; color: "sakura" | "kintsugi" | "matcha" | "fuji" | "jlpt" }> = {
    reflex_conjugation: { label: "Chia Thể Động Từ", ja: "活用", color: "sakura" },
    reflex_qna: { label: "Hỏi - Đáp Tức Thì", ja: "速答", color: "matcha" },
    reflex_transformation: { label: "Biến Đổi Câu", ja: "文型変換", color: "fuji" },
    reflex_context: { label: "Phản Ứng Tình Huống", ja: "状況対応", color: "kintsugi" },
    reflex_vocabulary: { label: "Từ Vựng Phản Xạ", ja: "語彙", color: "fuji" },
    reflex_keigo_vocab: { label: "Kính Ngữ Từ Vựng", ja: "敬語単語", color: "kintsugi" },
    mixed: { label: "Mixed Adaptive", ja: "混合", color: "kintsugi" },
  };

  const modeInfo = subModeMap[exercise.exercise_type] || { label: "Reflex Blitz", ja: "瞬発", color: "jlpt" };

  return (
    <div className="relative overflow-hidden rounded-3xl border border-border/90 bg-card shadow-sm washi-texture transition-all duration-300">
      {/* Top Header Strip */}
      <div className="bg-muted/40 border-b border-border/70 px-5 py-2.5 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Badge variant={modeInfo.color} size="sm" className="font-bold">
            {modeInfo.ja} • {modeInfo.label}
          </Badge>
        </div>

        <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground">
          {rc.jlpt_level && (
            <Badge variant="jlpt" size="sm" className="font-extrabold text-[10px]">
              {rc.jlpt_level}
            </Badge>
          )}
          <span className="px-2 py-0.5 rounded-md bg-background border text-[10px] uppercase font-bold tracking-wider">
            {exercise.difficulty || "Normal"}
          </span>
          <span>•</span>
          <span className="text-primary font-mono font-bold">
            {((rc.timer_limit_ms !== undefined ? rc.timer_limit_ms : exercise.timerLimitMs) ?? 3000) > 0
              ? `${((rc.timer_limit_ms !== undefined ? rc.timer_limit_ms : exercise.timerLimitMs) ?? 3000) / 1000}s`
              : "∞"}
          </span>
        </div>
      </div>

      {/* Main Prompt Content Area */}
      <div className="p-5 md:p-6 space-y-4">
        {isKeigoVocab ? (
          /* ====== KEIGO WORD BLITZ MODE ====== */
          <div className="text-center space-y-4">
            {/* Keigo target & Subject Ownership banner */}
            <div className="flex flex-col items-center justify-center gap-2">
              <div className="flex items-center justify-center gap-2 flex-wrap">
                <span className={`inline-flex items-center gap-1.5 px-3.5 py-1 rounded-2xl text-xs font-black border shadow-2xs ${
                  keigoTargetType === "sonkeigo"
                    ? "bg-amber-500/15 border-amber-500/30 text-amber-600 dark:text-amber-400"
                    : keigoTargetType === "kenjougo"
                    ? "bg-indigo-500/15 border-indigo-500/30 text-indigo-600 dark:text-indigo-400"
                    : "bg-emerald-500/15 border-emerald-500/30 text-emerald-600 dark:text-emerald-400"
                }`}>
                  <Crown className="h-3.5 w-3.5" />
                  <span>{keigoTargetLabel}</span>
                </span>
                {rc.jlpt_level && (
                  <Badge variant="jlpt" size="sm" className="font-extrabold text-[10px]">
                    JLPT {rc.jlpt_level}
                  </Badge>
                )}
              </div>

              {/* Subject Ownership Cue */}
              {subtitleMode !== "hidden" && keigoSubjectHint && (
                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl bg-muted/80 border border-border/80 text-xs font-bold text-foreground shadow-2xs">
                  <span>{keigoSubjectHint}</span>
                </div>
              )}
            </div>

            {subtitleMode === "hidden" ? (
              <div className="p-4 rounded-2xl bg-muted/40 border border-dashed text-center text-xs text-muted-foreground italic flex flex-col items-center justify-center space-y-2">
                <div className="flex items-center gap-2 font-bold text-amber-500 text-sm not-italic">
                  <Headphones className="h-5 w-5 animate-pulse" />
                  <span>Audio-Only: Hãy lắng nghe từ gốc và nói dạng kính ngữ</span>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <span className="inline-block text-[11px] font-bold uppercase tracking-widest text-muted-foreground">
                  Từ gốc thông thường (Plain Form)
                </span>
                <div className="text-3xl md:text-4xl font-black font-jp tracking-tight text-foreground flex justify-center">
                  <UniversalFurigana text={prompt} fontSize="xl" />
                </div>
                {keigoReading && keigoReading !== prompt && (
                  <div className="text-sm font-bold text-muted-foreground font-jp">
                    ({keigoReading})
                  </div>
                )}
                {keigoMeaning && (
                  <div className="text-sm font-semibold text-muted-foreground">
                    Ý nghĩa: <span className="font-bold text-foreground">"{keigoMeaning}"</span>
                  </div>
                )}

                {/* Target Task & Formula Hint */}
                <div className="pt-1 flex flex-col sm:flex-row items-center justify-center gap-2">
                  <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-2xl border shadow-xs animate-in fade-in zoom-in duration-200 ${
                    keigoTargetType === "sonkeigo"
                      ? "bg-amber-500/10 border-amber-500/25 text-amber-600 dark:text-amber-400"
                      : keigoTargetType === "kenjougo"
                      ? "bg-indigo-500/10 border-indigo-500/25 text-indigo-600 dark:text-indigo-400"
                      : "bg-emerald-500/10 border-emerald-500/25 text-emerald-600 dark:text-emerald-400"
                  }`}>
                    <ArrowRight className="h-4 w-4 animate-pulse" />
                    <span className="text-xs md:text-sm font-black">Nói ngay: {keigoTargetLabel}</span>
                  </div>

                  {keigoFormula && (
                    <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-2xl bg-muted/60 border border-border/80 text-xs font-mono font-bold text-foreground shadow-2xs">
                      <span className="text-[10px] uppercase font-sans font-extrabold text-amber-600 dark:text-amber-400">
                        💡 Công thức:
                      </span>
                      <span className="font-jp text-[11px] md:text-xs">{keigoFormula}</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        ) : isVocabulary ? (
          /* ====== VOCABULARY BLITZ MODE ====== */
          <div className="text-center space-y-4">
            {/* Vocabulary Badges */}
            <div className="flex items-center justify-center gap-2 flex-wrap mb-1">
              <span className="text-[10px] font-extrabold px-2.5 py-0.5 rounded-full bg-violet-500/15 text-violet-600 dark:text-violet-400 border border-violet-500/30">
                語彙 • Từ Vựng Phản Xạ
              </span>
              {vocabWordType && (
                <span className="px-2 py-0.5 rounded-lg bg-background border text-[10px] font-bold text-muted-foreground">
                  {wordTypeLabel[vocabWordType] || vocabWordType}
                </span>
              )}
            </div>

            {subtitleMode === "hidden" ? (
              <div className="p-4 rounded-2xl bg-muted/40 border border-dashed text-center text-xs text-muted-foreground italic flex flex-col items-center justify-center space-y-2">
                <div className="flex items-center gap-2 font-bold text-primary text-sm not-italic">
                  <Headphones className="h-5 w-5 animate-pulse" />
                  <span>Audio-Only: Hãy lắng nghe và phản xạ</span>
                </div>
              </div>
            ) : (
              /* 100% Spoken Japanese output challenge */
              <div className="space-y-3">
                <span className="inline-block text-[11px] font-bold uppercase tracking-widest text-muted-foreground">
                  Nghĩa tiếng Việt
                </span>
                <div className="text-2xl md:text-3xl font-black tracking-tight text-foreground">
                  {vocabWord}
                </div>

                <div className="inline-flex flex-col items-center gap-1.5 p-3 px-5 rounded-2xl bg-violet-500/10 border border-violet-500/25 shadow-xs animate-in fade-in zoom-in duration-200 max-w-lg mx-auto">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Phản xạ tiếng Nhật:</span>
                    <span className="text-xs font-extrabold text-violet-600 dark:text-violet-400 bg-violet-500/15 px-2.5 py-0.5 rounded-lg border border-violet-500/30">
                      Nói to từ vựng
                    </span>
                  </div>
                  {rc.collocation_ja && (
                    <div className="text-xs md:text-sm font-black text-foreground flex items-center justify-center gap-2 flex-wrap">
                      <span className="text-muted-foreground font-semibold">💡 Cụm tự nhiên:</span>
                      <span className="font-jp text-violet-600 dark:text-violet-400 bg-card px-2.5 py-0.5 rounded-lg border border-border/80">
                        {rc.collocation_ja}
                      </span>
                      {rc.collocation_vi && (
                        <span className="text-xs font-medium text-muted-foreground">({rc.collocation_vi})</span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        ) : isConjugation ? (
          subtitleMode === "hidden" ? (
            /* Audio-Only Mode for Conjugation */
            <div className="p-4 rounded-2xl bg-muted/40 border border-dashed text-center text-xs text-muted-foreground italic flex flex-col items-center justify-center space-y-2 max-w-md mx-auto">
              <div className="flex items-center gap-2 font-bold text-primary text-sm not-italic">
                <Headphones className="h-5 w-5 animate-pulse" />
                <span>Chế độ Audio-Only: Hãy lắng nghe động từ qua loa</span>
              </div>
              <div className="not-italic text-foreground flex items-center justify-center gap-2 flex-wrap">
                <span className="text-xs font-bold text-muted-foreground">Yêu cầu chia:</span>
                <span className="font-extrabold text-primary text-sm font-jp bg-primary/10 px-3 py-1 rounded-xl border border-primary/20">
                  {targetDetail ? `${targetDetail.formJa} — ${targetDetail.shortName}` : target || "Thể yêu cầu"}
                </span>
              </div>
            </div>
          ) : (
            /* Visible Japanese / Vietnamese Mode for Conjugation */
            <div className="text-center space-y-3.5">
              <span className="inline-block text-[11px] font-bold uppercase tracking-widest text-muted-foreground">
                Động từ gốc
              </span>
              <div className="text-2xl md:text-3xl font-black font-jp tracking-tight text-foreground flex justify-center">
                <UniversalFurigana text={verb || prompt} fontSize="xl" />
              </div>

              {displayTranslation && subtitleMode === "vietnamese" && (
                <div className="text-xs md:text-sm font-bold text-primary animate-in fade-in duration-200">
                  (Nghĩa: {displayTranslation})
                </div>
              )}

              {targetDetail ? (
                <div className="inline-flex flex-col items-center gap-1.5 p-3 px-5 rounded-2xl bg-primary/10 border border-primary/25 shadow-xs animate-in fade-in zoom-in duration-200 max-w-lg mx-auto">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Yêu cầu chia sang:</span>
                    <Badge variant="sakura" size="sm" className="font-extrabold font-jp text-xs">
                      {targetDetail.formJa}
                    </Badge>
                  </div>
                  <div className="text-sm md:text-base font-black text-primary flex items-center justify-center gap-2 flex-wrap">
                    <ArrowRight className="h-4 w-4 text-primary shrink-0 animate-pulse" />
                    <span>{targetDetail.shortName}</span>
                    <span className="text-xs font-semibold text-muted-foreground bg-card/90 px-2.5 py-0.5 rounded-lg border border-border/70">
                      {targetDetail.meaning}
                    </span>
                  </div>
                </div>
              ) : target ? (
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-2xl bg-primary/10 border border-primary/25 shadow-xs animate-in fade-in zoom-in duration-200">
                  <span className="text-xs font-bold text-muted-foreground">Chuyển sang:</span>
                  <span className="text-sm md:text-base font-black font-jp text-primary flex items-center gap-1.5">
                    <ArrowRight className="h-4 w-4" />
                    {target}
                  </span>
                </div>
              ) : null}
            </div>
          )
        ) : (
          /* Q&A / Transformation / Context Modes */
          <div className="text-center space-y-2 max-w-xl mx-auto">
            {subtitleMode === "hidden" ? (
              <div className="p-4 rounded-2xl bg-muted/40 border border-dashed text-center text-xs text-muted-foreground italic flex flex-col items-center justify-center space-y-1.5">
                <div className="flex items-center gap-2 font-bold text-primary text-sm not-italic">
                  <Headphones className="h-4 w-4 animate-pulse" />
                  <span>Chế độ Audio-Only: Hãy lắng nghe câu hỏi và phản xạ</span>
                </div>
                <p>Nội dung đề bài được ẩn để rèn luyện phản xạ thính giác 100%</p>
              </div>
            ) : (
              <div className="text-lg md:text-xl font-bold font-jp leading-relaxed text-foreground tracking-tight flex justify-center">
                <UniversalFurigana text={prompt} fontSize="lg" />
              </div>
            )}

            {displayTranslation && subtitleMode === "vietnamese" && (
              <div className="text-xs md:text-sm text-foreground/90 font-medium pt-1.5 border-t border-border/60 bg-primary/5 p-2 rounded-xl mt-2 animate-in fade-in duration-200">
                🇻🇳 Dịch nghĩa: <span className="font-bold text-primary">{displayTranslation}</span>
              </div>
            )}

            {/* Dedicated Transformation Target Badge & Formula Blueprint */}
            {isTransformation && subtitleMode !== "hidden" && (
              <div className="flex flex-col items-center gap-1.5 pt-1 animate-in fade-in duration-200">
                {transformTargetLabel && (
                  <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-2xl bg-primary/10 border border-primary/25 shadow-2xs">
                    <span className="text-[10px] font-extrabold uppercase tracking-wider text-muted-foreground flex items-center gap-1">
                      <Zap className="h-3.5 w-3.5 text-primary animate-pulse" />
                      <span>Đổi sang:</span>
                    </span>
                    <span className="text-xs md:text-sm font-black font-jp text-primary">
                      {transformTargetLabel}
                    </span>
                  </div>
                )}
                {transformFormula && (
                  <div className="inline-flex items-center gap-1.5 px-3 py-0.5 rounded-xl bg-muted/70 border border-border/80 text-xs font-mono font-bold text-foreground/90 shadow-2xs">
                    <span className="text-[10px] uppercase font-sans font-extrabold text-amber-600 dark:text-amber-400">
                      💡 Công thức:
                    </span>
                    <span className="font-jp text-[11px] md:text-xs">{transformFormula}</span>
                  </div>
                )}
              </div>
            )}

            {/* Dedicated Contextual Reaction Roleplay Prompt */}
            {isContext && subtitleMode !== "hidden" && (
              <div className="space-y-3 pt-1 animate-in fade-in duration-300">
                {/* Persona & Role Badge */}
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-2xl bg-muted/80 border border-border text-xs font-bold text-foreground shadow-2xs">
                  <span className="text-sm">
                    {contextRole.includes("Sếp") || contextRole.includes("Cấp trên")
                      ? "👔"
                      : contextRole.includes("Khách") || contextRole.includes("Đối tác")
                      ? "🤝"
                      : contextRole.includes("Bạn")
                      ? "🍻"
                      : contextRole.includes("Đồng nghiệp")
                      ? "☕"
                      : "🏪"}
                  </span>
                  <span className="font-extrabold text-primary font-jp">{contextRole}</span>
                  <span className="text-[11px] text-muted-foreground font-normal">• Lời thoại đối phương</span>
                </div>

                {/* Prominent Mission / Intent Box */}
                {contextIntent && (
                  <div className="p-3 px-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/25 text-left shadow-2xs space-y-1">
                    <div className="text-[10px] font-extrabold uppercase tracking-wider text-emerald-700 dark:text-emerald-300 flex items-center gap-1.5">
                      <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse shrink-0" />
                      <span>Nhiệm vụ phản hồi của bạn:</span>
                    </div>
                    <p className="text-xs md:text-sm font-bold text-foreground leading-snug">
                      {contextIntent}
                    </p>
                  </div>
                )}
              </div>
            )}

            {!isTransformation && !isContext && exercise.instructions && subtitleMode !== "hidden" && (
              <div className="text-xs text-muted-foreground/90 font-medium">
                🎯 {exercise.instructions}
              </div>
            )}

            {/* Speed Q&A Key Vocabulary & Answer Angles Scaffolding */}
            {subtitleMode !== "hidden" && (keyVocab.length > 0 || ideaSparks.length > 0) && (
              <div className="mt-3 pt-2.5 border-t border-border/60 flex flex-col items-center gap-2 animate-in fade-in duration-300">
                {/* Key Vocabulary Hints */}
                {keyVocab.length > 0 && (
                  <div className="flex items-center justify-center gap-1.5 flex-wrap">
                    <span className="text-[10px] font-extrabold uppercase tracking-wider text-muted-foreground flex items-center gap-1">
                      <BookOpen className="h-3 w-3 text-indigo-500" />
                      <span>Từ vựng gợi ý:</span>
                    </span>
                    {keyVocab.map((vocab, vIdx) => (
                      <span
                        key={vIdx}
                        className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-xl bg-indigo-500/10 border border-indigo-500/25 text-indigo-800 dark:text-indigo-200 text-xs font-semibold shadow-2xs"
                      >
                        <span className="font-bold font-jp">{vocab.ja}</span>
                        {vocab.vi && (
                          <span className="text-[10px] opacity-75 font-normal">
                            • {vocab.vi}
                          </span>
                        )}
                      </span>
                    ))}
                  </div>
                )}

                {/* Answer Angles / Idea Sparks */}
                {ideaSparks.length > 0 && (
                  <div className="flex items-center justify-center gap-1.5 flex-wrap">
                    <span className="text-[10px] font-extrabold uppercase tracking-wider text-muted-foreground flex items-center gap-1">
                      <Sparkles className="h-3 w-3 text-amber-500" />
                      <span>Hướng trả lời:</span>
                    </span>
                    {ideaSparks.map((spark: string, spIdx: number) => (
                      <span
                        key={spIdx}
                        className="px-2.5 py-0.5 rounded-full bg-card border border-border/80 text-foreground/90 text-xs font-medium shadow-2xs"
                      >
                        {spark}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Audio Prompt Player */}
        <div className="flex items-center justify-center gap-3 pt-1">
          <button
            type="button"
            onClick={onPlayAudio}
            className={cn(
              "inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all shadow-xs border",
              isPlaying
                ? "bg-primary text-primary-foreground border-primary animate-pulse ring-2 ring-primary/30"
                : "bg-muted/70 text-foreground border-border hover:bg-muted hover:border-primary/40"
            )}
            title="Nghe lại câu hỏi đề bài"
          >
            <Volume2 className={cn("h-3.5 w-3.5 text-primary", isPlaying && "text-white animate-bounce")} />
            <span>{isPlaying ? "Đang phát audio..." : "Nghe lại đề bài"}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
