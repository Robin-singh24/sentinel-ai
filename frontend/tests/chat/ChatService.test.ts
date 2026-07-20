import { describe, it, expect, vi, beforeEach } from "vitest";
import { chatService } from "@/features/chat/services/chat.service";
import { chatApi } from "@/api/chat";

vi.mock("@/api/chat");

describe("ChatService", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("delegates listConversations to API", async () => {
    const fakeConvs = [{ id: "1", title: "Test" }] as any;
    vi.mocked(chatApi.listConversations).mockResolvedValue(fakeConvs);

    const result = await chatService.listConversations("ws-1");
    expect(chatApi.listConversations).toHaveBeenCalledWith("ws-1");
    expect(result).toEqual(fakeConvs);
  });

  it("delegates createConversation to API", async () => {
    const fakeConv = { id: "1", title: "Test" } as any;
    vi.mocked(chatApi.createConversation).mockResolvedValue(fakeConv);

    const result = await chatService.createConversation("ws-1");
    expect(chatApi.createConversation).toHaveBeenCalledWith({ workspace_id: "ws-1" });
    expect(result).toEqual(fakeConv);
  });

  it("delegates sendMessage to API", async () => {
    const fakeResponse = { user_message: {}, assistant_message: {} } as any;
    vi.mocked(chatApi.sendMessage).mockResolvedValue(fakeResponse);

    const result = await chatService.sendMessage("conv-1", "hello");
    expect(chatApi.sendMessage).toHaveBeenCalledWith("conv-1", { content: "hello" });
    expect(result).toEqual(fakeResponse);
  });
});
