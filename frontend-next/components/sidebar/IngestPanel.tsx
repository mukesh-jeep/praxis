"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import {
  UploadCloud, CheckCircle2, XCircle, Loader2,
  FileText, ChevronDown, ChevronUp, Trash2, RefreshCw
} from "lucide-react";
import { toast } from "sonner";
import { useIngest } from "@/hooks/useIngest";
import { IngestedFile } from "@/types";

const STORAGE_KEY = "praxis_ingested_files";

function loadHistory(): IngestedFile[] {
  if (typeof window === "undefined") return [];
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
  } catch {
    return [];
  }
}

function saveHistory(files: IngestedFile[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(files));
}

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function timeAgo(ts: number) {
  const diff = Date.now() - ts;
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export function IngestPanel() {
  const { ingestFiles, isIngesting, progress } = useIngest();
  const [history, setHistory] = useState<IngestedFile[]>(loadHistory);
  const [showHistory, setShowHistory] = useState(true);

  const addToHistory = (entry: IngestedFile) => {
    setHistory((prev) => {
      const updated = [entry, ...prev].slice(0, 20); // keep last 20
      saveHistory(updated);
      return updated;
    });
  };

  const clearHistory = () => {
    setHistory([]);
    localStorage.removeItem(STORAGE_KEY);
  };

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      for (const file of acceptedFiles) {
        const entry: IngestedFile = {
          id: crypto.randomUUID(),
          name: file.name,
          size: file.size,
          chunks: 0,
          ingestedAt: Date.now(),
          status: "success",
        };
        try {
          const res = await ingestFiles([file]);
          if (res) {
            entry.chunks = res.chunks;
            entry.status = "success";
            toast.success(`Ingested "${file.name}"`, {
              description: `${res.chunks} chunks added to knowledge base.`,
            });
          }
        } catch (err: unknown) {
          const msg = err instanceof Error ? err.message : "Unknown error";
          entry.status = "error";
          entry.error = msg;
          toast.error(`Failed to ingest "${file.name}"`, { description: msg });
        }
        addToHistory(entry);
      }
    },
    [ingestFiles]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"] },
    disabled: isIngesting,
    multiple: true,
  });

  return (
    <div className="flex flex-col gap-3 p-2">
      {/* Drop zone */}
      <div
        {...getRootProps()}
        className={`
          flex flex-col items-center justify-center border-2 border-dashed rounded-xl p-5 text-center
          cursor-pointer transition-all duration-200
          ${isDragActive ? "border-[hsl(var(--primary))] bg-[hsl(var(--primary)/.08)] scale-[1.02]" : "border-[hsl(var(--border))] hover:border-[hsl(var(--primary)/.5)] hover:bg-[hsl(var(--muted)/.5)]"}
          ${isIngesting ? "opacity-60 cursor-not-allowed pointer-events-none" : ""}
        `}
      >
        <input {...getInputProps()} />

        {isIngesting ? (
          <Loader2 className="h-7 w-7 text-[hsl(var(--primary))] animate-spin mb-2" />
        ) : (
          <UploadCloud className={`h-7 w-7 mb-2 transition-colors ${isDragActive ? "text-[hsl(var(--primary))]" : "text-[hsl(var(--muted-foreground))]"}`} />
        )}

        {isIngesting ? (
          <div className="w-full space-y-2">
            <p className="text-xs font-medium text-[hsl(var(--muted-foreground))]">Processing PDF…</p>
            {/* Progress bar */}
            <div className="w-full h-1.5 rounded-full bg-[hsl(var(--muted))] overflow-hidden">
              <div
                className="h-full bg-[hsl(var(--primary))] transition-all duration-300 rounded-full"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="text-xs text-[hsl(var(--muted-foreground))]">{progress}%</p>
          </div>
        ) : isDragActive ? (
          <p className="text-xs font-semibold text-[hsl(var(--primary))]">Drop PDFs here…</p>
        ) : (
          <div className="space-y-0.5">
            <p className="text-xs font-medium text-[hsl(var(--foreground))]">Drag & drop PDF(s)</p>
            <p className="text-xs text-[hsl(var(--muted-foreground))]">or click to browse</p>
          </div>
        )}
      </div>

      {/* Ingestion history */}
      {history.length > 0 && (
        <div className="rounded-xl border border-[hsl(var(--border))] overflow-hidden">
          {/* Header */}
          <button
            onClick={() => setShowHistory((s) => !s)}
            className="w-full flex items-center justify-between px-3 py-2 bg-[hsl(var(--muted)/.3)] hover:bg-[hsl(var(--muted)/.5)] transition-colors text-xs text-[hsl(var(--muted-foreground))]"
          >
            <span className="font-medium uppercase tracking-wide">
              Ingested ({history.length})
            </span>
            <div className="flex items-center gap-1.5">
              <button
                onClick={(e) => { e.stopPropagation(); clearHistory(); }}
                className="p-1 rounded hover:bg-[hsl(var(--destructive)/.15)] hover:text-[hsl(var(--destructive))] transition-colors"
                title="Clear history"
              >
                <Trash2 size={11} />
              </button>
              {showHistory ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
            </div>
          </button>

          {/* File list */}
          {showHistory && (
            <div className="divide-y divide-[hsl(var(--border))] max-h-[220px] overflow-y-auto">
              {history.map((file) => (
                <div key={file.id} className="flex items-start gap-2.5 px-3 py-2.5 hover:bg-[hsl(var(--muted)/.2)] transition-colors">
                  <div className="shrink-0 mt-0.5">
                    {file.status === "success" ? (
                      <CheckCircle2 size={14} className="text-green-500" />
                    ) : (
                      <XCircle size={14} className="text-[hsl(var(--destructive))]" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium truncate leading-snug" title={file.name}>
                      {file.name}
                    </p>
                    {file.status === "success" ? (
                      <p className="text-[11px] text-[hsl(var(--muted-foreground))]">
                        {file.chunks} chunks · {formatBytes(file.size)} · {timeAgo(file.ingestedAt)}
                      </p>
                    ) : (
                      <p className="text-[11px] text-[hsl(var(--destructive))] truncate">{file.error}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
