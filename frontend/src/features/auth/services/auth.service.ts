import { authApi } from "@/api/auth";
import { storage } from "@/lib/storage";
import { LoginCredentials, RegisterCredentials, User } from "../types";

export const authService = {
  /**
   * Initializes the session by attempting to fetch the current user 
   * if a token is present in storage.
   * Returns the user if successful, null otherwise.
   */
  initialize: async (): Promise<User | null> => {
    const token = storage.getAccessToken();
    if (!token) return null;

    try {
      return await authApi.getCurrentUser();
    } catch {
      // Interceptor handles removing the invalid token
      return null;
    }
  },

  login: async (credentials: LoginCredentials): Promise<User> => {
    const { access_token } = await authApi.login(credentials);
    storage.setAccessToken(access_token);
    return await authApi.getCurrentUser();
  },

  register: async (credentials: RegisterCredentials): Promise<User> => {
    const { access_token } = await authApi.register(credentials);
    storage.setAccessToken(access_token);
    return await authApi.getCurrentUser();
  },

  logout: async (): Promise<void> => {
    try {
      await authApi.logout();
    } finally {
      // Always clear the token even if the logout call fails (e.g. server down)
      storage.removeAccessToken();
    }
  },
};
