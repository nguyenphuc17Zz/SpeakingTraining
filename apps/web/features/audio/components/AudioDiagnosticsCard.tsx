"use client";

import React, { useEffect, useState } from "react";
import { Activity, CheckCircle, XCircle, RefreshCw, Cpu, Server, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { audioApi } from "../services/audio-api";

export function AudioDiagnosticsCard() {
  const [diagnostics, setDiagnostics] = useState<Record<string, any> | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchDiagnostics = async () => {
    setIsLoading(true);
    try {
      const data = await audioApi.getDiagnostics();
      setDiagnostics(data);
    } catch (e) {
      console.warn("[Diagnostics] Fetch failed:", e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDiagnostics();
  }, []);

  return (
    <div className="p-5 rounded-2xl bg-card/80 border border-border space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            <Activity className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-foreground">Audio System Diagnostics</h3>
            <p className="text-xs text-muted-foreground">Trạng thái thời gian thực của Audio & Voice Engines</p>
          </div>
        </div>

        <Button
          size="sm"
          variant="outline"
          onClick={fetchDiagnostics}
          disabled={isLoading}
          className="h-8 px-2.5 text-xs"
        >
          <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${isLoading ? "animate-spin" : ""}`} />
          Làm mới
        </Button>
      </div>

      {diagnostics && (
        <div className="space-y-3 pt-2">
          {/* TTS Providers Status */}
          <div className="p-3.5 rounded-xl bg-background/70 border border-border space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-foreground">
              <Server className="h-4 w-4 text-rose-400" />
              <span>Text-to-Speech (TTS) Engines</span>
            </div>
            {diagnostics.tts_providers?.map((p: any) => (
              <div
                key={p.provider_id}
                className="flex items-center justify-between text-xs py-1 px-2 rounded-lg bg-card/60 border border-border/40"
              >
                <div className="flex items-center gap-2">
                  {p.is_available ? (
                    <CheckCircle className="h-3.5 w-3.5 text-emerald-400" />
                  ) : (
                    <XCircle className="h-3.5 w-3.5 text-rose-400" />
                  )}
                  <span className="font-medium text-foreground">{p.name}</span>
                </div>
                <div className="flex items-center gap-2 font-mono text-[11px] text-muted-foreground">
                  {p.latency_ms !== null && <span>{p.latency_ms}ms</span>}
                  <span>({p.available_voices_count} giọng)</span>
                </div>
              </div>
            ))}
          </div>

          {/* STT Providers */}
          <div className="p-3.5 rounded-xl bg-background/70 border border-border space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-foreground">
              <Cpu className="h-4 w-4 text-indigo-400" />
              <span>Speech-to-Text (STT) Engines</span>
            </div>
            {diagnostics.stt_providers?.map((p: any) => (
              <div
                key={p.provider_id}
                className="flex items-center justify-between text-xs py-1 px-2 rounded-lg bg-card/60 border border-border/40"
              >
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-3.5 w-3.5 text-emerald-400" />
                  <span className="font-medium text-foreground">{p.name}</span>
                </div>
                <div className="text-[11px] font-mono text-muted-foreground">
                  {p.available_models_count} models
                </div>
              </div>
            ))}
          </div>

          {/* Cache Stats */}
          {diagnostics.cache && (
            <div className="p-3.5 rounded-xl bg-background/70 border border-border flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <Zap className="h-4 w-4 text-amber-400" />
                <span className="font-medium text-foreground">TTS In-Memory LRU Cache</span>
              </div>
              <div className="flex items-center gap-3 font-mono text-[11px] text-muted-foreground">
                <span>{diagnostics.cache.entries} / {diagnostics.cache.max_entries} mục</span>
                <span className="text-emerald-400 font-bold">
                  {(diagnostics.cache.hit_rate * 100).toFixed(0)}% hit rate
                </span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
