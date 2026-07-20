import { documentsApi } from "@/api/documents";
import { Document } from "../types";

export const documentService = {
  listDocuments: async (workspaceId: string): Promise<Document[]> => {
    return await documentsApi.list(workspaceId);
  },

  getDocument: async (id: string): Promise<Document> => {
    return await documentsApi.get(id);
  },

  uploadDocument: async (workspaceId: string, file: File): Promise<Document> => {
    return await documentsApi.upload(workspaceId, file);
  },

  deleteDocument: async (id: string): Promise<void> => {
    return await documentsApi.delete(id);
  },
};
