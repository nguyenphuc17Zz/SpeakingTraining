import {
  CredentialCreateInput,
  CredentialRead,
  CredentialUpdateInput,
  ProviderDetail,
} from "@/types/provider";
import { apiClient } from "./api-client";

export const providersApi = {
  listProviders: () => apiClient.get<ProviderDetail[]>("/providers"),
  createCredential: (payload: CredentialCreateInput) =>
    apiClient.post<CredentialRead>("/providers/credentials", payload),
  updateCredential: (credentialId: string, payload: CredentialUpdateInput) =>
    apiClient.patch<CredentialRead>(
      `/providers/credentials/${credentialId}`,
      payload
    ),
  deleteCredential: (credentialId: string) =>
    apiClient.delete<void>(`/providers/credentials/${credentialId}`),
};
