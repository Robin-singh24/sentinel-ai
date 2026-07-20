import { useState } from "react";
import { useWorkspaceList } from "../hooks/useWorkspaces";
import { Workspace } from "../types";

import { WorkspaceGrid } from "../components/WorkspaceGrid";
import { CreateWorkspaceDialog } from "../components/CreateWorkspaceDialog";
import { RenameWorkspaceDialog } from "../components/RenameWorkspaceDialog";
import { DeleteWorkspaceDialog } from "../components/DeleteWorkspaceDialog";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";
import { useAuth } from "@/app/providers/AuthProvider";

export function WorkspaceDashboard() {
  const { data: workspaces, isLoading, isError } = useWorkspaceList();
  const { logout } = useAuth();

  const [workspaceToRename, setWorkspaceToRename] = useState<Workspace | null>(null);
  const [workspaceToDelete, setWorkspaceToDelete] = useState<Workspace | null>(null);

  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px]">
        <h3 className="text-xl font-bold text-destructive">Failed to load workspaces</h3>
        <p className="text-muted-foreground mt-2">Please try refreshing the page.</p>
        <Button variant="outline" className="mt-4" onClick={() => window.location.reload()}>
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Workspaces</h2>
          <p className="text-muted-foreground mt-1">
            Manage your workspaces and context boundaries.
          </p>
        </div>
        <div className="flex gap-2">
          <CreateWorkspaceDialog>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              New Workspace
            </Button>
          </CreateWorkspaceDialog>
          <Button variant="outline" onClick={() => logout()}>
            Logout
          </Button>
        </div>
      </div>

      <WorkspaceGrid
        workspaces={workspaces || []}
        isLoading={isLoading}
        onRename={setWorkspaceToRename}
        onDelete={setWorkspaceToDelete}
      />

      {/* Modals */}
      <RenameWorkspaceDialog
        workspace={workspaceToRename}
        open={!!workspaceToRename}
        onOpenChange={(open) => !open && setWorkspaceToRename(null)}
      />
      
      <DeleteWorkspaceDialog
        workspace={workspaceToDelete}
        open={!!workspaceToDelete}
        onOpenChange={(open) => !open && setWorkspaceToDelete(null)}
      />
    </div>
  );
}
