import { describe, it, expect, vi, beforeEach } from "vitest";
import { authService } from "@/features/auth/services/auth.service";
import { authApi } from "@/api/auth";
import { storage } from "@/lib/storage";

vi.mock("@/api/auth");
vi.mock("@/lib/storage");

describe("AuthService", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  describe("initialize", () => {
    it("returns null if no token is stored", async () => {
      vi.mocked(storage.getAccessToken).mockReturnValue(null);
      const result = await authService.initialize();
      expect(result).toBeNull();
      expect(authApi.getCurrentUser).not.toHaveBeenCalled();
    });

    it("returns user if token is valid", async () => {
      vi.mocked(storage.getAccessToken).mockReturnValue("fake-token");
      const fakeUser = { id: "1", email: "test@example.com" } as any;
      vi.mocked(authApi.getCurrentUser).mockResolvedValue(fakeUser);
      
      const result = await authService.initialize();
      expect(result).toEqual(fakeUser);
    });

    it("returns null on API failure", async () => {
      vi.mocked(storage.getAccessToken).mockReturnValue("fake-token");
      vi.mocked(authApi.getCurrentUser).mockRejectedValue(new Error("401"));
      
      const result = await authService.initialize();
      expect(result).toBeNull();
    });
  });

  describe("login", () => {
    it("stores token and fetches user", async () => {
      vi.mocked(authApi.login).mockResolvedValue({ access_token: "new-token", refresh_token: "ref" });
      const fakeUser = { id: "1", email: "test@example.com" } as any;
      vi.mocked(authApi.getCurrentUser).mockResolvedValue(fakeUser);

      const result = await authService.login({ email: "a@b.com", password: "123" });
      
      expect(storage.setAccessToken).toHaveBeenCalledWith("new-token");
      expect(result).toEqual(fakeUser);
    });
  });

  describe("logout", () => {
    it("calls api and always clears token", async () => {
      vi.mocked(authApi.logout).mockResolvedValue(undefined);
      
      await authService.logout();
      
      expect(authApi.logout).toHaveBeenCalled();
      expect(storage.removeAccessToken).toHaveBeenCalled();
    });

    it("clears token even if api throws", async () => {
      vi.mocked(authApi.logout).mockRejectedValue(new Error("Network Error"));
      
      await expect(authService.logout()).rejects.toThrow();
      expect(storage.removeAccessToken).toHaveBeenCalled();
    });
  });
});
