import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { uploadDocumentSchema, UploadDocumentInput } from "../schemas";
import { useUploadDocument } from "../hooks/useDocuments";
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
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Upload } from "lucide-react";

interface UploadDocumentDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function UploadDocumentDialog({ open, onOpenChange }: UploadDocumentDialogProps) {
  const { selectedWorkspaceId } = useWorkspace();
  const uploadMutation = useUploadDocument(selectedWorkspaceId);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<UploadDocumentInput>({
    resolver: zodResolver(uploadDocumentSchema),
  });

  const onSubmit = (data: UploadDocumentInput) => {
    if (!selectedWorkspaceId) return;

    const file = data.file[0];
    
    uploadMutation.mutate(file, {
      onSuccess: () => {
        toast.success("Document uploaded successfully");
        onOpenChange(false);
        reset();
      },
      onError: (error) => {
        toast.error("Failed to upload document");
        console.error("Upload document error", error);
      },
    });
  };

  const handleOpenChange = (newOpen: boolean) => {
    if (!uploadMutation.isPending) {
      onOpenChange(newOpen);
      if (!newOpen) reset();
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <form onSubmit={handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Upload Document</DialogTitle>
            <DialogDescription>
              Upload a file to extract insights and enable semantic search.
              Supported formats: PDF, TXT, MD, DOCX.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-6">
            <div className="space-y-2">
              <Label htmlFor="file">Select File</Label>
              <Input
                id="file"
                type="file"
                disabled={uploadMutation.isPending}
                {...register("file")}
              />
              {errors.file && (
                <p className="text-sm text-destructive">{errors.file.message as string}</p>
              )}
            </div>
            
            {uploadMutation.isPending && (
              <div className="flex items-center justify-center p-4 text-sm text-muted-foreground flex-col gap-2">
                <Upload className="h-6 w-6 animate-bounce" />
                <p>Uploading document...</p>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button 
              type="button" 
              variant="outline" 
              onClick={() => handleOpenChange(false)}
              disabled={uploadMutation.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={uploadMutation.isPending}>
              Upload
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
