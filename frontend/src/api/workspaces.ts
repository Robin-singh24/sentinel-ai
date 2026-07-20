import { apiClient } from "./client";
import { SuccessResponse } from "@/features/auth/types";
import { Workspace, WorkspaceCreate, WorkspaceUpdate } from "@/features/workspaces/types";

export const workspacesApi = {
  list: async (): Promise<Workspace[]> => {
    const { data } = await apiClient.get<SuccessResponse<Workspace[]>>("/workspaces");
    return data.data;
  },

  get: async (id: string): Promise<Workspace> => {
    const { data } = await apiClient.get<SuccessResponse<Workspace>>(`/workspaces/${id}`);
    return data.data;
  },

  create: async (payload: WorkspaceCreate): Promise<Workspace> => {
    const { data } = await apiClient.post<SuccessResponse<Workspace>>("/workspaces", payload);
    return data.data;
  },

  update: async (id: string, payload: WorkspaceUpdate): Promise<Workspace> => {
    const { data } = await apiClient.put<SuccessResponse<Workspace>>(`/workspaces/${id}`, payload);
    return data.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/workspaces/${id}`);
  },
};
