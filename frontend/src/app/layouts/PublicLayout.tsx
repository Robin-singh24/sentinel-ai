import { Outlet, Navigate } from "react-router-dom";
import { useAuth } from "@/app/providers/AuthProvider";

export function PublicLayout() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <div className="flex h-screen w-full items-center justify-center">Loading...</div>;
  }

  if (isAuthenticated) {
    // If user is already authenticated, redirect them to the app
    return <Navigate to="/" replace />;
  }

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center">
      <Outlet />
    </div>
  );
}
