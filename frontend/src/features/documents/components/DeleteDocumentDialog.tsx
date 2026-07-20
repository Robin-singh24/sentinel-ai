import { toast } from "sonner";
import { useDeleteDocument } from "../hooks/useDocuments";
import { Document } from "../types";
import { useWorkspace } from "@/app/providers/WorkspaceProvider";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

interface DeleteDocumentDialogProps {
  document: Document | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function DeleteDocumentDialog({ document, open, onOpenChange }: DeleteDocumentDialogProps) {
  const { selectedWorkspaceId } = useWorkspace();
  const deleteMutation = useDeleteDocument(selectedWorkspaceId);

  const onDelete = () => {
    if (!document) return;
    
    deleteMutation.mutate(document.id, {
      onSuccess: () => {
        toast.success("Document deleted");
        onOpenChange(false);
      },
      onError: (error) => {
        toast.error("Failed to delete document");
        console.error("Delete document error", error);
      },
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Delete Document</DialogTitle>
          <DialogDescription>
            Are you sure you want to delete "{document?.filename}"? 
            This action cannot be undone and will remove the file from this workspace permanently.
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
            {deleteMutation.isPending ? "Deleting..." : "Delete Document"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
