/**
 * Centralized storage abstraction for managing local storage access.
 * Do not use `window.localStorage` directly anywhere else in the application.
 */

const ACCESS_TOKEN_KEY = "sentinel_access_token";

export const storage = {
  getAccessToken: (): string | null => {
    return window.localStorage.getItem(ACCESS_TOKEN_KEY);
  },
  
  setAccessToken: (token: string): void => {
    window.localStorage.setItem(ACCESS_TOKEN_KEY, token);
  },
  
  removeAccessToken: (): void => {
    window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  },
};
