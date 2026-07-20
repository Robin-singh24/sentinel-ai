import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { AuthProvider, useAuth } from "@/app/providers/AuthProvider";
import { authService } from "@/features/auth/services/auth.service";

vi.mock("@/features/auth/services/auth.service");

function TestComponent() {
  const { isAuthenticated, isLoading, currentUser } = useAuth();
  if (isLoading) return <div>Loading...</div>;
  if (!isAuthenticated) return <div>Not Authenticated</div>;
  return <div>Welcome {currentUser?.email}</div>;
}

describe("AuthProvider", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("starts in loading state and resolves unauthenticated", async () => {
    vi.mocked(authService.initialize).mockResolvedValue(null);

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    // Initial state is loading
    expect(screen.getByText("Loading...")).toBeInTheDocument();

    // Resolves to not authenticated
    await waitFor(() => {
      expect(screen.getByText("Not Authenticated")).toBeInTheDocument();
    });
  });

  it("resolves authenticated when initialize succeeds", async () => {
    const fakeUser = { id: "1", email: "test@example.com" } as any;
    vi.mocked(authService.initialize).mockResolvedValue(fakeUser);

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByText("Welcome test@example.com")).toBeInTheDocument();
    });
  });
});
