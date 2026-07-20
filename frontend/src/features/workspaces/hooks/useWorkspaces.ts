import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { workspaceService } from "../services/workspace.service";
import { Workspace, WorkspaceCreate, WorkspaceUpdate } from "../types";

export const WORKSPACES_QUERY_KEY = ["workspaces"];

export function useWorkspaceList() {
  return useQuery({
    queryKey: WORKSPACES_QUERY_KEY,
    queryFn: workspaceService.listWorkspaces,
  });
}

export function useCreateWorkspace() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: WorkspaceCreate) => workspaceService.createWorkspace(data),
    onSuccess: (newWorkspace) => {
      // Optimistically update the cache or just invalidate to refetch
      queryClient.setQueryData<Workspace[]>(WORKSPACES_QUERY_KEY, (old) => {
        if (!old) return [newWorkspace];
        return [newWorkspace, ...old]; // Assuming newest first
      });
    },
  });
}

export function useUpdateWorkspace() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: WorkspaceUpdate }) =>
      workspaceService.updateWorkspace(id, data),
    onMutate: async ({ id, data }) => {
      await queryClient.cancelQueries({ queryKey: WORKSPACES_QUERY_KEY });
      const previousWorkspaces = queryClient.getQueryData<Workspace[]>(WORKSPACES_QUERY_KEY);
      
      queryClient.setQueryData<Workspace[]>(WORKSPACES_QUERY_KEY, (old) => {
        if (!old) return old;
        return old.map((ws) => (ws.id === id ? { ...ws, ...data } : ws));
      });
      
      return { previousWorkspaces };
    },
    onError: (_err, _newWs, context) => {
      if (context?.previousWorkspaces) {
        queryClient.setQueryData(WORKSPACES_QUERY_KEY, context.previousWorkspaces);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: WORKSPACES_QUERY_KEY });
    },
  });
}

export function useDeleteWorkspace() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string) => workspaceService.deleteWorkspace(id),
    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: WORKSPACES_QUERY_KEY });
      const previousWorkspaces = queryClient.getQueryData<Workspace[]>(WORKSPACES_QUERY_KEY);
      
      queryClient.setQueryData<Workspace[]>(WORKSPACES_QUERY_KEY, (old) => {
        if (!old) return old;
        return old.filter((ws) => ws.id !== id);
      });
      
      return { previousWorkspaces };
    },
    onError: (_err, _id, context) => {
      if (context?.previousWorkspaces) {
        queryClient.setQueryData(WORKSPACES_QUERY_KEY, context.previousWorkspaces);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: WORKSPACES_QUERY_KEY });
    },
  });
}
