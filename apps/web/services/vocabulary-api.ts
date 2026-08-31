import { apiClient } from "./api-client";
import {
  SaveVocabularyNotebookRequest,
  SaveVocabularyNotebookResponse,
  VocabularyLookupRequest,
  VocabularyLookupResponse,
} from "@/types/vocabulary-lookup";

export const vocabularyApi = {
  lookupAI: async (payload: VocabularyLookupRequest): Promise<VocabularyLookupResponse> => {
    try {
      // Primary: FastAPI backend /api/v1/vocabulary/ai-lookup
      return await apiClient.post<VocabularyLookupResponse>("/vocabulary/ai-lookup", payload);
    } catch (err) {
      // Fallback: Next.js API route /api/vocabulary/ai-lookup
      const res = await fetch("/api/vocabulary/ai-lookup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        throw err;
      }
      return await res.json();
    }
  },

  saveToNotebook: async (
    payload: SaveVocabularyNotebookRequest
  ): Promise<SaveVocabularyNotebookResponse> => {
    try {
      return await apiClient.post<SaveVocabularyNotebookResponse>(
        "/vocabulary/save-notebook",
        payload
      );
    } catch (err) {
      const res = await fetch("/api/vocabulary/save-notebook", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        throw err;
      }
      return await res.json();
    }
  },
};
