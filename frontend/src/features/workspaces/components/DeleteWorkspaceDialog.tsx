import { toast } from "sonner";
import { useDeleteWorkspace } from "../hooks/useWorkspaces";
import { Workspace } from "../types";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

interface DeleteWorkspaceDialogProps {
  workspace: Workspace | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function DeleteWorkspaceDialog({ workspace, open, onOpenChange }: DeleteWorkspaceDialogProps) {
  const deleteMutation = useDeleteWorkspace();

  const onDelete = () => {
    if (!workspace) return;
    
    deleteMutation.mutate(workspace.id, {
      onSuccess: () => {
        toast.success("Workspace deleted");
        onOpenChange(false);
      },
      onError: (error) => {
        toast.error("Failed to delete workspace");
        console.error("Delete workspace error", error);
      },
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Delete Workspace</DialogTitle>
          <DialogDescription>
            Are you sure you want to delete the workspace "{workspace?.name}"? 
            This action cannot be undone. All documents and chats in this workspace will be permanently removed.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter className="mt-4">
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button 
            type="button" 
            variant="destructive" 
            onClick={onDelete}
            disabled={deleteMutation.isPending}
          >
            {deleteMutation.isPending ? "Deleting..." : "Delete Workspace"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
