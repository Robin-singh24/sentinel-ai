import { MessageSquarePlus } from "lucide-react";
import { Button } from "@/components/ui/button";

interface EmptyConversationStateProps {
  onCreateClick: () => void;
  isCreating: boolean;
}

export function EmptyConversationState({ onCreateClick, isCreating }: EmptyConversationStateProps) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center p-8 text-center animate-in fade-in-50 h-full">
      <div className="bg-muted p-4 rounded-full mb-4">
        <MessageSquarePlus className="h-8 w-8 text-muted-foreground" />
      </div>
      <h3 className="text-2xl font-semibold tracking-tight">Select or Create a Conversation</h3>
      <p className="text-sm text-muted-foreground mt-2 max-w-md mb-6">
        Select an existing conversation from the sidebar or start a new one to chat with Sentinel AI about your workspace documents.
      </p>
      <Button onClick={onCreateClick} disabled={isCreating}>
        {isCreating ? "Creating..." : "Start New Conversation"}
      </Button>
    </div>
  );
}
