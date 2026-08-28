"use client";

import React, { useState } from "react";
import { useProviders } from "@/hooks/use-providers";
import { useAI } from "@/hooks/use-ai";
import { useAIUsage } from "@/hooks/use-ai-usage";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";
import {
  Key,
  ShieldCheck,
  Trash2,
  ExternalLink,
  CheckCircle2,
  Eye,
  EyeOff,
  Cpu,
  Sparkles,
  Zap,
  BarChart3,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  MoreHorizontal,
  Activity,
} from "lucide-react";
import { ProviderDetail } from "@/types/provider";
import { ProviderHealth } from "@/types/ai";

export function ProviderSettingsSection() {
  const {
    providers,
    loading: loadingProviders,
    actionLoading,
    saveCredential,
    deleteCredential,
    refetch: refetchProviders,
  } = useProviders();

  const {
    healthList,
    routingPolicy,
    testingProvider,
    refreshingModels,
    testConnection,
    updateRouting,
    refreshModels,
  } = useAI();

  const { usageSummary } = useAIUsage();

  const [selectedProvider, setSelectedProvider] = useState<ProviderDetail | null>(null);
  const [apiKeyInput, setApiKeyInput] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [feedbackMsg, setFeedbackMsg] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<Record<string, ProviderHealth>>({});
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [showUsage, setShowUsage] = useState(false);
  const [menuOpenId, setMenuOpenId] = useState<string | null>(null);

  const handleOpenConfig = (provider: ProviderDetail) => {
    setSelectedProvider(provider);
    setApiKeyInput("");
    setShowKey(false);
    setFeedbackMsg(null);
    setIsModalOpen(true);
  };

  const handleSave = async () => {
    if (!selectedProvider || !apiKeyInput.trim()) return;
    const ok = await saveCredential({
      provider: selectedProvider.id,
      api_key: apiKeyInput.trim(),
    });
    if (ok) {
      setIsModalOpen(false);
      setFeedbackMsg(`Đã lưu key ${selectedProvider.display_name} an toàn (AES-256).`);
      await refreshModels(selectedProvider.id);
      await refetchProviders();
    }
  };

  const handleDelete = async (credentialId: string) => {
    if (confirm("Bạn có chắc muốn xóa API key này?")) {
      await deleteCredential(credentialId);
      await refreshModels();
      await refetchProviders();
      setMenuOpenId(null);
      setFeedbackMsg("Đã xóa key.");
    }
  };

  const handleTestConnection = async (providerId: string) => {
    const res = await testConnection(providerId);
    if (res) setTestResult((prev) => ({ ...prev, [providerId]: res }));
    setMenuOpenId(null);
  };

  const handleSyncAllModels = async (providerId?: string) => {
    const updated = await refreshModels(providerId);
    await refetchProviders();
    if (updated.length > 0) {
      setFeedbackMsg(`Đã đồng bộ ${updated.length} models.`);
    } else {
      setFeedbackMsg("Đã đồng bộ — không có model mới.");
    }
  };

  const handleApplyModel = async (providerId: string, modelId: string) => {
    await updateRouting({
      preferred_provider: providerId,
      default_model: modelId,
    });
    setFeedbackMsg(`Đã chọn ${modelId} (${providerId.toUpperCase()}) — áp dụng cho toàn hệ thống (hội thoại, Coach, chấm bài).`);
  };

  const getHealth = (providerId: string): ProviderHealth | undefined =>
    testResult[providerId] || healthList.find((h) => h.provider_id === providerId);

  const configuredCount = providers.filter((p) => p.is_configured).length;
  const primaryId = routingPolicy?.preferred_provider || "gemini";

  return (
    <div className="space-y-5">
      {/* Header washi gọn */}
      <div className="relative overflow-hidden rounded-2xl border border-border bg-card washi-texture shadow-washi p-4 flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div className="absolute -top-10 -right-10 h-32 w-32 rounded-full bg-enso-gradient opacity-30 pointer-events-none" />
        <div className="relative flex items-center gap-3">
          <span className="h-10 w-10 rounded-xl bg-primary/10 border border-primary/15 flex items-center justify-center text-primary shrink-0">
            <Cpu className="h-5 w-5" />
          </span>
          <div>
            <h2 className="text-base font-bold text-foreground">
              Cấu hình AI <span className="font-jp text-xs font-normal text-muted-foreground">AI設定</span>
            </h2>
            <p className="text-sm text-muted-foreground">Quản lý key, chọn model và điều hướng thông minh.</p>
          </div>
        </div>
        <div className="relative flex items-center gap-2 flex-wrap">
          <span className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full bg-card border border-border text-muted-foreground">
            <span className={`h-2 w-2 rounded-full ${configuredCount > 0 ? "bg-emerald-500" : "bg-muted-foreground"}`} />
            {configuredCount}/{providers.length} đã kết nối
          </span>
          <span className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-primary/10 border border-primary/15 text-primary font-semibold">
            <Zap className="h-3 w-3" /> {primaryId.toUpperCase()}
            <span className="font-normal text-muted-foreground">đang dùng</span>
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleSyncAllModels()}
            isLoading={refreshingModels}
            className="h-8 text-xs"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${refreshingModels ? "animate-spin" : ""}`} />
            Đồng bộ model
          </Button>
          <span
            title="Mã hóa AES-256 khi lưu"
            className="hidden sm:inline-flex items-center gap-1 text-xs text-emerald-700 bg-emerald-500/10 px-2 py-1 rounded-full border border-emerald-500/20 dark:text-emerald-300"
          >
            <ShieldCheck className="h-3.5 w-3.5" /> AES-256
          </span>
        </div>
      </div>

      {feedbackMsg && (
        <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-700 dark:text-emerald-300 text-sm flex items-center justify-between gap-2">
          <span className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 shrink-0" />
            {feedbackMsg}
          </span>
          <button onClick={() => setFeedbackMsg(null)} className="text-sm font-bold px-2 hover:opacity-70">
            ✕
          </button>
        </div>
      )}

      {/* Routing — gọn 1 card */}
      <Card variant="washi" className="p-4 md:p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
            <span className="h-7 w-7 rounded-lg bg-primary/10 border border-primary/15 flex items-center justify-center text-primary">
              <Sparkles className="h-3.5 w-3.5" />
            </span>
            Điều hướng & Model hệ thống
          </h3>
          <span className="flex items-center gap-2 text-xs">
            <span className="text-muted-foreground">Chế độ:</span>
            <button
              onClick={() => updateRouting({ routing_mode: routingPolicy?.routing_mode === "auto" ? "manual" : "auto" })}
              className={`px-2.5 py-1 rounded-full text-xs font-bold border transition-colors ${
                routingPolicy?.routing_mode === "auto"
                  ? "bg-primary text-primary-foreground border-primary"
                  : "bg-muted text-muted-foreground border-border"
              }`}
            >
              {routingPolicy?.routing_mode === "manual" ? "Thủ công" : "Tự động"}
            </button>
            <span className="text-muted-foreground ml-1">Fallback:</span>
            <button
              onClick={() => updateRouting({ fallback_enabled: !routingPolicy?.fallback_enabled })}
              className={`px-2.5 py-1 rounded-full text-xs font-bold border transition-colors ${
                routingPolicy?.fallback_enabled
                  ? "bg-emerald-500 text-white border-emerald-600"
                  : "bg-muted text-muted-foreground border-border"
              }`}
            >
              {routingPolicy?.fallback_enabled ? "Bật" : "Tắt"}
            </button>
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <label className="space-y-1.5">
            <span className="text-xs font-semibold text-muted-foreground">Nhà cung cấp ưu tiên</span>
            <select
              value={routingPolicy?.preferred_provider || "gemini"}
              onChange={(e) => {
                const newProv = e.target.value;
                const provObj = providers.find((p) => p.id === newProv);
                const firstModel = provObj?.models[0]?.id || "";
                updateRouting({ preferred_provider: newProv, default_model: firstModel || routingPolicy?.default_model });
                if (firstModel) setFeedbackMsg(`Đã chuyển sang ${newProv.toUpperCase()} — ${firstModel}`);
              }}
              className="w-full h-10 bg-background border border-border rounded-xl px-3 text-sm text-foreground focus:outline-none focus:border-ring"
            >
              <option value="gemini">Gemini — Google (mặc định)</option>
              <option value="groq">Groq — Siêu tốc</option>
              <option value="openrouter">OpenRouter — Gateway</option>
            </select>
          </label>

          <label className="space-y-1.5">
            <span className="text-xs font-semibold text-muted-foreground flex items-center gap-1.5">
              Model đang dùng <Badge variant="matcha" size="sm" className="text-[10px]">Toàn hệ thống</Badge>
            </span>
            <select
              value={routingPolicy?.default_model || ""}
              onChange={(e) => handleApplyModel(routingPolicy?.preferred_provider || "gemini", e.target.value)}
              className="w-full h-10 bg-background border border-primary/20 rounded-xl px-3 text-sm font-mono text-foreground focus:outline-none focus:border-primary"
            >
              {(providers.find((p) => p.id === (routingPolicy?.preferred_provider || "gemini"))?.models || []).map((m) => (
                <option key={m.id} value={m.id}>
                  {m.id} {m.is_recommended ? "★" : ""} {m.context_window ? `· ${m.context_window >= 1_000_000 ? `${(m.context_window / 1_000_000).toFixed(0)}M` : `${Math.round(m.context_window / 1000)}k`}` : ""}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className="flex flex-wrap items-center gap-2 p-2.5 rounded-xl bg-amber-500/5 border border-amber-500/15">
          <span className="inline-flex items-center gap-1.5 text-xs font-bold text-amber-700 dark:text-amber-300">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-500 animate-pulse" /> Áp dụng toàn hệ thống
          </span>
          <span className="text-xs text-muted-foreground">
            Model bạn chọn ở đây sẽ dùng cho <span className="font-semibold text-foreground">mọi hội thoại, chấm bài, Coach, Shadowing, Playground</span>.
          </span>
        </div>
        <p className="text-xs text-muted-foreground">
          Fallback tự động: <span className="font-mono text-foreground">Gemini → Groq → OpenRouter</span>
          <span className="text-muted-foreground"> · Chọn model ở dropdown là áp dụng ngay.</span>
        </p>
      </Card>

      {/* Thống kê — accordion gọn */}
      {usageSummary && (
        <Card variant="washi" className="overflow-hidden">
          <button
            onClick={() => setShowUsage(!showUsage)}
            className="w-full flex items-center justify-between p-4 text-left hover:bg-muted/40 transition-colors"
          >
            <span className="flex items-center gap-2 text-sm font-semibold text-foreground">
              <BarChart3 className="h-4 w-4 text-muted-foreground" /> Thống kê sử dụng
              <span className="text-xs font-normal text-muted-foreground">
                · {usageSummary.total_requests.toLocaleString()} requests · {usageSummary.total_tokens.toLocaleString()} tokens
              </span>
            </span>
            {showUsage ? <ChevronUp className="h-4 w-4 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
          </button>
          {showUsage && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 p-4 pt-0">
              <span className="p-3 rounded-xl bg-muted border border-border block">
                <span className="text-xs text-muted-foreground flex items-center gap-1">
                  <Activity className="h-3 w-3" /> Requests
                </span>
                <span className="text-lg font-bold font-mono text-foreground">{usageSummary.total_requests.toLocaleString()}</span>
                <span className="text-xs text-emerald-600 dark:text-emerald-400">
                  {usageSummary.successful_requests} ok · {usageSummary.failed_requests} lỗi
                </span>
              </span>
              <span className="p-3 rounded-xl bg-muted border border-border block">
                <span className="text-xs text-muted-foreground">Tokens</span>
                <span className="text-lg font-bold font-mono text-foreground block">{usageSummary.total_tokens.toLocaleString()}</span>
                <span className="text-xs text-muted-foreground">
                  {usageSummary.total_input_tokens.toLocaleString()} in / {usageSummary.total_output_tokens.toLocaleString()} out
                </span>
              </span>
              <span className="p-3 rounded-xl bg-muted border border-border block">
                <span className="text-xs text-muted-foreground">Độ trễ TB</span>
                <span className="text-lg font-bold font-mono text-foreground block">{usageSummary.avg_latency_ms} ms</span>
                <span className="text-xs text-muted-foreground">Turnaround</span>
              </span>
              <span className="p-3 rounded-xl bg-muted border border-border block">
                <span className="text-xs text-muted-foreground">Chế độ</span>
                <span className="text-lg font-bold font-mono text-foreground block uppercase">{routingPolicy?.routing_mode || "auto"}</span>
                <span className="text-xs text-muted-foreground">Fallback {routingPolicy?.fallback_enabled ? "bật" : "tắt"}</span>
              </span>
            </div>
          )}
        </Card>
      )}

      {/* Provider list — compact */}
      {loadingProviders ? (
        <div className="p-10 text-center text-sm text-muted-foreground">Đang tải nhà cung cấp…</div>
      ) : (
        <div className="space-y-3">
          <h3 className="text-sm font-bold text-foreground px-1">Nhà cung cấp ({providers.length})</h3>
          {providers.map((p) => {
            const health = getHealth(p.id);
            const isPrimary = primaryId === p.id;
            const isExpanded = expandedId === p.id;
            const isTesting = testingProvider === p.id;
            const ctxLabel = (ctx?: number) =>
              !ctx ? "" : ctx >= 1_000_000 ? `${(ctx / 1_000_000).toFixed(0)}M` : `${Math.round(ctx / 1000)}k`;

            return (
              <Card key={p.id} variant="washi" className={`overflow-hidden transition-all ${isPrimary ? "ring-1 ring-primary/15 border-primary/20" : ""}`}>
                {/* Compact row */}
                <div className="flex items-center gap-3 p-3 md:p-4">
                  <button
                    onClick={() => setExpandedId(isExpanded ? null : p.id)}
                    className="flex-1 min-w-0 flex items-center gap-3 text-left"
                  >
                    <span
                      className={`h-9 w-9 rounded-xl flex items-center justify-center text-white font-bold text-xs shrink-0 ${
                        p.id === "gemini" ? "bg-gradient-to-br from-blue-500 to-indigo-600" : p.id === "groq" ? "bg-gradient-to-br from-amber-500 to-orange-600" : "bg-gradient-to-br from-violet-500 to-purple-600"
                      }`}
                    >
                      {p.display_name.charAt(0)}
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="flex items-center gap-1.5 flex-wrap">
                        <span className="text-sm font-bold text-foreground truncate">{p.display_name}</span>
                        {isPrimary && (
                          <Badge variant="fuji" size="sm" className="text-[10px]">
                            Đang dùng
                          </Badge>
                        )}
                        {!p.is_configured ? (
                          <span className="text-xs px-2 py-0.5 rounded-full bg-muted text-muted-foreground border border-border">Chưa có key</span>
                        ) : health?.status === "healthy" ? (
                          <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-700 border border-emerald-500/20 dark:text-emerald-400 flex items-center gap-1">
                            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" /> OK{health.latency_ms ? ` ${health.latency_ms}ms` : ""}
                          </span>
                        ) : health?.status === "degraded" ? (
                          <span className="text-xs px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-700 border border-amber-500/20 dark:text-amber-400">Chậm</span>
                        ) : health?.status === "unavailable" ? (
                          <span className="text-xs px-2 py-0.5 rounded-full bg-destructive/10 text-destructive border border-destructive/20">Lỗi</span>
                        ) : (
                          <span className="text-xs px-2 py-0.5 rounded-full bg-muted text-muted-foreground border border-border">Chưa kiểm tra</span>
                        )}
                      </span>
                      <span className="text-xs text-muted-foreground truncate hidden sm:block">
                        {p.is_configured ? `${p.credential?.masked_secret} · ${p.models.length} models` : p.description}
                      </span>
                    </span>
                    <span className="hidden md:flex items-center gap-1 text-xs text-muted-foreground shrink-0">
                      {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </span>
                  </button>

                  {/* Primary CTA */}
                  <Button
                    variant={p.is_configured ? "outline" : "akane"}
                    size="sm"
                    onClick={() => handleOpenConfig(p)}
                    className="shrink-0 h-8 text-xs"
                  >
                    <Key className="h-3.5 w-3.5" />
                    <span className="hidden sm:inline">{p.is_configured ? "Đổi key" : "Thêm key"}</span>
                    <span className="sm:hidden">{p.is_configured ? "Đổi" : "Thêm"}</span>
                  </Button>

                  {/* Kebab menu */}
                  <span className="relative shrink-0">
                    <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setMenuOpenId(menuOpenId === p.id ? null : p.id)} aria-label="Thêm hành động">
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                    {menuOpenId === p.id && (
                      <span className="absolute right-0 top-9 z-20 w-48 rounded-xl border border-border bg-card shadow-lg overflow-hidden flex flex-col py-1">
                        {p.is_configured && (
                          <button
                            onClick={() => handleTestConnection(p.id)}
                            disabled={isTesting}
                            className="px-3 py-2 text-sm text-left hover:bg-muted flex items-center gap-2"
                          >
                            <RefreshCw className={`h-3.5 w-3.5 ${isTesting ? "animate-spin" : ""}`} /> Kiểm tra kết nối
                          </button>
                        )}
                        <button onClick={() => handleSyncAllModels(p.id)} className="px-3 py-2 text-sm text-left hover:bg-muted flex items-center gap-2">
                          <RefreshCw className="h-3.5 w-3.5" /> Đồng bộ model
                        </button>
                        {p.credential && (
                          <button onClick={() => handleDelete(p.credential!.id)} className="px-3 py-2 text-sm text-left hover:bg-muted text-destructive flex items-center gap-2">
                            <Trash2 className="h-3.5 w-3.5" /> Xóa key
                          </button>
                        )}
                        {p.documentation_url && (
                          <a href={p.documentation_url} target="_blank" rel="noreferrer" className="px-3 py-2 text-sm hover:bg-muted flex items-center gap-2" onClick={() => setMenuOpenId(null)}>
                            <ExternalLink className="h-3.5 w-3.5" /> Tài liệu
                          </a>
                        )}
                      </span>
                    )}
                  </span>
                </div>

                {/* Expanded detail — chỉ dropdown gọn */}
                {isExpanded && (
                  <div className="px-3 md:px-4 pb-4 pt-0 space-y-3 border-t border-border/60 bg-muted/20">
                    <p className="text-sm text-muted-foreground pt-3 sm:hidden">{p.description}</p>
                    {p.credential && (
                      <span className="flex items-center gap-2 text-xs pt-2">
                        <span className="text-muted-foreground">Key đã lưu:</span>
                        <code className="px-2 py-1 rounded bg-background border border-border font-mono text-xs">{p.credential.masked_secret}</code>
                      </span>
                    )}
                    <label className="block space-y-1.5">
                      <span className="text-xs font-semibold text-muted-foreground flex items-center gap-1.5">
                        <Cpu className="h-3.5 w-3.5 text-primary" /> Model — chọn là áp dụng ngay ({p.models.length})
                      </span>
                      <select
                        value={isPrimary ? (routingPolicy?.default_model || p.default_model) : p.default_model}
                        onChange={(e) => handleApplyModel(p.id, e.target.value)}
                        className="w-full h-10 bg-background border border-border rounded-xl px-3 text-sm font-mono text-foreground focus:outline-none focus:border-primary"
                      >
                        {p.models.map((m) => (
                          <option key={m.id} value={m.id}>
                            {m.id}
                            {m.is_recommended ? " ★" : ""} {m.context_window ? `· ${ctxLabel(m.context_window)}` : ""}{" "}
                            {isPrimary && routingPolicy?.default_model === m.id ? "· đang dùng" : ""}
                          </option>
                        ))}
                      </select>
                    </label>
                    {health?.error_message && (
                      <span className="block p-2.5 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-xs">{health.error_message}</span>
                    )}
                    {/* Mobile actions duplicate for reachability */}
                    <span className="flex md:hidden items-center gap-2 pt-1">
                      {p.is_configured && (
                        <Button variant="outline" size="sm" onClick={() => handleTestConnection(p.id)} disabled={isTesting} className="flex-1 text-xs">
                          <RefreshCw className={`h-3.5 w-3.5 ${isTesting ? "animate-spin" : ""}`} /> Kiểm tra
                        </Button>
                      )}
                      {p.documentation_url && (
                        <a href={p.documentation_url} target="_blank" rel="noreferrer" className="flex-1">
                          <Button variant="outline" size="sm" className="w-full text-xs">
                            <ExternalLink className="h-3.5 w-3.5" /> Tài liệu
                          </Button>
                        </a>
                      )}
                    </span>
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      )}

      {/* Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={`Nhập API Key — ${selectedProvider?.display_name || ""}`}
        description="Key được mã hóa AES-256 trước khi lưu. Không hiển thị lại sau khi lưu."
      >
        <div className="space-y-4">
          <span className="block relative">
            <Input
              type={showKey ? "text" : "password"}
              label="API Key"
              placeholder={selectedProvider?.id === "gemini" ? "AIzaSy..." : selectedProvider?.id === "groq" ? "gsk_..." : "sk-or-v1-..."}
              value={apiKeyInput}
              onChange={(e) => setApiKeyInput(e.target.value)}
              helperText={
                selectedProvider?.documentation_url ? (
                  <span>
                    Lấy key tại{" "}
                    <a href={selectedProvider.documentation_url} target="_blank" rel="noreferrer" className="text-primary underline">
                      trang nhà cung cấp
                    </a>
                    .
                  </span>
                ) : (
                  "Lấy key từ trang nhà cung cấp."
                )
              }
            />
            <button
              type="button"
              onClick={() => setShowKey(!showKey)}
              className="absolute right-3 top-[30px] p-1 rounded text-muted-foreground hover:text-foreground hover:bg-muted"
              aria-label={showKey ? "Ẩn key" : "Hiện key"}
            >
              {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </span>
          <span className="flex justify-end gap-2 pt-3 border-t border-border">
            <Button variant="outline" size="sm" onClick={() => setIsModalOpen(false)} disabled={actionLoading}>
              Hủy
            </Button>
            <Button variant="akane" size="sm" onClick={handleSave} isLoading={actionLoading} disabled={!apiKeyInput.trim()}>
              <ShieldCheck className="h-4 w-4" /> Lưu an toàn
            </Button>
          </span>
        </div>
      </Modal>
    </div>
  );
}
