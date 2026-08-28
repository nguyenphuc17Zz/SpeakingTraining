const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options?.headers || {}) },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || err.message || `API Error ${res.status}`);
  }
  return res.json();
}

export type CoachPersona = "tanaka" | "aoi" | "kenji";

export interface CoachChatRequest {
  message: string;
  persona?: CoachPersona;
  context_mode?: string;
  current_route?: string;
  current_exercise_id?: string;
  current_session_id?: string;
  response_mode?: string;
  action_mode?: string;
}

export interface CoachChatResponse {
  response: string;
  intent: string;
  confidence: number | string;
  evidence: any[];
  recommendations: any[];
  key_points?: string[];
  tool_calls?: any[];
  next_action?: { type: string; payload: any; label?: string } | null;
  context_hash?: string;
}

export interface DailyBriefingDTO {
  date: string;
  yesterday_summary: string;
  today_focus_title: string;
  today_focus_reason: string;
  recommendation: {
    action_type: string;
    target: string;
    reason: string;
    duration_minutes: number;
    practice_url: string;
  };
  streak_status: string;
}

export interface CoachContextDTO {
  user_id: string;
  current_route: string;
  current_mode: string;
  current_sub_mode?: string | null;
  current_exercise_id?: string | null;
  current_task?: string | null;
  bottleneck_info: string;
  available_actions: string[];
  capability_flags?: Record<string, boolean>;
  context_hash?: string;
  recent_attempts?: any[];
}

export const coachCoreApi = {
  chat: (req: CoachChatRequest): Promise<CoachChatResponse> =>
    fetchJson<CoachChatResponse>("/coach/chat", { method: "POST", body: JSON.stringify(req) }),

  getDailyBriefing: (persona: CoachPersona = "tanaka"): Promise<DailyBriefingDTO> =>
    fetchJson<DailyBriefingDTO>(`/coach/briefing?persona=${persona}`),

  getQuickActions: (route: string = "/dashboard", exerciseId?: string): Promise<{ actions: any[]; mode: string }> => {
    const q = new URLSearchParams({ route });
    if (exerciseId) q.set("exercise_id", exerciseId);
    return fetchJson<{ actions: any[]; mode: string }>(`/coach/quick-actions?${q.toString()}`).catch(() => ({
      actions: [],
      mode: "general",
    }));
  },

  getProactive: (): Promise<any[]> =>
    fetchJson<any[]>("/coach/proactive").catch(() => []),

  getContext: (route: string = "/dashboard", exerciseId?: string): Promise<CoachContextDTO> => {
    const q = new URLSearchParams({ current_route: route });
    if (exerciseId) q.set("current_exercise_id", exerciseId);
    return fetchJson<CoachContextDTO>(`/coach/context?${q.toString()}`);
  },

  chatStream: async function* (req: CoachChatRequest): AsyncGenerator<{ type: string; text?: string; data?: any; tool_calls?: any[] }, void, unknown> {
    const res = await fetch(`${API_BASE}/coach/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
    if (!res.ok || !res.body) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `Stream error ${res.status}`);
    }
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";
      for (const line of lines) {
        if (!line.trim() || !line.startsWith("data: ")) continue;
        const dataStr = line.slice(6).trim();
        if (dataStr === "[DONE]") return;
        try {
          const json = JSON.parse(dataStr);
          yield json;
        } catch {
          // ignore partial
        }
      }
    }
  },
};
