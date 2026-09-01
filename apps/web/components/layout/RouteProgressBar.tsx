"use client";

import React, { useEffect, useState, useRef } from "react";
import { usePathname, useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";

export function RouteProgressBar() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const startProgress = () => {
    setLoading(true);
    setProgress(20);

    if (intervalRef.current) clearInterval(intervalRef.current);

    intervalRef.current = setInterval(() => {
      setProgress((prev) => {
        if (prev < 40) return prev + 15;
        if (prev < 75) return prev + 8;
        if (prev < 90) return prev + 2;
        return prev;
      });
    }, 150);
  };

  const completeProgress = () => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    setProgress(100);
    const timer = setTimeout(() => {
      setLoading(false);
      setProgress(0);
    }, 280);
    return () => clearTimeout(timer);
  };

  // Complete progress on route changes
  useEffect(() => {
    if (loading) {
      completeProgress();
    }
  }, [pathname, searchParams]);

  // Intercept click on internal links & monkey patch history.pushState
  useEffect(() => {
    const handleDocumentClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement | null;
      const anchor = target?.closest("a") as HTMLAnchorElement | null;

      if (!anchor) return;

      const href = anchor.getAttribute("href");
      if (!href) return;

      // Ignore external links, new tabs, anchors, downloads, or same-page hashes
      if (
        anchor.target === "_blank" ||
        e.ctrlKey ||
        e.metaKey ||
        e.shiftKey ||
        e.altKey ||
        href.startsWith("http://") ||
        href.startsWith("https://") ||
        href.startsWith("mailto:") ||
        href.startsWith("tel:") ||
        href.startsWith("#") ||
        href === pathname
      ) {
        return;
      }

      startProgress();
    };

    const handlePopState = () => {
      startProgress();
    };

    document.addEventListener("click", handleDocumentClick, { capture: true });
    window.addEventListener("popstate", handlePopState);

    return () => {
      document.removeEventListener("click", handleDocumentClick, { capture: true });
      window.removeEventListener("popstate", handlePopState);
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [pathname]);

  return (
    <AnimatePresence>
      {loading && (
        <div className="fixed top-0 left-0 right-0 z-[9999] pointer-events-none h-1 bg-transparent overflow-hidden">
          <motion.div
            initial={{ width: "0%", opacity: 0.8 }}
            animate={{ width: `${progress}%`, opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{
              duration: progress === 100 ? 0.2 : 0.3,
              ease: [0.4, 0, 0.2, 1],
            }}
            className="h-full bg-gradient-to-r from-emerald-500 via-teal-400 to-amber-400 shadow-[0_0_14px_rgba(16,185,129,0.85)]"
          />
        </div>
      )}
    </AnimatePresence>
  );
}
