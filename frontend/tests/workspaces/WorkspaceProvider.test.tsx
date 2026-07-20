import { render, screen, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { WorkspaceProvider, useWorkspace } from "@/app/providers/WorkspaceProvider";
import * as useWorkspacesHook from "@/features/workspaces/hooks/useWorkspaces";

vi.mock("@/features/workspaces/hooks/useWorkspaces");

function TestComponent() {
  const { selectedWorkspaceId, selectWorkspace, clearWorkspace } = useWorkspace();
  return (
    <div>
      <div data-testid="selected-id">{selectedWorkspaceId || "none"}</div>
      <button onClick={() => selectWorkspace("ws-1")}>Select 1</button>
      <button onClick={() => clearWorkspace()}>Clear</button>
    </div>
  );
}

describe("WorkspaceProvider", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    localStorage.clear();
  });

  it("initializes from local storage", () => {
    localStorage.setItem("sentinel_selected_workspace_id", "ws-initial");
    vi.mocked(useWorkspacesHook.useWorkspaceList).mockReturnValue({
      data: undefined,
      isSuccess: false,
    } as any);

    render(
      <WorkspaceProvider>
        <TestComponent />
      </WorkspaceProvider>
    );

    expect(screen.getByTestId("selected-id")).toHaveTextContent("ws-initial");
  });

  it("updates local storage when a workspace is selected", () => {
    vi.mocked(useWorkspacesHook.useWorkspaceList).mockReturnValue({
      data: undefined,
      isSuccess: false,
    } as any);

    render(
      <WorkspaceProvider>
        <TestComponent />
      </WorkspaceProvider>
    );

    act(() => {
      screen.getByText("Select 1").click();
    });

    expect(screen.getByTestId("selected-id")).toHaveTextContent("ws-1");
    expect(localStorage.getItem("sentinel_selected_workspace_id")).toBe("ws-1");
  });

  it("clears selection if workspace is deleted from server list", () => {
    localStorage.setItem("sentinel_selected_workspace_id", "deleted-ws");
    
    // Simulate successful fetch where "deleted-ws" is missing
    vi.mocked(useWorkspacesHook.useWorkspaceList).mockReturnValue({
      data: [{ id: "other-ws" }],
      isSuccess: true,
    } as any);

    render(
      <WorkspaceProvider>
        <TestComponent />
      </WorkspaceProvider>
    );

    // The effect runs and clears the workspace because "deleted-ws" isn't in data
    expect(screen.getByTestId("selected-id")).toHaveTextContent("none");
    expect(localStorage.getItem("sentinel_selected_workspace_id")).toBeNull();
  });

  it("keeps selection if workspace exists in server list", () => {
    localStorage.setItem("sentinel_selected_workspace_id", "active-ws");
    
    vi.mocked(useWorkspacesHook.useWorkspaceList).mockReturnValue({
      data: [{ id: "active-ws" }],
      isSuccess: true,
    } as any);

    render(
      <WorkspaceProvider>
        <TestComponent />
      </WorkspaceProvider>
    );

    expect(screen.getByTestId("selected-id")).toHaveTextContent("active-ws");
    expect(localStorage.getItem("sentinel_selected_workspace_id")).toBe("active-ws");
  });
});
