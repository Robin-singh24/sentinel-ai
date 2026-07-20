import { Workspace } from "../types";
import { useWorkspaceList } from "../hooks/useWorkspaces";
import { useWorkspace } from "@/app/providers/WorkspaceProvider";
import { Check, ChevronsUpDown } from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Skeleton } from "@/components/ui/skeleton";

export function WorkspaceSelector() {
  const { data: workspaces, isLoading } = useWorkspaceList();
  const { selectedWorkspaceId, selectWorkspace } = useWorkspace();

  if (isLoading) {
    return <Skeleton className="h-9 w-[200px]" />;
  }

  if (!workspaces || workspaces.length === 0) {
    return null; // Don't render selector if no workspaces
  }

  const selectedWorkspace = workspaces.find((w) => w.id === selectedWorkspaceId) || workspaces[0];

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          className="w-[200px] justify-between truncate"
        >
          {selectedWorkspace?.name || "Select workspace..."}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-[200px] p-0">
        {workspaces.map((workspace) => (
          <DropdownMenuItem
            key={workspace.id}
            onSelect={() => selectWorkspace(workspace.id)}
            className="cursor-pointer"
          >
            <Check
              className={cn(
                "mr-2 h-4 w-4",
                selectedWorkspaceId === workspace.id ? "opacity-100" : "opacity-0"
              )}
            />
            {workspace.name}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
