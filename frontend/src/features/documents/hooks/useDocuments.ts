import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { documentService } from "../services/document.service";

export const DOCUMENTS_QUERY_KEY = (workspaceId: string) => ["workspaces", workspaceId, "documents"];

export function useDocumentList(workspaceId: string | null) {
  return useQuery({
    queryKey: DOCUMENTS_QUERY_KEY(workspaceId!),
    queryFn: () => documentService.listDocuments(workspaceId!),
    enabled: !!workspaceId,
  });
}

export function useUploadDocument(workspaceId: string | null) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (file: File) => {
      if (!workspaceId) throw new Error("Workspace ID is required");
      return documentService.uploadDocument(workspaceId, file);
    },
    onSuccess: () => {
      if (workspaceId) {
        queryClient.invalidateQueries({ queryKey: DOCUMENTS_QUERY_KEY(workspaceId) });
      }
    },
  });
}

export function useDeleteDocument(workspaceId: string | null) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string) => documentService.deleteDocument(id),
    // Deletion relies entirely on backend-confirmation (no optimistic deletion)
    onSuccess: () => {
      if (workspaceId) {
        queryClient.invalidateQueries({ queryKey: DOCUMENTS_QUERY_KEY(workspaceId) });
      }
    },
  });
}
