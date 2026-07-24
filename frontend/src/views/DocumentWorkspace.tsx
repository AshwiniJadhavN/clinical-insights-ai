import { useEffect, useRef, useState } from "react";
import { AlertCircle, ArrowRight, FileText, Search, ShieldCheck, UploadCloud, X } from "lucide-react";
import { askQuestion, deleteDocument, DocumentSummary, QueryResponse, uploadDocument } from "../lib/api";
import { percent } from "../lib/utils";
import { AiResponseCard } from "../components/AiResponseCard";
import { Badge, Button, Card, EmptyState, SectionHeader } from "../components/ui";

type QueryHistoryItem = {
  question: string;
  confidenceScore: number;
  evidenceStatus: string;
  timestamp: number;
};

export function DocumentWorkspace({
  documents,
  guidedMode,
  queryHistory,
  revealHistoryConfidence,
  onQuerySuccess,
  onDocumentsChanged,
  onClearHistory
}: {
  documents: DocumentSummary[];
  guidedMode: boolean;
  queryHistory: QueryHistoryItem[];
  revealHistoryConfidence: boolean;
  onQuerySuccess: (summary: {
    question: string;
    confidenceScore: number;
    evidenceStatus: string;
  }) => void;
  onDocumentsChanged: () => Promise<void>;
  onClearHistory: () => void;
}) {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [deletingDocumentId, setDeletingDocumentId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);
  const hasDocuments = documents.length > 0;
  const queryLocked = guidedMode && !hasDocuments;
  const questionRef = useRef<HTMLTextAreaElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    questionRef.current?.focus();
  }, []);

  function openUploadPicker() {
    setError(null);
    setUploadMessage(null);
    fileInputRef.current?.click();
  }

  async function handleFileSelection(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    setUploading(true);
    setError(null);
    setUploadMessage(null);

    try {
      const response = await uploadDocument(file);
      await onDocumentsChanged();
      setUploadMessage(`${response.document.original_filename ?? response.document.filename} uploaded with status ${response.document.status ?? "ready"}.`);
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : "Unable to upload document right now.");
    } finally {
      setUploading(false);
      event.target.value = "";
    }
  }

  async function runQuery() {
    setError(null);

    if (queryLocked) {
      setError("Upload at least one document to unlock evidence-bound querying.");
      return;
    }

    setLoading(true);
    try {
      const response = await askQuestion(question, 5);
      setResult(response);
      onQuerySuccess({
        question,
        confidenceScore: response.confidence_score,
        evidenceStatus: response.evidence_status
      });
    } catch (queryError) {
      setError(queryError instanceof Error ? queryError.message : "Unable to generate response right now.");
    } finally {
      setLoading(false);
    }
  }

  async function handleDeleteDocument(doc: DocumentSummary) {
    const docId = doc.id ?? doc.document_id;
    if (!docId) {
      setError("Unable to remove this document: missing document id.");
      return;
    }

    const docName = doc.original_filename ?? doc.filename ?? "this document";
    const confirmed = window.confirm(`Remove ${docName}?`);
    if (!confirmed) {
      return;
    }

    setError(null);
    setUploadMessage(null);
    setDeletingDocumentId(docId);

    try {
      await deleteDocument(docId);
      await onDocumentsChanged();
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Unable to remove document right now.");
    } finally {
      setDeletingDocumentId(null);
    }
  }

  return (
    <div className="space-y-6" id="document-viewer">
      <SectionHeader
        title="Clinical Insights"
        description="Upload a document, ask a question, and get a grounded answer."
      />

      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.txt,text/plain,application/pdf"
        className="hidden"
        onChange={handleFileSelection}
      />

      {guidedMode && !result && (
        <Card className="p-4">
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone={hasDocuments ? "success" : "warning"}>
              {hasDocuments ? "Ready to query" : "No document yet"}
            </Badge>
          </div>
          <p className="mt-3 text-sm text-slate-600 dark:text-slate-400">
            Add one document, then ask your question.
          </p>
          {uploadMessage && (
            <p className="mt-3 text-sm text-teal-700 dark:text-teal-300">{uploadMessage}</p>
          )}
        </Card>
      )}

      <div className="grid gap-6 xl:grid-cols-[0.72fr_1.28fr]">
        <Card className="min-h-[620px] p-5">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <h3 className="text-base font-semibold text-medical-900 dark:text-white">Uploaded documents</h3>
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Add files here before asking a question.</p>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <Badge tone="info">{documents.length} sources</Badge>
              <Button variant="secondary" size="sm" onClick={openUploadPicker} disabled={uploading}>
                <UploadCloud className="h-4 w-4" />
                {uploading ? "Uploading..." : "Upload"}
              </Button>
            </div>
          </div>
          {documents.length > 0 ? (
            <div className="mt-4 space-y-3">
              {documents.map((doc) => (
                <div
                  key={doc.id ?? doc.filename}
                  className="w-full rounded-lg border border-slate-200 p-3 text-left transition hover:bg-slate-50 dark:border-white/10 dark:hover:bg-white/5"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="grid h-9 w-9 shrink-0 place-items-center rounded-lg border border-slate-200 bg-slate-50 dark:border-white/10 dark:bg-white/5">
                      <FileText className="h-4 w-4 text-slate-500" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-sm font-semibold text-medical-900 dark:text-white" title={doc.original_filename ?? doc.filename}>
                        {doc.original_filename ?? doc.filename}
                      </div>
                      <div className="mt-1 truncate text-xs text-slate-500 dark:text-slate-400">
                        {(doc.chunk_count ?? 0) > 0 ? `Indexed · ${doc.chunk_count} passages` : "Processing…"} · {doc.status === "ready" ? "Ready" : doc.status ?? "Ready"}
                      </div>
                    </div>
                    <button
                      type="button"
                      aria-label={`Remove ${doc.original_filename ?? doc.filename ?? "document"}`}
                      title="Remove document"
                      onClick={() => handleDeleteDocument(doc)}
                      disabled={Boolean(deletingDocumentId)}
                      className="grid h-8 w-8 shrink-0 place-items-center rounded-md border border-slate-200 text-slate-500 transition hover:bg-rose-50 hover:text-rose-600 disabled:cursor-not-allowed disabled:opacity-50 dark:border-white/10 dark:text-slate-400 dark:hover:bg-rose-400/10 dark:hover:text-rose-300"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="mt-5">
              <EmptyState
                icon={UploadCloud}
                title={guidedMode ? "No document indexed yet" : "No documents indexed yet"}
                description={
                  guidedMode
                    ? "Add a clinical note or PDF, wait for indexing, then ask a grounded question."
                    : "Add a document from the backend upload endpoint to make retrieval and answer generation available."
                }
              />
            </div>
          )}
        </Card>


        <div className="space-y-4">
          <Card className="p-6">
            <label className="text-sm font-semibold text-medical-900 dark:text-white" htmlFor="clinical-question">
              Clinical question
            </label>
            <textarea
              ref={questionRef}
              id="clinical-question"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              disabled={queryLocked || loading}
              placeholder="e.g. What are the key findings in this clinical note?"
              className="mt-3 min-h-28 w-full rounded-lg border border-slate-200 bg-white p-3 text-sm text-medical-900 outline-none transition placeholder:text-slate-400 focus:ring-2 focus:ring-teal-500 dark:border-white/10 dark:bg-white/5 dark:text-white dark:placeholder:text-slate-500"
            />
            {queryLocked && (
              <div className="mt-3 flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-700 dark:border-amber-400/30 dark:bg-amber-400/10 dark:text-amber-300">
                <ShieldCheck className="h-4 w-4" />
                Add one document to enable evidence-bound querying.
              </div>
            )}
            {error && (
              <div className="mt-3 flex items-center gap-2 rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700 dark:border-rose-400/30 dark:bg-rose-400/10 dark:text-rose-300">
                <AlertCircle className="h-4 w-4" />
                {error}
              </div>
            )}
            <Button className="mt-4 w-full sm:w-auto" onClick={runQuery} disabled={loading || !question.trim()}>
              <Search className="h-4 w-4" />
              Generate insight
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Card>

          {loading && (
            <Card className="p-5">
              <div className="flex items-center gap-3">
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-teal-500 border-t-transparent" />
                <p className="text-sm text-slate-600 dark:text-slate-400">Searching evidence and generating answer…</p>
              </div>
              <div className="mt-4 space-y-2">
                <div className="h-3 w-3/4 animate-pulse rounded bg-slate-100 dark:bg-white/10" />
                <div className="h-3 w-full animate-pulse rounded bg-slate-100 dark:bg-white/10" />
                <div className="h-3 w-2/3 animate-pulse rounded bg-slate-100 dark:bg-white/10" />
              </div>
            </Card>
          )}
          {result && <AiResponseCard result={result} revealConfidence={revealHistoryConfidence} />}

          <Card className="p-5">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-medical-900 dark:text-white">Recent query history</h3>
              <Button size="sm" variant="ghost" onClick={onClearHistory} disabled={queryHistory.length === 0}>
                Clear
              </Button>
            </div>
            <div className="mt-3 space-y-2">
              {queryHistory.length === 0 && (
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Run your first query to build a persisted session trail.
                </p>
              )}
              {queryHistory.filter((entry, i, arr) =>
                arr.findIndex(e => e.question === entry.question) === i
              ).map((entry) => (
                <button
                  key={`${entry.timestamp}-${entry.question}`}
                  type="button"
                  onClick={() => setQuestion(entry.question)}
                  className="w-full rounded-lg border border-slate-200 p-3 text-left transition hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-teal-500 dark:border-white/10 dark:hover:bg-white/5"
                  title="Click to reuse this question"
                >
                  <p className="text-sm text-medical-900 dark:text-white">{entry.question}</p>
                  <div className="mt-2 flex items-center gap-2">
                    <div className="h-1.5 w-24 overflow-hidden rounded-full bg-slate-100 dark:bg-white/10">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${
                          !revealHistoryConfidence
                            ? "w-0"
                            : entry.confidenceScore >= 0.75
                            ? "bg-emerald-500"
                            : entry.confidenceScore >= 0.5
                            ? "bg-amber-400"
                            : "bg-rose-500"
                        }`}
                        style={{ width: revealHistoryConfidence ? `${Math.round(entry.confidenceScore * 100)}%` : "0%" }}
                      />
                    </div>
                    <span className="text-xs text-slate-500 dark:text-slate-400">
                      {revealHistoryConfidence ? percent(entry.confidenceScore) : "N/A"} · {entry.evidenceStatus}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
