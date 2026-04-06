"use client";

import { useState, useEffect } from "react";
import {
  PlusCircle, Settings2, ShieldCheck, Database,
  Menu, X, Copy, Check, RefreshCw, Activity
} from "lucide-react";
import { toast } from "sonner";
import { IngestPanel } from "./IngestPanel";
import { useChatStore } from "@/store/chatStore";
import { useHealth, HealthStatus } from "@/hooks/useHealth";

// ── Health dot ──────────────────────────────────────────────────────────────
function HealthDot({ status, latency, onRefresh }: {
  status: HealthStatus;
  latency: number | null;
  onRefresh: () => void;
}) {
  const colors: Record<HealthStatus, string> = {
    healthy:  "bg-green-500",
    degraded: "bg-yellow-500",
    offline:  "bg-red-500",
    checking: "bg-[hsl(var(--muted-foreground))] animate-pulse",
  };
  const labels: Record<HealthStatus, string> = {
    healthy:  "API Online",
    degraded: "API Slow",
    offline:  "API Offline",
    checking: "Checking…",
  };

  return (
    <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-[hsl(var(--muted)/.3)] border border-[hsl(var(--border))]">
      <span className={`w-2 h-2 rounded-full shrink-0 ${colors[status]}`} />
      <div className="flex-1 min-w-0">
        <p className="text-[11px] font-semibold leading-none">{labels[status]}</p>
        {latency !== null && status !== "checking" && (
          <p className="text-[10px] text-[hsl(var(--muted-foreground))] mt-0.5">{latency}ms</p>
        )}
      </div>
      <button
        onClick={onRefresh}
        className="p-1 rounded hover:bg-[hsl(var(--muted))] transition-colors text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]"
        title="Re-check"
      >
        <RefreshCw size={11} />
      </button>
    </div>
  );
}

// ── Session pill ─────────────────────────────────────────────────────────────
function SessionPill({ sessionId }: { sessionId: string }) {
  const [copied, setCopied] = useState(false);
  const [mounted, setMounted] = useState(false);

  // Avoid SSR/client mismatch — sessionId is "" on server, real UUID on client
  useEffect(() => { setMounted(true); }, []);

  const copy = () => {
    navigator.clipboard.writeText(sessionId);
    setCopied(true);
    toast.success("Session ID copied");
    setTimeout(() => setCopied(false), 2000);
  };

  const displayId = mounted && sessionId ? `${sessionId.slice(0, 18)}…` : "…";

  return (
    <button
      onClick={copy}
      className="group w-full flex items-center gap-2 px-3 py-2 rounded-xl bg-[hsl(var(--muted)/.3)] border border-[hsl(var(--border))] hover:bg-[hsl(var(--muted)/.5)] transition-colors text-left"
      title="Click to copy session ID"
    >
      <Activity size={12} className="shrink-0 text-[hsl(var(--muted-foreground))]" />
      <div className="flex-1 min-w-0">
        <p className="text-[10px] text-[hsl(var(--muted-foreground))] uppercase tracking-wider font-medium leading-none mb-0.5">Session</p>
        <p className="text-[11px] font-mono truncate text-[hsl(var(--foreground))]">{displayId}</p>
      </div>
      <div className="shrink-0 text-[hsl(var(--muted-foreground))] group-hover:text-[hsl(var(--foreground))] transition-colors">
        {copied ? <Check size={11} className="text-green-500" /> : <Copy size={11} />}
      </div>
    </button>
  );
}

// ── Main Sidebar ─────────────────────────────────────────────────────────────
export function Sidebar() {
  const [isOpen, setIsOpen] = useState(false);
  const { setSessionId, clearMessages, sessionId, messages } = useChatStore();
  const { status, latency, check } = useHealth(30000);

  const handleNewSession = () => {
    setSessionId(crypto.randomUUID());
    clearMessages();
    setIsOpen(false);
    toast.info("New session started");
  };

  return (
    <>
      {/* Mobile hamburger */}
      <button
        className="lg:hidden absolute top-4 left-4 z-50 p-2 rounded-xl bg-[hsl(var(--card))] border border-[hsl(var(--border))] shadow-sm"
        onClick={() => setIsOpen(!isOpen)}
      >
        {isOpen ? <X size={18} /> : <Menu size={18} />}
      </button>

      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed lg:static top-0 left-0 h-full z-50 flex flex-col
          w-[280px] bg-[hsl(var(--card))] border-r border-[hsl(var(--border))]
          transition-transform duration-300 ease-in-out
          ${isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}
        `}
      >
        {/* Logo */}
        <div className="flex items-center gap-2.5 px-5 py-4 border-b border-[hsl(var(--border))]">
          <ShieldCheck className="h-5 w-5 text-[hsl(var(--primary))]" />
          <span className="font-bold tracking-tight text-base">Praxis RAG</span>
        </div>

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-5">

          {/* New Consultation */}
          <button
            onClick={handleNewSession}
            className="w-full flex items-center justify-center gap-2 h-9 px-4 rounded-xl bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] text-sm font-medium hover:opacity-90 active:scale-95 transition-all shadow-sm"
          >
            <PlusCircle size={15} />
            New Consultation
          </button>

          {/* Status section */}
          <div className="space-y-2">
            <p className="text-[10px] font-semibold text-[hsl(var(--muted-foreground))] uppercase tracking-widest px-1">
              System Status
            </p>
            <HealthDot status={status} latency={latency} onRefresh={check} />
            <SessionPill sessionId={sessionId} />

            {/* Message count */}
            <div className="flex items-center justify-between px-3 py-2 rounded-xl bg-[hsl(var(--muted)/.3)] border border-[hsl(var(--border))] text-[11px]">
              <span className="text-[hsl(var(--muted-foreground))]">Messages this session</span>
              <span className="font-semibold tabular-nums">{messages.length}</span>
            </div>
          </div>

          {/* Knowledge Base */}
          <div className="space-y-2">
            <p className="text-[10px] font-semibold text-[hsl(var(--muted-foreground))] uppercase tracking-widest px-1 flex items-center gap-1.5">
              <Database size={10} />
              Knowledge Base
            </p>
            <IngestPanel />
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-[hsl(var(--border))]">
          <button className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-sm text-[hsl(var(--muted-foreground))] hover:bg-[hsl(var(--muted)/.5)] hover:text-[hsl(var(--foreground))] transition-colors">
            <Settings2 size={15} />
            Settings
          </button>
        </div>
      </aside>
    </>
  );
}
