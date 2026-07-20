import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { renameWorkspaceSchema, RenameWorkspaceInput } from "../schemas";
import { useUpdateWorkspace } from "../hooks/useWorkspaces";
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
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface RenameWorkspaceDialogProps {
  workspace: Workspace | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function RenameWorkspaceDialog({ workspace, open, onOpenChange }: RenameWorkspaceDialogProps) {
  const updateMutation = useUpdateWorkspace();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<RenameWorkspaceInput>({
    resolver: zodResolver(renameWorkspaceSchema),
    defaultValues: {
      name: workspace?.name || "",
    },
  });

  useEffect(() => {
    if (workspace && open) {
      reset({ name: workspace.name });
    }
  }, [workspace, open, reset]);

  const onSubmit = (data: RenameWorkspaceInput) => {
    if (!workspace) return;
    
    // Only submit if name changed
    if (data.name === workspace.name) {
      onOpenChange(false);
      return;
    }

    updateMutation.mutate(
      { id: workspace.id, data },
      {
        onSuccess: () => {
          toast.success("Workspace renamed successfully");
          onOpenChange(false);
        },
        onError: (error) => {
          toast.error("Failed to rename workspace");
          console.error("Rename workspace error", error);
        },
      }
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Rename Workspace</DialogTitle>
            <DialogDescription>
              Enter a new name for your workspace.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="rename-name">Workspace Name</Label>
              <Input
                id="rename-name"
                {...register("name")}
              />
              {errors.name && (
                <p className="text-sm text-destructive">{errors.name.message}</p>
              )}
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={updateMutation.isPending}>
              {updateMutation.isPending ? "Saving..." : "Save"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
