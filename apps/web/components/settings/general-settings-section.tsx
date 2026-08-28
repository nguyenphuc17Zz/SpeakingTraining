"use client";

import React, { useEffect, useState } from "react";
import { useSettings } from "@/hooks/use-settings";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CheckCircle2, Globe, Clock, Volume2 } from "lucide-react";
import { soundFX } from "@/lib/sound-fx";

const LANGUAGE_OPTIONS = [
  { value: "vi", label: "Tiếng Việt" },
  { value: "ja", label: "日本語" },
  { value: "en", label: "English" },
] as const;

const TIMEZONE_OPTIONS = [
  { value: "Asia/Ho_Chi_Minh", label: "Việt Nam — Hồ Chí Minh (UTC+7)" },
  { value: "Asia/Tokyo", label: "Nhật Bản — Tokyo (UTC+9)" },
  { value: "Asia/Bangkok", label: "Thái Lan — Bangkok (UTC+7)" },
  { value: "Asia/Singapore", label: "Singapore (UTC+8)" },
  { value: "Asia/Seoul", label: "Hàn Quốc — Seoul (UTC+9)" },
  { value: "Asia/Shanghai", label: "Trung Quốc — Thượng Hải (UTC+8)" },
  { value: "UTC", label: "UTC" },
  { value: "America/New_York", label: "Mỹ — New York (UTC-4/-5)" },
] as const;

export function GeneralSettingsSection() {
  const { settings, loading, saving, updateSettings } = useSettings();
  const [formData, setFormData] = useState({
    language: "vi",
    timezone: "Asia/Ho_Chi_Minh",
  });
  const [savedMsg, setSavedMsg] = useState(false);

  useEffect(() => {
    if (settings) {
      setFormData({
        language: (settings.language as string) || "vi",
        timezone: settings.timezone || "Asia/Ho_Chi_Minh",
      });
    }
  }, [settings]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    // Chỉ gửi 2 field cần thiết, tránh ghi đè theme/AI provider đã quản lý ở tab khác
    const result = await updateSettings({
      language: formData.language,
      timezone: formData.timezone,
    } as any);
    if (result) {
      setSavedMsg(true);
      setTimeout(() => setSavedMsg(false), 3000);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-sm text-muted-foreground">Đang tải cài đặt chung…</div>;
  }

  return (
    <form onSubmit={handleSave} className="space-y-5">
      <div className="relative overflow-hidden rounded-2xl border border-border bg-card washi-texture shadow-washi p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="absolute -top-8 -right-8 h-24 w-24 rounded-full bg-enso-gradient opacity-30 pointer-events-none" />
        <div className="relative flex items-center gap-3">
          <span className="h-9 w-9 rounded-xl bg-primary/10 border border-primary/15 flex items-center justify-center text-primary shrink-0">
            <Globe className="h-4 w-4" />
          </span>
          <div>
            <h2 className="text-sm font-bold text-foreground">
              Cài đặt chung <span className="font-jp text-xs font-normal text-muted-foreground">基本設定</span>
            </h2>
            <p className="text-sm text-muted-foreground">Chọn ngôn ngữ và múi giờ — dùng để tính streak và quest hằng ngày.</p>
          </div>
        </div>
        <Button variant="akane" size="sm" type="submit" isLoading={saving} className="shrink-0">
          Lưu thay đổi
        </Button>
      </div>

      {savedMsg && (
        <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-700 dark:text-emerald-300 text-sm flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          <span>Đã lưu cài đặt chung.</span>
        </div>
      )}

      <Card variant="washi" className="p-5">
        <CardContent className="p-0">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <label className="space-y-1.5">
              <span className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                <Globe className="h-3.5 w-3.5 text-primary" /> Ngôn ngữ giao diện
              </span>
              <select
                value={formData.language}
                onChange={(e) => setFormData({ ...formData, language: e.target.value })}
                className="flex h-10 w-full rounded-xl border border-border bg-background px-3 text-sm text-foreground focus:outline-none focus:border-ring"
              >
                {LANGUAGE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label} ({opt.value})
                  </option>
                ))}
              </select>
              <span className="text-xs text-muted-foreground">Chọn ngôn ngữ bạn muốn hiển thị.</span>
            </label>

            <label className="space-y-1.5">
              <span className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                <Clock className="h-3.5 w-3.5 text-primary" /> Múi giờ
              </span>
              <select
                value={formData.timezone}
                onChange={(e) => setFormData({ ...formData, timezone: e.target.value })}
                className="flex h-10 w-full rounded-xl border border-border bg-background px-3 text-sm text-foreground focus:outline-none focus:border-ring"
              >
                {TIMEZONE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
              <span className="text-xs text-muted-foreground">Dùng để tính streak, quest và lịch sử 7 ngày.</span>
            </label>
          </div>

          <div className="mt-6 pt-5 border-t border-border space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xs font-bold text-foreground flex items-center gap-1.5">
                  <span>🔊 Hiệu ứng âm thanh Nhật Bản (Japanese Sound FX)</span>
                  <span className="text-[10px] font-jp text-primary font-bold">和風効果音</span>
                </h3>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Phát âm thanh Taiko, chuông gió Furin, kiếm Katana và giọt nước Zen khi hoàn thành bài học.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 flex-wrap pt-1">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => soundFX.playTaiko()}
                className="text-xs gap-1.5"
              >
                <span>🥁 Trống Taiko</span>
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => soundFX.playFurin()}
                className="text-xs gap-1.5"
              >
                <span>🎐 Chuông Furin</span>
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => soundFX.playKatana()}
                className="text-xs gap-1.5"
              >
                <span>⚔️ Kiếm Katana</span>
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => soundFX.playSuikinkutsu()}
                className="text-xs gap-1.5"
              >
                <span>💧 Giọt nước Zen</span>
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => soundFX.playVictory()}
                className="text-xs gap-1.5 text-primary border-primary/30"
              >
                <span>🎉 Fanfare Chiến Thắng</span>
              </Button>
            </div>
          </div>

          <div className="mt-4 p-3 rounded-xl bg-muted border border-border text-xs text-muted-foreground">
            <p>
              <span className="font-semibold text-foreground">Mẹo:</span> Bạn có thể đổi giao diện 4 phong cách Nhật Bản bất cứ lúc nào qua nút bấm ở thanh điều hướng trên cùng.
            </p>
          </div>
        </CardContent>
      </Card>
    </form>
  );
}
