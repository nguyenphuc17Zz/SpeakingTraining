import { ApiError } from "@/types/api";
import { dispatchToast } from "@/lib/toast";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

const DEFAULT_TIMEOUT_MS = 60000; // 60s default timeout

export interface RequestOptions {
  headers?: HeadersInit;
  timeoutMs?: number;
}

export class ApiClientError extends Error {
  public code: string;
  public details?: Record<string, unknown>;
  public status: number;

  constructor(error: ApiError, status: number) {
    super(error.message || "An unexpected error occurred");
    this.name = "ApiClientError";
    this.code = error.code || "UNKNOWN_ERROR";
    this.details = error.details as Record<string, unknown>;
    this.status = status;
  }
}

function resolveRequestOptions(options?: HeadersInit | RequestOptions): { headers?: HeadersInit; timeoutMs?: number } {
  if (!options) return {};
  if (options instanceof Headers || Array.isArray(options)) {
    return { headers: options };
  }
  if (typeof options === "object") {
    if ("timeoutMs" in options || "headers" in options) {
      return {
        headers: (options as RequestOptions).headers,
        timeoutMs: (options as RequestOptions).timeoutMs,
      };
    }
    return { headers: options as HeadersInit };
  }
  return {};
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (response.status === 204) {
    return {} as T;
  }

  let data: any;
  try {
    data = await response.json();
  } catch {
    if (!response.ok) {
      throw new ApiClientError(
        {
          code: `HTTP_${response.status}`,
          message: response.statusText || "Request failed",
        },
        response.status
      );
    }
    return {} as T;
  }

  if (!response.ok) {
    let err: ApiClientError;
    if (data && data.error) {
      err = new ApiClientError(data.error, response.status);
    } else {
      err = new ApiClientError(
        {
          code: `HTTP_${response.status}`,
          message: data.message || data.detail || "Request failed",
        },
        response.status
      );
    }
    // Global toast for 5xx, 429, 503, timeout — per user choice Global api-client
    if (err.status >= 500 || err.status === 429 || err.status === 503 || err.code === "TIMEOUT_ERROR" || err.code === "NETWORK_ERROR") {
      // Avoid toast for expected 404 on learning items (not monologue)
      if (!(err.status === 404 && typeof window !== "undefined" && window.location.pathname.includes("/learning"))) {
        try { dispatchToast(err.message, "error"); } catch {}
      }
    }
    throw err;
  }

  return data as T;
}

async function safeFetch(url: string, init?: RequestInit, timeoutMs = DEFAULT_TIMEOUT_MS): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(url, {
      ...init,
      signal: init?.signal || controller.signal,
    });
    return res;
  } catch (err: any) {
    if (err.name === "AbortError") {
      const timeoutSec = Math.round(timeoutMs / 1000);
      const e = new ApiClientError(
        {
          code: "TIMEOUT_ERROR",
          message: `Yêu cầu đến máy chủ API đã hết thời gian chờ (timeout sau ${timeoutSec}s). Vui lòng thử lại! (Nếu đây là lần đầu nạp model Whisper hoặc tác vụ AI nặng, hệ thống có thể cần thêm thời gian).`,
        },
        504
      );
      try { dispatchToast(e.message, "error"); } catch {}
      throw e;
    }
    console.warn(`[apiClient] Network fetch error for ${url}:`, err);
    const e = new ApiClientError(
      {
        code: "NETWORK_ERROR",
        message: "Không thể kết nối đến máy chủ Backend (http://localhost:8000). Vui lòng đảm bảo Backend server đang chạy (chạy start.bat hoặc uvicorn app.main:app)!",
      },
      503
    );
    try { dispatchToast(e.message, "error"); } catch {}
    throw e;
  } finally {
    clearTimeout(timeoutId);
  }
}

export const apiClient = {
  async get<T>(path: string, options?: HeadersInit | RequestOptions): Promise<T> {
    const { headers, timeoutMs } = resolveRequestOptions(options);
    const res = await safeFetch(
      `${API_BASE_URL}${path}`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          ...headers,
        },
        cache: "no-store",
      },
      timeoutMs
    );
    return handleResponse<T>(res);
  },

  async post<T>(path: string, body?: unknown, options?: HeadersInit | RequestOptions): Promise<T> {
    const { headers, timeoutMs } = resolveRequestOptions(options);
    const res = await safeFetch(
      `${API_BASE_URL}${path}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...headers,
        },
        body: body ? JSON.stringify(body) : undefined,
      },
      timeoutMs
    );
    return handleResponse<T>(res);
  },

  async postMultipart<T>(path: string, formData: FormData, options?: HeadersInit | RequestOptions): Promise<T> {
    const { headers, timeoutMs } = resolveRequestOptions(options);
    const res = await safeFetch(
      `${API_BASE_URL}${path}`,
      {
        method: "POST",
        headers: {
          ...headers,
        },
        body: formData,
      },
      timeoutMs
    );
    return handleResponse<T>(res);
  },

  async patch<T>(path: string, body?: unknown, options?: HeadersInit | RequestOptions): Promise<T> {
    const { headers, timeoutMs } = resolveRequestOptions(options);
    const res = await safeFetch(
      `${API_BASE_URL}${path}`,
      {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          ...headers,
        },
        body: body ? JSON.stringify(body) : undefined,
      },
      timeoutMs
    );
    return handleResponse<T>(res);
  },

  async put<T>(path: string, body?: unknown, options?: HeadersInit | RequestOptions): Promise<T> {
    const { headers, timeoutMs } = resolveRequestOptions(options);
    const res = await safeFetch(
      `${API_BASE_URL}${path}`,
      {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          ...headers,
        },
        body: body ? JSON.stringify(body) : undefined,
      },
      timeoutMs
    );
    return handleResponse<T>(res);
  },

  async delete<T>(path: string, options?: HeadersInit | RequestOptions): Promise<T> {
    const { headers, timeoutMs } = resolveRequestOptions(options);
    const res = await safeFetch(
      `${API_BASE_URL}${path}`,
      {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
          ...headers,
        },
      },
      timeoutMs
    );
    return handleResponse<T>(res);
  },
};

