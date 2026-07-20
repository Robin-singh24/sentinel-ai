import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ProtectedLayout } from "@/app/layouts/ProtectedLayout";
import { AuthProvider } from "@/app/providers/AuthProvider";
import { authService } from "@/features/auth/services/auth.service";

vi.mock("@/features/auth/services/auth.service");
vi.mock("@/app/providers/WorkspaceProvider", () => ({
  useWorkspace: () => ({ selectedWorkspaceId: null })
}));

function TestSetup({ initialEntries = ["/"] }) {
  return (
    <AuthProvider>
      <MemoryRouter initialEntries={initialEntries}>
        <Routes>
          <Route path="/login" element={<div>Login Page</div>} />
          <Route element={<ProtectedLayout />}>
            <Route path="/" element={<div>Protected Dashboard</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </AuthProvider>
  );
}

describe("Protected Routes", () => {
  it("redirects unauthenticated users to /login", async () => {
    vi.mocked(authService.initialize).mockResolvedValue(null);

    render(<TestSetup />);

    // AuthProvider starts loading, then resolves to unauthenticated.
    // ProtectedLayout sees isAuthenticated=false and redirects to /login.
    await waitFor(() => {
      expect(screen.getByText("Login Page")).toBeInTheDocument();
    });
    // The protected dashboard should not be rendered
    expect(screen.queryByText("Protected Dashboard")).not.toBeInTheDocument();
  });

  it("renders protected content for authenticated users", async () => {
    const fakeUser = { id: "1", email: "test@example.com" } as any;
    vi.mocked(authService.initialize).mockResolvedValue(fakeUser);

    render(<TestSetup />);

    await waitFor(() => {
      expect(screen.getByText("Protected Dashboard")).toBeInTheDocument();
    });
    expect(screen.queryByText("Login Page")).not.toBeInTheDocument();
  });
});
