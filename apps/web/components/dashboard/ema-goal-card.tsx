"use client";

import React, { useState, useEffect } from "react";
import { Sparkles, Edit3, Check, Calendar, Flame, Target, Clock, X } from "lucide-react";
import { HankoStamp } from "@/components/ui/hanko-stamp";
import { soundFX } from "@/lib/sound-fx";
import { cn } from "@/lib/utils";

export function EmaGoalCard({ className }: { className?: string }) {
  const [goalText, setGoalText] = useState("Đỗ kỳ thi JLPT N3 & Tự tin giao tiếp tiếng Nhật");
  const [targetDate, setTargetDate] = useState("2026-12-06");
  const [isEditing, setIsEditing] = useState(false);
  const [tempGoal, setTempGoal] = useState(goalText);
  const [tempDate, setTempDate] = useState(targetDate);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const savedGoal = localStorage.getItem("hanasu-ema-goal");
    const savedDate = localStorage.getItem("hanasu-ema-date");
    if (savedGoal) {
      setGoalText(savedGoal);
      setTempGoal(savedGoal);
    }
    if (savedDate) {
      setTargetDate(savedDate);
      setTempDate(savedDate);
    }
  }, []);

  const daysRemaining = Math.max(
    0,
    Math.ceil((new Date(targetDate).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24))
  );

  const handleSave = () => {
    soundFX.playHankoStamp();
    setGoalText(tempGoal);
    setTargetDate(tempDate);
    setIsEditing(false);

    if (typeof window !== "undefined") {
      localStorage.setItem("hanasu-ema-goal", tempGoal);
      localStorage.setItem("hanasu-ema-date", tempDate);
    }
  };

  const handleCancel = () => {
    setTempGoal(goalText);
    setTempDate(targetDate);
    setIsEditing(false);
  };

  const setPresetDate = (monthsFromNow: number) => {
    soundFX.playSuikinkutsu();
    const d = new Date();
    d.setMonth(d.getMonth() + monthsFromNow);
    setTempDate(d.toISOString().slice(0, 10));
  };

  const formattedTargetDate = (() => {
    try {
      const d = new Date(targetDate);
      return d.toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit", year: "numeric" });
    } catch {
      return targetDate;
    }
  })();

  return (
    <div
      className={cn(
        "relative rounded-2xl border-2 border-kintsugi-400/40 bg-gradient-to-b from-[#f9f4ea]/95 via-[#f4ebd6]/85 to-[#ece0c3]/95 dark:from-[#211d17]/95 dark:via-[#1c1813]/95 dark:to-[#171410]/95 shadow-kintsugi p-5 text-foreground overflow-hidden washi-texture",
        className
      )}
    >
      {/* Ribbon & Hanging Cord Accent */}
      <div className="absolute -top-3 left-1/2 -translate-x-1/2 flex flex-col items-center pointer-events-none">
        <div className="w-4 h-4 rounded-full bg-primary shadow-sm border border-primary/60" />
        <div className="w-0.5 h-3 bg-primary" />
      </div>

      {/* Shoji backdrop */}
      <div className="absolute inset-0 shoji-grid opacity-20 pointer-events-none" />

      {/* Header */}
      <div className="flex items-center justify-between border-b border-kintsugi-500/20 pb-2.5 mt-1">
        <div className="flex items-center gap-2">
          <span className="text-xl leading-none">🎋</span>
          <div>
            <div className="flex items-center gap-1.5">
              <h3 className="text-xs font-black font-display text-foreground tracking-wider uppercase">
                Thẻ Gỗ Ước Nguyện Ema
              </h3>
              <span className="text-[10px] font-jp font-bold text-primary px-1.5 py-0.2 rounded bg-primary/10 border border-primary/20">
                絵馬
              </span>
            </div>
            <p className="text-[10px] text-muted-foreground">Khắc ghi mục tiêu & ngày thi JLPT</p>
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          {isEditing ? (
            <>
              <button
                type="button"
                onClick={handleCancel}
                className="h-7 px-2 rounded-lg border border-border bg-card/80 hover:bg-muted text-muted-foreground text-[11px] font-bold flex items-center gap-1 transition-colors"
                title="Hủy chỉnh sửa"
              >
                <X className="h-3 w-3" />
                Hủy
              </button>
              <button
                type="button"
                onClick={handleSave}
                className="h-7 px-2.5 rounded-lg border border-primary/40 bg-primary hover:bg-primary/90 text-white text-[11px] font-bold flex items-center gap-1 transition-colors shadow-sm"
                title="Lưu mục tiêu và ngày"
              >
                <Check className="h-3 w-3" />
                Lưu
              </button>
            </>
          ) : (
            <button
              type="button"
              onClick={() => {
                setTempGoal(goalText);
                setTempDate(targetDate);
                setIsEditing(true);
              }}
              className="h-7 px-2.5 rounded-lg border border-kintsugi-400/30 bg-kintsugi-400/10 hover:bg-kintsugi-400/20 text-foreground text-[11px] font-bold flex items-center gap-1 transition-colors"
              title="Chỉnh sửa mục tiêu & ngày thi"
            >
              <Edit3 className="h-3 w-3 text-kintsugi-500" />
              Sửa
            </button>
          )}
        </div>
      </div>

      {/* Goal Content */}
      <div className="py-3 space-y-3 relative z-10">
        {isEditing ? (
          <div className="space-y-2.5">
            <div>
              <label className="text-[10px] font-bold text-muted-foreground block mb-1">
                Nội dung ước nguyện / mục tiêu:
              </label>
              <textarea
                value={tempGoal}
                onChange={(e) => setTempGoal(e.target.value)}
                rows={2}
                className="w-full text-xs font-bold p-2.5 rounded-xl border border-primary/60 bg-card text-foreground focus:outline-none focus:ring-1 focus:ring-primary leading-relaxed shadow-sm"
                placeholder="Nhập mục tiêu học tiếng Nhật của bạn..."
              />
            </div>

            <div>
              <label className="text-[10px] font-bold text-muted-foreground block mb-1">
                Ngày đích (Ngày thi JLPT / Phỏng vấn):
              </label>
              <input
                type="date"
                value={tempDate}
                onChange={(e) => setTempDate(e.target.value)}
                className="w-full h-8 text-xs font-bold px-2.5 rounded-xl border border-border bg-card text-foreground focus:outline-none focus:border-primary shadow-sm"
              />
            </div>

            {/* Quick date presets */}
            <div className="flex items-center gap-1.5 flex-wrap pt-0.5">
              <span className="text-[9px] text-muted-foreground font-semibold">Chọn nhanh:</span>
              <button
                type="button"
                onClick={() => setPresetDate(1)}
                className="px-2 py-0.5 rounded-md bg-muted/80 hover:bg-muted text-[10px] font-semibold text-foreground border border-border"
              >
                +1 tháng
              </button>
              <button
                type="button"
                onClick={() => setPresetDate(3)}
                className="px-2 py-0.5 rounded-md bg-muted/80 hover:bg-muted text-[10px] font-semibold text-foreground border border-border"
              >
                +3 tháng
              </button>
              <button
                type="button"
                onClick={() => setPresetDate(6)}
                className="px-2 py-0.5 rounded-md bg-muted/80 hover:bg-muted text-[10px] font-semibold text-foreground border border-border"
              >
                +6 tháng
              </button>
              <button
                type="button"
                onClick={() => setTempDate("2026-12-06")}
                className="px-2 py-0.5 rounded-md bg-primary/10 hover:bg-primary/20 text-primary text-[10px] font-bold border border-primary/20"
              >
                JLPT T12/2026
              </button>
            </div>
          </div>
        ) : (
          <p className="text-sm font-display font-black text-foreground leading-snug tracking-wide">
            "{goalText}"
          </p>
        )}

        {/* Footer Metrics */}
        <div className="flex items-center justify-between pt-1 border-t border-kintsugi-500/15">
          <div className="space-y-0.5">
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Calendar className="h-3.5 w-3.5 text-primary" />
              <span>Hạn mục tiêu:</span>
              <span className="font-bold text-foreground">{formattedTargetDate}</span>
            </div>
            <div className="flex items-center gap-1 text-[11px] text-muted-foreground">
              <Clock className="h-3 w-3 text-kintsugi-500" />
              <span>Còn lại:</span>
              <strong className="text-primary font-sans font-black text-xs">
                {daysRemaining} ngày
              </strong>
            </div>
          </div>

          <HankoStamp text="必勝" subtext="Quyết thắng" variant="primary" size="sm" />
        </div>
      </div>
    </div>
  );
}
