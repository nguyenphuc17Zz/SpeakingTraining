"use client";

import React, { useState, useEffect, useRef } from "react";
import { CloudRain, Sparkles, Check, ChevronDown, Zap, EyeOff, Snowflake } from "lucide-react";
import { WeatherMode } from "./atmospheric-weather-engine";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

interface WeatherOption {
  id: WeatherMode;
  name: string;
  kanji: string;
  emoji: string;
  desc: string;
}

const WEATHER_OPTIONS: WeatherOption[] = [
  { id: "auto", name: "Tự động (Theo Theme)", kanji: "自動", emoji: "🔄", desc: "Đổi thời tiết theo phong cách giao diện" },
  { id: "sakura", name: "Hoa Anh Đào", kanji: "桜吹雪", emoji: "🌸", desc: "Cánh hoa hồng phấn chao liệng trong gió" },
  { id: "rain", name: "Mưa Phùn Cố Đô", kanji: "京の雨", emoji: "🌧️", desc: "Mưa rơi êm đềm, tăng độ tập trung" },
  { id: "thunder", name: "Bão Sấm Lôi Thần", kanji: "雷神の嵐", emoji: "⚡", desc: "Sấm chớp bùng nổ, kịch tính đấu Boss" },
  { id: "snow", name: "Tuyết Rơi Phú Sĩ", kanji: "富士の雪", emoji: "❄️", desc: "Bông tuyết trắng bồng bềnh mùa đông" },
  { id: "momiji", name: "Lá Phong Mùa Thu", kanji: "紅葉狩り", emoji: "🍂", desc: "Lá đỏ cam xoay nhẹ trong gió thu" },
  { id: "hotaru", name: "Đom Đóm Đêm Hè", kanji: "蛍火", emoji: "✨", desc: "Đốm sáng lấp lánh lung linh ban đêm" },
  { id: "off", name: "Tắt hiệu ứng", kanji: "無効", emoji: "🚫", desc: "Không hiển thị hiệu ứng chuyển động" },
];

export function WeatherToggle({ className }: { className?: string }) {
  const [selectedWeather, setSelectedWeather] = useState<WeatherMode>("auto");
  const [isOpen, setIsOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMounted(true);
    if (typeof window === "undefined") return;
    const saved = localStorage.getItem("hanasu-weather-fx") as WeatherMode | null;
    if (saved) setSelectedWeather(saved);

    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelect = (weatherId: WeatherMode) => {
    soundFX.playSuikinkutsu();
    setSelectedWeather(weatherId);
    setIsOpen(false);

    if (typeof window !== "undefined") {
      localStorage.setItem("hanasu-weather-fx", weatherId);
      window.dispatchEvent(new Event("weather-change"));
    }
  };

  const currentOption = (mounted && WEATHER_OPTIONS.find((o) => o.id === selectedWeather)) || WEATHER_OPTIONS[0];

  return (
    <div className={cn("relative", className)} ref={dropdownRef}>
      <button
        onClick={() => {
          soundFX.playFurin();
          setIsOpen(!isOpen);
        }}
        className="h-9 px-2.5 rounded-xl border border-border bg-card/80 hover:bg-muted/80 backdrop-blur-md text-foreground text-xs font-bold flex items-center gap-1.5 transition-colors shadow-sm"
        title="Chọn hiệu ứng khí quyển thời tiết Nhật Bản"
        suppressHydrationWarning
      >
        <span className="text-sm" suppressHydrationWarning>{currentOption.emoji}</span>
        <span className="hidden sm:inline font-jp text-[11px] text-muted-foreground" suppressHydrationWarning>{currentOption.kanji}</span>
        <ChevronDown className={cn("h-3 w-3 text-muted-foreground transition-transform duration-200", isOpen && "rotate-180")} />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-64 rounded-2xl border border-border bg-card/95 washi-texture backdrop-blur-2xl shadow-sumi-lg p-2 z-50 animate-in fade-in zoom-in-95 duration-150">
          <div className="px-2 py-1.5 border-b border-border/60 mb-1">
            <p className="text-xs font-bold text-foreground flex items-center gap-1">
              <span>Khí Quyển Thời Tiết</span>
              <span className="text-[10px] font-jp text-primary font-bold">四季の風情</span>
            </p>
            <p className="text-[10px] text-muted-foreground">Hiệu ứng không gian học tập sống động</p>
          </div>

          <div className="space-y-0.5 max-h-72 overflow-y-auto scrollbar-none">
            {WEATHER_OPTIONS.map((opt) => {
              const isSelected = selectedWeather === opt.id;
              return (
                <button
                  key={opt.id}
                  onClick={() => handleSelect(opt.id)}
                  className={cn(
                    "w-full px-2.5 py-1.5 rounded-xl text-left text-xs transition-colors flex items-center justify-between group",
                    isSelected
                      ? "bg-primary/15 text-primary font-bold"
                      : "text-foreground hover:bg-muted/70"
                  )}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-sm">{opt.emoji}</span>
                    <div>
                      <p className="leading-none text-xs">{opt.name}</p>
                      <p className="text-[9px] text-muted-foreground mt-0.5 line-clamp-1">{opt.desc}</p>
                    </div>
                  </div>

                  {isSelected && <Check className="h-3.5 w-3.5 text-primary shrink-0" />}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
