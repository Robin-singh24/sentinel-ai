import { apiClient } from "./client";
import { 
  LoginCredentials, 
  RegisterCredentials, 
  User, 
  TokenResponse, 
  SuccessResponse 
} from "@/features/auth/types";

export const authApi = {
  login: async (credentials: LoginCredentials): Promise<TokenResponse> => {
    const { data } = await apiClient.post<SuccessResponse<TokenResponse>>(
      "/auth/login",
      credentials
    );
    return data.data;
  },

  register: async (credentials: RegisterCredentials): Promise<TokenResponse> => {
    const { data } = await apiClient.post<SuccessResponse<TokenResponse>>(
      "/auth/register",
      credentials
    );
    return data.data;
  },

  logout: async (): Promise<void> => {
    await apiClient.post("/auth/logout");
  },

  getCurrentUser: async (): Promise<User> => {
    const { data } = await apiClient.get<SuccessResponse<User>>("/auth/me");
    return data.data;
  },
};
