import { useCallback, useRef, useState } from "react";
import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";
import {
  FileText,
  Trash2,
  RotateCw,
  UploadCloud,
  AlertCircle,
  Sparkles,
  HelpCircle,
  ScanText,
} from "lucide-react";
import { listDocuments, uploadDocument, deleteDocument, retryDocument } from "../api/documents";
import { summarizeDocument, quizDocument } from "../api/aiFeatures";
import { StatusBadge } from "../components/StatusBadge";
import { Button } from "../components/Button";
import { Modal } from "../components/Modal";
import { SummaryPanel } from "../components/SummaryPanel";
import { QuizPanel } from "../components/QuizPanel";
import { extractErrorMessage } from "../api/client";
import type { DocumentRecord, QuizResponse, SummaryResponse } from "../types/api";

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

const ACCEPTED = [".pdf", ".docx", ".txt", ".md"];

export function DocumentsPage() {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const [activeModal, setActiveModal] = useState<{ type: "summary" | "quiz"; documentName: string } | null>(null);
  const [summaryResult, setSummaryResult] = useState<SummaryResponse | null>(null);
  const [quizResult, setQuizResult] = useState<QuizResponse | null>(null);
  const [featureError, setFeatureError] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["documents"],
    queryFn: listDocuments,
    // Poll while anything is still pending/processing so status updates live.
    refetchInterval: (query) => {
      const docs = query.state.data?.documents ?? [];
      const hasActive = docs.some((d) => d.status === "pending" || d.status === "processing");
      return hasActive ? 2000 : false;
    },
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadDocument(file),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["documents"] }),
    onError: (err) => setUploadError(extractErrorMessage(err, "Upload failed.")),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["documents"] }),
  });

  const retryMutation = useMutation({
    mutationFn: retryDocument,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["documents"] }),
  });

  const summarizeMutation = useMutation({
    mutationFn: summarizeDocument,
    onSuccess: (result) => {
      setSummaryResult(result);
      setFeatureError(null);
    },
    onError: (err) => setFeatureError(extractErrorMessage(err, "Couldn't generate a summary.")),
  });

  const quizMutation = useMutation({
    mutationFn: (documentId: string) => quizDocument(documentId, 5),
    onSuccess: (result) => {
      setQuizResult(result);
      setFeatureError(null);
    },
    onError: (err) => setFeatureError(extractErrorMessage(err, "Couldn't generate a quiz.")),
  });

  const handleFiles = useCallback(
    (files: FileList | null) => {
      if (!files) return;
      setUploadError(null);
      Array.from(files).forEach((file) => uploadMutation.mutate(file));
    },
    [uploadMutation]
  );

  const openSummary = (doc: DocumentRecord) => {
    setActiveModal({ type: "summary", documentName: doc.original_filename });
    setSummaryResult(null);
    setFeatureError(null);
    summarizeMutation.mutate(doc.id);
  };

  const openQuiz = (doc: DocumentRecord) => {
    setActiveModal({ type: "quiz", documentName: doc.original_filename });
    setQuizResult(null);
    setFeatureError(null);
    quizMutation.mutate(doc.id);
  };

  const closeModal = () => {
    setActiveModal(null);
    setSummaryResult(null);
    setQuizResult(null);
    setFeatureError(null);
  };

  const documents = data?.documents ?? [];
  const isFeatureLoading = summarizeMutation.isPending || quizMutation.isPending;

  return (
    <div className="mx-auto max-w-4xl px-8 py-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-paper-100">Documents</h1>
          <p className="text-sm text-paper-300">Upload files to make them searchable and answerable in chat.</p>
        </div>
        <Button onClick={() => fileInputRef.current?.click()}>
          <UploadCloud size={16} />
          Upload
        </Button>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={ACCEPTED.join(",")}
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
      </div>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragging(false);
          handleFiles(e.dataTransfer.files);
        }}
        className={`mb-6 flex flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed px-6 py-10 text-center transition-colors ${
          isDragging ? "border-rose-500 bg-rose-500/5" : "border-ink-600 bg-ink-800/30"
        }`}
      >
        <UploadCloud size={22} className="text-paper-300" />
        <p className="text-sm text-paper-200">Drag files here, or click Upload above</p>
        <p className="font-mono text-xs text-paper-300">{ACCEPTED.join(" · ")} · scanned PDFs are OCR'd automatically</p>
      </div>

      {uploadError && (
        <div className="mb-4 flex items-center gap-2 rounded-lg bg-crimson-500/10 px-3.5 py-2.5 text-sm text-crimson-400">
          <AlertCircle size={15} />
          {uploadError}
        </div>
      )}

      {isLoading ? (
        <p className="text-sm text-paper-300">Loading documents…</p>
      ) : documents.length === 0 ? (
        <div className="rounded-xl border border-ink-700 bg-ink-800/30 px-6 py-12 text-center">
          <FileText size={24} className="mx-auto mb-3 text-paper-300" />
          <p className="text-sm text-paper-200">No documents yet</p>
          <p className="text-sm text-paper-300">Upload your first file to start asking questions about it.</p>
        </div>
      ) : (
        <div className="flex flex-col gap-2">
          {documents.map((doc: DocumentRecord) => (
            <div
              key={doc.id}
              className="flex items-center gap-4 rounded-lg border border-ink-700 bg-ink-800/40 px-4 py-3"
            >
              <FileText size={18} className="flex-shrink-0 text-paper-300" />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-paper-100">{doc.original_filename}</p>
                <p className="font-mono text-xs text-paper-300">
                  {formatBytes(doc.file_size_bytes)}
                  {doc.chunk_count > 0 && ` · ${doc.chunk_count} chunks`}
                  {doc.page_count > 0 && ` · ${doc.page_count} pages`}
                </p>
                {doc.status === "failed" && doc.error_message && (
                  <p className="mt-1 text-xs text-crimson-400">{doc.error_message}</p>
                )}
              </div>

              {doc.ocr_page_count > 0 && (
                <span
                  className="flex items-center gap-1 rounded-full bg-amber-500/15 px-2 py-1 font-mono text-[11px] text-amber-400"
                  title={`${doc.ocr_page_count} page(s) were scanned images, read via OCR`}
                >
                  <ScanText size={11} />
                  OCR ×{doc.ocr_page_count}
                </span>
              )}

              <StatusBadge status={doc.status} />

              {doc.status === "indexed" && (
                <>
                  <button
                    onClick={() => openSummary(doc)}
                    className="rounded-md p-1.5 text-paper-300 hover:bg-ink-700 hover:text-rose-400"
                    title="Summarize"
                  >
                    <Sparkles size={15} />
                  </button>
                  <button
                    onClick={() => openQuiz(doc)}
                    className="rounded-md p-1.5 text-paper-300 hover:bg-ink-700 hover:text-rose-400"
                    title="Generate quiz"
                  >
                    <HelpCircle size={15} />
                  </button>
                </>
              )}

              {doc.status === "failed" && (
                <button
                  onClick={() => retryMutation.mutate(doc.id)}
                  className="rounded-md p-1.5 text-paper-300 hover:bg-ink-700 hover:text-paper-100"
                  title="Retry processing"
                >
                  <RotateCw size={15} />
                </button>
              )}
              <button
                onClick={() => deleteMutation.mutate(doc.id)}
                className="rounded-md p-1.5 text-paper-300 hover:bg-crimson-500/10 hover:text-crimson-400"
                title="Delete document"
              >
                <Trash2 size={15} />
              </button>
            </div>
          ))}
        </div>
      )}

      {activeModal && (
        <Modal
          title={activeModal.type === "summary" ? `Summary — ${activeModal.documentName}` : `Quiz — ${activeModal.documentName}`}
          onClose={closeModal}
        >
          {isFeatureLoading && (
            <div className="flex items-center justify-center py-10">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-rose-500 border-t-transparent" />
            </div>
          )}
          {featureError && (
            <p className="rounded-lg bg-crimson-500/10 px-3.5 py-2.5 text-sm text-crimson-400">{featureError}</p>
          )}
          {!isFeatureLoading && !featureError && activeModal.type === "summary" && summaryResult && (
            <SummaryPanel summary={summaryResult} />
          )}
          {!isFeatureLoading && !featureError && activeModal.type === "quiz" && quizResult && (
            <QuizPanel quiz={quizResult} />
          )}
        </Modal>
      )}
    </div>
  );
}
