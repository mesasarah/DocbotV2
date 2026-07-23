import { apiClient } from "./client";
import type { DocumentListResponse, DocumentRecord } from "../types/api";

export async function listDocuments(): Promise<DocumentListResponse> {
  const { data } = await apiClient.get<DocumentListResponse>("/api/v1/documents");
  return data;
}

export async function getDocument(id: string): Promise<DocumentRecord> {
  const { data } = await apiClient.get<DocumentRecord>(`/api/v1/documents/${id}`);
  return data;
}

export async function uploadDocument(file: File, onProgress?: (pct: number) => void): Promise<DocumentRecord> {
  const formData = new FormData();
  formData.append("file", file);

  const { data } = await apiClient.post<DocumentRecord>("/api/v1/documents/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (evt) => {
      if (onProgress && evt.total) {
        onProgress(Math.round((evt.loaded / evt.total) * 100));
      }
    },
  });
  return data;
}

export async function retryDocument(id: string): Promise<DocumentRecord> {
  const { data } = await apiClient.post<DocumentRecord>(`/api/v1/documents/${id}/retry`);
  return data;
}

export async function deleteDocument(id: string): Promise<void> {
  await apiClient.delete(`/api/v1/documents/${id}`);
}
