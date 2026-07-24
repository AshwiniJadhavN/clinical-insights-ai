import { ChevronLeft, ChevronRight, FileText, Search, ZoomIn, ZoomOut } from "lucide-react";
import { useState } from "react";
import { motion } from "framer-motion";
import { Card, Button } from "./ui";

export interface DocumentContent {
  id: string;
  filename: string;
  content: string;
  chunks: {
    id: string;
    text: string;
    confidence?: number;
    highlighted?: boolean;
  }[];
}

export function ClinicalDocumentViewer({
  document,
  selectedChunkId,
  onChunkSelect
}: {
  document: DocumentContent;
  selectedChunkId?: string;
  onChunkSelect?: (chunkId: string) => void;
}) {
  const [zoom, setZoom] = useState(100);
  const [searchQuery, setSearchQuery] = useState("");

  const filteredChunks = document.chunks.filter((chunk) =>
    chunk.text.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <Card className="overflow-hidden">
      <div className="grid gap-0 lg:grid-cols-[1fr_1.5fr_1fr]">
        {/* Left Panel: Document List & Navigation */}
        <div className="border-r border-slate-200 dark:border-white/10">
          <div className="border-b border-slate-200 p-4 dark:border-white/10">
            <div className="flex items-center gap-3">
              <div className="grid h-9 w-9 place-items-center rounded-lg bg-teal-100 dark:bg-teal-900/30">
                <FileText className="h-5 w-5 text-teal-600 dark:text-teal-400" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="truncate text-sm font-semibold text-medical-900 dark:text-white">
                  {document.filename}
                </div>
                <div className="text-xs text-slate-500 dark:text-slate-400">
                  {document.chunks.length} chunks
                </div>
              </div>
            </div>
          </div>

          {/* Search */}
          <div className="border-b border-slate-200 p-3 dark:border-white/10">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Search chunks..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-lg border border-slate-200 bg-white py-2 pl-10 pr-3 text-sm text-medical-900 placeholder-slate-500 outline-none transition focus:border-teal-500 focus:ring-1 focus:ring-teal-500 dark:border-white/10 dark:bg-white/5 dark:text-white dark:placeholder-slate-400"
              />
            </div>
          </div>

          {/* Chunks List */}
          <div className="max-h-[600px] overflow-y-auto">
            {filteredChunks.map((chunk) => (
              <motion.button
                key={chunk.id}
                onClick={() => onChunkSelect?.(chunk.id)}
                whileHover={{ x: 4 }}
                className={`w-full border-b border-slate-200 p-3 text-left transition dark:border-white/10 ${
                  selectedChunkId === chunk.id
                    ? "bg-teal-50 dark:bg-teal-400/10"
                    : "hover:bg-slate-50 dark:hover:bg-white/5"
                }`}
              >
                <div className="line-clamp-2 text-sm text-medical-900 dark:text-white">
                  {chunk.text}
                </div>
                {chunk.confidence && (
                  <div className="mt-2 text-xs text-slate-500 dark:text-slate-400">
                    Confidence: {(chunk.confidence * 100).toFixed(0)}%
                  </div>
                )}
              </motion.button>
            ))}
          </div>
        </div>

        {/* Center Panel: Document Content Viewer */}
        <div className="border-r border-slate-200 bg-slate-50/50 dark:border-white/10 dark:bg-white/2">
          <div className="border-b border-slate-200 flex items-center justify-between p-4 dark:border-white/10">
            <h3 className="text-sm font-semibold text-medical-900 dark:text-white">
              Document Preview
            </h3>
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setZoom(Math.max(50, zoom - 10))}
                icon={<ZoomOut className="h-4 w-4" />}
              />
              <span className="text-xs font-medium text-slate-600 dark:text-slate-400 min-w-12 text-center">
                {zoom}%
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setZoom(Math.min(200, zoom + 10))}
                icon={<ZoomIn className="h-4 w-4" />}
              />
            </div>
          </div>

          {/* Document Content */}
          <div className="max-h-[600px] overflow-auto p-6">
            <div
              style={{ fontSize: `${(zoom / 100) * 14}px` }}
              className="prose prose-sm max-w-none space-y-4 text-slate-700 dark:text-slate-300"
            >
              {document.content}
            </div>
          </div>
        </div>

        {/* Right Panel: Evidence & Metadata */}
        <div>
          <div className="border-b border-slate-200 p-4 dark:border-white/10">
            <h3 className="text-sm font-semibold text-medical-900 dark:text-white">
              Selected Evidence
            </h3>
          </div>

          <div className="max-h-[600px] overflow-y-auto p-4 space-y-4">
            {selectedChunkId ? (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-4"
              >
                {(() => {
                  const selected = document.chunks.find((c) => c.id === selectedChunkId);
                  return selected ? (
                    <>
                      <div className="rounded-lg bg-teal-50 p-3 dark:bg-teal-400/10">
                        <div className="text-sm leading-6 text-slate-700 dark:text-slate-300">
                          {selected.text}
                        </div>
                      </div>

                      {selected.confidence && (
                        <div className="rounded-lg border border-slate-200 p-3 dark:border-white/10">
                          <div className="text-xs font-semibold uppercase tracking-widest text-slate-600 dark:text-slate-400">
                            Confidence Score
                          </div>
                          <div className="mt-2">
                            <div className="text-2xl font-semibold text-medical-900 dark:text-white">
                              {(selected.confidence * 100).toFixed(0)}%
                            </div>
                            <div className="mt-2 h-2 w-full rounded-full bg-slate-200 dark:bg-white/10">
                              <div
                                className="h-2 rounded-full bg-teal-500 dark:bg-teal-400"
                                style={{ width: `${selected.confidence * 100}%` }}
                              />
                            </div>
                          </div>
                        </div>
                      )}

                      <div className="text-xs text-slate-500 dark:text-slate-400">
                        Chunk ID: {selected.id}
                      </div>
                    </>
                  ) : null;
                })()}
              </motion.div>
            ) : (
              <div className="text-center py-8 text-slate-500 dark:text-slate-400">
                <p className="text-sm">Select a chunk to view evidence</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
}
