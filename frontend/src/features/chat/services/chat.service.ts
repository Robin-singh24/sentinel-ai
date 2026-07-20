import { chatApi } from "@/api/chat";
import {
  Conversation,
  CreateConversationRequest,
  SendMessageRequest,
  SendMessageResponse,
} from "../types";

export const chatService = {
  listConversations: async (workspaceId: string): Promise<Conversation[]> => {
    return await chatApi.listConversations(workspaceId);
  },

  getConversation: async (id: string): Promise<Conversation> => {
    return await chatApi.getConversation(id);
  },

  createConversation: async (workspaceId: string): Promise<Conversation> => {
    const payload: CreateConversationRequest = { workspace_id: workspaceId };
    return await chatApi.createConversation(payload);
  },

  deleteConversation: async (id: string): Promise<void> => {
    return await chatApi.deleteConversation(id);
  },

  sendMessage: async (conversationId: string, content: string): Promise<SendMessageResponse> => {
    const payload: SendMessageRequest = { content };
    return await chatApi.sendMessage(conversationId, payload);
  },
};
