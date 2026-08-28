export type ModelCapability =
  | "text"
  | "streaming"
  | "vision"
  | "audio"
  | "reasoning"
  | "structured_output";

export interface ModelMetadata {
  id: string;
  provider_id: string;
  display_name: string;
  context_window: number;
  capabilities: ModelCapability[];
  is_recommended: boolean;
  is_enabled: boolean;
}

export interface CredentialRead {
  id: string;
  user_id: string;
  provider: string;
  masked_secret: string;
  is_enabled: boolean;
  is_configured: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProviderDetail {
  id: string;
  display_name: string;
  description: string;
  default_model: string;
  models: ModelMetadata[];
  is_configured: boolean;
  requires_api_key: boolean;
  documentation_url: string;
  credential?: CredentialRead | null;
}

export interface CredentialCreateInput {
  provider: string;
  api_key: string;
  is_enabled?: boolean;
}

export interface CredentialUpdateInput {
  api_key?: string;
  is_enabled?: boolean;
}
