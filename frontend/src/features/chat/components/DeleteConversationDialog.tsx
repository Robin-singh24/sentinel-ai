import { toast } from "sonner";
import { useDeleteConversation } from "../hooks/useChat";
import { Conversation } from "../types";
import { useWorkspace } from "@/app/providers/WorkspaceProvider";
import { useNavigate, useParams } from "react-router-dom";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

interface DeleteConversationDialogProps {
  conversation: Conversation | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function DeleteConversationDialog({ conversation, open, onOpenChange }: DeleteConversationDialogProps) {
  const { selectedWorkspaceId } = useWorkspace();
  const { conversationId: activeConversationId } = useParams<{ conversationId: string }>();
  const navigate = useNavigate();
  
  const deleteMutation = useDeleteConversation(selectedWorkspaceId);

  const onDelete = () => {
    if (!conversation) return;
    
    deleteMutation.mutate(conversation.id, {
      onSuccess: () => {
        toast.success("Conversation deleted");
        
        // If we deleted the active conversation, route away
        if (conversation.id === activeConversationId) {
          navigate(`/workspaces/${selectedWorkspaceId}/chat`);
        }
        
        onOpenChange(false);
      },
      onError: (error) => {
        toast.error("Failed to delete conversation");
        console.error("Delete conversation error", error);
      },
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Delete Conversation</DialogTitle>
          <DialogDescription>
            Are you sure you want to delete "{conversation?.title || "this conversation"}"? 
            This will permanently remove the message history.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter className="mt-4">
          <Button 
            type="button" 
            variant="outline" 
            onClick={() => onOpenChange(false)}
            disabled={deleteMutation.isPending}
          >
            Cancel
          </Button>
          <Button 
            type="button" 
            variant="destructive" 
            onClick={onDelete}
            disabled={deleteMutation.isPending}
          >
            {deleteMutation.isPending ? "Deleting..." : "Delete Conversation"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
