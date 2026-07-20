import { createContext, useContext, useState, ReactNode, useEffect, useCallback } from "react";
import { User, LoginCredentials, RegisterCredentials } from "@/features/auth/types";
import { authService } from "@/features/auth/services/auth.service";

interface AuthState {
  currentUser: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

interface AuthContextValue extends AuthState {
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (credentials: RegisterCredentials) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    currentUser: null,
    isAuthenticated: false,
    isLoading: true,
  });

  const initialize = useCallback(async () => {
    try {
      const user = await authService.initialize();
      setState({
        currentUser: user,
        isAuthenticated: !!user,
        isLoading: false,
      });
    } catch {
      setState({
        currentUser: null,
        isAuthenticated: false,
        isLoading: false,
      });
    }
  }, []);

  useEffect(() => {
    initialize();
  }, [initialize]);

  const login = async (credentials: LoginCredentials) => {
    const user = await authService.login(credentials);
    setState({
      currentUser: user,
      isAuthenticated: true,
      isLoading: false,
    });
  };

  const register = async (credentials: RegisterCredentials) => {
    const user = await authService.register(credentials);
    setState({
      currentUser: user,
      isAuthenticated: true,
      isLoading: false,
    });
  };

  const logout = async () => {
    await authService.logout();
    setState({
      currentUser: null,
      isAuthenticated: false,
      isLoading: false,
    });
  };

  // We don't block render based on loading, we pass isLoading so the app or layouts can decide
  return (
    <AuthContext.Provider value={{ ...state, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
