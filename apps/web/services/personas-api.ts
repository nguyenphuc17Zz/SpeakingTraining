import {
  Persona,
  PersonaCreateInput,
  PersonaGenerateInput,
  PersonaGenerateResponse,
  PersonaUpdateInput,
} from "@/types/persona";
import { apiClient } from "./api-client";

export const personasApi = {
  listPersonas: () => apiClient.get<Persona[]>("/personas"),
  getPersona: (id: string) => apiClient.get<Persona>(`/personas/${id}`),
  createPersona: (payload: PersonaCreateInput) =>
    apiClient.post<Persona>("/personas", payload),
  updatePersona: (id: string, payload: PersonaUpdateInput) =>
    apiClient.patch<Persona>(`/personas/${id}`, payload),
  deletePersona: (id: string) => apiClient.delete<void>(`/personas/${id}`),
  generateRandomPersona: (payload: PersonaGenerateInput = {}) =>
    apiClient.post<PersonaGenerateResponse>("/personas/generate", payload),
  restoreDefaults: () => apiClient.post<Persona[]>("/personas/restore-defaults"),
};
