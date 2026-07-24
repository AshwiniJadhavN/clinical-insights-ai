export type HealthResponse = {
  status?: string;
  embedder?: { status?: string };
  vector_store?: { status?: string };
  database?: { status?: string };
};

export type DocumentSummary = {
  id?: string;
  document_id?: string;
  filename?: string;
  original_filename?: string;
  chunk_count?: number;
  status?: string;
  created_at?: string;
};

export type QueryResponse = {
  query_id?: string;
  request_id?: string;
  answer: string;
  retrieved_chunk?: string | null;
  confidence_score: number;
  confidence_level?: string;
  evidence_status: string;
  retrieval_count: number;
  model_used: string;
  safety_decision?: string;
  review_required?: boolean;
  created_at?: string;
  correlation_id?: string | null;
  disclaimer?: string;
  citations: Array<{
    doc_id: string;
    original_filename?: string;
    similarity_score: number;
    excerpt?: string;
  }>;
};

export type UploadResponse = {
  message: string;
  document: DocumentSummary;
};

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const isFormData = init?.body instanceof FormData;
  const response = await fetch(`${API_BASE}${path}`, {
    headers: isFormData ? init?.headers : { "Content-Type": "application/json", ...init?.headers },
    ...init
  });

  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail ?? `Request failed with ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export async function getHealth() {
  return request<HealthResponse>("/health");
}

export async function getDocuments() {
  const payload = await request<{ documents?: DocumentSummary[] } | DocumentSummary[]>("/documents/");
  return Array.isArray(payload) ? payload : payload.documents ?? [];
}

export async function uploadDocument(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  return request<UploadResponse>("/documents/upload", {
    method: "POST",
    body: formData
  });
}

export async function deleteDocument(documentId: string) {
  await request<void>(`/documents/${documentId}`, {
    method: "DELETE"
  });
}

export async function askQuestion(question: string, topK = 5) {
  return request<QueryResponse>("/query", {
    method: "POST",
    body: JSON.stringify({ question, top_k: topK })
  });
}
