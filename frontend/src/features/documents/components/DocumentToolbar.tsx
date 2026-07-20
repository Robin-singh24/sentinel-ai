import { RefreshCw, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useQueryClient } from "@tanstack/react-query";
import { DOCUMENTS_QUERY_KEY } from "../hooks/useDocuments";

interface DocumentToolbarProps {
  workspaceId: string;
  onUploadClick: () => void;
  isFetching: boolean;
}

export function DocumentToolbar({ workspaceId, onUploadClick, isFetching }: DocumentToolbarProps) {
  const queryClient = useQueryClient();

  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: DOCUMENTS_QUERY_KEY(workspaceId) });
  };

  return (
    <div className="flex items-center justify-between">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Documents</h2>
        <p className="text-muted-foreground mt-1">
          Manage and process documents in this workspace.
        </p>
      </div>
      <div className="flex items-center gap-2">
        <Button 
          variant="outline" 
          size="icon"
          onClick={handleRefresh} 
          disabled={isFetching}
          title="Refresh documents"
        >
          <RefreshCw className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`} />
          <span className="sr-only">Refresh</span>
        </Button>
        <Button onClick={onUploadClick}>
          <Upload className="mr-2 h-4 w-4" />
          Upload Document
        </Button>
      </div>
    </div>
  );
}
