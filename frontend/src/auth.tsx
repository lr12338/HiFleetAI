import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

import {
  fetchCurrentUser,
  loginWithPassword,
  type AuthUser,
  type LoginRequest,
} from './auth-client';

export const AUTH_TOKEN_STORAGE_KEY = 'hifleetai.access_token';

type AuthContextValue = {
  user: AuthUser | null;
  token: string | null;
  isInitializing: boolean;
  isLoggingIn: boolean;
  login: (payload: LoginRequest) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

function readStoredToken(): string | null {
  return window.localStorage.getItem(AUTH_TOKEN_STORAGE_KEY);
}

function writeStoredToken(accessToken: string): void {
  window.localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, accessToken);
}

function clearStoredToken(): void {
  window.localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => readStoredToken());
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  const logout = useCallback(() => {
    clearStoredToken();
    setToken(null);
    setUser(null);
    setIsInitializing(false);
  }, []);

  useEffect(() => {
    const storedToken = readStoredToken();

    if (!storedToken) {
      setToken(null);
      setUser(null);
      setIsInitializing(false);
      return;
    }

    let cancelled = false;
    setToken(storedToken);

    void fetchCurrentUser(storedToken)
      .then((nextUser) => {
        if (!cancelled) {
          setUser(nextUser);
        }
      })
      .catch(() => {
        if (!cancelled) {
          logout();
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsInitializing(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [logout]);

  const login = useCallback(async (payload: LoginRequest) => {
    setIsLoggingIn(true);

    try {
      const result = await loginWithPassword(payload);
      writeStoredToken(result.access_token);
      setToken(result.access_token);
      setUser(result.user);
    } finally {
      setIsLoggingIn(false);
      setIsInitializing(false);
    }
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      isInitializing,
      isLoggingIn,
      login,
      logout,
    }),
    [isInitializing, isLoggingIn, login, logout, token, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }

  return context;
}
