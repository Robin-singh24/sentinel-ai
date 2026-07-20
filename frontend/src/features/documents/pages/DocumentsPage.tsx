import { useState } from "react";
import { useWorkspace } from "@/app/providers/WorkspaceProvider";
import { useDocumentList } from "../hooks/useDocuments";
import { Document } from "../types";
import { Navigate } from "react-router-dom";

import { DocumentToolbar } from "../components/DocumentToolbar";
import { DocumentTable } from "../components/DocumentTable";
import { EmptyDocumentsState } from "../components/EmptyDocumentsState";
import { UploadDocumentDialog } from "../components/UploadDocumentDialog";
import { DeleteDocumentDialog } from "../components/DeleteDocumentDialog";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";

export function DocumentsPage() {
  const { selectedWorkspaceId } = useWorkspace();
  const { data: documents, isLoading, isError, isFetching } = useDocumentList(selectedWorkspaceId);

  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [documentToDelete, setDocumentToDelete] = useState<Document | null>(null);

  // Fallback if no workspace is selected
  if (!selectedWorkspaceId) {
    return <Navigate to="/" replace />;
  }

  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px]">
        <h3 className="text-xl font-bold text-destructive">Failed to load documents</h3>
        <p className="text-muted-foreground mt-2">Please try refreshing the page.</p>
        <Button variant="outline" className="mt-4" onClick={() => window.location.reload()}>
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <DocumentToolbar 
        workspaceId={selectedWorkspaceId} 
        onUploadClick={() => setIsUploadOpen(true)}
        isFetching={isFetching}
      />

      {isLoading ? (
        <div className="space-y-4">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-20 w-full" />
        </div>
      ) : documents?.length === 0 ? (
        <EmptyDocumentsState />
      ) : (
        <DocumentTable 
          documents={documents || []} 
          onDelete={setDocumentToDelete} 
        />
      )}

      {/* Modals */}
      <UploadDocumentDialog 
        open={isUploadOpen} 
        onOpenChange={setIsUploadOpen} 
      />
      
      <DeleteDocumentDialog
        document={documentToDelete}
        open={!!documentToDelete}
        onOpenChange={(open) => !open && setDocumentToDelete(null)}
      />
    </div>
  );
}
