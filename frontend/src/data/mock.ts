export const recentAnalyses = [
  { name: "Guardrail refusal review", owner: "AI Safety", confidence: 0.91, status: "Ready" },
  { name: "Retrieval quality check", owner: "Platform", confidence: 0.84, status: "Review" },
  { name: "Audit chain verification", owner: "DevOps", confidence: 0.78, status: "Queued" }
];

export const auditEvents = [
  { id: "AUD-1042", event: "Evidence threshold passed", time: "09:42", status: "Info" },
  { id: "AUD-1041", event: "Advisory draft blocked", time: "09:38", status: "Review" },
  { id: "AUD-1040", event: "Document indexed", time: "09:33", status: "Ready" }
];

export const processingSteps = [
  "Upload",
  "OCR",
  "Chunking",
  "Embedding",
  "Vector DB",
  "Retriever",
  "Reranker",
  "LLM",
  "Validation",
  "Guardrails",
  "Response"
];
