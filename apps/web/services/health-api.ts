import { apiClient } from "./api-client";

export interface HealthStatus {
  status: string;
  app_name: string;
  environment: string;
  version: string;
}

export interface ComponentHealth {
  status: string;
  component: string;
  connected: boolean;
  error?: string;
  message?: string;
}

export const healthApi = {
  getHealth: () => apiClient.get<HealthStatus>("/health"),
  getDbHealth: () => apiClient.get<ComponentHealth>("/health/db"),
  getRedisHealth: () => apiClient.get<ComponentHealth>("/health/redis"),
};
