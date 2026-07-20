import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { chatService } from "../services/chat.service";
import { Conversation, SendMessageResponse } from "../types";

export const CONVERSATIONS_LIST_KEY = (workspaceId: string) => ["workspaces", workspaceId, "conversations"];
export const CONVERSATION_DETAIL_KEY = (conversationId: string) => ["conversations", conversationId];

export function useConversationList(workspaceId: string | null) {
  return useQuery({
    queryKey: CONVERSATIONS_LIST_KEY(workspaceId!),
    queryFn: () => chatService.listConversations(workspaceId!),
    enabled: !!workspaceId,
  });
}

export function useConversation(conversationId: string | null) {
  return useQuery({
    queryKey: CONVERSATION_DETAIL_KEY(conversationId!),
    queryFn: () => chatService.getConversation(conversationId!),
    enabled: !!conversationId,
  });
}

export function useCreateConversation(workspaceId: string | null) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: () => {
      if (!workspaceId) throw new Error("Workspace ID is required");
      return chatService.createConversation(workspaceId);
    },
    onSuccess: () => {
      if (workspaceId) {
        queryClient.invalidateQueries({ queryKey: CONVERSATIONS_LIST_KEY(workspaceId) });
      }
    },
  });
}

export function useDeleteConversation(workspaceId: string | null) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string) => chatService.deleteConversation(id),
    onSuccess: (_, id) => {
      if (workspaceId) {
        queryClient.invalidateQueries({ queryKey: CONVERSATIONS_LIST_KEY(workspaceId) });
      }
      queryClient.removeQueries({ queryKey: CONVERSATION_DETAIL_KEY(id) });
    },
  });
}

export function useSendMessage(conversationId: string | null) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (content: string) => {
      if (!conversationId) throw new Error("Conversation ID is required");
      return chatService.sendMessage(conversationId, content);
    },
    onSuccess: (response: SendMessageResponse) => {
      if (!conversationId) return;
      
      // Update cache directly if the response provides the new messages
      queryClient.setQueryData(
        CONVERSATION_DETAIL_KEY(conversationId),
        (old: Conversation | undefined) => {
          if (!old) return old;
          return {
            ...old,
            messages: [
              ...(old.messages || []),
              response.user_message,
              response.assistant_message
            ].filter(Boolean)
          };
        }
      );
      
      // We also invalidate as a fallback to ensure we're totally in sync
      queryClient.invalidateQueries({ queryKey: CONVERSATION_DETAIL_KEY(conversationId) });
    },
  });
}
