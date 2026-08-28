"use client";
import React, { useEffect, useState, useRef } from "react";
import { AlertCircle, CheckCircle2, Info } from "lucide-react";

type Toast = { id: number; message: string; type: "error" | "success" | "info" };

export function GlobalToast() {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const idRef = useRef(1);
  const lastSeenRef = useRef<Map<string, number>>(new Map());

  useEffect(() => {
    const handler = (e: Event) => {
      const ce = e as CustomEvent;
      const { message, type } = ce.detail || {};
      if (!message) return;
      const key = `${type || "error"}:${String(message)}`;
      const now = Date.now();
      const last = lastSeenRef.current.get(key) || 0;
      if (now - last < 2000) return; // dedup 2s
      lastSeenRef.current.set(key, now);
      const id = idRef.current++;
      setToasts((prev) => {
        const next = [...prev, { id, message: String(message), type: type || "error" }];
        // cap at 3 toasts
        return next.length > 3 ? next.slice(next.length - 3) : next;
      });
      setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 4000);
    };
    window.addEventListener("app-toast" as any, handler as any);
    return () => window.removeEventListener("app-toast" as any, handler as any);
  }, []);

  if (!toasts.length) return null;
  return (
    <div className="fixed top-4 right-4 z-[100] space-y-2 max-w-[380px]" role="region" aria-live="polite" aria-label="Notifications">
      {toasts.map((t) => (
        <div
          key={t.id}
          role={t.type === "error" ? "alert" : "status"}
          aria-live={t.type === "error" ? "assertive" : "polite"}
          className={`rounded-xl border shadow-lg px-4 py-3 text-sm flex items-start gap-2 backdrop-blur ${
            t.type === "error" ? "bg-red-50 border-red-200 text-red-800" : t.type === "success" ? "bg-emerald-50 border-emerald-200 text-emerald-800" : "bg-card border-border"
          }`}
        >
          {t.type === "error" ? <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" /> : t.type === "success" ? <CheckCircle2 className="h-4 w-4 mt-0.5 shrink-0" /> : <Info className="h-4 w-4 mt-0.5 shrink-0" />}
          <span className="flex-1 leading-relaxed">{t.message}</span>
          <button type="button" aria-label="Dismiss notification" onClick={() => setToasts((prev) => prev.filter((x) => x.id !== t.id))} className="text-xs opacity-60 hover:opacity-100 shrink-0">✕</button>
        </div>
      ))}
    </div>
  );
}
