import { describe, it, expect, vi, beforeEach } from "vitest";
import { documentService } from "@/features/documents/services/document.service";
import { documentsApi } from "@/api/documents";

vi.mock("@/api/documents");

describe("DocumentService", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("delegates listDocuments to API", async () => {
    const fakeDocs = [{ id: "1", filename: "doc.txt" }] as any;
    vi.mocked(documentsApi.list).mockResolvedValue(fakeDocs);

    const result = await documentService.listDocuments("ws-1");
    expect(documentsApi.list).toHaveBeenCalledWith("ws-1");
    expect(result).toEqual(fakeDocs);
  });

  it("delegates getDocument to API", async () => {
    const fakeDoc = { id: "1", filename: "doc.txt" } as any;
    vi.mocked(documentsApi.get).mockResolvedValue(fakeDoc);

    const result = await documentService.getDocument("1");
    expect(documentsApi.get).toHaveBeenCalledWith("1");
    expect(result).toEqual(fakeDoc);
  });

  it("delegates uploadDocument to API", async () => {
    const fakeFile = new File(["content"], "doc.txt", { type: "text/plain" });
    const fakeDoc = { id: "1", filename: "doc.txt" } as any;
    vi.mocked(documentsApi.upload).mockResolvedValue(fakeDoc);

    const result = await documentService.uploadDocument("ws-1", fakeFile);
    expect(documentsApi.upload).toHaveBeenCalledWith("ws-1", fakeFile);
    expect(result).toEqual(fakeDoc);
  });

  it("delegates deleteDocument to API", async () => {
    vi.mocked(documentsApi.delete).mockResolvedValue(undefined);

    await documentService.deleteDocument("1");
    expect(documentsApi.delete).toHaveBeenCalledWith("1");
  });
});
