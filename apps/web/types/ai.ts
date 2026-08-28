export type AITask =
  | "conversation"
  | "deep_analysis"
  | "grammar_correction"
  | "translation"
  | "summarization"
  | "curriculum"
  | "memory"
  | "pronunciation_analysis"
  | "video_analysis"
  | "playground"
  | "general";

export type MessageRole = "system" | "user" | "assistant" | "tool";

export interface AIMessage {
  role: MessageRole;
  content: string;
  name?: string;
  metadata?: Record<string, any>;
}

export interface ResponseFormat {
  type: "text" | "json_object" | "json_schema";
  json_schema?: Record<string, any>;
}

export interface GenerateRequestInput {
  messages: AIMessage[];
  task?: AITask;
  model?: string;
  provider?: string;
  temperature?: number;
  max_output_tokens?: number;
  system_instruction?: string;
  response_format?: ResponseFormat;
  stream?: boolean;
  metadata?: Record<string, any>;
}

export interface AIUsage {
  input_tokens?: number | null;
  output_tokens?: number | null;
  total_tokens?: number | null;
  cached_tokens?: number | null;
  reasoning_tokens?: number | null;
  estimated_cost_usd?: number | null;
}

export interface AIResponseRead {
  text: string;
  model: string;
  provider: string;
  usage: AIUsage;
  finish_reason?: string;
  latency_ms: number;
  fallback_occurred: boolean;
  attempt_history: Array<Record<string, any>>;
  request_id?: string;
  metadata?: Record<string, any>;
}

export type AIStreamEventType =
  | "started"
  | "text_delta"
  | "usage"
  | "completed"
  | "error";

export interface AIStreamEvent {
  type: AIStreamEventType;
  text_delta?: string;
  usage?: AIUsage;
  provider?: string;
  model?: string;
  finish_reason?: string;
  error?: string;
  fallback_occurred?: boolean;
  latency_ms?: number;
  request_id?: string;
  metadata?: Record<string, any>;
}

export type ProviderHealthStatus =
  | "healthy"
  | "degraded"
  | "unavailable"
  | "not_configured";

export interface ProviderHealth {
  provider_id: string;
  status: ProviderHealthStatus;
  is_configured: boolean;
  latency_ms?: number | null;
  last_checked_at?: string | null;
  error_message?: string | null;
  metadata?: Record<string, any>;
}

export interface AIRoutingPolicyRead {
  routing_mode: "auto" | "manual";
  preferred_provider: string;
  default_model: string;
  fallback_enabled: boolean;
  fallback_priority: string[];
}

export interface AIRoutingPolicyUpdate {
  routing_mode?: "auto" | "manual";
  preferred_provider?: string;
  default_model?: string;
  fallback_enabled?: boolean;
  fallback_priority?: string[];
}

export interface AIUsageRecordRead {
  id: string;
  user_id: string;
  request_id: string;
  provider: string;
  model: string;
  task: string;
  input_tokens?: number | null;
  output_tokens?: number | null;
  total_tokens?: number | null;
  latency_ms: number;
  success: boolean;
  error_type?: string | null;
  fallback_occurred: boolean;
  attempts_count: number;
  created_at: string;
}

export interface AIUsageSummaryRead {
  total_requests: int_num;
  successful_requests: int_num;
  failed_requests: int_num;
  total_input_tokens: int_num;
  total_output_tokens: int_num;
  total_tokens: int_num;
  avg_latency_ms: number;
  recent_records: AIUsageRecordRead[];
}

type int_num = number;
