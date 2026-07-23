import { apiClient } from "./client";
import type { AnalyticsSummary } from "../types/api";

export async function getAnalyticsSummary(): Promise<AnalyticsSummary> {
  const { data } = await apiClient.get<AnalyticsSummary>("/api/v1/analytics/summary");
  return data;
}
