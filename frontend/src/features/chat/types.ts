export type MessageRole = "user" | "assistant" | "system";

export interface Message {
  id: string;
  conversation_id: string;
  role: MessageRole;
  content: string;
  created_at: string;
}

export interface Conversation {
  id: string;
  workspace_id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
  messages?: Message[];
}

export interface CreateConversationRequest {
  workspace_id: string;
}

export interface SendMessageRequest {
  content: string;
}

// Assumed response when sending a message
// If the backend returns both new messages, we can use it to update cache directly.
export interface SendMessageResponse {
  user_message: Message;
  assistant_message: Message;
}
