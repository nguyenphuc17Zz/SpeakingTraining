import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./features/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        // --- Curated Japanese Color Palette ---
        // 墨 Sumi (Charcoal Calligraphy Ink)
        sumi: {
          50: "#f6f7f9",
          100: "#eceef2",
          200: "#d5d8e2",
          300: "#b0b6c7",
          400: "#848ea7",
          500: "#636d8b",
          600: "#4d5571",
          700: "#3e445b",
          800: "#272a36",
          850: "#1f222d",
          900: "#171922",
          925: "#13141b",
          950: "#0d0e13",
        },
        // 桜 Sakura (Cherry Blossom)
        sakura: {
          50: "#fff1f4",
          100: "#ffe4e9",
          200: "#fecdd7",
          300: "#fda4b7",
          400: "#fb7193",
          500: "#f43f6e",
          600: "#e11d51",
          700: "#be123c",
        },
        // 金 Kintsugi / Kin (Gold leaf & lacquer)
        kintsugi: {
          50: "#fbf8ef",
          100: "#f5eed7",
          200: "#ebdbae",
          300: "#dfc47f",
          400: "#d4af37",
          500: "#c29b28",
          600: "#a67f1e",
          700: "#85601a",
          800: "#6e4e1b",
        },
        // 朱 Torii / Shu-iro (Vermilion Shinto shrine red)
        torii: {
          50: "#fff1f1",
          100: "#ffe1e1",
          200: "#ffc7c7",
          300: "#ffa0a0",
          400: "#f86b6b",
          500: "#e84040",
          600: "#d32727",
          700: "#b21e1e",
        },
        // 抹茶 Matcha (Ceremonial Green Tea)
        matcha: {
          50: "#f0fdf4",
          100: "#dcfce7",
          200: "#bbf7d0",
          300: "#86efac",
          400: "#4ade80",
          500: "#22c55e",
          600: "#16a34a",
          700: "#15803d",
        },
        // 藍染 Aizome (Deep Japanese Indigo)
        aizome: {
          50: "#f0f6fe",
          100: "#ddeafc",
          200: "#c1dafa",
          300: "#95c1f6",
          400: "#60a0f0",
          500: "#3b7fe7",
          600: "#2461cb",
          700: "#1e4ca5",
          800: "#1e4086",
          900: "#1b376d",
          950: "#0c1830",
        },
        // 和紙 Washi (Traditional Japanese Paper)
        washi: {
          50: "#fdfbf7",
          100: "#f7f0e6",
          200: "#ede3d2",
          300: "#ded0b7",
          400: "#cabb97",
        },
        // 富士 Fuji (Mount Fuji Lavender Mist)
        fuji: {
          50: "#eef2ff",
          100: "#e0e7ff",
          200: "#c7d2fe",
          400: "#818cf8",
          500: "#6366f1",
          600: "#4f46e5",
          900: "#1e1b4b",
        },
      },
      borderRadius: {
        "3xl": "1.75rem",
        "2xl": "1.25rem",
        xl: "1rem",
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      fontFamily: {
        sans: ["'Plus Jakarta Sans'", "var(--font-sans)", "'Noto Sans JP'", "Inter", "-apple-system", "sans-serif"],
        jp: ["'Zen Maru Gothic'", "var(--font-jp)", "'Noto Sans JP'", "'Hiragino Kaku Gothic Pro'", "sans-serif"],
        display: ["'Shippori Mincho'", "var(--font-display)", "'Zen Maru Gothic'", "serif"],
        mono: ["'JetBrains Mono'", "'Fira Code'", "monospace"],
      },
      boxShadow: {
        washi: "0 4px 20px -4px rgba(30, 58, 95, 0.07), 0 1px 3px rgba(0,0,0,0.03)",
        "washi-lg": "0 12px 36px -8px rgba(30, 58, 95, 0.1), 0 4px 12px rgba(0,0,0,0.04)",
        sumi: "0 4px 24px -2px rgba(0, 0, 0, 0.45), 0 1px 3px rgba(0,0,0,0.3)",
        "sumi-lg": "0 16px 48px -8px rgba(0, 0, 0, 0.65), 0 4px 16px rgba(0,0,0,0.4)",
        kintsugi: "0 0 0 1px rgba(212, 175, 55, 0.25), 0 8px 32px -4px rgba(212, 175, 55, 0.15)",
        enso: "0 0 0 1px rgba(16, 185, 129, 0.15), 0 8px 28px rgba(16, 185, 129, 0.08)",
        "tokyo-glow": "0 0 25px -5px rgba(16, 185, 129, 0.25), 0 8px 30px rgba(59, 130, 246, 0.15)",
      },
      keyframes: {
        "enso-draw": {
          "0%": { strokeDashoffset: "1000" },
          "100%": { strokeDashoffset: "0" },
        },
        "sakura-fall": {
          "0%": { transform: "translateY(-10px) rotate(0deg)", opacity: "0" },
          "15%": { opacity: "0.85" },
          "85%": { opacity: "0.85" },
          "100%": { transform: "translateY(120px) rotate(220deg)", opacity: "0" },
        },
        "pulse-glow": {
          "0%, 100%": { opacity: "0.6", transform: "scale(1)" },
          "50%": { opacity: "1", transform: "scale(1.05)" },
        },
        shimmer: {
          "0%": { transform: "translateX(-100%)" },
          "100%": { transform: "translateX(100%)" },
        },
      },
      animation: {
        "enso-draw": "enso-draw 1.2s ease-out forwards",
        "sakura-fall": "sakura-fall 3.5s ease-in-out infinite",
        "pulse-glow": "pulse-glow 3s ease-in-out infinite",
        shimmer: "shimmer 1.8s infinite",
      },
      backgroundImage: {
        "washi-grain":
          "radial-gradient(circle at 1px 1px, rgba(30,58,95,0.035) 1px, transparent 0)",
        "enso-gradient":
          "conic-gradient(from 180deg at 50% 50%, transparent 0deg, rgba(16,185,129,0.08) 120deg, transparent 240deg)",
        "kintsugi-gradient":
          "linear-gradient(135deg, rgba(212,175,55,0.2) 0%, rgba(212,175,55,0.05) 50%, transparent 100%)",
      },
    },
  },
  plugins: [],
};
export default config;
