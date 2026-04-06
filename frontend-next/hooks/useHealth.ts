"use client";

import { useCallback, useEffect, useState } from "react";

export type HealthStatus = "healthy" | "degraded" | "offline" | "checking";

export function useHealth(pollIntervalMs = 30000) {
  const [status, setStatus] = useState<HealthStatus>("checking");
  const [latency, setLatency] = useState<number | null>(null);

  const check = useCallback(async () => {
    setStatus("checking");
    const start = Date.now();
    try {
      const res = await fetch("/api/health", { cache: "no-store" });
      const elapsed = Date.now() - start;
      if (res.ok) {
        setLatency(elapsed);
        setStatus(elapsed > 3000 ? "degraded" : "healthy");
      } else {
        setStatus("offline");
        setLatency(null);
      }
    } catch {
      setStatus("offline");
      setLatency(null);
    }
  }, []);

  useEffect(() => {
    check();
    const id = setInterval(check, pollIntervalMs);
    return () => clearInterval(id);
  }, [check, pollIntervalMs]);

  return { status, latency, check };
}
