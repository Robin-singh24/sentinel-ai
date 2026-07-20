import { describe, it, expect } from "vitest";
import { uploadDocumentSchema } from "@/features/documents/schemas";

describe("Document Schemas", () => {
  it("rejects empty files", () => {
    const result = uploadDocumentSchema.safeParse({ file: [] });
    expect(result.success).toBe(false);
  });

  it("rejects file larger than 10MB", () => {
    const largeFile = new File([new ArrayBuffer(11 * 1024 * 1024)], "test.pdf", { type: "application/pdf" });
    const result = uploadDocumentSchema.safeParse({ file: [largeFile] });
    expect(result.success).toBe(false);
  });

  it("rejects unsupported file types", () => {
    const invalidFile = new File(["test"], "test.csv", { type: "text/csv" });
    const result = uploadDocumentSchema.safeParse({ file: [invalidFile] });
    expect(result.success).toBe(false);
  });

  it("accepts valid files", () => {
    const validFile = new File(["test"], "test.pdf", { type: "application/pdf" });
    const result = uploadDocumentSchema.safeParse({ file: [validFile] });
    expect(result.success).toBe(true);
  });
});
