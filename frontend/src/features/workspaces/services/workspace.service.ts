import { workspacesApi } from "@/api/workspaces";
import { Workspace, WorkspaceCreate, WorkspaceUpdate } from "../types";

export const workspaceService = {
  listWorkspaces: async (): Promise<Workspace[]> => {
    return await workspacesApi.list();
  },

  getWorkspace: async (id: string): Promise<Workspace> => {
    return await workspacesApi.get(id);
  },

  createWorkspace: async (data: WorkspaceCreate): Promise<Workspace> => {
    return await workspacesApi.create(data);
  },

  updateWorkspace: async (id: string, data: WorkspaceUpdate): Promise<Workspace> => {
    return await workspacesApi.update(id, data);
  },

  deleteWorkspace: async (id: string): Promise<void> => {
    return await workspacesApi.delete(id);
  },
};
