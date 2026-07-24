import { Copy, Download, ExternalLink, FileText, ShieldCheck } from "lucide-react";
import { QueryResponse } from "../lib/api";
import { percent } from "../lib/utils";
import { Badge, Button, Card } from "./ui";

export function AiResponseCard({
  result,
  revealConfidence = false
}: {
  result: QueryResponse;
  revealConfidence?: boolean;
}) {
  const needsHumanVerification = Boolean(result.review_required) || result.safety_decision === "clarify";

  async function handleCopy() {
    const citationSummary = result.citations
      .map((citation) => `${citation.original_filename ?? citation.doc_id} (${citation.similarity_score.toFixed(3)})`)
      .join("\n");

    await navigator.clipboard.writeText(
      [`Answer: ${result.answer}`, `Evidence: ${result.retrieved_chunk ?? "N/A"}`, `Sources:\n${citationSummary}`].join("\n\n")
    );
  }

  function handleExport() {
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `clinical-insight-${result.request_id ?? result.query_id ?? "response"}.json`;
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <Card className="overflow-hidden">
      <div className="border-b border-slate-200 px-5 py-4 dark:border-white/10">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-teal-600" />
              <h3 className="text-base font-semibold text-medical-900 dark:text-white">
                Response
              </h3>
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" size="sm" aria-label="Copy response" onClick={handleCopy}>
              <Copy className="h-4 w-4" />
              Copy
            </Button>
            <Button variant="secondary" size="sm" aria-label="Export response" onClick={handleExport}>
              <Download className="h-4 w-4" />
              Export
            </Button>
          </div>
        </div>
      </div>

      <div className="grid gap-5 p-5 lg:grid-cols-[1.35fr_0.65fr]">
        <div className="space-y-5">
          <section>
            <h4 className="text-sm font-semibold text-medical-900 dark:text-white">Summary</h4>
            <p className="mt-2 text-sm leading-6 text-slate-700 dark:text-slate-300">{result.answer}</p>
          </section>
          <section>
            <h4 className="text-sm font-semibold text-medical-900 dark:text-white">Evidence</h4>
            <div className="mt-2 rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm leading-6 text-slate-700 dark:border-white/10 dark:bg-white/5 dark:text-slate-300">
              {result.retrieved_chunk ?? "No retrieved chunk was returned."}
            </div>
          </section>
          <details className="rounded-lg border border-slate-200 bg-white p-4 dark:border-white/10 dark:bg-white/5">
            <summary className="cursor-pointer list-none text-sm font-semibold text-medical-900 dark:text-white">
              How this answer was produced
            </summary>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <MetadataItem label="Retrieval count" value={String(result.retrieval_count)} />
              <MetadataItem label="Model version" value={result.model_used} />
              <MetadataItem label="Confidence level" value={result.confidence_level ?? "N/A"} />
              <MetadataItem label="Safety decision" value={result.safety_decision ?? "N/A"} />
              <MetadataItem label="Evidence status" value={result.evidence_status} />
              <MetadataItem label="Review required" value={result.review_required ? "Yes" : "No"} />
              <MetadataItem label="Query ID" value={result.query_id ?? "N/A"} />
              <MetadataItem label="Correlation ID" value={result.correlation_id ?? "N/A"} />
              <MetadataItem label="Created at" value={result.created_at ?? "N/A"} />
            </div>
          </details>
          {needsHumanVerification && (
            <section className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-700 dark:border-amber-400/30 dark:bg-amber-400/10 dark:text-amber-300">
              This response needs human review before use in a clinical workflow.
            </section>
          )}
        </div>

        <aside className="space-y-4">
          <div className="rounded-lg border border-slate-200 p-4 dark:border-white/10">
            <div className="text-xs font-semibold uppercase tracking-normal text-slate-500">
              Confidence
            </div>
            <div className="mt-2 text-3xl font-semibold text-medical-900 dark:text-white">
              {revealConfidence ? percent(result.confidence_score) : "N/A"}
            </div>
            <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-white/10">
              <div
                className={`h-full rounded-full transition-all duration-700 ${
                  !revealConfidence
                    ? "w-0"
                    : result.confidence_score >= 0.75
                    ? "bg-emerald-500"
                    : result.confidence_score >= 0.5
                    ? "bg-amber-400"
                    : "bg-rose-500"
                }`}
                style={{ width: revealConfidence ? `${Math.round(result.confidence_score * 100)}%` : "0%" }}
              />
            </div>
            <div className="mt-2 flex gap-2">
              <Badge tone={result.evidence_status === "sufficient" ? "success" : "warning"}>
                {result.evidence_status}
              </Badge>
              {needsHumanVerification && <Badge tone="warning">human review</Badge>}
            </div>
          </div>

          <div className="rounded-lg border border-slate-200 p-4 dark:border-white/10">
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-medical-900 dark:text-white">
              <FileText className="h-4 w-4" />
              Sources
            </div>
            <div className="space-y-3">
              {result.citations.map((citation) => (
                <a
                  key={`${citation.doc_id}-${citation.similarity_score}`}
                  className="block rounded-lg bg-slate-50 p-3 text-sm transition hover:bg-slate-100 dark:bg-white/5 dark:hover:bg-white/10"
                  href="#document-viewer"
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="font-medium text-medical-900 dark:text-white">
                      {citation.original_filename ?? citation.doc_id}
                    </span>
                    <ExternalLink className="h-3.5 w-3.5 text-slate-400" />
                  </div>
                  <div className="mt-2 flex items-center gap-2">
                    <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-200 dark:bg-white/10">
                      <div
                        className="h-full rounded-full bg-teal-500 transition-all duration-500"
                        style={{ width: `${Math.round(citation.similarity_score * 100)}%` }}
                      />
                    </div>
                    <span className="shrink-0 text-xs text-slate-500 dark:text-slate-400">
                      {Math.round(citation.similarity_score * 100)}%
                    </span>
                  </div>
                </a>
              ))}
            </div>
          </div>
        </aside>
      </div>
    </Card>
  );
}

function MetadataItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 dark:border-white/10 dark:bg-white/5">
      <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
        {label}
      </div>
      <div className="mt-1 break-words text-xs text-slate-700 dark:text-slate-300">{value}</div>
    </div>
  );
}
