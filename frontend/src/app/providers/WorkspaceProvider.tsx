import { createContext, useContext, useState, ReactNode, useEffect, useCallback } from "react";
import { useWorkspaceList } from "@/features/workspaces/hooks/useWorkspaces";

const WORKSPACE_STORAGE_KEY = "sentinel_selected_workspace_id";

interface WorkspaceContextValue {
  selectedWorkspaceId: string | null;
  selectWorkspace: (id: string) => void;
  clearWorkspace: () => void;
}

const WorkspaceContext = createContext<WorkspaceContextValue | undefined>(undefined);

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState<string | null>(() => {
    return localStorage.getItem(WORKSPACE_STORAGE_KEY);
  });
  
  const { data: workspaces, isSuccess } = useWorkspaceList();

  const selectWorkspace = useCallback((id: string) => {
    setSelectedWorkspaceId(id);
    localStorage.setItem(WORKSPACE_STORAGE_KEY, id);
  }, []);

  const clearWorkspace = useCallback(() => {
    setSelectedWorkspaceId(null);
    localStorage.removeItem(WORKSPACE_STORAGE_KEY);
  }, []);

  // Handle Workspace Deletion / Missing ID
  useEffect(() => {
    if (isSuccess && workspaces) {
      if (selectedWorkspaceId) {
        const exists = workspaces.some((ws) => ws.id === selectedWorkspaceId);
        if (!exists) {
          clearWorkspace();
        }
      }
    }
  }, [isSuccess, workspaces, selectedWorkspaceId, clearWorkspace]);

  return (
    <WorkspaceContext.Provider value={{ selectedWorkspaceId, selectWorkspace, clearWorkspace }}>
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (context === undefined) {
    throw new Error("useWorkspace must be used within a WorkspaceProvider");
  }
  return context;
}
