import { useNavigate, useParams } from "react-router-dom";
import { MessageSquare, Plus, Trash2 } from "lucide-react";
import { Conversation } from "../types";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

interface ConversationSidebarProps {
  workspaceId: string;
  conversations: Conversation[];
  isLoading: boolean;
  onCreateClick: () => void;
  onDeleteClick: (conversation: Conversation) => void;
  isCreating: boolean;
}

export function ConversationSidebar({
  workspaceId,
  conversations,
  isLoading,
  onCreateClick,
  onDeleteClick,
  isCreating,
}: ConversationSidebarProps) {
  const { conversationId } = useParams<{ conversationId: string }>();
  const navigate = useNavigate();

  return (
    <div className="w-64 border-r bg-muted/20 flex flex-col h-full">
      <div className="p-4 border-b">
        <Button 
          className="w-full justify-start" 
          onClick={onCreateClick}
          disabled={isCreating}
        >
          <Plus className="mr-2 h-4 w-4" />
          New Conversation
        </Button>
      </div>
      
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {isLoading ? (
          Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-10 w-full rounded-md" />
          ))
        ) : conversations.length === 0 ? (
          <div className="p-4 text-sm text-center text-muted-foreground">
            No conversations yet.
          </div>
        ) : (
          conversations.map((conv) => {
            const isActive = conversationId === conv.id;
            return (
              <div
                key={conv.id}
                className={cn(
                  "group flex items-center justify-between px-3 py-2 text-sm rounded-md cursor-pointer transition-colors",
                  isActive ? "bg-primary text-primary-foreground" : "hover:bg-muted"
                )}
                onClick={() => navigate(`/workspaces/${workspaceId}/chat/${conv.id}`)}
              >
                <div className="flex items-center truncate max-w-[150px]">
                  <MessageSquare className="mr-2 h-4 w-4 flex-shrink-0" />
                  <span className="truncate">{conv.title || "New Conversation"}</span>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className={cn(
                    "h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity",
                    isActive ? "text-primary-foreground hover:bg-primary/80 hover:text-primary-foreground" : "text-muted-foreground hover:text-destructive"
                  )}
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteClick(conv);
                  }}
                  title="Delete conversation"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
