"use client";

/**
 * Kana & Phonetic Normalizer for Japanese Reflex Training
 * Handles Homophones (同音異義語), Katakana <-> Hiragana conversions,
 * and punctuation removal for resilient spoken response matching.
 */

/**
 * Converts Katakana characters in a string to Hiragana.
 */
export function katakanaToHiragana(str: string): string {
  if (!str) return "";
  return str.replace(/[\u30a1-\u30f6]/g, (match) => {
    const chr = match.charCodeAt(0) - 0x60;
    return String.fromCharCode(chr);
  });
}

/**
 * Normalizes Japanese text:
 * 1. Converts Katakana to Hiragana
 * 2. Strips spaces, ASCII/Japanese punctuation (。、！？!? .)
 * 3. Lowercases alphabet characters
 */
export function normalizeJapaneseSpeech(text: string): string {
  if (!text) return "";
  let norm = text.trim();
  // Strip Japanese & ASCII punctuation and whitespace
  norm = norm.replace(/[。！？、\s\!\?\,\.\u3000]+/g, "");
  // Convert Katakana to Hiragana
  norm = katakanaToHiragana(norm);
  return norm.toLowerCase();
}

/**
 * Dictionary of common verb stems to their pure Hiragana phonetic readings.
 * Ensures that homophone misrecognitions by STT (e.g. 帰らない vs 変えない vs かえらない)
 * match identically.
 */
export const VERB_HOMOPHONE_MAP: Record<string, string[]> = {
  "かえる": ["帰る", "変える", "買える", "代える", "換える", "孵る", "蛙"],
  "きく": ["聞く", "聴く", "効く", "利く", "菊"],
  "いく": ["行く", "逝く", "生く"],
  "あう": ["会う", "合う", "逢う", "遭う"],
  "みる": ["見る", "観る", "視る", "診る"],
  "かく": ["書く", "描く", "掻く"],
  "とる": ["取る", "撮る", "採る", "捕る", "執る"],
  "きる": ["着る", "切る", "斬る", "伐る"],
  "はなす": ["話す", "離す", "放す"],
  "かう": ["買う", "飼う"],
  "たつ": ["立つ", "建つ", "経つ", "絶つ", "断つ"],
  "つく": ["着く", "付く", "突く", "就く"],
  "しる": ["知る", "汁"],
  "いる": ["居る", "要る", "入る", "射る", "煎る"],
  "あける": ["開ける", "明ける", "空ける"],
  "しめる": ["閉める", "締める", "占める"],
};

/**
 * Check if two Japanese strings are phonetically equivalent (matching homophones or hiragana).
 */
export function isPhoneticallyEquivalent(input: string, target: string): boolean {
  const normInput = normalizeJapaneseSpeech(input);
  const normTarget = normalizeJapaneseSpeech(target);

  if (normInput === normTarget) return true;

  // Check homophone groups
  for (const [kanaReading, variants] of Object.entries(VERB_HOMOPHONE_MAP)) {
    const inputMatches = variants.some((v) => normInput.includes(normalizeJapaneseSpeech(v))) || normInput.includes(kanaReading);
    const targetMatches = variants.some((v) => normTarget.includes(normalizeJapaneseSpeech(v))) || normTarget.includes(kanaReading);

    if (inputMatches && targetMatches) {
      return true;
    }
  }

  return false;
}
