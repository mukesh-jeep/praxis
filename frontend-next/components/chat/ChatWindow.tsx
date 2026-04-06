"use client";

import { useChat } from "@/hooks/useChat";
import { MessageBubble } from "./MessageBubble";
import { ChatInput } from "./ChatInput";
import { useEffect, useRef } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";

export function ChatWindow() {
  const { messages, sendMessage, isLoading, error } = useChat();
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  return (
    <div className="flex flex-col h-full bg-background relative">
      <ScrollArea className="flex-1 w-full p-4 lg:p-8">
        <div className="max-w-3xl mx-auto flex flex-col gap-6 pb-32">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center text-center mt-32 space-y-4 opacity-50">
              <div className="w-16 h-16 bg-muted rounded-2xl flex items-center justify-center mb-4 text-2xl shadow-sm">
                ⚕️
              </div>
              <h2 className="text-2xl font-semibold tracking-tight">Medical RAG Assistant</h2>
              <p className="max-w-md text-sm">
                Ask a clinical question, or drag and drop a medical PDF/Image to get evidence-based insights.
              </p>
            </div>
          ) : (
            messages.map((msg) => <MessageBubble key={msg.id} message={msg} />)
          )}
          {error && (
            <div className="bg-destructive/10 text-destructive px-4 py-3 rounded-lg text-sm mb-4 mx-auto max-w-3xl w-full border border-destructive/20">
              {error}
            </div>
          )}
          <div ref={scrollRef} className="h-4" />
        </div>
      </ScrollArea>

      <div className="absolute bottom-0 left-0 w-full bg-gradient-to-t from-background via-background pb-6 pt-10 px-4">
        <div className="max-w-3xl mx-auto">
          <ChatInput onSend={sendMessage} isLoading={isLoading} />
        </div>
      </div>
    </div>
  );
}
