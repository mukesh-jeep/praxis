import { useState, useRef, useCallback } from "react";
import { INGEST_API_URL } from "@/lib/api";
import { IngestResult } from "@/types";

export function useIngest() {
  const [isIngesting, setIsIngesting] = useState(false);
  const [result, setResult] = useState<IngestResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);

  const ingestFiles = useCallback(async (files: File[]): Promise<IngestResult | undefined> => {
    if (!files.length) return;

    setIsIngesting(true);
    setError(null);
    setResult(null);
    setProgress(10); // Start

    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));

    // Simulate progress while waiting (server is sync, no real progress stream)
    const progressTimer = setInterval(() => {
      setProgress((p) => (p < 85 ? p + 5 : p));
    }, 400);

    try {
      const response = await fetch(INGEST_API_URL, {
        method: "POST",
        body: formData,
      });

      clearInterval(progressTimer);

      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || "Ingestion failed");
      }

      const data: IngestResult = await response.json();
      setResult(data);
      setProgress(100);
      setTimeout(() => setProgress(0), 1500);
      return data;
    } catch (err: unknown) {
      clearInterval(progressTimer);
      const message = err instanceof Error ? err.message : "An error occurred during ingestion";
      setError(message);
      setProgress(0);
      throw err;
    } finally {
      setIsIngesting(false);
    }
  }, []);

  return { ingestFiles, isIngesting, result, error, progress };
}
