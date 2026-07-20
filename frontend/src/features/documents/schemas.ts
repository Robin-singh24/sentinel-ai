import { z } from "zod";

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const ACCEPTED_FILE_TYPES = [
  "application/pdf",
  "text/plain",
  "text/markdown",
  "application/msword",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document", // .docx
];

export const uploadDocumentSchema = z.object({
  file: z
    .any()
    .refine((fileList) => fileList && fileList.length > 0, "A file is required.")
    .refine((fileList) => fileList[0]?.size <= MAX_FILE_SIZE, "Max file size is 10MB.")
    .refine(
      (fileList) => ACCEPTED_FILE_TYPES.includes(fileList[0]?.type),
      "Only PDF, TXT, MD, and Word documents are supported."
    ),
});

export type UploadDocumentInput = z.infer<typeof uploadDocumentSchema>;
