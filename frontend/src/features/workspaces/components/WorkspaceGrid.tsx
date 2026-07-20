import { Workspace } from "../types";
import { WorkspaceCard } from "./WorkspaceCard";
import { Skeleton } from "@/components/ui/skeleton";

interface WorkspaceGridProps {
  workspaces: Workspace[];
  isLoading: boolean;
  onRename: (workspace: Workspace) => void;
  onDelete: (workspace: Workspace) => void;
}

export function WorkspaceGrid({ workspaces, isLoading, onRename, onDelete }: WorkspaceGridProps) {
  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="space-y-3">
            <Skeleton className="h-[125px] w-full rounded-xl" />
          </div>
        ))}
      </div>
    );
  }

  if (workspaces.length === 0) {
    return (
      <div className="flex min-h-[400px] flex-col items-center justify-center rounded-md border border-dashed p-8 text-center animate-in fade-in-50">
        <h3 className="text-2xl font-semibold tracking-tight">No workspaces found</h3>
        <p className="text-sm text-muted-foreground mt-2">
          You don't have any workspaces yet. Create one to get started.
        </p>
      </div>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {workspaces.map((workspace) => (
        <WorkspaceCard
          key={workspace.id}
          workspace={workspace}
          onRename={onRename}
          onDelete={onDelete}
        />
      ))}
    </div>
  );
}
