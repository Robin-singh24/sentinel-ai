import { useState, useEffect, useRef } from "react";
import { useParams, Navigate, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { useWorkspace } from "@/app/providers/WorkspaceProvider";
import { 
  useConversationList, 
  useConversation, 
  useCreateConversation, 
  useSendMessage 
} from "../hooks/useChat";
import { Conversation } from "../types";

import { ConversationSidebar } from "../components/ConversationSidebar";
import { EmptyConversationState } from "../components/EmptyConversationState";
import { MessageBubble } from "../components/MessageBubble";
import { PromptInput } from "../components/PromptInput";
import { DeleteConversationDialog } from "../components/DeleteConversationDialog";
import { Skeleton } from "@/components/ui/skeleton";

export function ChatPage() {
  const { selectedWorkspaceId } = useWorkspace();
  const { conversationId } = useParams<{ conversationId: string }>();
  const navigate = useNavigate();
  
  const [conversationToDelete, setConversationToDelete] = useState<Conversation | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Fallback if no workspace is selected
  if (!selectedWorkspaceId) {
    return <Navigate to="/" replace />;
  }

  const { 
    data: conversations, 
    isLoading: isLoadingList 
  } = useConversationList(selectedWorkspaceId);

  const { 
    data: activeConversation, 
    isLoading: isLoadingConversation 
  } = useConversation(conversationId || null);

  const createMutation = useCreateConversation(selectedWorkspaceId);
  const sendMutation = useSendMessage(conversationId || null);

  const handleCreateConversation = () => {
    createMutation.mutate(undefined, {
      onSuccess: (newConv) => {
        navigate(`/workspaces/${selectedWorkspaceId}/chat/${newConv.id}`);
      },
      onError: (error) => {
        toast.error("Failed to create conversation");
        console.error("Create conversation error", error);
      }
    });
  };

  const handleSendMessage = (content: string) => {
    sendMutation.mutate(content, {
      onError: (error) => {
        toast.error("Failed to send message");
        console.error("Send message error", error);
      }
    });
  };

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    if (activeConversation?.messages?.length) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [activeConversation?.messages]);

  return (
    <div className="flex h-[calc(100vh-theme(spacing.16))] -mx-8 -my-6 border-t">
      {/* Sidebar */}
      <ConversationSidebar
        workspaceId={selectedWorkspaceId}
        conversations={conversations || []}
        isLoading={isLoadingList}
        onCreateClick={handleCreateConversation}
        onDeleteClick={setConversationToDelete}
        isCreating={createMutation.isPending}
      />

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0 bg-background">
        {!conversationId ? (
          <EmptyConversationState 
            onCreateClick={handleCreateConversation} 
            isCreating={createMutation.isPending} 
          />
        ) : isLoadingConversation ? (
          <div className="flex-1 p-6 space-y-6 overflow-y-auto">
            <Skeleton className="h-20 w-3/4 rounded-xl" />
            <Skeleton className="h-20 w-3/4 rounded-xl ml-auto" />
            <Skeleton className="h-20 w-3/4 rounded-xl" />
          </div>
        ) : !activeConversation ? (
          <div className="flex-1 flex items-center justify-center text-muted-foreground p-4 text-center">
            Conversation not found or has been deleted.
          </div>
        ) : (
          <>
            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
              {activeConversation.messages?.length === 0 ? (
                <div className="flex h-full items-center justify-center text-center text-muted-foreground animate-in fade-in-50">
                  <div>
                    <p className="font-medium text-foreground">Conversation started</p>
                    <p className="text-sm mt-1">Send a message to begin the chat.</p>
                  </div>
                </div>
              ) : (
                activeConversation.messages?.map((msg) => (
                  <MessageBubble key={msg.id} message={msg} />
                ))
              )}
              {/* Invisible element to scroll to */}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 md:p-6 border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
              <div className="max-w-4xl mx-auto">
                <PromptInput 
                  onSend={handleSendMessage} 
                  isSending={sendMutation.isPending} 
                />
              </div>
            </div>
          </>
        )}
      </div>

      {/* Modals */}
      <DeleteConversationDialog
        conversation={conversationToDelete}
        open={!!conversationToDelete}
        onOpenChange={(open) => !open && setConversationToDelete(null)}
      />
    </div>
  );
}
