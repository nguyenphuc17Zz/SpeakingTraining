"use client";

// In-memory translation cache for zero-latency lookups
const translationCache = new Map<string, string>();

// Local common Japanese verb dictionary fallback
const LOCAL_VERB_MAP: Record<string, string> = {
  "食べる": "Ăn",
  "見る": "Xem, nhìn",
  "行く": "Đi",
  "書く": "Viết",
  "読む": "Đọc",
  "飲む": "Uống",
  "する": "Làm",
  "来る": "Đến",
  "話す": "Nói chuyện",
  "買う": "Mua",
  "待つ": "Chờ, đợi",
  "立つ": "Đứng",
  "教える": "Dạy, chỉ bảo",
  "考える": "Suy nghĩ",
  "借りる": "Mượn",
  "出る": "Ra ngoài, rời khỏi",
  "泳ぐ": "Bơi",
  "急ぐ": "Vội, gấp",
  "信じる": "Tin tưởng",
  "感じる": "Cảm thấy",
  "覚える": "Ghi nhớ, học thuộc",
  "届ける": "Giao, gửi đến",
  "調べる": "Tra cứu, tìm hiểu",
  "歩く": "Đi bộ",
  "走る": "Chạy",
  "寝る": "Ngủ",
  "起きる": "Thức dậy",
  "働く": "Làm việc",
  "休む": "Nghỉ ngơi",
  "聞く": "Nghe, hỏi",
  "会う": "Gặp gỡ",
  "遊ぶ": "Chơi",
  "呼ぶ": "Gọi",
  "開ける": "Mở",
  "閉める": "Đóng",
};

/**
 * Translate Japanese text to Vietnamese using free Google Translate Client Engine.
 * 100% Free, Zero token cost, cached in-memory.
 */
export async function translateJaToVi(text: string): Promise<string> {
  if (!text || !text.trim()) return "";
  const trimmed = text.trim();

  // 1. Check in-memory cache
  if (translationCache.has(trimmed)) {
    return translationCache.get(trimmed)!;
  }

  // 2. Check local quick dictionary
  if (LOCAL_VERB_MAP[trimmed]) {
    const res = LOCAL_VERB_MAP[trimmed];
    translationCache.set(trimmed, res);
    return res;
  }

  // 3. Fetch from Google Translate Public API
  try {
    const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=ja&tl=vi&dt=t&q=${encodeURIComponent(
      trimmed
    )}`;
    const response = await fetch(url);
    if (!response.ok) throw new Error("Google Translate HTTP error");

    const data = await response.json();
    if (Array.isArray(data) && Array.isArray(data[0])) {
      const translated = data[0]
        .map((segment: any) => segment?.[0] || "")
        .filter(Boolean)
        .join("")
        .trim();

      if (translated) {
        translationCache.set(trimmed, translated);
        return translated;
      }
    }
  } catch (err) {
    console.warn("[GoogleTranslate] Auto-translation failed, using fallback:", err);
  }

  // Fallback to local map or empty
  return LOCAL_VERB_MAP[trimmed] || "";
}
