import { describe, it, expect, vi, beforeEach } from "vitest";
import { workspaceService } from "@/features/workspaces/services/workspace.service";
import { workspacesApi } from "@/api/workspaces";

vi.mock("@/api/workspaces");

describe("WorkspaceService", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("delegates listWorkspaces to API", async () => {
    const fakeWorkspaces = [{ id: "1", name: "Ws 1" }] as any;
    vi.mocked(workspacesApi.list).mockResolvedValue(fakeWorkspaces);

    const result = await workspaceService.listWorkspaces();
    expect(workspacesApi.list).toHaveBeenCalled();
    expect(result).toEqual(fakeWorkspaces);
  });

  it("delegates createWorkspace to API", async () => {
    const fakeWorkspace = { id: "1", name: "Ws 1" } as any;
    vi.mocked(workspacesApi.create).mockResolvedValue(fakeWorkspace);

    const result = await workspaceService.createWorkspace({ name: "Ws 1" });
    expect(workspacesApi.create).toHaveBeenCalledWith({ name: "Ws 1" });
    expect(result).toEqual(fakeWorkspace);
  });

  it("delegates updateWorkspace to API", async () => {
    const fakeWorkspace = { id: "1", name: "New Name" } as any;
    vi.mocked(workspacesApi.update).mockResolvedValue(fakeWorkspace);

    const result = await workspaceService.updateWorkspace("1", { name: "New Name" });
    expect(workspacesApi.update).toHaveBeenCalledWith("1", { name: "New Name" });
    expect(result).toEqual(fakeWorkspace);
  });

  it("delegates deleteWorkspace to API", async () => {
    vi.mocked(workspacesApi.delete).mockResolvedValue(undefined);

    await workspaceService.deleteWorkspace("1");
    expect(workspacesApi.delete).toHaveBeenCalledWith("1");
  });
});
