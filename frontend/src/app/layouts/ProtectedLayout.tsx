import { Link, Outlet, Navigate } from "react-router-dom";
import { useAuth } from "@/app/providers/AuthProvider";
import { useWorkspace } from "@/app/providers/WorkspaceProvider";
import { Button } from "@/components/ui/button";

export function ProtectedLayout() {
  const { isAuthenticated, isLoading, logout } = useAuth();
  const { selectedWorkspaceId } = useWorkspace();

  if (isLoading) {
    return <div className="flex h-screen w-full items-center justify-center">Loading...</div>;
  }

  if (!isAuthenticated) {
    // Redirect unauthenticated users to login page
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="flex min-h-screen w-full flex-col bg-muted/40">
      <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b bg-background px-4 md:px-6">
        <Link to="/" className="font-semibold text-lg mr-4">
          Sentinel AI
        </Link>
        <nav className="flex items-center gap-4 text-sm lg:gap-6 flex-1">
          <Link to="/" className="text-muted-foreground hover:text-foreground">
            Workspaces
          </Link>
          {selectedWorkspaceId && (
            <>
              <Link to="/documents" className="text-muted-foreground hover:text-foreground">
                Documents
              </Link>
              <Link to={`/workspaces/${selectedWorkspaceId}/chat`} className="text-muted-foreground hover:text-foreground">
                Chat
              </Link>
            </>
          )}
        </nav>
        <Button variant="ghost" onClick={logout}>
          Log out
        </Button>
      </header>
      <div className="flex flex-col sm:gap-4 sm:py-4">
        <main className="grid flex-1 items-start gap-4 p-4 sm:px-6 sm:py-0 md:gap-8 max-w-7xl mx-auto w-full">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
