import { create } from "zustand";
import { Message } from "@/types";

interface ChatState {
  messages: Message[];
  isLoading: boolean;
  sessionId: string;
  setSessionId: (id: string) => void;
  addMessage: (message: Message) => void;
  appendToLastMessage: (chunk: string) => void;
  setIsLoading: (isLoading: boolean) => void;
  clearMessages: () => void;
  setMessages: (messages: Message[]) => void;
}

function getInitialSessionId(): string {
  if (typeof window === "undefined") return ""; // SSR — will be replaced on client
  const stored = localStorage.getItem("praxis_session_id");
  if (stored) return stored;
  const id = crypto.randomUUID();
  localStorage.setItem("praxis_session_id", id);
  return id;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  isLoading: false,
  sessionId: getInitialSessionId(),
  setSessionId: (id) => {
    if (typeof window !== "undefined") {
      localStorage.setItem("praxis_session_id", id);
    }
    set({ sessionId: id });
  },
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  appendToLastMessage: (chunk) =>
    set((state) => {
      const messages = [...state.messages];
      if (messages.length > 0) {
        messages[messages.length - 1] = {
          ...messages[messages.length - 1],
          content: messages[messages.length - 1].content + chunk,
        };
      }
      return { messages };
    }),
  setIsLoading: (isLoading) => set({ isLoading }),
  clearMessages: () => set({ messages: [] }),
  setMessages: (messages) => set({ messages }),
}));
