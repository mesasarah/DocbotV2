import { apiClient } from "./client";
import type { ExtractEntitiesResponse, GraphResponse } from "../types/api";

export async function getKnowledgeGraph(documentId?: string): Promise<GraphResponse> {
  const { data } = await apiClient.get<GraphResponse>("/api/v1/knowledge-graph", {
    params: documentId ? { document_id: documentId } : undefined,
  });
  return data;
}

export async function extractEntities(documentId: string): Promise<ExtractEntitiesResponse> {
  const { data } = await apiClient.post<ExtractEntitiesResponse>(
    `/api/v1/knowledge-graph/documents/${documentId}/extract`
  );
  return data;
}
