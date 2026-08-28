"use client";

import React, { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { audioApi } from "@/features/audio/services/audio-api";
import { VoicevoxEngine } from "@/types/audio";
import {
  FolderOpen,
  Save,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Volume2,
  ChevronDown,
  ChevronUp,
  HelpCircle,
  Zap,
  Play,
  Loader2,
} from "lucide-react";

interface VoicevoxEngineCardProps {
  onEngineReload?: () => void;
}

export function VoicevoxEngineCard({ onEngineReload }: VoicevoxEngineCardProps) {
  const [engine, setEngine] = useState<VoicevoxEngine | null>(null);
  const [pathInput, setPathInput] = useState("E:\\VoiceVox");
  const [urlInput, setUrlInput] = useState("http://127.0.0.1:50021");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [startingEngine, setStartingEngine] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [showGuide, setShowGuide] = useState(false);
  const [msg, setMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const fetchEngine = async () => {
    setLoading(true);
    try {
      const data = await audioApi.getEngine();
      setEngine(data);
      if (data.path) setPathInput(data.path);
      if (data.url) setUrlInput(data.url);
    } catch (e: any) {
      setMsg({ type: "error", text: e.message || "Không tải được thông tin engine." });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEngine();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setMsg(null);
    try {
      const data = await audioApi.updateEngine({ path: pathInput.trim(), url: urlInput.trim() });
      setEngine(data);
      setMsg({
        type: "success",
        text: `Đã lưu — ${data.path_exists ? "Tìm thấy thư mục" : "Chưa thấy thư mục"} · ${
          data.run_exe_exists ? "Có run.exe" : "Chưa thấy run.exe"
        }`,
      });
      onEngineReload?.();
    } catch (e: any) {
      setMsg({ type: "error", text: e.message || "Lưu thất bại" });
    } finally {
      setSaving(false);
    }
  };

  const handleCheck = async () => {
    setLoading(true);
    setMsg(null);
    try {
      const data = await audioApi.getEngine();
      setEngine(data);
      setMsg({
        type: data.is_available ? "success" : "error",
        text: data.is_available
          ? `VOICEVOX kết nối thành công (${data.latency_ms}ms) — ${data.available_voices_count} giọng sẵn sàng!`
          : `Chưa kết nối: ${data.status_message}`,
      });
      if (data.is_available) {
        onEngineReload?.();
      }
    } catch (e: any) {
      setMsg({ type: "error", text: e.message });
    } finally {
      setLoading(false);
    }
  };

  const handleStartEngine = async () => {
    setStartingEngine(true);
    setMsg(null);
    try {
      const data = await audioApi.startEngine();
      setEngine(data);
      if (data.is_available) {
        setMsg({
          type: "success",
          text: `Đã khởi động VOICEVOX thành công! Toàn bộ ${data.available_voices_count} giọng đọc thật đã sẵn sàng.`,
        });
        onEngineReload?.();
      } else {
        setMsg({
          type: "error",
          text: "Đã gửi lệnh khởi động, vui lòng bấm 'Kiểm tra lại' sau vài giây.",
        });
      }
    } catch (e: any) {
      setMsg({ type: "error", text: `Khởi động thất bại: ${e.message}` });
    } finally {
      setStartingEngine(false);
    }
  };

  if (loading && !engine) {
    return (
      <div className="p-5 rounded-2xl bg-card border border-border flex items-center justify-center gap-2 text-muted-foreground text-xs">
        <RefreshCw className="h-4 w-4 animate-spin text-primary" />
        <span>Đang kiểm tra trạng thái VOICEVOX Engine...</span>
      </div>
    );
  }

  const isLive = engine?.is_available;
  const pathOk = engine?.path_exists;
  const exeOk = engine?.run_exe_exists;

  return (
    <div className="rounded-2xl border border-border bg-card shadow-sm p-4 sm:p-5 space-y-4">
      {/* Header status bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div
            className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 border ${
              isLive
                ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-600 dark:text-emerald-400"
                : "bg-amber-500/10 border-amber-500/20 text-amber-600 dark:text-amber-400"
            }`}
          >
            <Volume2 className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="text-sm font-bold text-foreground">Bộ tổng hợp giọng nói VOICEVOX</h3>
              <Badge
                variant={isLive ? "matcha" : "outline"}
                size="sm"
                className={isLive ? "" : "border-amber-500/40 text-amber-600 dark:text-amber-300 bg-amber-500/10"}
              >
                {isLive ? `Online · ${engine?.latency_ms || 10}ms` : "Chế độ Ngoại tuyến (Fallback)"}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">
              {isLive
                ? `Đang chạy mượt mà với đầy đủ ${engine?.available_voices_count || 127} phong cách giọng đọc Nhật Bản.`
                : "Đang dùng các giọng đọc tiếng Nhật có sẵn. Bấm 'Khởi động VOICEVOX' để mở toàn bộ 120+ giọng."}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0 flex-wrap">
          {!isLive && exeOk && (
            <Button
              variant="akane"
              size="sm"
              onClick={handleStartEngine}
              disabled={startingEngine}
              className="text-xs h-8 rounded-xl gap-1.5 shadow-sm"
            >
              {startingEngine ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Play className="h-3.5 w-3.5 fill-current" />
              )}
              {startingEngine ? "Đang khởi động..." : "Khởi động VOICEVOX"}
            </Button>
          )}

          <Button
            variant="outline"
            size="sm"
            onClick={handleCheck}
            disabled={loading}
            className="text-xs h-8 rounded-xl"
          >
            <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} />
            Kiểm tra lại
          </Button>

          {!isLive && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowGuide(!showGuide)}
              className="text-xs h-8 text-amber-600 dark:text-amber-400 hover:bg-amber-500/10 rounded-xl"
            >
              <HelpCircle className="h-3.5 w-3.5 mr-1" />
              Hướng dẫn
            </Button>
          )}
        </div>
      </div>

      {/* Guide if offline */}
      {showGuide && !isLive && (
        <div className="p-3.5 rounded-xl bg-amber-500/8 dark:bg-amber-500/10 border border-amber-500/25 dark:border-amber-500/30 text-xs text-foreground/90 space-y-2 animate-in fade-in">
          <div className="font-bold text-amber-700 dark:text-amber-300 flex items-center gap-1.5">
            <Zap className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400" />
            Cách mở khóa toàn bộ giọng VOICEVOX trên máy tính:
          </div>
          <ol className="list-decimal list-inside space-y-1 pl-1 text-[11px] leading-relaxed text-muted-foreground">
            <li>
              Bấm nút <strong className="text-foreground">"Khởi động VOICEVOX"</strong> ở trên để hệ thống tự bật.
            </li>
            <li>
              Hoặc mở thư mục <code className="font-mono text-foreground">{engine?.path || "E:\\VoiceVox"}</code> và chạy{" "}
              <code className="font-mono text-foreground font-semibold">run.exe</code>.
            </li>
            <li>
              Quay lại đây và nhấn <strong>"Kiểm tra lại"</strong> để cập nhật danh mục giọng nói.
            </li>
          </ol>
        </div>
      )}

      {/* Feedback Message */}
      {msg && (
        <div
          className={`p-2.5 rounded-xl border text-xs flex items-center gap-2 ${
            msg.type === "success"
              ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-700 dark:text-emerald-300"
              : "bg-destructive/10 border-destructive/20 text-destructive"
          }`}
        >
          {msg.type === "success" ? (
            <CheckCircle2 className="h-4 w-4 shrink-0" />
          ) : (
            <AlertCircle className="h-4 w-4 shrink-0" />
          )}
          <span>{msg.text}</span>
        </div>
      )}

      {/* Advanced Settings Accordion */}
      <div className="pt-2 border-t border-border/60">
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center justify-between w-full text-xs font-semibold text-muted-foreground hover:text-foreground py-1 transition-colors"
        >
          <span className="flex items-center gap-1.5">
            <FolderOpen className="h-3.5 w-3.5 text-primary" />
            Tùy chỉnh đường dẫn & cổng kết nối (Nâng cao)
          </span>
          {showAdvanced ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>

        {showAdvanced && (
          <div className="mt-3 space-y-3 p-3.5 rounded-xl bg-muted/40 border border-border text-xs animate-in fade-in">
            {engine && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px]">
                <div className="flex items-center gap-1.5 text-muted-foreground">
                  <span>Thư mục:</span>
                  <span className={pathOk ? "text-emerald-600 font-semibold" : "text-amber-600"}>
                    {pathOk ? "✓ Đã tìm thấy" : "✕ Chưa tìm thấy"}
                  </span>
                </div>
                <div className="flex items-center gap-1.5 text-muted-foreground">
                  <span>File run.exe:</span>
                  <span className={exeOk ? "text-emerald-600 font-semibold" : "text-amber-600"}>
                    {exeOk ? `✓ Đã tìm thấy (${engine.run_exe_path})` : "✕ Chưa tìm thấy"}
                  </span>
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <label className="space-y-1 block">
                <span className="text-[11px] font-semibold text-foreground">Đường dẫn cài đặt</span>
                <input
                  type="text"
                  value={pathInput}
                  onChange={(e) => setPathInput(e.target.value)}
                  placeholder="E:\VoiceVox"
                  className="w-full h-8 px-2.5 rounded-lg border border-border bg-background text-xs text-foreground focus:outline-none focus:border-ring"
                />
                <span className="text-[10px] text-muted-foreground">Ví dụ: E:\VoiceVox</span>
              </label>

              <label className="space-y-1 block">
                <span className="text-[11px] font-semibold text-foreground">Địa chỉ Engine URL</span>
                <input
                  type="text"
                  value={urlInput}
                  onChange={(e) => setUrlInput(e.target.value)}
                  placeholder="http://127.0.0.1:50021"
                  className="w-full h-8 px-2.5 rounded-lg border border-border bg-background text-xs font-mono text-foreground focus:outline-none focus:border-ring"
                />
                <span className="text-[10px] text-muted-foreground">Mặc định: 127.0.0.1:50021</span>
              </label>
            </div>

            <div className="flex justify-end pt-1">
              <Button
                variant="primary"
                size="sm"
                onClick={handleSave}
                disabled={saving}
                className="h-8 text-xs rounded-lg"
              >
                <Save className="h-3.5 w-3.5 mr-1" />
                {saving ? "Đang lưu..." : "Lưu đường dẫn"}
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
