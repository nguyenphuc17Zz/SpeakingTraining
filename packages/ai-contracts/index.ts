/**
 * Shared AI & Speech Provider Contracts
 */

export type AIProviderId = 'gemini' | 'groq' | 'openrouter' | 'custom';

export type ModelCapability =
  | 'text'
  | 'streaming'
  | 'vision'
  | 'audio'
  | 'reasoning'
  | 'structured_output';

export type AITask =
  | 'conversation'
  | 'deep_analysis'
  | 'grammar_correction'
  | 'translation'
  | 'summarization'
  | 'curriculum'
  | 'memory'
  | 'pronunciation_analysis'
  | 'video_analysis'
  | 'playground'
  | 'general';

export type MessageRole = 'system' | 'user' | 'assistant' | 'tool';

export interface AIMessage {
  role: MessageRole;
  content: string;
  name?: string;
  audio_bytes?: string;
  image_url?: string;
  metadata?: Record<string, any>;
}

export interface ResponseFormat {
  type: 'text' | 'json_object' | 'json_schema';
  json_schema?: Record<string, any>;
}

export interface AIRequest {
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

export interface AIResponse {
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
  | 'started'
  | 'text_delta'
  | 'usage'
  | 'completed'
  | 'error';

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
  | 'healthy'
  | 'degraded'
  | 'unavailable'
  | 'not_configured';

export interface ProviderHealth {
  provider_id: string;
  status: ProviderHealthStatus;
  is_configured: boolean;
  latency_ms?: number | null;
  last_checked_at?: string | null;
  error_message?: string | null;
  metadata?: Record<string, any>;
}

export interface ModelMetadata {
  id: string;
  provider_id: string;
  display_name: string;
  context_window: number;
  capabilities: ModelCapability[];
  is_recommended?: boolean;
  is_enabled: boolean;
}

export interface ProviderMetadata {
  id: string;
  display_name: string;
  description: string;
  default_model: string;
  models: ModelMetadata[];
  is_configured: boolean;
  requires_api_key: boolean;
  documentation_url: string;
}

export interface AIRoutingPolicy {
  routing_mode: 'auto' | 'manual';
  preferred_provider: string;
  default_model: string;
  fallback_enabled: boolean;
  fallback_priority: string[];
}

export interface AIUsageRecord {
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

export type STTProviderId = 'whisper_local' | 'whisper_api' | 'gemini_audio';
export type TTSProviderId = 'voicevox' | 'gemini_tts' | 'edge_tts';

export interface STTModelMetadata {
  id: string;
  name: string;
  sizeMb?: number;
  accuracy: 'high' | 'balanced' | 'fast';
  isLocal: boolean;
}

export interface TTSVoiceMetadata {
  id: string;
  name: string;
  speaker: string;
  gender: 'female' | 'male' | 'neutral';
  previewAudioUrl?: string;
}
