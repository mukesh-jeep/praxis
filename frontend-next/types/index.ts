export type Role = "user" | "assistant" | "system";

export interface Message {
  id: string;
  role: Role;
  content: string;
  streaming?: boolean;
  file?: File;
  fileType?: "text" | "image";
}

export interface Session {
  id: string;
  title: string;
  timestamp: number;
}

export interface IngestResult {
  ingested: number;
  chunks: number;
  message: string;
}

export interface IngestedFile {
  id: string;
  name: string;
  size: number;
  chunks: number;
  ingestedAt: number; // timestamp
  status: "success" | "error";
  error?: string;
}
