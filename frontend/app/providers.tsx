// Client-side authentication context and persisted session restoration.
"use client";

import { createContext, useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { apiGet, apiPost } from "@/lib/api";
import {
  type AuthResponse,
  type AuthUser,
  type CurrentUser,
  clearStoredAuth,
  getAccessToken,
  getStoredUser,
  storeAuth,
} from "@/lib/auth";

export interface AuthContextType {
  user: AuthUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (fullName: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }): JSX.Element {
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    async function restoreSession(): Promise<void> {
      const token = getAccessToken();
      const cachedUser = getStoredUser();
      if (!token || !cachedUser) {
        clearStoredAuth();
        if (isMounted) setIsLoading(false);
        return;
      }
      try {
        const verifiedUser = await apiGet<CurrentUser>("/api/v1/auth/me");
        if (isMounted) {
          setUser(verifiedUser);
          storeAuth(token, verifiedUser);
        }
      } catch {
        clearStoredAuth();
        if (isMounted) setUser(null);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }

    void restoreSession();
    return () => {
      isMounted = false;
    };
  }, []);

  const login = useCallback(async (email: string, password: string): Promise<void> => {
    try {
      const result = await apiPost<AuthResponse>("/api/v1/auth/login", { email, password });
      storeAuth(result.access_token, result.user);
      setUser(result.user);
    } catch (error: unknown) {
      clearStoredAuth();
      setUser(null);
      throw error;
    }
  }, []);

  const register = useCallback(async (
    fullName: string,
    email: string,
    password: string,
  ): Promise<void> => {
    try {
      const result = await apiPost<AuthResponse>("/api/v1/auth/register", {
        full_name: fullName,
        email,
        password,
      });
      storeAuth(result.access_token, result.user);
      setUser(result.user);
    } catch (error: unknown) {
      clearStoredAuth();
      setUser(null);
      throw error;
    }
  }, []);

  const logout = useCallback(async (): Promise<void> => {
    try {
      await apiPost<{ message: string }>("/api/v1/auth/logout", {});
    } catch {
      // Local credentials are still removed if the backend is unavailable.
    } finally {
      clearStoredAuth();
      setUser(null);
      router.replace("/login");
    }
  }, [router]);

  const value = useMemo<AuthContextType>(() => ({
    user,
    isLoading,
    isAuthenticated: user !== null,
    login,
    register,
    logout,
  }), [isLoading, login, logout, register, user]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

