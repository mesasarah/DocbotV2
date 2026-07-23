export interface User {
  id: string;
  email: string;
  full_name: string;
  role: "user" | "admin";
  is_active: boolean;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export type DocumentStatus = "pending" | "processing" | "indexed" | "failed";

export interface DocumentRecord {
  id: string;
  filename: string;
  original_filename: string;
  file_type: string;
  file_size_bytes: number;
  status: DocumentStatus;
  page_count: number;
  chunk_count: number;
  ocr_page_count: number;
  error_message: string;
  created_at: string;
  indexed_at: string | null;
}

export interface DocumentListResponse {
  total: number;
  documents: DocumentRecord[];
}

export interface SourceSnippet {
  document_id: string;
  filename: string;
  page: number | null;
  snippet: string;
  score: number;
}

export interface ChatQueryResponse {
  session_id: string;
  answer: string;
  sources: SourceSnippet[];
  confidence: number;
}

export interface ChatMessageRecord {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface ChatSessionRecord {
  id: string;
  title: string;
  created_at: string;
}

export interface ChatHistoryResponse {
  session: ChatSessionRecord;
  messages: ChatMessageRecord[];
}

export interface ApiErrorBody {
  detail: string;
}

export interface DailyCount {
  date: string;
  count: number;
}

export interface AnalyticsSummary {
  total_documents: number;
  indexed_documents: number;
  processing_documents: number;
  failed_documents: number;
  total_chunks: number;
  total_ocr_pages: number;
  total_queries: number;
  total_entities: number;
  uploads_by_day: DailyCount[];
  queries_by_day: DailyCount[];
  documents_by_type: Record<string, number>;
}

export type EntityType = "PERSON" | "ORGANIZATION" | "LOCATION" | "TECHNOLOGY" | "DATE" | "OTHER";

export interface GraphNode {
  id: string;
  name: string;
  type: EntityType;
  document_count: number;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  label: string;
  document_id: string;
}

export interface GraphResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface ExtractEntitiesResponse {
  document_id: string;
  entities_found: number;
  relations_found: number;
}

export interface SummaryResponse {
  document_id: string;
  executive_summary: string;
  bullet_points: string[];
  key_insights: string[];
}

export interface QuizQuestion {
  question: string;
  options: string[];
  correct_index: number;
  explanation: string;
}

export interface QuizResponse {
  document_id: string;
  questions: QuizQuestion[];
}
