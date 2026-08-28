import {
  AIRoutingPolicyRead,
  AIRoutingPolicyUpdate,
  AIResponseRead,
  AIStreamEvent,
  AIUsageSummaryRead,
  GenerateRequestInput,
  ProviderHealth,
} from "@/types/ai";
import { ModelMetadata, ProviderDetail } from "@/types/provider";
import { apiClient } from "./api-client";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const aiApi = {
  listProviders: () => apiClient.get<ProviderDetail[]>("/ai/providers"),

  listModels: (provider?: string, refresh: boolean = false) => {
    const params = new URLSearchParams();
    if (provider) params.append("provider", provider);
    if (refresh) params.append("refresh", "true");
    const q = params.toString() ? `?${params.toString()}` : "";
    return apiClient.get<ModelMetadata[]>(`/ai/models${q}`);
  },

  refreshModels: (provider?: string) => {
    const q = provider ? `?provider=${encodeURIComponent(provider)}` : "";
    return apiClient.post<ModelMetadata[]>(`/ai/models/refresh${q}`);
  },

  getHealth: () => apiClient.get<ProviderHealth[]>("/ai/health"),

  testConnection: (provider: string) =>
    apiClient.post<ProviderHealth>("/ai/test-connection", { provider }),

  generate: (payload: GenerateRequestInput) =>
    apiClient.post<AIResponseRead>("/ai/generate", payload),

  getUsage: (params?: { provider?: string; task?: string; limit?: number; offset?: number }) => {
    const sp = new URLSearchParams();
    if (params?.provider) sp.append("provider", params.provider);
    if (params?.task) sp.append("task", params.task);
    if (params?.limit !== undefined) sp.append("limit", params.limit.toString());
    if (params?.offset !== undefined) sp.append("offset", params.offset.toString());
    const query = sp.toString() ? `?${sp.toString()}` : "";
    return apiClient.get<AIUsageSummaryRead>(`/ai/usage${query}`);
  },

  getRoutingPolicy: () => apiClient.get<AIRoutingPolicyRead>("/ai/routing"),

  updateRoutingPolicy: (payload: AIRoutingPolicyUpdate) =>
    apiClient.put<AIRoutingPolicyRead>("/ai/routing", payload),


  /**
   * SSE Stream generation reader
   */
  streamGenerate: async (
    payload: GenerateRequestInput,
    callbacks: {
      onStarted?: (event: AIStreamEvent) => void;
      onTextDelta?: (delta: string) => void;
      onUsage?: (usage: any) => void;
      onCompleted?: (event: AIStreamEvent) => void;
      onError?: (error: string) => void;
    },
    signal?: AbortSignal
  ) => {
    const response = await fetch(`${API_BASE}/ai/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
      signal,
    });

    if (!response.ok) {
      const errText = await response.text();
      let msg = `HTTP error ${response.status}`;
      try {
        const parsed = JSON.parse(errText);
        msg = parsed.detail?.message || parsed.detail || msg;
      } catch {}
      callbacks.onError?.(msg);
      return;
    }

    const reader = response.body?.getReader();
    if (!reader) {
      callbacks.onError?.("ReadableStream not supported by browser/runtime.");
      return;
    }

    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed || !trimmed.startsWith("data: ")) continue;

          const dataStr = trimmed.slice(6).trim();
          if (dataStr === "[DONE]") {
            continue;
          }

          try {
            const event: AIStreamEvent = JSON.parse(dataStr);
            if (event.type === "started") {
              callbacks.onStarted?.(event);
            } else if (event.type === "text_delta" && event.text_delta) {
              callbacks.onTextDelta?.(event.text_delta);
            } else if (event.type === "usage" && event.usage) {
              callbacks.onUsage?.(event.usage);
            } else if (event.type === "completed") {
              callbacks.onCompleted?.(event);
            } else if (event.type === "error" && event.error) {
              callbacks.onError?.(event.error);
            }
          } catch (parseErr) {
            console.error("Failed to parse SSE chunk:", parseErr);
          }
        }
      }
    } catch (err: any) {
      if (err.name === "AbortError") {
        return;
      }
      callbacks.onError?.(err.message || "Streaming interrupted");
    } finally {
      reader.releaseLock();
    }
  },
};
