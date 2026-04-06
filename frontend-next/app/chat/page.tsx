import { ChatWindow } from "@/components/chat/ChatWindow";
import { Sidebar } from "@/components/sidebar/Sidebar";

export default function ChatPage() {
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar />
      <main className="flex-1 flex flex-col relative min-w-0">
        <ChatWindow />
      </main>
    </div>
  );
}
