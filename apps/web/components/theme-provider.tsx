"use client";

import React, { createContext, useCallback, useContext, useEffect, useState } from "react";

export type JapaneseThemeId = "matcha" | "aizome" | "kohaku" | "haru";
export type LegacyTheme = "light" | "dark";
export type Theme = JapaneseThemeId | LegacyTheme;

export interface JapaneseThemeMeta {
  id: JapaneseThemeId;
  name: string;
  kanji: string;
  subtitle: string;
  type: "light" | "dark";
  primaryColor: string;
  bgHex: string;
  accentColor: string;
  description: string;
  emoji: string;
}

export const JAPANESE_THEMES: JapaneseThemeMeta[] = [
  {
    id: "matcha",
    name: "Matcha Zen",
    kanji: "抹茶・竹林",
    subtitle: "Trà Đạo & Rừng Trúc Dịu Mắt",
    type: "dark",
    primaryColor: "#10b981",
    accentColor: "#d4af37",
    bgHex: "#101116",
    description: "Xanh ngọc bích trà đạo trên nền than Sumi mờ, êm mắt tuyệt đối khi học lâu.",
    emoji: "🍵",
  },
  {
    id: "aizome",
    name: "Aizome Ocean",
    kanji: "藍染・富士",
    subtitle: "Chàm Biển & Núi Phú Sĩ",
    type: "dark",
    primaryColor: "#3b82f6",
    accentColor: "#38bdf8",
    bgHex: "#0b1120",
    description: "Xanh chàm hoàng gia cổ truyền sâu lắng, công nghệ cao và tăng cường tập trung.",
    emoji: "🌊",
  },
  {
    id: "kohaku",
    name: "Kohaku Amber",
    kanji: "琥珀・金継ぎ",
    subtitle: "Hổ Phách & Dát Vàng Kyoto",
    type: "dark",
    primaryColor: "#f59e0b",
    accentColor: "#10b981",
    bgHex: "#121319",
    description: "Vàng hổ phách ấm áp quý phái, tạo cảm giác sang trọng cổ kính không gây chói.",
    emoji: "🍂",
  },
  {
    id: "haru",
    name: "Haru Washi",
    kanji: "春・和紙",
    subtitle: "Giấy Washi Ấm & Xanh Rừng Trúc",
    type: "light",
    primaryColor: "#059669",
    accentColor: "#d4af37",
    bgHex: "#fcf9f2",
    description: "Màu giấy dó tự nhiên Nhật Bản, trong trẻo và thanh lịch cho ban ngày.",
    emoji: "🌸",
  },
];

interface ThemeContextValue {
  theme: JapaneseThemeId;
  legacyTheme: LegacyTheme;
  isDark: boolean;
  activeThemeMeta: JapaneseThemeMeta;
  themes: JapaneseThemeMeta[];
  setTheme: (t: Theme) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextValue>({
  theme: "matcha",
  legacyTheme: "dark",
  isDark: true,
  activeThemeMeta: JAPANESE_THEMES[0],
  themes: JAPANESE_THEMES,
  setTheme: () => {},
  toggleTheme: () => {},
});

export function useTheme() {
  return useContext(ThemeContext);
}

function normalizeTheme(val: string | null): JapaneseThemeId {
  if (!val) return "matcha";
  if (val === "dark" || val === "kyoto" || val === "tokyo") return "matcha";
  if (val === "light") return "haru";
  if (["matcha", "aizome", "kohaku", "haru"].includes(val)) {
    return val as JapaneseThemeId;
  }
  return "matcha";
}

function applyThemeClasses(themeId: JapaneseThemeId) {
  const root = document.documentElement;
  const allThemeClasses = ["theme-haru", "theme-matcha", "theme-kyoto", "theme-tokyo", "theme-aizome", "theme-kohaku", "dark", "light"];
  root.classList.remove(...allThemeClasses);

  if (themeId === "haru") {
    root.classList.add("light", "theme-haru");
  } else {
    root.classList.add("dark", `theme-${themeId}`);
  }
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<JapaneseThemeId>("matcha");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem("hanasu-theme");
    const normalized = normalizeTheme(stored);
    setThemeState(normalized);
    applyThemeClasses(normalized);
    setMounted(true);
  }, []);

  const setTheme = useCallback((t: Theme) => {
    const normalized = normalizeTheme(t);
    setThemeState(normalized);
    localStorage.setItem("hanasu-theme", normalized);
    applyThemeClasses(normalized);
  }, []);

  const toggleTheme = useCallback(() => {
    setTheme(theme === "haru" ? "matcha" : "haru");
  }, [theme, setTheme]);

  const activeThemeMeta = JAPANESE_THEMES.find((item) => item.id === theme) || JAPANESE_THEMES[0];
  const isDark = activeThemeMeta.type === "dark";
  const legacyTheme: LegacyTheme = isDark ? "dark" : "light";

  return (
    <ThemeContext.Provider
      value={{
        theme,
        legacyTheme,
        isDark,
        activeThemeMeta,
        themes: JAPANESE_THEMES,
        setTheme,
        toggleTheme,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
}
