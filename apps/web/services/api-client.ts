import { ApiError } from "@/types/api";
import { dispatchToast } from "@/lib/toast";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

const DEFAULT_TIMEOUT_MS = 60000; // 60s default timeout

export interface RequestOptions {
  headers?: HeadersInit;
  timeoutMs?: number;
  signal?: AbortSignal;
  suppressToast?: boolean;
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

function resolveRequestOptions(options?: HeadersInit | RequestOptions): {
  headers?: HeadersInit;
  timeoutMs?: number;
  signal?: AbortSignal;
  suppressToast?: boolean;
} {
  if (!options) return {};
  if (options instanceof Headers || Array.isArray(options)) {
    return { headers: options };
  }
  if (typeof options === "object") {
    const opts = options as RequestOptions;
    return {
      headers: opts.headers,
      timeoutMs: opts.timeoutMs,
      signal: opts.signal,
      suppressToast: opts.suppressToast,
    };
  }
  return {};
}

async function handleResponse<T>(response: Response, suppressToast = false): Promise<T> {
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

    // Global toast for 5xx, 429, 503, timeout, network error unless suppressed
    if (!suppressToast && (err.status >= 500 || err.status === 429 || err.status === 503 || err.code === "TIMEOUT_ERROR" || err.code === "NETWORK_ERROR")) {
      try {
        dispatchToast(err.message, "error");
      } catch {}
    }
    throw err;
  }

  return data as T;
}

function linkAbortSignals(
  userSignal?: AbortSignal,
  timeoutMs = DEFAULT_TIMEOUT_MS
): { signal: AbortSignal; cleanup: () => void; isTimeout: () => boolean } {
  const timeoutController = new AbortController();
  let timedOut = false;

  const timeoutId = setTimeout(() => {
    timedOut = true;
    timeoutController.abort();
  }, timeoutMs);

  if (!userSignal) {
    return {
      signal: timeoutController.signal,
      cleanup: () => clearTimeout(timeoutId),
      isTimeout: () => timedOut,
    };
  }

  if (userSignal.aborted) {
    clearTimeout(timeoutId);
    return {
      signal: userSignal,
      cleanup: () => {},
      isTimeout: () => false,
    };
  }

  // Modern AbortSignal.any support
  if (typeof AbortSignal !== "undefined" && "any" in AbortSignal && typeof (AbortSignal as any).any === "function") {
    const anySignal = (AbortSignal as any).any([userSignal, timeoutController.signal]);
    return {
      signal: anySignal,
      cleanup: () => clearTimeout(timeoutId),
      isTimeout: () => timedOut,
    };
  }

  // Cross-browser fallback
  const compositeController = new AbortController();
  const onUserAbort = () => compositeController.abort();
  const onTimeoutAbort = () => {
    timedOut = true;
    compositeController.abort();
  };

  userSignal.addEventListener("abort", onUserAbort, { once: true });
  timeoutController.signal.addEventListener("abort", onTimeoutAbort, { once: true });

  return {
    signal: compositeController.signal,
    cleanup: () => {
      clearTimeout(timeoutId);
      userSignal.removeEventListener("abort", onUserAbort);
      timeoutController.signal.removeEventListener("abort", onTimeoutAbort);
    },
    isTimeout: () => timedOut,
  };
}

async function safeFetch(
  url: string,
  init?: RequestInit,
  timeoutMs = DEFAULT_TIMEOUT_MS,
  suppressToast = false
): Promise<Response> {
  const { signal, cleanup, isTimeout } = linkAbortSignals(init?.signal as AbortSignal | undefined, timeoutMs);

  try {
    const res = await fetch(url, {
      ...init,
      signal,
    });
    return res;
  } catch (err: any) {
    if (err.name === "AbortError") {
      if (isTimeout()) {
        const timeoutSec = Math.round(timeoutMs / 1000);
        const e = new ApiClientError(
          {
            code: "TIMEOUT_ERROR",
            message: `Yêu cầu đến máy chủ API đã hết thời gian chờ (timeout sau ${timeoutSec}s). Vui lòng thử lại! (Nếu đây là lần đầu nạp model Whisper hoặc tác vụ AI nặng, hệ thống có thể cần thêm thời gian).`,
          },
          504
        );
        if (!suppressToast) {
          try {
            dispatchToast(e.message, "error");
          } catch {}
        }
        throw e;
      }
      // Intentional user cancellation / component unmount: do not show toast
      throw err;
    }

    console.warn(`[apiClient] Network fetch error for ${url}:`, err);
    const e = new ApiClientError(
      {
        code: "NETWORK_ERROR",
        message:
          "Không thể kết nối đến máy chủ Backend (http://localhost:8000). Vui lòng đảm bảo Backend server đang chạy (chạy start.bat hoặc uvicorn app.main:app)!",
      },
      503
    );
    if (!suppressToast) {
      try {
        dispatchToast(e.message, "error");
      } catch {}
    }
    throw e;
  } finally {
    cleanup();
  }
}

export const apiClient = {
  async get<T>(path: string, options?: HeadersInit | RequestOptions): Promise<T> {
    const { headers, timeoutMs, signal, suppressToast } = resolveRequestOptions(options);
    const res = await safeFetch(
      `${API_BASE_URL}${path}`,
      {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          ...headers,
        },
        signal,
        cache: "no-store",
      },
      timeoutMs,
      suppressToast
    );
    return handleResponse<T>(res, suppressToast);
  },

  async post<T>(path: string, body?: unknown, options?: HeadersInit | RequestOptions): Promise<T> {
    const { headers, timeoutMs, signal, suppressToast } = resolveRequestOptions(options);
    const res = await safeFetch(
      `${API_BASE_URL}${path}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...headers,
        },
        body: body ? JSON.stringify(body) : undefined,
        signal,
      },
      timeoutMs,
      suppressToast
    );
    return handleResponse<T>(res, suppressToast);
  },

  async postMultipart<T>(path: string, formData: FormData, options?: HeadersInit | RequestOptions): Promise<T> {
    const { headers, timeoutMs, signal, suppressToast } = resolveRequestOptions(options);
    const res = await safeFetch(
      `${API_BASE_URL}${path}`,
      {
        method: "POST",
        headers: {
          ...headers,
        },
        body: formData,
        signal,
      },
      timeoutMs,
      suppressToast
    );
    return handleResponse<T>(res, suppressToast);
  },

  async patch<T>(path: string, body?: unknown, options?: HeadersInit | RequestOptions): Promise<T> {
    const { headers, timeoutMs, signal, suppressToast } = resolveRequestOptions(options);
    const res = await safeFetch(
      `${API_BASE_URL}${path}`,
      {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          ...headers,
        },
        body: body ? JSON.stringify(body) : undefined,
        signal,
      },
      timeoutMs,
      suppressToast
    );
    return handleResponse<T>(res, suppressToast);
  },

  async put<T>(path: string, body?: unknown, options?: HeadersInit | RequestOptions): Promise<T> {
    const { headers, timeoutMs, signal, suppressToast } = resolveRequestOptions(options);
    const res = await safeFetch(
      `${API_BASE_URL}${path}`,
      {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          ...headers,
        },
        body: body ? JSON.stringify(body) : undefined,
        signal,
      },
      timeoutMs,
      suppressToast
    );
    return handleResponse<T>(res, suppressToast);
  },

  async delete<T>(path: string, options?: HeadersInit | RequestOptions): Promise<T> {
    const { headers, timeoutMs, signal, suppressToast } = resolveRequestOptions(options);
    const res = await safeFetch(
      `${API_BASE_URL}${path}`,
      {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
          ...headers,
        },
        signal,
      },
      timeoutMs,
      suppressToast
    );
    return handleResponse<T>(res, suppressToast);
  },
};

