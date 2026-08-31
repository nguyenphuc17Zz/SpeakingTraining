"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import ReactDOM from "react-dom";
import { Sparkles, Command } from "lucide-react";
import { useVocabularyLookup } from "../context/VocabularyLookupContext";
import { BubbleSelectionState } from "@/types/vocabulary-lookup";

export function SelectionLookupBubble() {
  const {
    isBubbleVisible,
    selectionState,
    setSelectionState,
    hideBubble,
    openLookup,
    isOpen: isModalOpen,
  } = useVocabularyLookup();

  const [mounted, setMounted] = useState(false);
  const bubbleRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Extract contextual sentence/paragraph from DOM node
  const extractContextFromNode = useCallback((node: Node | null): string => {
    if (!node) return "";
    const el = node instanceof HTMLElement ? node : node.parentElement;
    if (!el) return "";
    const container = el.closest(
      "p, div, li, blockquote, article, section, h1, h2, h3, h4, h5, h6, table"
    );
    if (container && container.textContent) {
      return container.textContent.trim().replace(/\s+/g, " ");
    }
    return el.textContent?.trim().replace(/\s+/g, " ") || "";
  }, []);

  // Extract contextual line/sentence from textarea/input value
  const extractContextFromInput = useCallback(
    (value: string, start: number, end: number): string => {
      if (!value) return "";
      const lineStart = value.lastIndexOf("\n", start);
      const lineEnd = value.indexOf("\n", end);
      const s = lineStart === -1 ? 0 : lineStart + 1;
      const e = lineEnd === -1 ? value.length : lineEnd;
      const line = value.substring(s, e).trim();
      return line || value.trim();
    },
    []
  );

  const handleSelectionCheck = useCallback(() => {
    if (typeof window === "undefined" || isModalOpen) return;

    // 1. Check if user is selecting inside an active textarea or input
    const activeEl = document.activeElement;
    if (
      activeEl &&
      (activeEl instanceof HTMLInputElement ||
        activeEl instanceof HTMLTextAreaElement)
    ) {
      const start = activeEl.selectionStart;
      const end = activeEl.selectionEnd;

      if (
        typeof start === "number" &&
        typeof end === "number" &&
        start !== end
      ) {
        const text = activeEl.value.substring(start, end).trim();
        if (text.length > 0 && text.length <= 300) {
          const inputRect = activeEl.getBoundingClientRect();
          const ctx = extractContextFromInput(activeEl.value, start, end);

          const newState: BubbleSelectionState = {
            text,
            context: ctx,
            rect: {
              top: inputRect.top,
              bottom: inputRect.bottom,
              left: inputRect.left,
              right: inputRect.right,
              width: inputRect.width,
              height: inputRect.height,
            },
            inputElement: activeEl,
            selectionStart: start,
            selectionEnd: end,
          };
          setSelectionState(newState);
          return;
        }
      }
    }

    // 2. Check standard DOM window selection
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed || sel.rangeCount === 0) {
      return;
    }

    const text = sel.toString().trim();
    if (!text || text.length > 300) {
      setSelectionState(null);
      return;
    }

    try {
      const range = sel.getRangeAt(0);
      const rect = range.getBoundingClientRect();

      if (rect.width === 0 && rect.height === 0) {
        setSelectionState(null);
        return;
      }

      // Check if selection is inside bubble itself
      const startNode = range.startContainer;
      if (
        bubbleRef.current &&
        startNode &&
        bubbleRef.current.contains(
          startNode instanceof HTMLElement ? startNode : startNode.parentElement
        )
      ) {
        return;
      }

      const contextText = extractContextFromNode(range.commonAncestorContainer);

      const newState: BubbleSelectionState = {
        text,
        context: contextText,
        rect: {
          top: rect.top,
          bottom: rect.bottom,
          left: rect.left,
          right: rect.right,
          width: rect.width,
          height: rect.height,
        },
        inputElement: null,
      };

      setSelectionState(newState);
    } catch {
      setSelectionState(null);
    }
  }, [
    isModalOpen,
    extractContextFromInput,
    extractContextFromNode,
    setSelectionState,
  ]);

  useEffect(() => {
    if (typeof document === "undefined") return;

    let timeoutId: NodeJS.Timeout;
    const debouncedCheck = () => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(handleSelectionCheck, 80);
    };

    const handlePointerUp = (e: MouseEvent | TouchEvent) => {
      if (
        bubbleRef.current &&
        bubbleRef.current.contains(e.target as Node)
      ) {
        return;
      }
      debouncedCheck();
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      if (
        [
          "Shift",
          "ArrowLeft",
          "ArrowRight",
          "ArrowUp",
          "ArrowDown",
          "Home",
          "End",
        ].includes(e.key)
      ) {
        debouncedCheck();
      }
    };

    const handleMouseDown = (e: MouseEvent) => {
      if (
        bubbleRef.current &&
        !bubbleRef.current.contains(e.target as Node)
      ) {
        const sel = window.getSelection();
        if (sel && sel.isCollapsed) {
          hideBubble();
        }
      }
    };

    document.addEventListener("mouseup", handlePointerUp);
    document.addEventListener("touchend", handlePointerUp);
    document.addEventListener("keyup", handleKeyUp);
    document.addEventListener("dblclick", debouncedCheck);
    document.addEventListener("mousedown", handleMouseDown);

    return () => {
      clearTimeout(timeoutId);
      document.removeEventListener("mouseup", handlePointerUp);
      document.removeEventListener("touchend", handlePointerUp);
      document.removeEventListener("keyup", handleKeyUp);
      document.removeEventListener("dblclick", debouncedCheck);
      document.removeEventListener("mousedown", handleMouseDown);
    };
  }, [handleSelectionCheck, hideBubble]);

  if (!mounted || !isBubbleVisible || !selectionState || isModalOpen) {
    return null;
  }

  const { rect } = selectionState;
  const bubbleWidth = 180;
  const bubbleHeight = 38;
  const scrollY = window.scrollY || window.pageYOffset;
  const scrollX = window.scrollX || window.pageXOffset;

  let left = rect.left + scrollX + rect.width / 2 - bubbleWidth / 2;
  const padding = 12;
  const maxLeft = window.innerWidth - bubbleWidth - padding;
  left = Math.max(padding, Math.min(left, maxLeft));

  let top: number;
  let isAbove = true;
  if (rect.top >= bubbleHeight + 16) {
    top = rect.top + scrollY - bubbleHeight - 6;
  } else {
    isAbove = false;
    top = rect.bottom + scrollY + 6;
  }

  const handleBubbleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    openLookup(
      selectionState.text,
      selectionState.context,
      true,
      selectionState.inputElement
    );
  };

  return ReactDOM.createPortal(
    <div
      ref={bubbleRef}
      style={{
        position: "absolute",
        top: `${top}px`,
        left: `${left}px`,
        zIndex: 99999,
      }}
      className="pointer-events-auto select-none"
    >
      <button
        onClick={handleBubbleClick}
        type="button"
        aria-label="Tra cứu từ vựng AI"
        className="group flex items-center gap-2 px-3 py-1.5 rounded-full
          bg-card/95 text-foreground
          border border-border/80 dark:border-primary/40
          shadow-lg shadow-black/10 dark:shadow-black/40
          backdrop-blur-md transition-all duration-200 ease-out
          hover:scale-105 hover:border-primary hover:shadow-primary/20
          active:scale-95 animate-in fade-in zoom-in-95 duration-150"
      >
        <span className="flex items-center justify-center h-5 w-5 rounded-full bg-primary text-primary-foreground shadow-sm">
          <Sparkles className="h-3 w-3 animate-pulse" />
        </span>

        <div className="flex flex-col text-left">
          <div className="flex items-center gap-1.5 leading-none">
            <span className="text-xs font-bold tracking-tight text-foreground group-hover:text-primary transition-colors">
              Tra Cứu AI
            </span>
            <span className="text-[9px] px-1 py-0.2 rounded bg-primary/15 text-primary font-mono font-bold">
              話
            </span>
          </div>
          <span className="text-[9px] text-muted-foreground line-clamp-1 max-w-[85px] font-jp mt-0.5">
            {selectionState.text}
          </span>
        </div>

        <span className="text-[9px] text-muted-foreground/70 hidden sm:inline-flex items-center gap-0.5 border border-border/60 rounded px-1 py-0.5 ml-0.5 bg-muted/40 font-mono">
          <Command className="h-2 w-2" />⇧K
        </span>
      </button>

      {/* Triangular Pointer Arrow */}
      <div
        className={`absolute left-1/2 -translate-x-1/2 w-0 h-0 border-x-[5px] border-x-transparent ${
          isAbove
            ? "border-t-[5px] border-t-card/95 top-full"
            : "border-b-[5px] border-b-card/95 bottom-full"
        }`}
      />
    </div>,
    document.body
  );
}
