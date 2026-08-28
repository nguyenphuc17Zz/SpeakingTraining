"use client";

import React, { useState, useRef } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Sparkles,
  Play,
  Zap,
  Activity,
  BarChart3,
  Cpu,
  RefreshCw,
  Terminal,
  Sliders,
  AlertCircle,
  CheckCircle2,
  Layers,
  ArrowRight,
  Flame,
} from "lucide-react";
import { useAI } from "@/hooks/use-ai";
import { aiApi } from "@/services/ai-api";
import { AITask, AIResponseRead, AIStreamEvent } from "@/types/ai";

const PROMPT_PRESETS = [
  {
    name: "日常会話 (Daily Conversation)",
    task: "conversation" as AITask,
    system: "You are Yuki, a friendly 24-year-old Tokyo resident. Speak entirely in natural Japanese suited for an N3 learner. Keep replies concise (1-3 sentences).",
    prompt: "こんにちは！今日はいい天気ですね。週末は何をして過ごしましたか？",
  },
  {
    name: "接客・敬語 (Keigo Politeness)",
    task: "conversation" as AITask,
    system: "You are a polite hotel concierge in Kyoto. Speak in flawless Sonkeigo and Kenjougo.",
    prompt: "すみません、チェックインをお願いしたいのですが、予約の確認をしていただけますか？",
  },
  {
    name: "文法・ニュアンス添削 (Grammar Correction)",
    task: "grammar_correction" as AITask,
    system: "You are an expert Japanese teacher. Analyze the user's sentence and point out grammatical errors, particle misuse, and give 2 natural alternatives.",
    prompt: "私は昨日友達と寿司を食べましたでした。とても美味しかったです。",
  },
  {
    name: "居酒屋注文 (Izakaya Roleplay)",
    task: "conversation" as AITask,
    system: "You are an energetic Izakaya waiter in Osaka. Use friendly, energetic Japanese (with light Kansai-ben). Recommend seasonal sashimi and drinks.",
    prompt: "すみません！生ビール２つと、おすすめの料理を教えてください！",
  },
];

export default function AIPlaygroundPage() {
  const { models, healthList } = useAI();

  const [provider, setProvider] = useState<string>("auto");
  const [model, setModel] = useState<string>("");
  const [task, setTask] = useState<AITask>("conversation");
  const [temperature, setTemperature] = useState<number>(0.7);
  const [streaming, setStreaming] = useState<boolean>(true);
  const [systemInstruction, setSystemInstruction] = useState<string>(
    "You are a helpful and natural Japanese speaking tutor. Keep answers concise."
  );
  const [userInput, setUserInput] = useState<string>("こんにちは！日本語の練習をしましょう。");

  // Execution state
  const [loading, setLoading] = useState<boolean>(false);
  const [outputText, setOutputText] = useState<string>("");
  const [diagnostic, setDiagnostic] = useState<AIResponseRead | null>(null);
  const [streamError, setStreamError] = useState<string | null>(null);
  const [activeRouteInfo, setActiveRouteInfo] = useState<{
    provider?: string;
    model?: string;
    latency_ms?: number;
    fallback?: boolean;
    requestId?: string;
  } | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);

  const handleApplyPreset = (preset: typeof PROMPT_PRESETS[0]) => {
    setTask(preset.task);
    setSystemInstruction(preset.system);
    setUserInput(preset.prompt);
  };

  const handleRun = async () => {
    if (!userInput.trim()) return;

    setLoading(true);
    setOutputText("");
    setStreamError(null);
    setDiagnostic(null);
    setActiveRouteInfo(null);

    const payload = {
      messages: [{ role: "user" as const, content: userInput.trim() }],
      task,
      provider: provider === "auto" ? undefined : provider,
      model: model || undefined,
      temperature,
      system_instruction: systemInstruction.trim() || undefined,
      stream: streaming,
    };

    if (streaming) {
      abortControllerRef.current = new AbortController();
      let streamedBuffer = "";
      const startTime = Date.now();

      await aiApi.streamGenerate(
        payload,
        {
          onStarted: (evt) => {
            setActiveRouteInfo((prev) => ({
              ...prev,
              provider: evt.provider,
              model: evt.model,
              requestId: evt.request_id,
            }));
          },
          onTextDelta: (delta) => {
            streamedBuffer += delta;
            setOutputText(streamedBuffer);
          },
          onUsage: (usage) => {
            setDiagnostic((prev) =>
              prev
                ? { ...prev, usage }
                : {
                    text: streamedBuffer,
                    model: model || "default",
                    provider: provider,
                    usage,
                    latency_ms: Date.now() - startTime,
                    fallback_occurred: false,
                    attempt_history: [],
                  }
            );
          },
          onCompleted: (evt) => {
            setActiveRouteInfo((prev) => ({
              ...prev,
              provider: evt.provider,
              model: evt.model,
              latency_ms: evt.latency_ms || Date.now() - startTime,
              fallback: evt.fallback_occurred,
              requestId: evt.request_id,
            }));
            setLoading(false);
          },
          onError: (err) => {
            setStreamError(err);
            setLoading(false);
          },
        },
        abortControllerRef.current.signal
      );
    } else {
      try {
        const resp = await aiApi.generate(payload);
        setOutputText(resp.text);
        setDiagnostic(resp);
        setActiveRouteInfo({
          provider: resp.provider,
          model: resp.model,
          latency_ms: resp.latency_ms,
          fallback: resp.fallback_occurred,
          requestId: resp.request_id,
        });
      } catch (err: any) {
        setStreamError(err.message || "Execution failed");
      } finally {
        setLoading(false);
      }
    }
  };

  const filteredModels = models.filter((m) =>
    provider === "auto" ? true : m.provider_id === provider
  );

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-border">
        <div>
          <div className="flex items-center gap-2">
            <Sparkles className="h-6 w-6 text-primary" />
            <h1 className="text-xl font-bold text-foreground">
              AI Router Playground & Diagnostics (AIプレイグラウンド)
            </h1>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Test prompt execution, real-time streaming, latency telemetry, and automatic fallback across Gemini, Groq, and OpenRouter.
          </p>
        </div>
      </div>

      {/* Preset Pills */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
        <span className="text-muted-foreground shrink-0 font-semibold">Presets:</span>
        {PROMPT_PRESETS.map((p, idx) => (
          <button
            key={idx}
            onClick={() => handleApplyPreset(p)}
            className="px-3 py-1 rounded-xl bg-card border border-border text-foreground hover:text-primary hover:border-primary/40 transition-all shrink-0 flex items-center gap-1.5"
          >
            <Flame className="h-3 w-3 text-primary" />
            <span>{p.name}</span>
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Form: Parameters & Prompt */}
        <div className="lg:col-span-7 space-y-4">
          <Card glass className="p-5 space-y-4">
            <h2 className="text-sm font-bold text-foreground flex items-center gap-2">
              <Sliders className="h-4 w-4 text-aizome-400" />
              <span>Routing & Generation Parameters</span>
            </h2>

            {/* Provider & Model Selectors */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div>
                <label className="block text-muted-foreground font-semibold mb-1">Target Provider</label>
                <select
                  value={provider}
                  onChange={(e) => {
                    setProvider(e.target.value);
                    setModel("");
                  }}
                  className="w-full bg-card border border-border rounded-xl px-3 py-2 text-foreground focus:outline-none focus:border-primary"
                >
                  <option value="auto">✨ Auto Router (Intelligent Fallback)</option>
                  <option value="gemini">Google Gemini (Default Primary)</option>
                  <option value="groq">Groq LPU (Ultra-Fast)</option>
                  <option value="openrouter">OpenRouter (Gateway)</option>
                </select>
              </div>

              <div>
                <label className="block text-muted-foreground font-semibold mb-1">Model Selection</label>
                <select
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  className="w-full bg-card border border-border rounded-xl px-3 py-2 text-foreground focus:outline-none focus:border-primary font-mono"
                >
                  <option value="">✨ Default Recommended for Task</option>
                  {filteredModels.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.id} {m.is_recommended ? "★ (Recommended)" : ""} {m.context_window ? `[${m.context_window >= 1000000 ? `${(m.context_window / 1000000).toFixed(0)}M` : `${Math.round(m.context_window / 1000)}k`} ctx]` : ""} ({m.provider_id})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Task & Temperature */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
              <div>
                <label className="block text-muted-foreground font-semibold mb-1">AI Task</label>
                <select
                  value={task}
                  onChange={(e) => setTask(e.target.value as AITask)}
                  className="w-full bg-card border border-border rounded-xl px-3 py-2 text-foreground focus:outline-none focus:border-primary"
                >
                  <option value="conversation">Conversation Turn</option>
                  <option value="deep_analysis">Deep Analysis</option>
                  <option value="grammar_correction">Grammar Correction</option>
                  <option value="translation">Translation</option>
                  <option value="summarization">Summarization</option>
                  <option value="playground">General Playground</option>
                </select>
              </div>

              <div>
                <label className="block text-muted-foreground font-semibold mb-1">
                  Temperature: <span className="font-mono text-aizome-300">{temperature}</span>
                </label>
                <input
                  type="range"
                  min="0.0"
                  max="1.0"
                  step="0.1"
                  value={temperature}
                  onChange={(e) => setTemperature(parseFloat(e.target.value))}
                  className="w-full mt-2 accent-primary"
                />
              </div>

              <div>
                <label className="block text-muted-foreground font-semibold mb-1">Stream Mode</label>
                <button
                  type="button"
                  onClick={() => setStreaming(!streaming)}
                  className={`w-full py-2 px-3 rounded-xl border text-xs font-bold transition-all flex items-center justify-center gap-2 ${
                    streaming
                      ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40 shadow-sm"
                      : "bg-card text-muted-foreground border-border"
                  }`}
                >
                  <Zap className="h-3.5 w-3.5" />
                  <span>{streaming ? "SSE Streaming (ON)" : "Single-Turn (OFF)"}</span>
                </button>
              </div>
            </div>

            {/* System Instruction */}
            <div className="space-y-1 text-xs">
              <label className="block text-muted-foreground font-semibold">System Instruction</label>
              <textarea
                value={systemInstruction}
                onChange={(e) => setSystemInstruction(e.target.value)}
                rows={2}
                placeholder="Persona system seed or instruction..."
                className="w-full bg-card border border-border rounded-xl p-3 text-foreground text-xs focus:outline-none focus:border-primary resize-none font-mono"
              />
            </div>

            {/* User Input */}
            <div className="space-y-1 text-xs">
              <label className="block text-muted-foreground font-semibold">User Message (Japanese Prompt)</label>
              <textarea
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                rows={3}
                placeholder="Type Japanese text here..."
                className="w-full bg-card border border-border rounded-xl p-3 text-foreground text-sm focus:outline-none focus:border-primary resize-none"
              />
            </div>

            {/* Execute Button */}
            <div className="flex justify-end pt-2">
              <Button
                variant="primary"
                size="md"
                onClick={handleRun}
                isLoading={loading}
                disabled={!userInput.trim()}
                className="w-full sm:w-auto"
              >
                <Play className="h-4 w-4 fill-current" />
                <span>Run AI Execution (実行)</span>
              </Button>
            </div>
          </Card>
        </div>

        {/* Right Form: Output & Diagnostics Panel */}
        <div className="lg:col-span-5 space-y-4">
          <Card glass className="p-5 flex flex-col h-full min-h-[420px]">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <h2 className="text-sm font-bold text-foreground flex items-center gap-2">
                <Terminal className="h-4 w-4 text-emerald-400" />
                <span>AI Stream Response & Telemetry</span>
              </h2>
              {loading && (
                <span className="flex items-center gap-1.5 text-xs text-primary animate-pulse">
                  <span className="h-2 w-2 rounded-full bg-primary animate-ping" />
                  Generating...
                </span>
              )}
            </div>

            {/* Live Output Box */}
            <div className="flex-1 my-3 p-4 rounded-xl bg-background/80 border border-border overflow-y-auto text-sm text-foreground leading-relaxed font-sans min-h-[160px]">
              {streamError ? (
                <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/30 text-destructive text-xs flex items-start gap-2">
                  <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                  <div>
                    <p className="font-bold">Execution Error</p>
                    <p className="mt-1 font-mono text-[11px]">{streamError}</p>
                  </div>
                </div>
              ) : outputText ? (
                <div>
                  <p className="whitespace-pre-wrap">{outputText}</p>
                  {loading && (
                    <span className="inline-block w-2 h-4 bg-primary ml-1 animate-pulse" />
                  )}
                </div>
              ) : (
                <p className="text-xs text-muted-foreground italic">
                  Response text and token streaming will appear here after clicking Run...
                </p>
              )}
            </div>

            {/* Diagnostic Inspector Strip */}
            <div className="pt-3 border-t border-border/80 space-y-2 text-xs">
              <div className="flex items-center justify-between text-muted-foreground">
                <span className="font-semibold uppercase tracking-wider text-[10px]">Diagnostics</span>
                {activeRouteInfo?.fallback && (
                  <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 text-[10px] font-mono border border-amber-500/30">
                    ⚠ Fallback Route Engaged
                  </span>
                )}
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                <div className="p-2 rounded-lg bg-card border border-border">
                  <span className="text-[10px] text-muted-foreground block">Provider</span>
                  <span className="font-mono font-bold text-foreground">
                    {activeRouteInfo?.provider || diagnostic?.provider || "—"}
                  </span>
                </div>

                <div className="p-2 rounded-lg bg-card border border-border">
                  <span className="text-[10px] text-muted-foreground block">Latency</span>
                  <span className="font-mono font-bold text-amber-300">
                    {activeRouteInfo?.latency_ms ? `${activeRouteInfo.latency_ms} ms` : diagnostic?.latency_ms ? `${diagnostic.latency_ms} ms` : "—"}
                  </span>
                </div>

                <div className="p-2 rounded-lg bg-card border border-border">
                  <span className="text-[10px] text-muted-foreground block">Input Tokens</span>
                  <span className="font-mono font-bold text-indigo-300">
                    {diagnostic?.usage.input_tokens ?? "—"}
                  </span>
                </div>

                <div className="p-2 rounded-lg bg-card border border-border">
                  <span className="text-[10px] text-muted-foreground block">Output Tokens</span>
                  <span className="font-mono font-bold text-rose-300">
                    {diagnostic?.usage.output_tokens ?? "—"}
                  </span>
                </div>
              </div>

              {activeRouteInfo?.requestId && (
                <div className="flex items-center justify-between text-[11px] text-muted-foreground pt-1 font-mono">
                  <span>Request ID:</span>
                  <span className="text-muted-foreground">{activeRouteInfo.requestId}</span>
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
