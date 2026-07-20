export type DocumentStatus = "uploading" | "processing" | "ready" | "failed";

export interface Document {
  id: string;
  filename: string;
  file_size: number;
  mime_type: string;
  status: DocumentStatus;
  created_at: string;
  updated_at: string;
  workspace_id: string;
  owner_id: string;
  error_message?: string | null;
}
