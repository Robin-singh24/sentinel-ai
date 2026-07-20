import { apiClient } from "./client";
import { SuccessResponse } from "@/features/auth/types";
import { Document } from "@/features/documents/types";

export const documentsApi = {
  list: async (workspaceId: string): Promise<Document[]> => {
    const { data } = await apiClient.get<SuccessResponse<Document[]>>("/documents", {
      params: { workspace_id: workspaceId },
    });
    return data.data;
  },

  get: async (id: string): Promise<Document> => {
    const { data } = await apiClient.get<SuccessResponse<Document>>(`/documents/${id}`);
    return data.data;
  },

  upload: async (workspaceId: string, file: File): Promise<Document> => {
    const formData = new FormData();
    formData.append("workspace_id", workspaceId);
    formData.append("file", file);

    const { data } = await apiClient.post<SuccessResponse<Document>>("/documents", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return data.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/documents/${id}`);
  },
};
