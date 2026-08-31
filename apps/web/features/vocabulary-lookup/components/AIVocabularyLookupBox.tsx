"use client";

import React, { useState, useEffect, useRef } from "react";
import ReactDOM from "react-dom";
import {
  Sparkles,
  Volume2,
  Bookmark,
  BookmarkCheck,
  Copy,
  Check,
  RefreshCw,
  X,
  FileText,
  HelpCircle,
  Zap,
  BookOpen,
  ArrowUpRight,
  Layers,
  Send,
  Edit3,
} from "lucide-react";
import { useVocabularyLookup } from "../context/VocabularyLookupContext";
import { dispatchToast } from "@/lib/toast";

const JLPT_LEVELS = ["N5", "N4", "N3", "N2", "N1"];
const REGISTERS = [
  { id: "auto", label: "Tự động" },
  { id: "casual", label: "Thân mật" },
  { id: "polite", label: "Lịch sự" },
  { id: "business", label: "Kính ngữ" },
];

export function AIVocabularyLookupBox() {
  const {
    isOpen,
    closeLookup,
    query,
    contextText,
    targetLevel,
    registerPreference,
    lookupResult,
    isLoading,
    error,
    isSaved,
    isSaving,
    setQuery,
    setContextText,
    setTargetLevel,
    setRegisterPreference,
    fetchLookup,
    saveToNotebook,
    insertTextToActiveInput,
    openLookup,
  } = useVocabularyLookup();

  const [mounted, setMounted] = useState(false);
  const [activeTab, setActiveTab] = useState<"nuance" | "alternatives">("nuance");
  const [copied, setCopied] = useState(false);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [showContextEditor, setShowContextEditor] = useState(false);

  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Reset tab when result changes
  useEffect(() => {
    if (lookupResult) {
      setActiveTab("nuance");
    }
  }, [lookupResult]);

  // Keyboard escape listener and focus
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === "Escape") {
          closeLookup();
        }
      };
      window.addEventListener("keydown", handleKeyDown);
      return () => {
        document.body.style.overflow = "unset";
        window.removeEventListener("keydown", handleKeyDown);
      };
    }
  }, [isOpen, closeLookup]);

  // Audio speech synthesis helper
  const playJapaneseAudio = (textToSpeak: string) => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      dispatchToast("Trình duyệt không hỗ trợ phát âm thanh.", "info");
      return;
    }

    try {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(textToSpeak);
      utterance.lang = "ja-JP";
      utterance.rate = 0.9;

      utterance.onstart = () => setIsPlayingAudio(true);
      utterance.onend = () => setIsPlayingAudio(false);
      utterance.onerror = () => setIsPlayingAudio(false);

      window.speechSynthesis.speak(utterance);
    } catch {
      setIsPlayingAudio(false);
    }
  };

  const handleCopyAnalysis = () => {
    if (!lookupResult?.best_match) return;
    const bm = lookupResult.best_match;
    const text = [
      `Từ vựng: ${bm.expression} (${bm.reading})`,
      `Nghĩa tiếng Việt: ${bm.meaning_vi}`,
      `Từ loại: ${bm.part_of_speech} | Cấp độ: ${bm.jlpt_level} | Sắc thái: ${bm.register}`,
      `Giải thích sắc thái: ${bm.nuance_explanation}`,
      bm.usage_collocation ? `Cụm từ liên kết: ${bm.usage_collocation}` : "",
      ...bm.examples.map(
        (ex, idx) =>
          `Ví dụ ${idx + 1} (${ex.situation || "Thực tế"}): ${ex.ja} — ${ex.vi}`
      ),
    ]
      .filter(Boolean)
      .join("\n");

    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(text);
      setCopied(true);
      dispatchToast("Đã sao chép toàn bộ phân tích từ vựng!", "success");
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (!mounted || !isOpen) return null;

  const bm = lookupResult?.best_match;
  const alts = lookupResult?.alternatives || [];

  return ReactDOM.createPortal(
    <div className="fixed inset-0 z-[100000] flex items-center justify-center p-3 sm:p-4 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 dark:bg-black/80 backdrop-blur-sm transition-opacity animate-in fade-in duration-200"
        onClick={closeLookup}
      />

      {/* Modal Dialog Container */}
      <div
        className="relative z-10 w-full max-w-2xl max-h-[90vh] flex flex-col rounded-2xl sm:rounded-3xl
          bg-card text-foreground
          border border-border/80 shadow-2xl shadow-black/20 dark:shadow-black/60
          backdrop-blur-xl animate-in fade-in zoom-in-95 duration-200 overflow-hidden"
      >
        {/* Top Header Bar */}
        <div className="flex items-center justify-between px-4 sm:px-5 py-3 border-b border-border/60 bg-muted/30 shrink-0">
          <div className="flex items-center gap-2.5">
            <span className="h-7 w-7 sm:h-8 sm:w-8 rounded-xl bg-primary/10 text-primary border border-primary/20 flex items-center justify-center shadow-sm shrink-0">
              <Sparkles className="h-4 w-4" />
            </span>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm sm:text-base font-extrabold tracking-tight text-foreground">
                  Tra Cứu Từ Vựng AI
                </h3>
                <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded-full bg-primary/15 text-primary border border-primary/25">
                  Theo ngữ cảnh
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-1.5">
            {bm && (
              <button
                onClick={handleCopyAnalysis}
                type="button"
                className="h-8 px-2.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted text-xs font-medium flex items-center gap-1 transition-colors"
                title="Sao chép toàn bộ"
              >
                {copied ? (
                  <>
                    <Check className="h-3.5 w-3.5 text-primary" />
                    <span className="text-primary text-[11px]">Đã chép</span>
                  </>
                ) : (
                  <>
                    <Copy className="h-3.5 w-3.5" />
                    <span className="text-[11px] hidden sm:inline">Sao chép</span>
                  </>
                )}
              </button>
            )}

            <button
              onClick={closeLookup}
              className="h-8 w-8 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted flex items-center justify-center transition-colors"
              aria-label="Đóng"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Search & Context Controls Bar */}
        <div className="px-4 sm:px-5 py-3 border-b border-border/50 bg-background/50 flex flex-col gap-2.5 shrink-0">
          {/* Main Search Input */}
          <div className="flex items-center gap-2">
            <div className="relative flex-1">
              <input
                ref={inputRef}
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    fetchLookup();
                  }
                }}
                placeholder="Nhập từ hoặc cụm từ tiếng Nhật..."
                className="w-full h-9 pl-3.5 pr-8 rounded-xl bg-card border border-border/80 text-sm font-jp font-medium text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all shadow-sm"
              />
              {query && (
                <button
                  type="button"
                  onClick={() => setQuery("")}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground p-0.5"
                >
                  <X className="h-3 w-3" />
                </button>
              )}
            </div>

            <button
              onClick={() => fetchLookup()}
              disabled={isLoading || !query.trim()}
              className="h-9 px-4 rounded-xl bg-primary hover:bg-primary/90 disabled:opacity-50 text-primary-foreground text-xs font-bold flex items-center gap-1.5 shadow-sm transition-all active:scale-95 shrink-0"
            >
              <RefreshCw
                className={`h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`}
              />
              <span>Phân Tích</span>
            </button>
          </div>

          {/* Context Snippet Drawer */}
          <div className="flex flex-col gap-1">
            {showContextEditor ? (
              <div className="space-y-1.5 animate-in fade-in duration-150">
                <div className="flex items-center justify-between text-[11px] text-muted-foreground">
                  <span className="flex items-center gap-1 font-medium">
                    <FileText className="h-3 w-3 text-primary" />
                    Chỉnh sửa ngữ cảnh câu văn:
                  </span>
                  <button
                    type="button"
                    onClick={() => setShowContextEditor(false)}
                    className="text-primary hover:underline text-[11px] font-medium"
                  >
                    Xong
                  </button>
                </div>
                <textarea
                  value={contextText}
                  onChange={(e) => setContextText(e.target.value)}
                  rows={2}
                  placeholder="Nhập câu văn hoặc đoạn văn chứa từ..."
                  className="w-full p-2.5 rounded-xl bg-card border border-border/80 text-xs font-jp text-foreground focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all resize-none shadow-sm"
                />
              </div>
            ) : contextText ? (
              <div className="flex items-center justify-between gap-2 px-2.5 py-1.5 rounded-xl bg-muted/40 border border-border/50 text-xs font-jp">
                <div className="flex items-center gap-1.5 min-w-0 text-muted-foreground">
                  <FileText className="h-3 w-3 text-primary shrink-0" />
                  <span className="line-clamp-1 italic text-foreground/85">
                    「{contextText}」
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => setShowContextEditor(true)}
                  className="text-primary hover:underline text-[11px] font-medium shrink-0 flex items-center gap-1"
                >
                  <Edit3 className="h-2.5 w-2.5" />
                  <span>Sửa</span>
                </button>
              </div>
            ) : (
              <div className="flex items-center justify-between text-[11px] text-muted-foreground/70">
                <button
                  type="button"
                  onClick={() => setShowContextEditor(true)}
                  className="text-primary hover:underline flex items-center gap-1 font-medium"
                >
                  + Thêm ngữ cảnh câu văn để phân tích sắc thái chính xác
                </button>
              </div>
            )}
          </div>

          {/* Filter Pills (JLPT & Register) */}
          <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-border/40 text-[11px]">
            <div className="flex items-center gap-1">
              <span className="text-muted-foreground font-semibold mr-1">
                JLPT:
              </span>
              {JLPT_LEVELS.map((lvl) => (
                <button
                  key={lvl}
                  type="button"
                  onClick={() => {
                    setTargetLevel(lvl);
                    fetchLookup(undefined, undefined, lvl);
                  }}
                  className={`text-[10px] font-bold px-2 py-0.5 rounded-md border transition-all ${
                    targetLevel === lvl
                      ? "bg-primary text-primary-foreground border-primary shadow-xs"
                      : "bg-muted/40 text-muted-foreground border-border/60 hover:bg-muted hover:text-foreground"
                  }`}
                >
                  {lvl}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-1">
              <span className="text-muted-foreground font-semibold mr-1">
                Sắc thái:
              </span>
              {REGISTERS.map((reg) => (
                <button
                  key={reg.id}
                  type="button"
                  onClick={() => {
                    setRegisterPreference(reg.id);
                    fetchLookup(undefined, undefined, undefined, reg.id);
                  }}
                  className={`text-[10px] font-medium px-2 py-0.5 rounded-md border transition-all ${
                    registerPreference === reg.id
                      ? "bg-amber-500/15 text-amber-700 dark:text-amber-300 border-amber-500/40 shadow-xs font-bold"
                      : "bg-muted/40 text-muted-foreground border-border/60 hover:bg-muted hover:text-foreground"
                  }`}
                >
                  {reg.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Scrollable Content Body */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-5 space-y-4 min-h-[260px]">
          {/* Loading Skeleton State */}
          {isLoading && (
            <div className="space-y-3.5 animate-pulse">
              <div className="p-4 rounded-2xl bg-muted/40 border border-border/40 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="h-7 w-32 bg-muted rounded-lg" />
                  <div className="h-5 w-16 bg-muted rounded-md" />
                </div>
                <div className="h-4 w-44 bg-muted/80 rounded" />
                <div className="h-5 w-60 bg-primary/20 rounded" />
              </div>
              <div className="p-4 rounded-2xl bg-muted/30 border border-border/30 space-y-2">
                <div className="h-4 w-28 bg-muted rounded" />
                <div className="h-3 w-full bg-muted/60 rounded" />
                <div className="h-3 w-4/5 bg-muted/60 rounded" />
              </div>
            </div>
          )}

          {/* Error State */}
          {!isLoading && error && (
            <div className="p-5 rounded-2xl bg-destructive/10 border border-destructive/20 text-center space-y-3">
              <div className="h-9 w-9 mx-auto rounded-full bg-destructive/15 text-destructive flex items-center justify-center">
                <HelpCircle className="h-5 w-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-destructive">
                  Không thể phân tích từ vựng
                </h4>
                <p className="text-xs text-muted-foreground mt-1">{error}</p>
              </div>
              <button
                onClick={() => fetchLookup()}
                className="px-4 py-1.5 rounded-xl bg-primary text-primary-foreground text-xs font-bold shadow hover:bg-primary/90 transition-all"
              >
                Thử lại
              </button>
            </div>
          )}

          {/* Success Result View */}
          {!isLoading && !error && bm && (
            <div className="space-y-3.5">
              {/* 1. Hero Word Banner Card */}
              <div className="p-4 sm:p-5 rounded-2xl bg-gradient-to-br from-card via-card to-primary/5 border border-border/80 shadow-sm space-y-2.5 relative">
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-0.5">
                    {/* Furigana Reading */}
                    <div className="text-xs font-jp font-semibold text-primary tracking-wider">
                      {bm.reading}
                    </div>
                    {/* Main Expression */}
                    <div className="flex items-center gap-2.5">
                      <h2 className="text-2xl sm:text-3xl font-extrabold font-jp tracking-tight text-foreground">
                        {bm.expression}
                      </h2>
                      {/* Audio Button */}
                      <button
                        onClick={() => playJapaneseAudio(bm.expression)}
                        type="button"
                        className={`h-7 w-7 rounded-full flex items-center justify-center transition-all ${
                          isPlayingAudio
                            ? "bg-primary text-primary-foreground scale-110 shadow-sm"
                            : "bg-muted text-muted-foreground hover:text-foreground hover:bg-muted/80"
                        }`}
                        title="Nghe phát âm chuẩn"
                      >
                        <Volume2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>

                  {/* Level & Register Badges */}
                  <div className="flex flex-col items-end gap-1 shrink-0">
                    <div className="flex items-center gap-1.5">
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-primary/10 text-primary border border-primary/25">
                        {bm.jlpt_level}
                      </span>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-amber-500/10 text-amber-700 dark:text-amber-300 border border-amber-500/25">
                        {bm.register}
                      </span>
                    </div>
                    <div className="text-[10px] text-muted-foreground flex items-center gap-1">
                      <span>Tự nhiên:</span>
                      <span className="font-bold text-primary">
                        {bm.naturalness_score}%
                      </span>
                    </div>
                  </div>
                </div>

                {/* Meaning */}
                <div className="pt-2 border-t border-border/50 flex items-baseline gap-2">
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-muted text-muted-foreground border border-border/40">
                    {bm.part_of_speech}
                  </span>
                  <span className="text-base sm:text-lg font-extrabold text-foreground">
                    {bm.meaning_vi}
                  </span>
                </div>
              </div>

              {/* Segmented Tab Navigation */}
              <div className="flex items-center gap-1 p-1 rounded-xl bg-muted/50 border border-border/60">
                <button
                  type="button"
                  onClick={() => setActiveTab("nuance")}
                  className={`flex-1 py-1.5 px-3 rounded-lg text-xs font-bold flex items-center justify-center gap-1.5 transition-all ${
                    activeTab === "nuance"
                      ? "bg-card text-foreground shadow-xs border border-border/50"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <Sparkles className="h-3.5 w-3.5 text-primary" />
                  <span>Sắc Thái & Ví Dụ</span>
                </button>

                <button
                  type="button"
                  onClick={() => setActiveTab("alternatives")}
                  className={`flex-1 py-1.5 px-3 rounded-lg text-xs font-bold flex items-center justify-center gap-1.5 transition-all ${
                    activeTab === "alternatives"
                      ? "bg-card text-foreground shadow-xs border border-border/50"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <Layers className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400" />
                  <span>Từ Thay Thế ({alts.length})</span>
                </button>
              </div>

              {/* Tab 1 Content: Nuance, Collocations, Examples */}
              {activeTab === "nuance" && (
                <div className="space-y-3 animate-in fade-in duration-150">
                  {/* Nuance Analysis Card */}
                  <div className="p-3.5 rounded-2xl bg-primary/5 border border-primary/20 space-y-1.5">
                    <div className="flex items-center gap-1.5 text-xs font-bold text-primary">
                      <Sparkles className="h-3.5 w-3.5" />
                      <span>Giải Thích Sắc Thái Ngữ Cảnh</span>
                    </div>
                    <p className="text-xs sm:text-sm text-foreground/90 leading-relaxed pl-5 font-normal">
                      {bm.nuance_explanation}
                    </p>
                  </div>

                  {/* Collocations */}
                  {bm.usage_collocation && (
                    <div className="p-3 rounded-2xl bg-muted/40 border border-border/60 flex items-start gap-2">
                      <Zap className="h-4 w-4 text-amber-500 shrink-0 mt-0.5" />
                      <div className="space-y-0.5 flex-1">
                        <span className="text-[11px] font-bold text-amber-700 dark:text-amber-300">
                          Cụm từ liên kết tự nhiên (Collocations):
                        </span>
                        <p className="text-xs font-jp font-medium text-foreground">
                          {bm.usage_collocation}
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Example Sentences */}
                  {bm.examples && bm.examples.length > 0 && (
                    <div className="space-y-2">
                      <div className="flex items-center gap-1.5 text-xs font-bold text-muted-foreground px-1">
                        <BookOpen className="h-3.5 w-3.5 text-primary" />
                        <span>Ví Dụ Thực Tế & Hoàn Cảnh</span>
                      </div>

                      <div className="grid grid-cols-1 gap-2">
                        {bm.examples.map((ex, index) => (
                          <div
                            key={index}
                            className="p-3 rounded-xl bg-card border border-border/70 space-y-1 hover:border-primary/40 transition-all shadow-2xs"
                          >
                            <div className="flex items-center justify-between gap-2">
                              <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-muted text-muted-foreground border border-border/40">
                                {ex.situation || `Ví dụ ${index + 1}`}
                              </span>
                              <button
                                onClick={() => playJapaneseAudio(ex.ja)}
                                className="h-6 w-6 rounded bg-muted hover:bg-muted/80 text-muted-foreground hover:text-foreground flex items-center justify-center transition-colors"
                                title="Nghe câu ví dụ"
                              >
                                <Volume2 className="h-3 w-3" />
                              </button>
                            </div>
                            <p className="text-xs sm:text-sm font-jp font-medium text-foreground leading-snug">
                              {ex.ja}
                            </p>
                            <p className="text-xs text-muted-foreground leading-normal">
                              {ex.vi}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Tab 2 Content: Alternatives & Synonyms */}
              {activeTab === "alternatives" && (
                <div className="space-y-2.5 animate-in fade-in duration-150">
                  {alts && alts.length > 0 ? (
                    <div className="grid grid-cols-1 gap-2.5">
                      {alts.map((alt, index) => (
                        <div
                          key={index}
                          className="p-3.5 rounded-xl bg-card border border-border/70 hover:border-primary/40 transition-all space-y-2 shadow-2xs"
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div>
                              <div className="flex items-baseline gap-1.5">
                                <span className="font-jp font-bold text-sm sm:text-base text-foreground">
                                  {alt.expression}
                                </span>
                                <span className="text-[11px] text-muted-foreground font-jp">
                                  ({alt.reading})
                                </span>
                              </div>
                              <p className="text-xs font-bold text-primary mt-0.5">
                                {alt.meaning_vi}
                              </p>
                            </div>

                            <button
                              onClick={() =>
                                openLookup(alt.expression, contextText, true)
                              }
                              className="text-[11px] text-primary hover:underline flex items-center gap-0.5 font-medium shrink-0"
                              title="Tra cứu từ này"
                            >
                              <span>Tra cứu</span>
                              <ArrowUpRight className="h-3 w-3" />
                            </button>
                          </div>

                          <p className="text-xs text-muted-foreground leading-relaxed pl-2 border-l-2 border-amber-500/40">
                            <strong className="text-foreground/90 font-medium">
                              Khác biệt sắc thái:{" "}
                            </strong>
                            {alt.difference_explanation}
                          </p>

                          <div className="flex justify-end pt-1">
                            <button
                              onClick={() =>
                                insertTextToActiveInput(alt.expression)
                              }
                              className="text-[11px] px-2.5 py-1 rounded-lg bg-muted hover:bg-primary/15 hover:text-primary text-muted-foreground font-medium transition-colors"
                            >
                              + Chèn từ này vào ô gõ
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="p-6 text-center text-xs text-muted-foreground">
                      Không có từ thay thế trực tiếp cho cụm từ này.
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Action Toolbar Bottom Bar */}
        {bm && (
          <div className="px-4 sm:px-5 py-3 border-t border-border/60 bg-muted/20 flex items-center justify-between gap-2 shrink-0">
            {/* 1-Tap Insertion */}
            <button
              onClick={() => insertTextToActiveInput(bm.expression)}
              type="button"
              className="px-3.5 py-2 rounded-xl bg-card hover:bg-muted text-foreground text-xs font-bold flex items-center gap-1.5 border border-border/80 hover:border-primary/40 transition-all active:scale-95 shadow-xs"
              title="Chèn từ vào ô soạn thảo đang active hoặc sao chép"
            >
              <Send className="h-3.5 w-3.5 text-primary" />
              <span>Chèn vào ô gõ</span>
            </button>

            {/* Save to Notebook */}
            <button
              onClick={saveToNotebook}
              disabled={isSaved || isSaving}
              type="button"
              className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-sm transition-all active:scale-95 ${
                isSaved
                  ? "bg-primary/15 text-primary border border-primary/30 cursor-default"
                  : "bg-primary hover:bg-primary/90 text-primary-foreground"
              }`}
            >
              {isSaving ? (
                <>
                  <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                  <span>Đang lưu...</span>
                </>
              ) : isSaved ? (
                <>
                  <BookmarkCheck className="h-3.5 w-3.5 text-primary" />
                  <span>Đã lưu vào Sổ tay</span>
                </>
              ) : (
                <>
                  <Bookmark className="h-3.5 w-3.5" />
                  <span>Lưu vào Sổ tay</span>
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>,
    document.body
  );
}
