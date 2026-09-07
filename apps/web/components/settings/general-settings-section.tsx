"use client";

import React, { useEffect, useState } from "react";
import { useSettings } from "@/hooks/use-settings";
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
    <form onSubmit={handleSave} className="space-y-6">
      {/* Header Banner */}
      <div className="rounded-xl border border-border bg-card p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-2xs">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center text-primary shrink-0">
            <Globe className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-foreground">Cài đặt chung</h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              Cấu hình ngôn ngữ hiển thị và múi giờ phục vụ việc tính toán streak và nhiệm vụ hàng ngày.
            </p>
          </div>
        </div>
        <Button size="sm" type="submit" isLoading={saving} className="shrink-0 font-medium">
          Lưu thay đổi
        </Button>
      </div>

      {savedMsg && (
        <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-xs font-medium flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          <span>Đã lưu cài đặt chung thành công.</span>
        </div>
      )}

      {/* Settings Options Card */}
      <div className="rounded-xl border border-border bg-card p-5 space-y-6 shadow-2xs">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div className="space-y-2">
            <label className="text-xs font-medium text-foreground flex items-center gap-1.5">
              <Globe className="h-3.5 w-3.5 text-muted-foreground" />
              Ngôn ngữ giao diện
            </label>
            <select
              value={formData.language}
              onChange={(e) => setFormData({ ...formData, language: e.target.value })}
              className="flex h-9 w-full rounded-lg border border-border bg-background px-3 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-ring transition-colors"
            >
              {LANGUAGE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label} ({opt.value})
                </option>
              ))}
            </select>
            <p className="text-[11px] text-muted-foreground">Ngôn ngữ ưu tiên cho giao diện người dùng và điều hướng.</p>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-medium text-foreground flex items-center gap-1.5">
              <Clock className="h-3.5 w-3.5 text-muted-foreground" />
              Múi giờ hoạt động
            </label>
            <select
              value={formData.timezone}
              onChange={(e) => setFormData({ ...formData, timezone: e.target.value })}
              className="flex h-9 w-full rounded-lg border border-border bg-background px-3 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-ring transition-colors"
            >
              {TIMEZONE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            <p className="text-[11px] text-muted-foreground">Múi giờ chuẩn xác để tính chuỗi Streak và lịch sử luyện tập.</p>
          </div>
        </div>

        {/* Audio Effects Audition */}
        <div className="pt-5 border-t border-border space-y-3">
          <div>
            <h3 className="text-xs font-semibold text-foreground flex items-center gap-1.5">
              <Volume2 className="h-3.5 w-3.5 text-muted-foreground" />
              <span>Kiểm tra hiệu ứng âm thanh phản hồi</span>
            </h3>
            <p className="text-[11px] text-muted-foreground mt-0.5">
              Âm thanh phản hồi ngắn khi hoàn thành mục tiêu, bài tập hoặc đạt combo.
            </p>
          </div>

          <div className="flex items-center gap-2 flex-wrap pt-1">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => soundFX.playTaiko()}
              className="text-xs h-8 gap-1.5"
            >
              <span>🥁 Taiko</span>
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => soundFX.playFurin()}
              className="text-xs h-8 gap-1.5"
            >
              <span>🎐 Furin</span>
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => soundFX.playKatana()}
              className="text-xs h-8 gap-1.5"
            >
              <span>⚔️ Katana</span>
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => soundFX.playSuikinkutsu()}
              className="text-xs h-8 gap-1.5"
            >
              <span>💧 Zen Drop</span>
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => soundFX.playVictory()}
              className="text-xs h-8 gap-1.5 text-primary border-primary/30"
            >
              <span>✨ Success Fanfare</span>
            </Button>
          </div>
        </div>
      </div>
    </form>
  );
}
