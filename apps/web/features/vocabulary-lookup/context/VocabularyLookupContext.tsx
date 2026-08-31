"use client";

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import {
  BubbleSelectionState,
  VocabularyLookupRequest,
  VocabularyLookupResponse,
} from "@/types/vocabulary-lookup";
import { vocabularyApi } from "@/services/vocabulary-api";
import { dispatchToast } from "@/lib/toast";

interface VocabularyLookupContextValue {
  isOpen: boolean;
  query: string;
  contextText: string;
  targetLevel: string;
  registerPreference: string;
  lookupResult: VocabularyLookupResponse | null;
  isLoading: boolean;
  error: string | null;
  isSaved: boolean;
  isSaving: boolean;
  selectionState: BubbleSelectionState | null;
  isBubbleVisible: boolean;

  openLookup: (
    query: string,
    context?: string,
    autoFetch?: boolean,
    inputElement?: HTMLInputElement | HTMLTextAreaElement | null
  ) => void;
  closeLookup: () => void;
  setQuery: (q: string) => void;
  setContextText: (ctx: string) => void;
  setTargetLevel: (lvl: string) => void;
  setRegisterPreference: (reg: string) => void;
  fetchLookup: (
    q?: string,
    ctx?: string,
    level?: string,
    reg?: string
  ) => Promise<void>;
  saveToNotebook: () => Promise<boolean>;
  insertTextToActiveInput: (textToInsert: string) => void;
  setSelectionState: (state: BubbleSelectionState | null) => void;
  hideBubble: () => void;
}

const VocabularyLookupContext = createContext<VocabularyLookupContextValue | null>(
  null
);

export function VocabularyLookupProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [query, setQuery] = useState<string>("");
  const [contextText, setContextText] = useState<string>("");
  const [targetLevel, setTargetLevel] = useState<string>("N3");
  const [registerPreference, setRegisterPreference] = useState<string>("auto");
  const [lookupResult, setLookupResult] = useState<VocabularyLookupResponse | null>(
    null
  );
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [isSaved, setIsSaved] = useState<boolean>(false);
  const [isSaving, setIsSaving] = useState<boolean>(false);

  const [selectionState, setSelectionState] = useState<BubbleSelectionState | null>(
    null
  );
  const [isBubbleVisible, setIsBubbleVisible] = useState<boolean>(false);

  // Store last active input/textarea to support 1-tap insertion
  const lastActiveInputRef = useRef<HTMLInputElement | HTMLTextAreaElement | null>(
    null
  );
  const lastSelectionRangeRef = useRef<{ start: number; end: number } | null>(
    null
  );

  const hideBubble = useCallback(() => {
    setIsBubbleVisible(false);
  }, []);

  const handleSetSelectionState = useCallback(
    (state: BubbleSelectionState | null) => {
      setSelectionState(state);
      if (state && state.text.trim().length > 0) {
        setIsBubbleVisible(true);
        if (state.inputElement) {
          lastActiveInputRef.current = state.inputElement;
          if (
            typeof state.selectionStart === "number" &&
            typeof state.selectionEnd === "number"
          ) {
            lastSelectionRangeRef.current = {
              start: state.selectionStart,
              end: state.selectionEnd,
            };
          }
        }
      } else {
        setIsBubbleVisible(false);
      }
    },
    []
  );

  const fetchLookup = useCallback(
    async (
      customQuery?: string,
      customContext?: string,
      customLevel?: string,
      customReg?: string
    ) => {
      const q = (customQuery !== undefined ? customQuery : query).trim();
      const ctx = (customContext !== undefined ? customContext : contextText).trim();
      const lvl = customLevel !== undefined ? customLevel : targetLevel;
      const reg = customReg !== undefined ? customReg : registerPreference;

      if (!q) {
        setError("Vui lòng nhập từ hoặc cụm từ cần tra cứu.");
        return;
      }

      setIsLoading(true);
      setError(null);
      setIsSaved(false);

      try {
        const payload: VocabularyLookupRequest = {
          query: q,
          context: ctx,
          target_level: lvl,
          register_preference: reg,
        };

        const res = await vocabularyApi.lookupAI(payload);
        setLookupResult(res);
      } catch (err: any) {
        console.error("Vocabulary lookup error:", err);
        setError(
          err?.message || "Không thể phân tích từ vựng lúc này. Vui lòng thử lại!"
        );
      } finally {
        setIsLoading(false);
      }
    },
    [query, contextText, targetLevel, registerPreference]
  );

  const openLookup = useCallback(
    (
      newQuery: string,
      newContext?: string,
      autoFetch: boolean = true,
      inputElement?: HTMLInputElement | HTMLTextAreaElement | null
    ) => {
      const trimmedQ = newQuery.trim();
      setQuery(trimmedQ);
      setContextText(newContext || "");
      setError(null);
      setIsSaved(false);
      hideBubble();

      if (inputElement) {
        lastActiveInputRef.current = inputElement;
        lastSelectionRangeRef.current = {
          start: inputElement.selectionStart || 0,
          end: inputElement.selectionEnd || 0,
        };
      }

      setIsOpen(true);

      if (autoFetch && trimmedQ) {
        fetchLookup(trimmedQ, newContext || "");
      }
    },
    [fetchLookup, hideBubble]
  );

  const closeLookup = useCallback(() => {
    setIsOpen(false);
  }, []);

  const saveToNotebook = useCallback(async (): Promise<boolean> => {
    if (!lookupResult?.best_match || isSaved || isSaving) return false;

    setIsSaving(true);
    try {
      const bm = lookupResult.best_match;
      await vocabularyApi.saveToNotebook({
        expression: bm.expression,
        reading: bm.reading,
        meaning_vi: bm.meaning_vi,
        nuance_explanation: bm.nuance_explanation,
        context: contextText || (bm.examples[0] ? bm.examples[0].ja : ""),
        jlpt_level: bm.jlpt_level,
        part_of_speech: bm.part_of_speech,
        register: bm.register,
        tags: [bm.jlpt_level, bm.register].filter(Boolean),
      });

      setIsSaved(true);
      dispatchToast(
        `Đã lưu 「${bm.expression}」 vào Sổ tay từ vựng & Lộ trình học!`,
        "success"
      );
      return true;
    } catch (err: any) {
      console.error("Failed to save notebook:", err);
      dispatchToast(
        err?.message || "Lỗi lưu vào sổ tay từ vựng.",
        "error"
      );
      return false;
    } finally {
      setIsSaving(false);
    }
  }, [lookupResult, isSaved, isSaving, contextText]);

  const insertTextToActiveInput = useCallback(
    (textToInsert: string) => {
      const el = lastActiveInputRef.current;
      if (!el || typeof document === "undefined" || !document.body.contains(el)) {
        // Fallback: Copy to clipboard if no input active
        if (typeof navigator !== "undefined" && navigator.clipboard) {
          navigator.clipboard.writeText(textToInsert);
          dispatchToast(`Đã sao chép 「${textToInsert}」 vào bộ nhớ tạm!`, "info");
        }
        return;
      }

      try {
        el.focus();
        const start =
          lastSelectionRangeRef.current?.start ??
          el.selectionStart ??
          el.value.length;
        const end =
          lastSelectionRangeRef.current?.end ??
          el.selectionEnd ??
          el.value.length;

        const val = el.value;
        const before = val.substring(0, start);
        const after = val.substring(end);
        const newVal = `${before}${textToInsert}${after}`;

        el.value = newVal;

        // Trigger react onChange if bound
        el.dispatchEvent(new Event("input", { bubbles: true }));
        el.dispatchEvent(new Event("change", { bubbles: true }));

        // Move caret right after inserted text
        const nextPos = start + textToInsert.length;
        el.setSelectionRange(nextPos, nextPos);

        dispatchToast(`Đã chèn 「${textToInsert}」 vào ô nhập liệu!`, "success");
      } catch (err) {
        console.error("Insert text error:", err);
      }
    },
    []
  );

  // Global Keyboard Shortcut: Ctrl+Shift+K or Cmd+Shift+K
  useEffect(() => {
    const handleGlobalKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === "k") {
        e.preventDefault();
        e.stopPropagation();

        if (isOpen) {
          closeLookup();
          return;
        }

        // Check if there is active selection in window
        let selectedText = "";
        let context = "";
        let inputEl: HTMLInputElement | HTMLTextAreaElement | null = null;

        const activeEl = document.activeElement;
        if (
          activeEl &&
          (activeEl instanceof HTMLInputElement ||
            activeEl instanceof HTMLTextAreaElement)
        ) {
          inputEl = activeEl;
          const start = activeEl.selectionStart || 0;
          const end = activeEl.selectionEnd || 0;
          if (start !== end) {
            selectedText = activeEl.value.substring(start, end);
            // Context: surrounding sentence or whole line
            context = activeEl.value;
          }
        }

        if (!selectedText && typeof window !== "undefined") {
          const sel = window.getSelection();
          if (sel && sel.rangeCount > 0) {
            selectedText = sel.toString().trim();
            const node = sel.anchorNode;
            if (node) {
              const parent =
                node instanceof HTMLElement ? node : node.parentElement;
              const container = parent?.closest(
                "p, div, li, blockquote, article, section, h1, h2, h3, h4, h5, h6"
              );
              context = container?.textContent?.trim() || "";
            }
          }
        }

        openLookup(selectedText, context, Boolean(selectedText), inputEl);
      }
    };

    window.addEventListener("keydown", handleGlobalKeyDown);
    return () => window.removeEventListener("keydown", handleGlobalKeyDown);
  }, [isOpen, openLookup, closeLookup]);

  const value: VocabularyLookupContextValue = {
    isOpen,
    query,
    contextText,
    targetLevel,
    registerPreference,
    lookupResult,
    isLoading,
    error,
    isSaved,
    isSaving,
    selectionState,
    isBubbleVisible,
    openLookup,
    closeLookup,
    setQuery,
    setContextText,
    setTargetLevel,
    setRegisterPreference,
    fetchLookup,
    saveToNotebook,
    insertTextToActiveInput,
    setSelectionState: handleSetSelectionState,
    hideBubble,
  };

  return (
    <VocabularyLookupContext.Provider value={value}>
      {children}
    </VocabularyLookupContext.Provider>
  );
}

export function useVocabularyLookup(): VocabularyLookupContextValue {
  const ctx = useContext(VocabularyLookupContext);
  if (!ctx) {
    throw new Error(
      "useVocabularyLookup must be used within a VocabularyLookupProvider"
    );
  }
  return ctx;
}
