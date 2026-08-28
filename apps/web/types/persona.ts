export interface Persona {
  id: string;
  name: string;
  description: string;
  role: string;
  personality: string;
  speaking_style: string;
  difficulty: "N5" | "N4" | "N3" | "N2" | "N1" | string;
  is_system: boolean;
  avatar_url?: string | null;
  system_prompt?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PersonaCreateInput {
  name: string;
  description: string;
  role: string;
  personality: string;
  speaking_style: string;
  difficulty?: string;
  avatar_url?: string;
  system_prompt?: string;
}

export interface PersonaUpdateInput {
  name?: string;
  description?: string;
  role?: string;
  personality?: string;
  speaking_style?: string;
  difficulty?: string;
  avatar_url?: string;
  system_prompt?: string;
}

export interface PersonaGenerateInput {
  theme?: string;
  difficulty?: string;
  language?: string;
}

export interface PersonaGenerateResponse extends PersonaCreateInput {
  reasoning?: string | null;
}
