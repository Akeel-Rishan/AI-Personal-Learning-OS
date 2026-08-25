// Browser-safe authentication types and local access-token storage helpers.
export const ACCESS_TOKEN_KEY = "access_token";
export const AUTH_USER_KEY = "auth_user";

export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_verified?: boolean;
}

export interface AuthResponse {
  user: AuthUser;
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;
}

export interface CurrentUser extends AuthUser {
  profile: {
    preferred_explanation_style: string;
    daily_study_minutes: number;
    timezone: string;
    avatar_url: string | null;
  } | null;
}

function isAuthUser(value: unknown): value is AuthUser {
  if (typeof value !== "object" || value === null) return false;
  const candidate = value as Record<string, unknown>;
  return typeof candidate.id === "string"
    && typeof candidate.email === "string"
    && typeof candidate.full_name === "string"
    && typeof candidate.is_active === "boolean";
}

export function getAccessToken(): string | null {
  return typeof window === "undefined" ? null : window.localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getStoredUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  const serializedUser = window.localStorage.getItem(AUTH_USER_KEY);
  if (!serializedUser) return null;
  try {
    const parsedUser: unknown = JSON.parse(serializedUser);
    return isAuthUser(parsedUser) ? parsedUser : null;
  } catch {
    return null;
  }
}

export function storeAuth(accessToken: string, user: AuthUser): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  window.localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
}

export function clearStoredAuth(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(AUTH_USER_KEY);
}

