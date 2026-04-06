import { useState } from "react";
import { useChatStore } from "@/store/chatStore";
import { CHAT_API_URL } from "@/lib/api";

export function useChat() {
  const { messages, addMessage, sessionId, setSessionId, appendToLastMessage, setIsLoading } = useChatStore();
  const [error, setError] = useState<string | null>(null);

  const sendMessage = async (query: string, file?: File | null) => {
    if (!query.trim() && !file) return;

    setError(null);
    setIsLoading(true);

    // Optimistic user message
    const userMsgId = crypto.randomUUID();
    addMessage({
      id: userMsgId,
      role: "user",
      content: query,
      file: file || undefined,
      fileType: file && file.type.startsWith("image") ? "image" : (file ? "text" : undefined),
    });

    const form = new FormData();
    form.append("query", query);
    form.append("session_id", sessionId);
    if (file) {
      form.append("file", file);
    }

    // Placeholder for assistant
    const assistantMsgId = crypto.randomUUID();
    addMessage({
      id: assistantMsgId,
      role: "assistant",
      content: "",
      streaming: true,
    });

    try {
      const res = await fetch(CHAT_API_URL, {
        method: "POST",
        body: form,
      });

      if (!res.ok) {
        throw new Error(await res.text() || "Failed to send message");
      }

      // Check if response is stream or json. Currently backend is json.
      const contentType = res.headers.get("content-type");
      if (contentType && contentType.includes("application/json")) {
        const data = await res.json();
        // Just append the whole answer
        appendToLastMessage(data.answer);
        
        if (data.session_id && data.session_id !== sessionId) {
          setSessionId(data.session_id);
        }
      } else {
        // Fallback or stream handler if they change backend to SSE
        const reader = res.body?.getReader();
        const decoder = new TextDecoder();
        
        if (reader) {
           while (true) {
             const { done, value } = await reader.read();
             if (done) break;
             const chunk = decoder.decode(value, { stream: true });
             appendToLastMessage(chunk);
           }
        }
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Something went wrong.";
      console.error(err);
      setError(message);
      appendToLastMessage("\n\n*Error: Could not retrieve response.*");
    } finally {
      setIsLoading(false);
      // turn off streaming flag
      useChatStore.setState((state) => {
        const _m = [...state.messages];
        if (_m.length > 0) _m[_m.length - 1].streaming = false;
        return { messages: _m };
      });
    }
  };

  return {
    messages,
    sendMessage,
    isLoading: useChatStore((state) => state.isLoading),
    error,
  };
}
