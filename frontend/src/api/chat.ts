import { apiClient } from "./client";
import { SuccessResponse } from "@/features/auth/types";
import {
  Conversation,
  CreateConversationRequest,
  SendMessageRequest,
  SendMessageResponse,
} from "@/features/chat/types";

export const chatApi = {
  listConversations: async (workspaceId: string): Promise<Conversation[]> => {
    const { data } = await apiClient.get<SuccessResponse<Conversation[]>>("/conversations", {
      params: { workspace_id: workspaceId },
    });
    return data.data;
  },

  getConversation: async (id: string): Promise<Conversation> => {
    const { data } = await apiClient.get<SuccessResponse<Conversation>>(`/conversations/${id}`);
    return data.data;
  },

  createConversation: async (payload: CreateConversationRequest): Promise<Conversation> => {
    const { data } = await apiClient.post<SuccessResponse<Conversation>>("/conversations", payload);
    return data.data;
  },

  deleteConversation: async (id: string): Promise<void> => {
    await apiClient.delete(`/conversations/${id}`);
  },

  sendMessage: async (conversationId: string, payload: SendMessageRequest): Promise<SendMessageResponse> => {
    const { data } = await apiClient.post<SuccessResponse<SendMessageResponse>>(
      `/conversations/${conversationId}/messages`,
      payload
    );
    return data.data;
  },
};
