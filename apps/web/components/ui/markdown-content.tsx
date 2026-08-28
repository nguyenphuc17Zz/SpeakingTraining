"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface MarkdownContentProps {
  content: string;
  className?: string;
}

/**
 * Lightweight, zero-dependency, safe Markdown parser & renderer
 * Specifically optimized for Japanese Assistant responses:
 * - Bold (**text**)
 * - Italic (*text*)
 * - Inline Code (`code`)
 * - Code Blocks (```lang ... ```)
 * - Headers (###, ##, #)
 * - Bullet lists (- item, * item)
 * - Numbered lists (1. item)
 * - Blockquotes (> quote)
 * - Tables (| Header 1 | Header 2 |)
 */
export function MarkdownContent({ content, className }: MarkdownContentProps) {
  if (!content) return null;

  // Split into code blocks vs text blocks
  const parts = content.split(/(```[\s\S]*?```)/g);

  const renderInlineFormatted = (text: string) => {
    // Process inline code, bold, italic
    // We break by inline tokens
    const tokens = text.split(/(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*)/g);

    return tokens.map((token, idx) => {
      if (token.startsWith("`") && token.endsWith("`") && token.length > 1) {
        const code = token.slice(1, -1);
        return (
          <code
            key={idx}
            className="px-1.5 py-0.5 mx-0.5 rounded-md bg-muted/90 border border-border/80 font-jp font-bold text-primary text-[11px]"
          >
            {code}
          </code>
        );
      }
      if (token.startsWith("**") && token.endsWith("**") && token.length > 3) {
        const bold = token.slice(2, -2);
        return (
          <strong key={idx} className="font-extrabold text-foreground">
            {bold}
          </strong>
        );
      }
      if (token.startsWith("*") && token.endsWith("*") && token.length > 2) {
        const italic = token.slice(1, -1);
        return (
          <em key={idx} className="italic text-foreground/90">
            {italic}
          </em>
        );
      }
      return token;
    });
  };

  const renderBlock = (block: string, blockIdx: number) => {
    // Code block
    if (block.startsWith("```") && block.endsWith("```")) {
      const firstLineEnd = block.indexOf("\n");
      const lang = firstLineEnd !== -1 ? block.slice(3, firstLineEnd).trim() : "";
      const code = firstLineEnd !== -1 ? block.slice(firstLineEnd + 1, -3) : block.slice(3, -3);

      return (
        <div key={blockIdx} className="my-2 rounded-xl border border-border bg-muted/60 overflow-hidden text-[11px]">
          {lang && (
            <div className="px-3 py-1 bg-muted/90 border-b border-border/70 text-[10px] font-mono text-muted-foreground uppercase font-bold flex items-center justify-between">
              <span>{lang}</span>
            </div>
          )}
          <pre className="p-3 font-mono text-foreground overflow-x-auto whitespace-pre-wrap leading-relaxed">
            {code}
          </pre>
        </div>
      );
    }

    // Split standard text into lines
    const lines = block.split("\n");
    const elements: React.ReactNode[] = [];
    let currentList: { type: "ul" | "ol"; items: string[] } | null = null;
    let currentTable: { headers: string[]; rows: string[][] } | null = null;

    const flushList = () => {
      if (!currentList) return;
      if (currentList.type === "ul") {
        elements.push(
          <ul key={`ul-${elements.length}`} className="my-1.5 space-y-1 pl-1">
            {currentList.items.map((item, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-primary font-bold text-xs select-none mt-0.5">•</span>
                <span className="flex-1">{renderInlineFormatted(item)}</span>
              </li>
            ))}
          </ul>
        );
      } else {
        elements.push(
          <ol key={`ol-${elements.length}`} className="my-1.5 space-y-1 pl-1 list-decimal list-inside text-xs">
            {currentList.items.map((item, i) => (
              <li key={i} className="text-foreground">
                <span className="ml-1">{renderInlineFormatted(item)}</span>
              </li>
            ))}
          </ol>
        );
      }
      currentList = null;
    };

    const flushTable = () => {
      if (!currentTable) return;
      elements.push(
        <div key={`table-${elements.length}`} className="my-2 overflow-x-auto rounded-xl border border-border">
          <table className="w-full text-[11px] text-left border-collapse">
            <thead className="bg-muted/80 text-foreground font-bold border-b border-border">
              <tr>
                {currentTable.headers.map((h, i) => (
                  <th key={i} className="p-2 border-r border-border last:border-r-0">
                    {renderInlineFormatted(h)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60">
              {currentTable.rows.map((row, rIdx) => (
                <tr key={rIdx} className="hover:bg-muted/40 transition-colors">
                  {row.map((cell, cIdx) => (
                    <td key={cIdx} className="p-2 border-r border-border/60 last:border-r-0">
                      {renderInlineFormatted(cell)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
      currentTable = null;
    };

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const trimmed = line.trim();

      if (!trimmed) {
        flushList();
        flushTable();
        continue;
      }

      // Check table row: | col1 | col2 |
      if (trimmed.startsWith("|") && trimmed.endsWith("|")) {
        flushList();
        const cells = trimmed
          .slice(1, -1)
          .split("|")
          .map((c) => c.trim());

        // Ignore separator line like |---|---|
        if (cells.every((c) => /^[-:]+$/.test(c))) {
          continue;
        }

        if (!currentTable) {
          currentTable = { headers: cells, rows: [] };
        } else {
          currentTable.rows.push(cells);
        }
        continue;
      } else {
        flushTable();
      }

      // Check Headers
      if (trimmed.startsWith("### ")) {
        flushList();
        elements.push(
          <h4 key={`h4-${i}`} className="text-xs font-black font-display text-foreground mt-2.5 mb-1 tracking-tight">
            {renderInlineFormatted(trimmed.slice(4))}
          </h4>
        );
        continue;
      }
      if (trimmed.startsWith("## ")) {
        flushList();
        elements.push(
          <h3 key={`h3-${i}`} className="text-sm font-black font-display text-primary mt-3 mb-1 tracking-tight">
            {renderInlineFormatted(trimmed.slice(3))}
          </h3>
        );
        continue;
      }
      if (trimmed.startsWith("# ")) {
        flushList();
        elements.push(
          <h2 key={`h2-${i}`} className="text-sm font-black font-display text-primary mt-3 mb-1.5 border-b border-border/60 pb-1">
            {renderInlineFormatted(trimmed.slice(2))}
          </h2>
        );
        continue;
      }

      // Check Blockquote
      if (trimmed.startsWith("> ")) {
        flushList();
        elements.push(
          <blockquote
            key={`quote-${i}`}
            className="border-l-2 border-primary pl-2.5 py-1 my-1.5 text-xs italic text-muted-foreground bg-muted/30 rounded-r-lg"
          >
            {renderInlineFormatted(trimmed.slice(2))}
          </blockquote>
        );
        continue;
      }

      // Check Bullet list (- item, * item)
      if (/^[-*]\s+/.test(trimmed)) {
        const itemText = trimmed.replace(/^[-*]\s+/, "");
        if (!currentList || currentList.type !== "ul") {
          flushList();
          currentList = { type: "ul", items: [itemText] };
        } else {
          currentList.items.push(itemText);
        }
        continue;
      }

      // Check Numbered list (1. item)
      if (/^\d+\.\s+/.test(trimmed)) {
        const itemText = trimmed.replace(/^\d+\.\s+/, "");
        if (!currentList || currentList.type !== "ol") {
          flushList();
          currentList = { type: "ol", items: [itemText] };
        } else {
          currentList.items.push(itemText);
        }
        continue;
      }

      // Normal paragraph line
      flushList();
      elements.push(
        <p key={`p-${i}`} className="text-xs leading-relaxed my-1">
          {renderInlineFormatted(trimmed)}
        </p>
      );
    }

    flushList();
    flushTable();

    return <div key={blockIdx}>{elements}</div>;
  };

  return <div className={cn("space-y-1 text-xs select-text", className)}>{parts.map(renderBlock)}</div>;
}
