import { Routes, Route } from "react-router-dom";
import { ProtectedLayout } from "../layouts/ProtectedLayout";
import { PublicLayout } from "../layouts/PublicLayout";
import { LoginPage } from "@/features/auth/pages/LoginPage";
import { RegisterPage } from "@/features/auth/pages/RegisterPage";
import { WorkspaceDashboard } from "@/features/workspaces/pages/WorkspaceDashboard";
import { DocumentsPage } from "@/features/documents/pages/DocumentsPage";
import { ChatPage } from "@/features/chat/pages/ChatPage";
import { NotFound } from "@/pages/NotFound";

export function AppRouter() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route element={<PublicLayout />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Route>

      {/* Protected Routes */}
      <Route element={<ProtectedLayout />}>
        <Route path="/" element={<WorkspaceDashboard />} />
        <Route path="/documents" element={<DocumentsPage />} />
        <Route path="/workspaces/:workspaceId/chat" element={<ChatPage />} />
        <Route path="/workspaces/:workspaceId/chat/:conversationId" element={<ChatPage />} />
      </Route>

      {/* Catch-all 404 */}
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
