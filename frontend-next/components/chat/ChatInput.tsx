"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Paperclip, Send, X, Image as ImageIcon } from "lucide-react";

interface ChatInputProps {
  onSend: (query: string, file?: File | null) => void;
  isLoading: boolean;
}

export function ChatInput({ onSend, isLoading }: ChatInputProps) {
  const [query, setQuery] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [query]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      
      if (selectedFile.type.startsWith("image/")) {
        const url = URL.createObjectURL(selectedFile);
        setPreview(url);
      } else {
        setPreview(null);
      }
    }
  };

  const removeFile = () => {
    setFile(null);
    if (preview) {
      URL.revokeObjectURL(preview);
      setPreview(null);
    }
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleSend = () => {
    if ((!query.trim() && !file) || isLoading) return;
    onSend(query, file);
    setQuery("");
    removeFile();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="relative bg-background border shadow-sm rounded-2xl p-3 flex flex-col gap-3 transition-shadow focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-0">
      
      {/* File Attachment Preview */}
      {file && (
        <div className="flex items-center gap-3 bg-muted/50 p-2 rounded-lg w-fit border fade-in animate-in slide-in-from-bottom-2">
          {preview ? (
            <img src={preview} alt="Attachment" className="h-10 w-10 object-cover rounded pointer-events-none" />
          ) : (
            <div className="h-10 w-10 bg-primary/10 flex items-center justify-center rounded text-primary">
              <Paperclip size={20} />
            </div>
          )}
          <div className="text-sm max-w-[200px] truncate pr-2">
            <p className="font-medium truncate">{file.name}</p>
            <p className="text-xs text-muted-foreground">{(file.size / 1024).toFixed(1)} KB</p>
          </div>
          <Button variant="ghost" size="icon" className="h-6 w-6 ml-auto hover:bg-destructive/10 hover:text-destructive" onClick={removeFile}>
            <X size={14} />
          </Button>
        </div>
      )}

      {/* Input Area */}
      <div className="flex items-end gap-2">
        <input
          type="file"
          ref={fileInputRef}
          className="hidden"
          accept=".pdf,.png,.jpg,.jpeg,.webp"
          onChange={handleFileChange}
        />
        <Button
          variant="ghost"
          size="icon"
          className="shrink-0 rounded-full h-10 w-10 text-muted-foreground hover:text-foreground"
          onClick={() => fileInputRef.current?.click()}
          disabled={isLoading}
          type="button"
        >
          <Paperclip size={20} />
        </Button>
        
        <Textarea
          ref={textareaRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a medical question, or attach a document/image..."
          className="min-h-[40px] resize-none border-0 focus-visible:ring-0 px-2 py-2.5 bg-transparent scrollbar-thin shadow-none"
          disabled={isLoading}
          rows={1}
        />

        <Button
          onClick={handleSend}
          disabled={(!query.trim() && !file) || isLoading}
          size="icon"
          className="shrink-0 rounded-full h-10 w-10 transition-transform active:scale-95"
        >
          <Send size={18} className={query.trim() || file ? "text-primary-foreground" : "text-muted-foreground opacity-50"} />
        </Button>
      </div>
    </div>
  );
}
