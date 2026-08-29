"use client";

import { useEffect, useState } from "react";

export type FuriganaColorId =
  | "sakura"
  | "torii"
  | "amber"
  | "matcha"
  | "ocean"
  | "lavender"
  | "sumi"
  | "cyan"
  | "custom";

export interface FuriganaColorOption {
  id: FuriganaColorId;
  name: string;
  className: string;
  bgClass: string;
  borderClass: string;
  hex: string;
}

export const FURIGANA_COLORS: FuriganaColorOption[] = [
  {
    id: "matcha",
    name: "Xanh Matcha (Zen)",
    className: "text-emerald-400",
    bgClass: "bg-emerald-500/20",
    borderClass: "border-emerald-500/40",
    hex: "#34d399",
  },
  {
    id: "ocean",
    name: "Đại Dương Lam",
    className: "text-sky-400",
    bgClass: "bg-sky-500/20",
    borderClass: "border-sky-500/40",
    hex: "#38bdf8",
  },
  {
    id: "amber",
    name: "Hoàng Kim Cam",
    className: "text-amber-400",
    bgClass: "bg-amber-500/20",
    borderClass: "border-amber-500/40",
    hex: "#fbbf24",
  },
  {
    id: "cyan",
    name: "Lam Ngọc (Cyan)",
    className: "text-cyan-400",
    bgClass: "bg-cyan-500/20",
    borderClass: "border-cyan-500/40",
    hex: "#22d3ee",
  },
  {
    id: "lavender",
    name: "Oải Hương Tím",
    className: "text-purple-400",
    bgClass: "bg-purple-500/20",
    borderClass: "border-purple-500/40",
    hex: "#c084fc",
  },
  {
    id: "sumi",
    name: "Mực Sumi Bạc",
    className: "text-slate-300",
    bgClass: "bg-slate-500/20",
    borderClass: "border-slate-500/40",
    hex: "#cbd5e1",
  },
  {
    id: "sakura",
    name: "Hoa Anh Đào",
    className: "text-rose-400",
    bgClass: "bg-rose-500/20",
    borderClass: "border-rose-500/40",
    hex: "#fb7185",
  },
  {
    id: "torii",
    name: "Hổ Phách Cổ",
    className: "text-amber-500",
    bgClass: "bg-amber-500/20",
    borderClass: "border-amber-500/40",
    hex: "#f59e0b",
  },
];

export type FuriganaDisplayMode = "kanji_reading" | "kanji" | "hidden";

const STORAGE_KEY = "shadowing_furigana_color";
const STORAGE_CUSTOM_HEX_KEY = "shadowing_furigana_custom_hex";
const STORAGE_DISPLAY_MODE_KEY = "hanasu_furigana_display_mode";

export function useFuriganaSettings() {
  const [colorId, setColorId] = useState<FuriganaColorId>("matcha");
  const [customHex, setCustomHex] = useState<string>("#34d399");
  const [displayMode, setDisplayModeState] = useState<FuriganaDisplayMode>("kanji_reading");

  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY) as FuriganaColorId;
      const savedCustom = localStorage.getItem(STORAGE_CUSTOM_HEX_KEY);
      const savedMode = localStorage.getItem(STORAGE_DISPLAY_MODE_KEY) as FuriganaDisplayMode;
      if (savedCustom) setCustomHex(savedCustom);
      if (saved) setColorId(saved);
      if (savedMode) setDisplayModeState(savedMode);
    } catch {
      // ignore SSR or storage errors
    }

    const handleStorage = () => {
      try {
        const current = localStorage.getItem(STORAGE_KEY) as FuriganaColorId;
        const currentCustom = localStorage.getItem(STORAGE_CUSTOM_HEX_KEY);
        const currentMode = localStorage.getItem(STORAGE_DISPLAY_MODE_KEY) as FuriganaDisplayMode;
        if (currentCustom) setCustomHex(currentCustom);
        if (current) setColorId(current);
        if (currentMode) setDisplayModeState(currentMode);
      } catch {}
    };

    window.addEventListener("storage", handleStorage);
    window.addEventListener("furigana-color-changed", handleStorage);
    window.addEventListener("furigana-mode-changed", handleStorage);

    return () => {
      window.removeEventListener("storage", handleStorage);
      window.removeEventListener("furigana-color-changed", handleStorage);
      window.removeEventListener("furigana-mode-changed", handleStorage);
    };
  }, []);

  const changeColor = (newColor: FuriganaColorId) => {
    setColorId(newColor);
    try {
      localStorage.setItem(STORAGE_KEY, newColor);
      window.dispatchEvent(new CustomEvent("furigana-color-changed", { detail: newColor }));
    } catch {}
  };

  const changeCustomColor = (hex: string) => {
    setCustomHex(hex);
    setColorId("custom");
    try {
      localStorage.setItem(STORAGE_KEY, "custom");
      localStorage.setItem(STORAGE_CUSTOM_HEX_KEY, hex);
      window.dispatchEvent(new CustomEvent("furigana-color-changed", { detail: "custom" }));
    } catch {}
  };

  const setDisplayMode = (mode: FuriganaDisplayMode) => {
    setDisplayModeState(mode);
    try {
      localStorage.setItem(STORAGE_DISPLAY_MODE_KEY, mode);
      window.dispatchEvent(new CustomEvent("furigana-mode-changed", { detail: mode }));
    } catch {}
  };

  const presetOption = FURIGANA_COLORS.find((c) => c.id === colorId);
  const activeHex = colorId === "custom" ? customHex : (presetOption?.hex || "#34d399");
  const furiganaClass = presetOption?.className || "";
  const furiganaStyle = { color: activeHex };

  return {
    colorId,
    customHex,
    activeHex,
    displayMode,
    setDisplayMode,
    changeColor,
    changeCustomColor,
    furiganaClass,
    furiganaStyle,
    activeOption: presetOption || {
      id: "custom" as FuriganaColorId,
      name: "Tùy chỉnh",
      className: "",
      bgClass: "bg-primary/20",
      borderClass: "border-primary/40",
      hex: activeHex,
    },
    options: FURIGANA_COLORS,
  };
}
