import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";

import {
  clearStoredToken,
  fetchSession,
  getStoredToken,
  logout as apiLogout,
  storeToken,
} from "./api";
import type { AuthSession, AuthState } from "./types";

interface AuthContextValue extends AuthState {
  login: (token?: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshSession: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

interface AuthProviderProps {
  children: ReactNode;
  authMode: "local" | "oidc";
}

export function AuthProvider({ children, authMode }: AuthProviderProps) {
  const [state, setState] = useState<AuthState>({
    status: "loading",
    session: null,
    token: null,
  });

  const loadSession = useCallback(
    async (token?: string) => {
      try {
        const session = await fetchSession(token);
        setState({
          status: "authenticated",
          session,
          token: token ?? null,
        });
      } catch {
        setState({
          status: "unauthenticated",
          session: null,
          token: null,
        });
      }
    },
    [],
  );

  // Initial session load
  useEffect(() => {
    if (authMode === "local") {
      // Local mode — always authenticated, no token needed
      void loadSession();
      return;
    }

    // OIDC mode — check for stored token
    const storedToken = getStoredToken();
    if (storedToken) {
      void loadSession(storedToken);
    } else {
      setState({
        status: "unauthenticated",
        session: null,
        token: null,
      });
    }
  }, [authMode, loadSession]);

  const login = useCallback(
    async (token?: string) => {
      if (token) {
        storeToken(token);
      }
      await loadSession(token);
    },
    [loadSession],
  );

  const logout = useCallback(async () => {
    const currentToken = state.token;
    try {
      await apiLogout(currentToken ?? undefined);
    } catch {
      // Best-effort logout
    }
    clearStoredToken();
    setState({
      status: "unauthenticated",
      session: null,
      token: null,
    });
  }, [state.token]);

  const refreshSession = useCallback(async () => {
    await loadSession(state.token ?? undefined);
  }, [loadSession, state.token]);

  return (
    <AuthContext.Provider
      value={{ ...state, login, logout, refreshSession }}
    >
      {children}
    </AuthContext.Provider>
  );
}