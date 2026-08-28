import { UserSettings, UserSettingsUpdate } from "@/types/settings";
import { apiClient } from "./api-client";

export const settingsApi = {
  getSettings: () => apiClient.get<UserSettings>("/settings"),
  updateSettings: (payload: UserSettingsUpdate) =>
    apiClient.patch<UserSettings>("/settings", payload),
};
