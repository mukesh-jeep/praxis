"use client";

import { Message } from "@/types";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { cn } from "@/lib/utils";
import { Bot, User, FileText, ImageIcon } from "lucide-react";

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={cn("flex w-full gap-3", isUser ? "flex-row-reverse" : "flex-row")}>
      {/* Avatar */}
      <div
        className={cn(
          "flex shrink-0 items-center justify-center rounded-full border h-8 w-8 text-xs font-semibold shadow-sm",
          isUser
            ? "bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] border-[hsl(var(--primary))]"
            : "bg-[hsl(var(--muted))] border-[hsl(var(--border))]"
        )}
      >
        {isUser ? <User size={14} /> : <Bot size={14} />}
      </div>

      {/* Content */}
      <div className={cn("flex flex-col gap-1.5 max-w-[85%]", isUser ? "items-end" : "items-start")}>
        {/* File chip */}
        {message.file && (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[hsl(var(--muted))] border border-[hsl(var(--border))] text-xs max-w-[240px]">
            {message.fileType === "image" ? <ImageIcon size={14} /> : <FileText size={14} />}
            <span className="truncate">{message.file.name}</span>
          </div>
        )}

        {/* Bubble */}
        {message.content ? (
          <div
            className={cn(
              "px-4 py-3 rounded-2xl text-sm leading-relaxed shadow-sm",
              isUser
                ? "bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] rounded-tr-sm"
                : "bg-[hsl(var(--card))] border border-[hsl(var(--border))] rounded-tl-sm text-[hsl(var(--foreground))]"
            )}
          >
            {isUser ? (
              <span className="whitespace-pre-wrap break-words">{message.content}</span>
            ) : (
              <div className="markdown-body">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {message.content}
                </ReactMarkdown>
              </div>
            )}
          </div>
        ) : message.streaming ? (
          /* Typing indicator */
          <div className="px-4 py-4 rounded-2xl rounded-tl-sm bg-[hsl(var(--card))] border border-[hsl(var(--border))] shadow-sm flex items-center gap-1">
            {[0, 0.15, 0.3].map((delay, i) => (
              <span
                key={i}
                className="w-2 h-2 rounded-full bg-[hsl(var(--muted-foreground))] animate-pulse"
                style={{ animationDelay: `${delay}s` }}
              />
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}
