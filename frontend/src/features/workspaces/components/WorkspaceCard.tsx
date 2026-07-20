import { Workspace } from "../types";
import { useWorkspace } from "@/app/providers/WorkspaceProvider";
import { formatDistanceToNow } from "date-fns";
import { MoreVertical, Pencil, Trash2 } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";

import { useNavigate } from "react-router-dom";

interface WorkspaceCardProps {
  workspace: Workspace;
  onRename: (workspace: Workspace) => void;
  onDelete: (workspace: Workspace) => void;
}

export function WorkspaceCard({ workspace, onRename, onDelete }: WorkspaceCardProps) {
  const { selectedWorkspaceId, selectWorkspace } = useWorkspace();
  const navigate = useNavigate();
  const isSelected = selectedWorkspaceId === workspace.id;

  const handleSelect = () => {
    selectWorkspace(workspace.id);
    navigate("/documents");
  };

  return (
    <Card 
      className={`cursor-pointer transition-colors hover:bg-muted/50 ${isSelected ? 'ring-2 ring-primary' : ''}`}
      onClick={handleSelect}
    >
      <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
        <div className="space-y-1">
          <CardTitle className="text-xl">{workspace.name}</CardTitle>
          <CardDescription>
            Created {formatDistanceToNow(new Date(workspace.created_at), { addSuffix: true })}
          </CardDescription>
        </div>
        <div onClick={(e) => e.stopPropagation()}>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <MoreVertical className="h-4 w-4" />
                <span className="sr-only">Open menu</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onRename(workspace)}>
                <Pencil className="mr-2 h-4 w-4" />
                Rename
              </DropdownMenuItem>
              <DropdownMenuItem 
                onClick={() => onDelete(workspace)}
                className="text-destructive focus:bg-destructive focus:text-destructive-foreground"
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardHeader>
      <CardContent>
        {/* Additional workspace stats or context could go here */}
      </CardContent>
    </Card>
  );
}
