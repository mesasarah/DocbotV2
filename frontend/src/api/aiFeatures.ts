import { apiClient } from "./client";
import type { QuizResponse, SummaryResponse } from "../types/api";

export async function summarizeDocument(documentId: string): Promise<SummaryResponse> {
  const { data } = await apiClient.post<SummaryResponse>(`/api/v1/documents/${documentId}/summarize`);
  return data;
}

export async function quizDocument(documentId: string, numQuestions = 5): Promise<QuizResponse> {
  const { data } = await apiClient.post<QuizResponse>(
    `/api/v1/documents/${documentId}/quiz`,
    null,
    { params: { num_questions: numQuestions } }
  );
  return data;
}
