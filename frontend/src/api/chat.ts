import { apiClient } from "./client";
import type { ChatHistoryResponse, ChatQueryResponse, ChatSessionRecord } from "../types/api";

export async function sendChatQuery(
  message: string,
  session_id?: string,
  document_ids?: string[]
): Promise<ChatQueryResponse> {
  const { data } = await apiClient.post<ChatQueryResponse>("/api/v1/chat/query", {
    message,
    session_id: session_id ?? null,
    document_ids: document_ids ?? null,
  });
  return data;
}

export async function listChatSessions(): Promise<ChatSessionRecord[]> {
  const { data } = await apiClient.get<ChatSessionRecord[]>("/api/v1/chat/sessions");
  return data;
}

export async function getChatHistory(sessionId: string): Promise<ChatHistoryResponse> {
  const { data } = await apiClient.get<ChatHistoryResponse>(`/api/v1/chat/sessions/${sessionId}`);
  return data;
}

export async function deleteChatSession(sessionId: string): Promise<void> {
  await apiClient.delete(`/api/v1/chat/sessions/${sessionId}`);
}
